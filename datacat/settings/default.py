# ============================================================
#     Flask configuration
# ============================================================
# See: http://flask.pocoo.org/docs/latest/config/#builtin-configuration-values

DEBUG = False
TESTING = False

# SECRET_KEY = 'This is some secret'


# ============================================================
#     Datacat configuration
# ============================================================

DATABASE = {
    'database': None,
    'user': None,
    'password': None,
    'host': 'localhost',
    'port': 5432,
}

PLUGINS = [
    'datacat.ext.core:core_plugin',
    'datacat.ext.geo:geo_plugin',
]

RESOURCE_ACCESSORS = {
    'http': 'datacat.utils.resource_access:HttpResourceAccessor',
    'https': 'datacat.utils.resource_access:HttpResourceAccessor',
    'internal': 'datacat.utils.resource_access:InternalResourceAccessor',
}


# ============================================================
#     Celery configuration
# ============================================================
# See: http://docs.celeryproject.org/en/latest/configuration.html


CELERY_BROKER_URL = 'redis://localhost:6379/0'
CELERY_RESULT_BACKEND = 'redis://localhost:6379/0'

# CELERY_ACCEPT_CONTENT = ['pickle', 'json', 'msgpack', 'yaml']
CELERY_ACCEPT_CONTENT = ['json', 'msgpack', 'yaml']
