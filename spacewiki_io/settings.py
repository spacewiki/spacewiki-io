SLACK_KEY = None
SLACK_SECRET = None
SUBSPACE_DATABASE_NAME = '%(slack_id)s'
SUBSPACE_DATABASE_URL = 'postgres:///' + SUBSPACE_DATABASE_NAME
SUBSPACE_UPLOAD_PATH = 'uploads/%(slack_id)s'
ADMIN_DB_URL = 'postgres:///spacewiki'
IO_DOMAIN = 'spacewiki.io'
IO_SCHEME = 'https'
DEADSPACE = False
LOGIN_NEEDED = False

LOG_CONFIG = {
    'version': 1,
    'handlers': {
        'colorlog': {
            'class': 'colorlog.StreamHandler',
            'formatter': 'colorformat'
        }
    },
    'formatters': {
        'colorformat': {
            '()': 'colorlog.ColoredFormatter',
            'format': '%(log_color)s%(levelname)s:%(name)s:%(message)s'
        }
    },
    'loggers': {
        'socketio': {'level': 'WARNING'},
        'engineio': {'level': 'WARNING'},
        'http': {'level': 'INFO'},
        'peewee': {'level': 'INFO'},
        'raven': {'level': 'WARNING'},
        'dispatcher': {'level': 'DEBUG'},
    },
    'root': {
        'level': 'DEBUG',
        'handlers': ['colorlog']
    }
}

try:
    from local_hosted_settings import *
except ImportError:
    pass
