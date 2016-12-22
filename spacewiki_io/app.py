import logging.config
from flask_assets import Environment
from flask import Flask
from spacewiki_io import model, routes, signin, io_common, deadspace
from spacewiki.middleware import ReverseProxied
from slacker import Slacker
import peewee
from raven.contrib.flask import Sentry

def create_base_app(with_config=True):
    APP = Flask(__name__)
    if with_config:
        APP.config.from_object('spacewiki_io.settings')
    ASSETS = Environment(APP)
    ASSETS.from_yaml("assets.yml")
    APP.secret_key = APP.config['SECRET_SESSION_KEY']
    APP.wsgi_app = ReverseProxied(APP.wsgi_app)
    APP.register_blueprint(io_common.BLUEPRINT)
    Sentry(APP)
    return APP

def create_app(with_config=True):
    APP = create_base_app(with_config)

    APP.register_blueprint(routes.BLUEPRINT)
    APP.register_blueprint(model.BLUEPRINT)
    APP.register_blueprint(signin.BLUEPRINT)
    APP.register_blueprint(io_common.BLUEPRINT)

    if 'LOG_CONFIG' in APP.config:
        logging.config.dictConfig(APP.config['LOG_CONFIG'])

    sentry = Sentry(APP)

    return APP

def create_deadspace_app():
    deadspace_app = create_base_app()
    deadspace_app.register_blueprint(deadspace.BLUEPRINT)
    return deadspace_app
