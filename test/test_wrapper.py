from flask import Flask, request, session
import hypothesis
import hypothesis.strategies as st
import unittest
from spacewiki_io import io_wrapper, io_common, dispatcher
from spacewiki import app, model
from flask_login import current_user
import tempfile

class WrapperTestCase(unittest.TestCase):
    def setUp(self):
        self.app = app.create_app(False)
        tmp_dir = tempfile.mkdtemp()
        self.app.config['DATABASE_URL'] = 'sqlite:///%s/db.sqlite3'%(tmp_dir)
        with self.app.app_context():
            model.syncdb()
        self.app.secret_key = 'foo'
        self.app.register_blueprint(io_wrapper.BLUEPRINT)
        self.app.register_blueprint(io_common.BLUEPRINT)
        self.client = self.app.test_client()
        self.dispatcher = dispatcher.Dispatcher(self.app)

    @hypothesis.given(st.text(min_size=5))
    def test_cross_domain_login(self, auth_id):
        with self.app.app_context():
            login_user,_ = model.Identity.get_or_create(auth_id=auth_id,
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
                self.assertEqual(client.get('/static/cache/spacewiki-io-app.css').status_code, 200)
                self.assertFalse(current_user.is_authenticated)
                self.assertTrue(current_user.is_anonymous)
                self.assertTrue('_spacewikiio_auth_id' not in session)

    def test_anon_login(self):
        with self.dispatcher.dispatch_context():
            with self.app.test_client() as client:
                self.assertEqual(client.get('/').status_code, 403)
                self.assertEqual(client.get('/static/cache/spacewiki-io-app.css').status_code, 200)
                self.assertNotEqual(current_user, None)
                self.assertFalse(current_user.is_authenticated)
                self.assertTrue(current_user.is_anonymous)
                self.assertTrue('_spacewikiio_auth_id' not in session)
