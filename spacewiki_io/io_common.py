from flask import Blueprint, current_app, request
import dispatcher

BLUEPRINT = Blueprint('io_common', __name__, static_folder='static')

def try_io_url(error, endpoint, values):
    mgmt_app = dispatcher.DISPATCHER.default_app
    values.pop('_external', None)
    req_host = request.host.split(':', 1)
    if len(req_host) == 2:
        port = ':'+req_host[1]
    else:
        port = ''
    urls = mgmt_app.url_map.bind(mgmt_app.config['IO_DOMAIN']+port, "/",
            url_scheme=mgmt_app.config['IO_SCHEME'])
    return urls.build(endpoint, values, force_external=True)

@BLUEPRINT.before_app_first_request
def configure_url_handler():
    current_app.url_build_error_handlers.append(try_io_url)

@BLUEPRINT.app_context_processor
def add_dispatcher_settings():
    return dict(dispatcher_settings=dispatcher.current_dispatcher.default_app.config)
