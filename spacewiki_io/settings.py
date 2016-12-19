SLACK_KEY = None
SLACK_SECRET = None
SPACE_DB_URL_PATTERN = 'postgres:///%s'
ADMIN_DB_URL = 'postgres:///spacewiki'
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
