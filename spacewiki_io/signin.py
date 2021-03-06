from flask import Blueprint, redirect, url_for, flash, request, current_app, g
from slacker import Error
from werkzeug import Local, LocalProxy
import slack, dispatcher, model

BLUEPRINT = Blueprint('signin', __name__, template_folder='templates')

@BLUEPRINT.route('/slack_login_flow')
def slack_login():
    try:
        slacker = slack.consume_token(url_for('.slack_login', _external=True))
    except Error, e:
        flash("There was an error logging in: %s"%e)
        return redirect(url_for('routes.index'))
    if slacker is None:
        flash('You denied the request to login')
        return redirect(url_for('routes.index'))
    space = model.Space.from_user_slacker(slacker)
    if space is not None:
        dispatcher.current_dispatcher.login_from_user_slacker(slacker)
        req_host = request.host.split(':', 1)
        if len(req_host) == 2:
            port = ':'+req_host[1]
        else:
            port = ''
        return redirect('%s://%s.%s/'%(current_app.config['IO_SCHEME'], space.domain,
            current_app.config['IO_DOMAIN']+port))
    else:
        flash("Your team doesn't have a wiki yet!")
        return redirect(url_for('routes.index'))
