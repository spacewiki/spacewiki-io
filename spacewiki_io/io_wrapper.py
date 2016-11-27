from flask import Blueprint, render_template, session, request, current_app
from flask_login import current_user, login_user
import peewee
import app, model
import spacewiki.model

BLUEPRINT = Blueprint('io_wrapper', __name__, template_folder='templates')

@BLUEPRINT.before_app_request
def confirm_logged_in():
    common_user = session.get('_spacewikiio_auth_id', None)
    if common_user is not None:
        del session['_spacewikiio_auth_id']
        try:
            u = spacewiki.model.Identity.get(spacewiki.model.Identity.auth_id ==
                    common_user, spacewiki.model.Identity.auth_type == 'slack')
            login_user(u)
        except peewee.DoesNotExist:
            pass
    if not current_user.is_authenticated:
        if not request.path.startswith('/static'):
            return render_template('private.html')

def try_io_url(error, endpoint, values):
    mgmt_app = app.create_app()
    values.pop('_external', None)
    urls = mgmt_app.url_map.bind("spacewiki.io", "/", url_scheme='https')
    return urls.build(endpoint, values, force_external=True)

@BLUEPRINT.before_app_first_request
def configure_url_handler():
    current_app.url_build_error_handlers.append(try_io_url)
