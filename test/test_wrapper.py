from flask import Flask, request, session
import hypothesis
import hypothesis.strategies as st
import unittest
from spacewiki_io import io_wrapper, io_common, dispatcher, app
from flask_testing import TestCase
import spacewiki.app
import spacewiki.model
from flask_login import current_user
import tempfile

class WrapperTestCase(TestCase):
    def create_app(self):
        ret = spacewiki.app.create_app(False)
        tmp_dir = tempfile.mkdtemp()
        ret.config['DATABASE_URL'] = 'sqlite:///%s/space.sqlite3'%(tmp_dir)
        ret.config['SECRET_KEY'] = 'foo'
        ret.register_blueprint(io_wrapper.BLUEPRINT)
        ret.register_blueprint(io_common.BLUEPRINT)
        with ret.app_context():
            spacewiki.model.syncdb()
        return ret

    def setUp(self):
        self.client = self.app.test_client()
        dispatch_app = app.create_app(False)
        dispatch_app.config['IO_DOMAIN'] = 'localhost'
        dispatch_app.config['IO_SCHEME'] = 'http'
        dispatch_app.config['SECRET_KEY'] = 'foo'
        self.dispatcher = dispatcher.Dispatcher(dispatch_app)

    def test_template_vars(self):
        with self.dispatcher.dispatch_context():
            with self.app.test_client() as client:
                client.get('/')
                self.assertEqual(self.get_context_variable('dispatcher_settings'),
                        self.dispatcher.default_app.config)

    @hypothesis.given(st.text(min_size=5))
    def test_cross_domain_login(self, auth_id):
        with self.app.app_context():
            login_user,_ = spacewiki.model.Identity.get_or_create(auth_id=auth_id,
                    auth_type='slack',
                    display_name='',
                    handle='')
        with self.dispatcher.dispatch_context():
            with self.app.test_client() as client:
                with client.session_transaction() as sess:
                    sess['_spacewikiio_auth_id'] = auth_id
                self.assertEqual(client.get('/').status_code, 200)
                self.assertNotEqual(current_user, None)
                self.assertEqual(current_user, login_user)
                self.assertTrue(current_user.is_authenticated)
                self.assertFalse(current_user.is_anonymous)
                self.assertTrue('_spacewikiio_auth_id' not in session)

    @hypothesis.given(st.text(min_size=5))
    def test_invalid_login(self, auth_id):
        with self.dispatcher.dispatch_context():
            with self.app.test_client() as client:
                with client.session_transaction() as sess:
                    sess['_spacewikiio_auth_id'] = auth_id
                self.assertEqual(client.get('/').status_code, 403)
                self.assertNotEqual(client.get('/static/cache/spacewiki-io-app.css').status_code,
                        403)
                self.assertFalse(current_user.is_authenticated)
                self.assertTrue(current_user.is_anonymous)
                self.assertTrue('_spacewikiio_auth_id' not in session)

    def test_anon_login(self):
        with self.dispatcher.dispatch_context():
            with self.app.test_client() as client:
                self.assertEqual(client.get('/').status_code, 403)
                self.assertNotEqual(client.get('/static/cache/spacewiki-io-app.css').status_code,
                        403)
                self.assertNotEqual(current_user, None)
                self.assertFalse(current_user.is_authenticated)
                self.assertTrue(current_user.is_anonymous)
                self.assertTrue('_spacewikiio_auth_id' not in session)
