from flask import Blueprint, current_app, render_template, url_for, redirect,\
    request, session, flash
from slacker import Slacker, Error
from flask_login import login_user
import model, dispatcher
import peewee
import spacewiki.model
import stripe
import slack

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

def deadspace():
    return render_template('deadspace.html')

def private():
    return render_template('private.html')

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
    session['slack_team'] = slack_team['team']['id']
    return redirect(url_for('routes.signup'))

@BLUEPRINT.route('/signup')
def signup():
    return render_template('signup.html')

@BLUEPRINT.route('/signup/<plan>')
def choose_plan(plan):
    slack_team_id = session.get('slack_team', None)
    space = model.Space.get(slack_team_id=slack_team_id)
    session['plan_type'] = plan
    if plan == 'free':
        space.active = True
        space.save()
        return redirect(url_for('routes.finished'))
    return render_template('pay.html', plan=plan, space=space)

@BLUEPRINT.route('/payment', methods=['POST'])
def payment():
    slack_team_id = session.get('slack_team', None)
    plan_type = session.get('plan_type', None)
    space = model.Space.get(slack_team_id=slack_team_id)
    subscription_id = None
    if plan_type == 'startup':
        subscription_id = 'startup'
    if plan_type == 'corporate':
        subscription_id = 'corporate'
    stripe.api_key = current_app.config['STRIPE_SECRET_KEY']

    stripe_token = request.form['stripeToken']

    if space.stripe_customer_id == '':
        customer = stripe.Customer.create(source=stripe_token)
        space.stripe_customer_id = customer.id
    
    current_app.logger.debug("Processing new subscription for %s plan", plan_type)
    # plan == None means they picked the 'donate' button
    if subscription_id is not None:
        sub = stripe.Subscription.create(
            customer = space.stripe_customer_id,
            plan=subscription_id
        )
        space.stripe_subscription_id = sub.id
    else:
        donation_value = int(float(request.form['donationValue']) * 100)
        stripe.Charge.create(
            customer = space.stripe_customer_id,
            amount = donation_value,
            currency = 'USD'
        )

    space.active = True
    space.save()
    return redirect(url_for('routes.finished'))

@BLUEPRINT.route('/welcome')
def finished():
    slack_team_id = session.get('slack_team', None)
    space = model.Space.get(slack_team_id=slack_team_id)
    return render_template('finished.html', space=space)

