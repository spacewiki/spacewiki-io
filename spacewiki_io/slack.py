from flask import request, current_app, session
from slacker import Slacker
import dispatcher, model
import spacewiki.model

def consume_token(uri):
    login_code = request.args.get('code', None)
    if login_code is None:
        return None
    resp = Slacker.oauth.access(current_app.config['SLACK_KEY'],
            current_app.config['SLACK_SECRET'], login_code, uri).body
    return Slacker(resp['access_token'])

def login_slack_id(slack_id):
    try:
        identity = spacewiki.model.Identity.get(spacewiki.model.Identity.auth_id == slack_id,
                spacewiki.model.Identity.auth_type == 'slack')
    except:
        identity = spacewiki.model.Identity.create(
                auth_id=slack_id,
                auth_type='slack',
                display_name='',
                handle=slack_id
        )
    session['_spacewikiio_auth_id'] = slack_id
    return identity

def login_from_user_slacker(slacker):
    user_id = slacker.api.get('users.identity').body
    #handle = slacker.api.get('auth.test').body['user']
    slack_id = user_id['user']['id']
    display_name = user_id['user']['name']
    space = model.Space.from_user_slacker(slacker)
    space_app = dispatcher.DISPATCHER.get_wiki_app(space)
    with space_app.app_context():
        user_id = login_slack_id(slack_id)
        user_id.display_name = display_name
        #user_id.handle = handle
        user_id.save()
