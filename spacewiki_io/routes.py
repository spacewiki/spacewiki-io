from flask import Blueprint, current_app, render_template, url_for, redirect,\
    request, session, flash
from slacker import Error
from flask_login import login_user
import model, slack
import peewee

BLUEPRINT = Blueprint('routes', __name__, template_folder='templates')

@BLUEPRINT.app_context_processor
def add_site_settings():
    return dict(settings=current_app.config)

@BLUEPRINT.route('/')
def index(path=None):
        return render_template('index.html')

@BLUEPRINT.route('/terms-of-service')
def tos():
    return render_template('tos.html')

@BLUEPRINT.route('/privacy')
def privacy_policy():
    return render_template('privacy.html')

@BLUEPRINT.route('/slack_add_flow')
def add_to_slack():
    try:
        slacker = slack.consume_token(url_for('routes.add_to_slack', _external=True))
    except Error, e:
        flash("There was an error logging you in: %s"%e)
        return redirect(url_for('routes.index'))
    if slacker is None:
        flash('You denied the request to login')
        return redirect(url_for('routes.index'))
    space = model.Space.from_team_slacker(slacker)
    slack_team = slacker.api.get('team.info').body
    if space.active:
        space.make_space_database()
        return redirect('https://%s.spacewiki.io/'%(space.domain))
    # TODO: This is where we'd redirect to the signup workflow if the space
    # needs activation.
    space.active = True
    space.save()
    space.make_space_database()
    session['slack_team'] = slack_team['team']['id']
    return redirect(url_for('routes.finished'))

@BLUEPRINT.route('/welcome')
def finished():
    slack_team_id = session.get('slack_team', None)
    space = model.Space.get(slack_team_id=slack_team_id)
    return render_template('finished.html', space=space)
