from flask import Blueprint, render_template, redirect, url_for, current_app
import model
import stripe

BLUEPRINT = Blueprint('signup', __name__)

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
