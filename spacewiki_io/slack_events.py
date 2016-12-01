from slacker import Slacker
from flask import Blueprint, request, current_app, abort, g
import re
import model, dispatcher
import peewee
import spacewiki.model

URL_PATTERN = re.compile('<https://(?P<domain>.+)\.spacewiki\.io/(?P<slug>.*)>')

BLUEPRINT = Blueprint('slack_events', __name__)

RTM_EVENTS = {}

def slack_event(key):
    def wrapper(f):
        RTM_EVENTS[key] = f
        return f
    return wrapper

def handle_slack_event(space, event):
    evt_type = event['type']
    if evt_type in RTM_EVENTS:
        return RTM_EVENTS[evt_type](space, event)
    else:
        current_app.logger.warning("Unhandled slack event: %s", evt_type)
        return None

def revision_to_slack_attachment(url, rev):
    author_list = []
    revision_count = 0
    first_edit = None
    for r in rev.page.revisions:
        author_list.append(r.author)
        revision_count += 1
        first_edit = r.timestamp.date()
    authors = ', '.join(set(a.display_name for a in
            author_list))

    return {
        'fallback': rev.page.title,
        'title': rev.page.title,
        'title_link': url,
        'text': rev.summary+'...',
        'color': '#582A72', # Primary color from CSS
        'footer': 'SpaceWiki',
        'mrkdwn_in': ['text'],
        'fields': [
            {
                'title': 'Last modified',
                'value': str(rev.timestamp.date()),
                'short': True
            },
            {
                'title': 'Authors',
                'value': authors,
                'short': True
            },
            {
                'title': 'History',
                'value': "%s revisions since %s"%(revision_count,
                    str(first_edit)),
                'short': True
            }
        ]
    }

@slack_event('message')
def on_message(space, event):
    matches = URL_PATTERN.match(event['text'])
    if matches is None:
        return
    if matches.group('domain') != space.domain:
        return
    url = 'https://%s.spacewiki.io/%s'%(matches.group('domain'),
            matches.group('slug'))
    space_slacker = Slacker(space.slack_access_token)
    slug = matches.group('slug')
    space_app = dispatcher.DISPATCHER.get_wiki_app(space)
    with space_app.app_context():
        rev = spacewiki.model.Page.latestRevision(slug)

        if rev is None:
            current_app.logger.debug("No page at %s", slug)
            return "OK"

        attachment = revision_to_slack_attachment(url, rev)
        space_slacker.chat.post_message(
                               channel=event['channel'],
                               text=rev.page.title,
                               unfurl_links=False,
                               attachments=[attachment]
                               )

@BLUEPRINT.route('/hook', methods=['POST'])
def on_slack_event():
    evt = request.get_json()
    app_token = evt['token']
    if app_token != current_app.config['SLACK_VERIFICATION_TOKEN']:
        raise RuntimeError, "Got slack challenge, but no token is set!"
    if evt['type'] == 'url_verification':
        app_challenge = evt['challenge']
        current_app.logger.debug("Got slack challenge, responding with token.")
        return app_challenge

    if evt['type'] == 'event_callback':
        team_id = evt['team_id']
        try:
            space = model.Space.get(model.Space.slack_team_id == team_id)
        except peewee.DoesNotExist:
            raise RuntimeError, "Got an event for %s, but no wiki exists!"%(team_id)
        ret = handle_slack_event(space, evt['event'])
        if ret is None:
            return ''
        return ret
    raise RuntimeError, "Unknown event envelope type %s"%(evt['type'])
