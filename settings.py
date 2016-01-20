__author__ = 'katharine'

from os import environ as _environ

RESPONSE_TIME_LIMIT = int(_environ.get('RESPONSE_TIME_LIMIT', 8))
TELEGRAM_TOKEN = _environ.get('TELEGRAM_TOKEN').decode('utf-8')
IMGUR_TOKEN = _environ.get('IMGUR_TOKEN').decode('utf-8')
REDIS_URL = _environ.get('REDIS_URL').decode('utf-8')
CACHE_TIME = int(_environ.get('CACHE_TIME', 86400))
PARTIAL_RESULT_CACHE_TIME = int(_environ.get('PARTIAL_RESULT_CACHE_TIME', 20))
PORT = int(_environ.get('PORT', 5000))
