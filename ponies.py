__author__ = 'katharine'

import time

import gevent
import gevent.pool
import redis
import requests

import settings

_pool = redis.BlockingConnectionPool.from_url(settings.REDIS_URL, max_connections=5)
_redis = redis.Redis(connection_pool=_pool)


def check_pony_cache(url):
    result = _redis.get("mp4:{}".format(url))
    if result is not None:
        return result.decode('utf-8')
    return None


def cache_pony(url, converted):
    _redis.set("mp4:{}".format(url), converted.encode('utf-8'))


def convert_to_mp4(url):
    cached = check_pony_cache(url)
    if cached is not None:
        return cached
    print("Converting {} to mp4...".format(url))
    result = requests.post("https://api.imgur.com/3/image", {
        "image": url,
        "type": "URL"
    }, headers={
        'Authorization': 'Client-ID {}'.format(settings.IMGUR_TOKEN),
        'Content-Type': 'application/x-www-form-urlencoded',
    })
    try:
        result.raise_for_status()
    except requests.HTTPError as e:
        print(e.response.content)
        return None
    mp4_url = result.json()['data'].get('mp4', None)
    if mp4_url is not None:
        cache_pony(url, mp4_url)
    return mp4_url


def process_image(image):
    medium_size = 'https:' + image['representations']['medium']
    thumb_size = 'https:' + image['representations']['thumb']
    result = requests.head(medium_size)
    size = int(result.headers['Content-Length'])
    if size >= 10000000: # 10 MB max size.
        return None
    mp4_url = convert_to_mp4(medium_size)
    if mp4_url is not None:
        return mp4_url, thumb_size, image['id'], (image['width'], image['height'])
    else:
        return None


def find_ponies(query):
    print("Searching...")
    results = requests.get("https://derpibooru.org/search.json", {
        'q': 'animated, safe, -transparent background, ' + query,
        'sf': 'score',
        'sd': 'desc'
    })
    results.raise_for_status()
    return results.json()['search']


def process_ponies(ponies, time_limit=None):
    if time_limit is not None:
        print("{} seconds left to process ponies.".format(time_limit))
    group = gevent.pool.Group()
    greenlets = []
    for result in ponies:
        greenlets.append(group.spawn(process_image, result))
    group.join(timeout=time_limit)
    telegram_answers = []
    timed_out = 0
    for i, greenlet in enumerate(greenlets):
        try:
            result = greenlet.get(block=False)
        except gevent.Timeout:
            print("Giving up on http://derpiboo.ru/{}".format(ponies[i]['id']))
            timed_out += 1
        else:
            if result is not None:
                telegram_answers.append(result)
    return telegram_answers, timed_out


def answer_ponies(query_id, results, timed_out):
    result = requests.post(
        "https://api.telegram.org/bot{}/answerInlineQuery".format(settings.TELEGRAM_TOKEN),
        headers={"Content-Type": "application/json"},
        json={
            'inline_query_id': query_id,
            'cache_time': settings.CACHE_TIME if timed_out == 0 else settings.PARTIAL_RESULT_CACHE_TIME,
            'is_personal': False,
            'results': [
                {
                    'type': 'mpeg4_gif',
                    'id': url,
                    'mpeg4_url': url,
                    'thumb_url': thumb,
                    'mpeg4_width': dimensions[0],
                    'mpeg4_height': dimensions[1],
                } for url, thumb, id_number, dimensions in results
            ]
        })
    print(result.content)
    result.raise_for_status()


def handle_request(query_id, query):
    start = time.time()
    if query != '':
        ponies = find_ponies(query)
        results, timed_out = process_ponies(ponies, time_limit=(settings.RESPONSE_TIME_LIMIT - (time.time() - start)))
    else:
        results, timed_out = [], 0
    end = time.time()
    print("Took {} seconds to generate a response.".format(end - start))
    answer_ponies(query_id, results, timed_out)
