import logging
from threading import Lock
from spacewiki_io import model, routes
from flask import current_app, session, request, render_template, url_for
from flask.globals import _request_ctx_stack
from flask_login import current_user, login_user
import peewee
import spacewiki.app
import spacewiki.model
import spacewiki.auth
import io_wrapper, deadspace, app, signin
from raven.contrib.flask import Sentry

logger = logging.getLogger('dispatcher')

def make_wiki_app(space):
    space_app = spacewiki.app.create_app()
    space_app.secret_key = current_app.secret_key
    sentry_dsn = current_app.config.get('SENTRY_DSN', None)
    if sentry_dsn is not None:
        space_app.config['SENTRY_DSN'] = current_app.config['SENTRY_DSN']
    space_app.config['SLACK_KEY']  = current_app.config['SLACK_KEY']
    space_app.config['DATABASE_URL'] = space.db_url
    space_app.config['SITE_NAME'] = space.domain
    space_app.config['UPLOAD_PATH'] = '/srv/spacewiki/uploads/%s'%(space.domain)
    space_app.config['ASSETS_CACHE'] = '/tmp/'
    sentry = Sentry(space_app)
    space_app.register_blueprint(io_wrapper.BLUEPRINT)
    space_app.logger.setLevel(logging.DEBUG)
    space.make_space_database()
    with space_app.app_context():
        spacewiki.model.syncdb()
    return space_app

class SubdomainDispatcher(object):
    def __init__(self, domain):
        self.domain = domain
        self.lock = Lock()
        self.instances = {}
        self.default_app = app.create_app()
        self.deadspace_app = app.create_app()
        self.deadspace_app.register_blueprint(deadspace.BLUEPRINT)

    def get_application(self, host):
        logger.debug("Got request for %s while serving %s", host, self.domain)
        host = host.split(':')[0]

        if not host.endswith(self.domain):
            return self.default_app

        subdomain = host[:-len(self.domain)].rstrip('.')

        if subdomain == '':
            return self.default_app

        with self.default_app.app_context():
            model.get_db()
            try:
                space = model.Space.get(domain=subdomain)
            except peewee.DoesNotExist:
                return self.deadspace_app

            with self.lock:
                app = self.instances.get(subdomain)
                if app is None:
                    logger.info("Booting new application for %s", host)
                    app = make_wiki_app(space)
                    self.instances[subdomain] = app
                return app

    def __call__(self, environ, start_response):
        app = self.get_application(environ['HTTP_HOST'])
        return app(environ, start_response)
