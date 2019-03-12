import os
from celery.schedules import crontab
from kombu import Queue


BASE_DIR = os.path.dirname(os.path.abspath(__file__))

DATABASE = {
    'url': os.environ.get('DB_URL', 'postgresql://postgres:@db:5432/postgres'),
}

CACHE = {
    'host': os.environ.get('CACHE_HOST', 'redis'),
    'db': os.environ.get('CACHE_DB', '1'),
}

BROKER_URL = os.environ.get('BROKER_URL', 'redis://redis:6379/0')

CELERY_IMPORTS = (
    'app.tasks',
)

CELERY_ENABLE_UTC = True
CELERY_TIMEZONE = 'UTC'

CELERY_TASK_SERIALIZER = 'json'
CELERY_ACCEPT_CONTENT = ['application/json']

CELERY_TASK_ALWAYS_EAGER = False
CELERY_TASK_IGNORE_RESULT = True

CELERYD_TASK_TIME_LIMIT = 600

CELERY_DEFAULT_QUEUE = 'default'

CELERY_QUEUES = (
    Queue('default'),
    Queue('exchanges'),
)

CELERYBEAT_SCHEDULE = {
    'exchange_updater_BitfinexExchange': {
        'task': 'app.tasks.exchange_updater',
        'schedule': crontab(minute='*/10'),
        'args': ('app.exchanges.BitfinexExchange',),
        'options': {'time_limit': 600}
    },
    'exchange_updater_BittrexExchange': {
        'task': 'app.tasks.exchange_updater',
        'schedule': crontab(minute='*/1'),
        'args': ('app.exchanges.BittrexExchange',),
        'options': {'time_limit': 60}
    },
    'exchange_updater_OpenExchangeRatesExchange': {
        'task': 'app.tasks.exchange_updater',
        'schedule': crontab(minute=0, hour='*/1'),
        'args': ('app.exchanges.OpenExchangeRatesExchange',),
        'options': {'time_limit': 60}
    },
}

BOT_TOKEN = os.environ.get('BOT_TOKEN')

BOT_PARSERS = [
    'app.parsers.SimpleParser',
]

OPENEXCHANGERATES_TOKEN = os.environ.get('OPENEXCHANGERATES_TOKEN')

LANGUAGES = (
    'en_US',
)

LANGUAGE_CODE = 'en_US'

LOGGING = {
    'version': 1,
    'formatters': {
        'default': {
            'format': '[%(asctime)s] %(levelname)-5.5s [%(name)s:%(lineno)s][%(threadName)s] %(message)s',
        }
    },
    'handlers': {
        'console': {
            'class': 'logging.StreamHandler',
            'formatter': 'default'
        }
    },
    'root': {
        'level': 'INFO',
        'handlers': ['console']
    }
}
