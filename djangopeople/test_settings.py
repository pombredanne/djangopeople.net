import warnings
warnings.simplefilter('always')

from .settings import *  # noqa

STATICFILES_STORAGE = 'django.contrib.staticfiles.storage.StaticFilesStorage'
BASE_PATH = os.path.join(OUR_ROOT, os.pardir)

PASSWORD_HASHERS = [
    'tests.hashers.NotHashingHasher',
]

LOGGING['loggers']['raven']['handlers'] = []
LOGGING['loggers']['sentry.errors']['handlers'] = []
