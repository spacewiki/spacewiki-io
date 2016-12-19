from flask_assets import Environment
from flask import Flask
from spacewiki_io import model, routes, signin, io_common
from spacewiki.middleware import ReverseProxied
from slacker import Slacker
import peewee
from raven.contrib.flask import Sentry


def create_app():
    APP = Flask(__name__)
    APP.config.from_object('spacewiki_io.settings')
    ASSETS = Environment(APP)
    ASSETS.from_yaml("assets.yml")
    APP.secret_key = APP.config['SECRET_SESSION_KEY']
    APP.wsgi_app = ReverseProxied(APP.wsgi_app)

    APP.register_blueprint(routes.BLUEPRINT)
    APP.register_blueprint(model.BLUEPRINT)
    APP.register_blueprint(signin.BLUEPRINT)
    APP.register_blueprint(io_common.BLUEPRINT)

    sentry = Sentry(APP)

    return APP
