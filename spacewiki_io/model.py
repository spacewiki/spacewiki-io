import peewee
from playhouse.db_url import connect
from flask import g, current_app, Blueprint

BLUEPRINT = Blueprint('model', __name__)

@BLUEPRINT.before_app_request
def get_db():
    db = getattr(g, '_database', None)
    if db is None:
        g._database = db = connect(current_app.config['ADMIN_DB_URL'])
    ADMIN_DATABASE.initialize(db)

ADMIN_DATABASE = peewee.Proxy()

class BaseModel(peewee.Model):
    class Meta:
        database = ADMIN_DATABASE

class Space(BaseModel):
    slack_team_id = peewee.CharField()
    domain = peewee.CharField(default='')
    slack_access_token = peewee.CharField(default='')
    active = peewee.BooleanField(default=False)
    stripe_customer_id = peewee.CharField(default='')
    stripe_subscription_id = peewee.CharField(default='')

    @staticmethod
    def from_team_slacker(slacker):
        slack_team = slacker.api.get('team.info').body
        team_id = slack_team['team']['id']
        domain = slack_team['team']['domain']
        try:
            space = Space.get(Space.slack_team_id == team_id)
            if space.domain != domain:
                space.domain = domain
                current_app.logger.info("Updating domain for %s", space)
            if space.slack_access_token != slacker.api.token:
                space.slack_access_token = slacker.api.token
                current_app.logger.info("Updating auth token for %s", space)
            space.save()
            current_app.logger.info("Saved space %s domain as %s", space, space.domain)
        except peewee.DoesNotExist:
            space = Space.create(slack_team_id = team_id,
                    domain=domain,
                    slack_access_token=slacker.api.token)
            current_app.logger.info("Created new space for %s", space)
        return space

    @staticmethod
    def from_user_slacker(slacker):
        user_id = slacker.api.get('users.identity').body
        team_id = user_id['team']['id']
        try:
            space = Space.get(Space.slack_team_id == team_id)
            current_app.logger.debug("Space found for %s", team_id)
            return space
        except peewee.DoesNotExist:
            current_app.logger.debug("No space found for %s", team_id)
            return None
