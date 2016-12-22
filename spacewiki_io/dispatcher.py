import logging
from threading import Lock
from spacewiki_io import model, routes
from playhouse.db_url import parse as parse_db_url
import psycopg2
from flask import current_app, session, request, render_template, url_for, \
    Config, g
from flask.globals import _request_ctx_stack
from flask_login import current_user, login_user
import peewee
import spacewiki.app
import spacewiki.model
import spacewiki.auth
import io_wrapper, deadspace, app, signin, io_common
from werkzeug import LocalStack, LocalProxy
from raven.contrib.flask import Sentry
from contextlib import contextmanager

logger = logging.getLogger('dispatcher')

local_dispatcher = LocalStack()
current_dispatcher = local_dispatcher()

class SubspaceConfig(Config):
    def __init__(self, space, template):
        super(Config, self).__init__()
        self._template = template
        self._replacements = {
            'slack_id': space.slack_team_id.lower(),
            'domain': space.domain
        }
        self['SLACK_TOKEN'] = space.slack_access_token
        self['SLACK_ID'] = space.slack_team_id.lower()
        self['SITE_NAME'] = space.domain
        self['ASSETS_CACHE'] = '/tmp/'

    def __missing__(self, key):
        subkey = 'SUBSPACE_'+key
        ret = self._template['SUBSPACE_'+key]
        ret = ret % self._replacements
        # Make sure we skip __missing__ next time
        self[key] = ret
        return ret

class Dispatcher(object):

    def __init__(self, default_app=None):
        self.lock = Lock()
        self.instances = {}
        if default_app is None:
            self.default_app = app.create_app()
        else:
            self.default_app = default_app
        self.deadspace_app = app.create_deadspace_app()
        self.domain = self.default_app.config['IO_DOMAIN']

    def get_wiki_app(self, space, create_db=True):
        with self.lock:
            space_app = self.instances.get(space.domain)

            if space_app is not None:
                return space_app

            logger.info("Booting new application for %s", space.slack_team_id)
            space_app = spacewiki.app.create_app()
            self.instances[space.domain] = space_app

        # Configure
        del space_app.config['DATABASE_URL']
        conf = SubspaceConfig(space, self.default_app.config)
        conf.from_mapping(**space_app.config)
        space_app.config = conf
        space_app.secret_key = self.default_app.secret_key
        space_app.logger.setLevel(logging.DEBUG)

        # Setup crash reporting
        sentry = Sentry(space_app)

        # Install hooks
        space_app.register_blueprint(io_wrapper.BLUEPRINT)
        space_app.register_blueprint(io_common.BLUEPRINT)

        # Boot database
        if create_db:
            db_name = space_app.config['DATABASE_NAME']
            self.create_database(db_name)
        with space_app.app_context():
            spacewiki.model.syncdb()
        return space_app

    def create_database(self, db_name):
        parsed = parse_db_url(self.default_app.config['ADMIN_DB_URL'])
        db_string = 'dbname=%s'%(parsed['database'])
        if 'host' in parsed:
            db_string += ' host='+parsed['host']
        if 'user' in parsed:
            db_string += ' user='+parsed['user']
        if 'password' in parsed:
            db_string += ' password='+parsed['password']
        db = psycopg2.connect(db_string)
        db.autocommit = True
        cur = db.cursor()
        try:
            cur.execute("CREATE DATABASE %s" % db_name)
            current_app.logger.info("Created new database for team %s", self)
        except psycopg2.ProgrammingError:
            current_app.logger.debug("Team %s already has a database.", self)

    def get_application(self, host):
        domain = self.default_app.config['IO_DOMAIN']
        logger.debug("Got request for %s while serving %s", host, domain)
        host = host.split(':')[0]

        if not host.endswith(domain):
            return self.default_app

        subdomain = host[:-len(domain)].rstrip('.')

        if subdomain == '':
            return self.default_app

        with self.default_app.app_context():
            model.get_db()
            try:
                space = model.Space.get(domain=subdomain)
            except peewee.DoesNotExist:
                return self.deadspace_app

            return self.get_wiki_app(space)

    def login_slack_id(self, slack_id):
        try:
            identity = spacewiki.model.Identity.get(spacewiki.model.Identity.auth_id == slack_id,
                    spacewiki.model.Identity.auth_type == 'slack')
        except:
            identity = spacewiki.model.Identity.create(
                    auth_id=slack_id,
                    auth_type='slack',
                    display_name='',
                    handle=slack_id
            )
        session['_spacewikiio_auth_id'] = slack_id
        return identity

    def login_from_user_slacker(self, slacker):
        user_id = slacker.api.get('users.identity').body
        #handle = slacker.api.get('auth.test').body['user']
        slack_id = user_id['user']['id']
        display_name = user_id['user']['name']
        space = model.Space.from_user_slacker(slacker)
        space_app = current_dispatcher.get_wiki_app(space)
        with space_app.app_context():
            user_id = self.login_slack_id(slack_id)
            user_id.display_name = display_name
            #user_id.handle = handle
            user_id.save()

    @contextmanager
    def dispatch_context(self):
        local_dispatcher.push(self)
        yield
        local_dispatcher.pop()

    def __call__(self, environ, start_response):
        with self.dispatch_context():
            app = self.get_application(environ['HTTP_HOST'])
            return app(environ, start_response)
