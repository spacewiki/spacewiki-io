from flask import request, current_app, session
from slacker import Slacker

def consume_token(uri):
    login_code = request.args.get('code', None)
    if login_code is None:
        return None
    resp = Slacker.oauth.access(current_app.config['SLACK_KEY'],
            current_app.config['SLACK_SECRET'], login_code, uri).body
    return Slacker(resp['access_token'])
