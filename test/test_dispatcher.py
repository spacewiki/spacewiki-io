import unittest
import hypothesis
import hypothesis.strategies as st
from spacewiki_io import dispatcher, model, app, settings
import tempfile
import string

TeamID = st.text(string.ascii_lowercase, min_size=5)
TeamDomain = st.text(string.ascii_lowercase + '-_', min_size=5)
ConfigTemplate = st.dictionaries(st.text(string.ascii_uppercase, min_size=1),
        st.text(string.ascii_uppercase))

class SubspaceTestCase(unittest.TestCase):
    def setUp(self):
        self._app = app.create_app(False)
        self._app.config['ADMIN_DB_URL'] = 'sqlite:///:memory:'
        self._app.config['SECRET_KEY'] = 'foo'
        self._app.config['SUBSPACE_SECRET_KEY'] = 'foo'
        with self._app.app_context():
            model.ADMIN_DATABASE.create_tables([model.Space])

    @hypothesis.given(TeamID, ConfigTemplate, ConfigTemplate, ConfigTemplate)
    def test_inheritance(self, team_id, template, subspaceTemplate, siteConfig):
        merged_template = {}
        merged_template.update(template)
        for k, v in subspaceTemplate.iteritems():
            merged_template['SUBSPACE_'+k] = v
        space = model.Space(slack_team_id=team_id)
        conf = dispatcher.SubspaceConfig(space, merged_template)
        conf.from_mapping(**siteConfig)

        with self._app.app_context():
            for k, v in template.iteritems():
                if k in subspaceTemplate or k in siteConfig:
                    continue
                with self.assertRaises(KeyError):
                    conf[k]

            for k, v in subspaceTemplate.iteritems():
                if k in siteConfig:
                    continue
                self.assertEqual(conf[k], subspaceTemplate[k])

            for k, v in siteConfig.iteritems():
                self.assertEqual(conf[k], siteConfig[k])
        
    @hypothesis.given(TeamID, TeamDomain)
    def test_replacements(self, team_id, domain):
        space = model.Space(slack_team_id=team_id, domain=domain)
        template = {'SUBSPACE_DOMAIN': '%(domain)s', 'SUBSPACE_ID':
        '%(slack_id)s'}
        conf = dispatcher.SubspaceConfig(space, template)
        with self._app.app_context():
            self.assertEqual(conf['DOMAIN'], domain)
            self.assertEqual(conf['ID'], team_id)

class DispatcherTestCase(unittest.TestCase):
    def setUp(self):
        self._app = app.create_app(False)
        tmp_dir = tempfile.mkdtemp()
        self._app.config['ADMIN_DB_URL'] = 'sqlite:///%s/admin.sqlite3'%(tmp_dir)
        self._app.config['SUBSPACE_DATABASE_URL'] = 'sqlite:///%s/'%(tmp_dir) + '%(slack_id)s.sqlite3'
        self._app.config['SECRET_KEY'] = 'foo'
        self._app.config['SUBSPACE_SECRET_KEY'] = 'foo'
        with self._app.app_context():
            model.ADMIN_DATABASE.create_tables([model.Space], True)
        self.dispatcher = dispatcher.Dispatcher()
        self.dispatcher.default_app = self._app

    @hypothesis.given(TeamID, TeamDomain)
    def test_app_config(self, team_id, domain):
        space = model.Space(slack_team_id=team_id, domain=domain)
        with self._app.app_context():
            space_app = self.dispatcher.get_wiki_app(space, False)

    @hypothesis.given(TeamID, TeamDomain, TeamDomain)
    def test_subdomain(self, team_id, domain, io_domain):
        self._app.config['IO_DOMAIN'] = io_domain
        with self._app.app_context():
            space = model.Space.create(slack_team_id=team_id, domain=domain)
            space_app = self.dispatcher.get_wiki_app(space, False)
            subdomain_app = self.dispatcher.get_application(space.domain+'.'+io_domain)
            self.assertEqual(space_app, subdomain_app)

            subdomain_client = subdomain_app.test_client()
            resp = subdomain_client.get('/')
            self.assertEqual(resp.status_code, 403)

    @hypothesis.given(TeamDomain, TeamDomain)
    def test_dead_space(self, domain, io_domain):
        self._app.config['IO_DOMAIN'] = io_domain
        with self._app.app_context():
            subdomain_app = self.dispatcher.get_application(domain+'.'+io_domain)
            self.assertNotEqual(subdomain_app, self.dispatcher.default_app)
            self.assertEqual(subdomain_app, self.dispatcher.deadspace_app)

            subdomain_client = subdomain_app.test_client()
            self.assertEqual(subdomain_client.get('/').status_code, 404)
            self.assertEqual(subdomain_client.get('/static/cache/spacewiki-io-app.css').status_code, 200)
