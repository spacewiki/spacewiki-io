# Hosted SpaceWiki

All wiki-as-a-service software sucks. SpaceWiki.io sucks less than most.

SpaceWiki is provided as a service via https://spacewiki.io/. There, users can
sign in with their slack teams and each team is provisioned a wiki. Payment is
optional but requested.

## Development

You'll need the following tools available:

* virtualenv
* Postgres
* r.js (``npm install -g requirejs``)

You'll additionally need an API key for each service you'll be testing with:

* A slack API key: https://api.slack.com/apps/
* A stripe API key: https://stripe.com/

To begin:

```
$ virtualenv virtualenv/
$ source virtualenv/bin/activate
$ pip install -r requirements.txt
```

SpaceWiki.io is a wrapper around the upstream SpaceWiki project. This app uses
SpaceWiki as any other package, albeit with a fairly tight linkage. To set this
up, you'll need to prepare a copy of SpaceWiki for consumption. You'll want to
have activated the virtualenv created above and be sure that you aren't within
your spacewiki-io git clone.

```
$ git clone git://github.com/spacewiki/spacewiki
$ cd spacewiki
$ ./setup.py develop
```

This will setup symlinks in your virtualenv to point to this local git
clone of SpaceWiki.

Next, create a local_hosted_settings.py in the root of your spacewiki-io
directory (same place where manage.py lives) with appropriate values. There is
currently one required configuration for local development:

* ``SECRET_SESSION_KEY`` - Used to generate session cookies. Keep this secret,
  as it is used to process slack logins between subdomains.

The defaults are good enough for local development with a postgres server
available via:

```
$ docker run --net=host postgres
```

The default configuration assumes that there is a database named 'spacewiki', so
create that before getting too far ahead:

```
$ psql -h localhost -U postgres
```

Other configuration variables are:

* ``SLACK_KEY`` - Public slack key from api.slack.com
* ``SLACK_SECRET`` - Private slack API key from api.slack.com
* ``SPACE_DB_URL_PATTERN`` - This must be a string containing '%s' which will be
  replaced with the team's database name. For example,
  ``postgres://postgres:postgres@localhost/%s`` for the default docker postgres
  container
* ``ADMIN_DB_URL`` - A peewee database URI
* ``STRIPE_SECRET_KEY`` - Secret API key from stripe.com
* ``STRIPE_KEY`` - Public API key from stripe.com

To start the server:

  ``$ ./manage.py runserver``

If you plan on interacting with the slack workflows at all, you'll need to add
http://localhost:5000/ (or the port of your chosing) to be able to test the
slack buttons. In your slack app's OAuth & Permissions page, add this URL to the
list of redirect URLs.

## Deployment

Deployment is done by pushing to spacewiki.io:/srv/spacewiki/io-git. Server-side
hooks will rebuild and reload the application.
