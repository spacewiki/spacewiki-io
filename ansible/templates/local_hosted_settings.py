STRIPE_SECRET_KEY = '{{stripe_secret_key}}'
STRIPE_KEY = '{{stripe_key}}'
SLACK_KEY = '{{slack_key}}'
SLACK_SECRET = '{{slack_secret}}'
SLACK_VERIFICATION_TOKEN = '{{slack_verification_token}}'
SECRET_KEY = '{{secret_session_key}}'
PREFERRED_URL_SCHEME = 'https'
SESSION_COOKIE_DOMAIN = '.spacewiki.io'
SENTRY_DSN = '{{sentry_dsn}}'
IO_DOMAIN = 'spacewiki.io'
IO_SCHEME = 'https'
ADMIN_DB_URL = 'postgres:///spacewiki'

SUBSPACE_DATABASE_NAME = 'spacewiki_site_%(slack_id)s'
SUBSPACE_DATABASE_URL = 'postgres:///' + SUBSPACE_DATABASE_NAME
SUBSPACE_UPLOAD_PATH = '/srv/spacewiki/uploads/%(domain)s'
SUBSPACE_HEADER_INJECTION = """
<script src="https://cdn.ravenjs.com/3.9.1/raven.min.js">
</script>
<script type="text/javascript">
Raven.config('https://c310feb89d34481f91a9bb51bc7328bf@sentry.io/122996').install();
</script>
"""
