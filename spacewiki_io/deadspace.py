from flask import render_template, request, Blueprint

BLUEPRINT = Blueprint('deadspace', __name__)

@BLUEPRINT.before_app_request
def deadspace():
    if not request.path.startswith('/static'):
        return render_template('deadspace.html'), 404
