from hashlib import sha1

import requests
from django.conf import settings
from django.core.cache import cache

LASTFM_API_URL = 'https://ws.audioscrobbler.com/2.0/'
CACHE_TIMEOUT = 60 * 60


def get_track_info(artist, track):
    data = _request('track.getInfo', {'artist': artist, 'track': track, 'autocorrect': 1})
    if not data['ok']:
        return data
    track_data = data['data'].get('track')
    if not track_data:
        return _error('not_found', 'Информация о треке не найдена.')
    return _ok({
        'type': 'track',
        'title': track_data.get('name', track),
        'artist': _artist_name(track_data.get('artist'), artist),
        'url': track_data.get('url', ''),
        'image': _largest_image(track_data.get('album', {}).get('image', [])),
        'summary': _summary(track_data.get('wiki', {})),
        'listeners': track_data.get('listeners', ''),
        'playcount': track_data.get('playcount', ''),
        'tags': _tags(track_data.get('toptags', {}).get('tag', [])),
        'raw': track_data,
    })


def get_artist_info(artist):
    data = _request('artist.getInfo', {'artist': artist, 'autocorrect': 1})
    if not data['ok']:
        return data
    artist_data = data['data'].get('artist')
    if not artist_data:
        return _error('not_found', 'Информация об исполнителе не найдена.')
    return _ok({
        'type': 'artist',
        'artist': artist_data.get('name', artist),
        'url': artist_data.get('url', ''),
        'image': _largest_image(artist_data.get('image', [])),
        'summary': _summary(artist_data.get('bio', {})),
        'listeners': artist_data.get('stats', {}).get('listeners', ''),
        'playcount': artist_data.get('stats', {}).get('playcount', ''),
        'tags': _tags(artist_data.get('tags', {}).get('tag', [])),
        'raw': artist_data,
    })


def get_artist_top_tracks(artist):
    data = _request('artist.getTopTracks', {'artist': artist, 'limit': 6, 'autocorrect': 1})
    if not data['ok']:
        return data
    tracks = data['data'].get('toptracks', {}).get('track', [])
    return _ok({
        'type': 'top_tracks',
        'artist': artist,
        'tracks': [
            {
                'title': item.get('name', ''),
                'artist': _artist_name(item.get('artist'), artist),
                'playcount': item.get('playcount', ''),
                'listeners': item.get('listeners', ''),
                'url': item.get('url', ''),
                'image': _largest_image(item.get('image', [])),
            }
            for item in _as_list(tracks)
        ],
    })


def get_similar_artists(artist):
    data = _request('artist.getSimilar', {'artist': artist, 'limit': 6, 'autocorrect': 1})
    if not data['ok']:
        return data
    artists = data['data'].get('similarartists', {}).get('artist', [])
    return _ok({
        'type': 'similar_artists',
        'artist': artist,
        'artists': [
            {
                'name': item.get('name', ''),
                'url': item.get('url', ''),
                'image': _largest_image(item.get('image', [])),
                'match': item.get('match', ''),
            }
            for item in _as_list(artists)
        ],
    })


def search_tracks(query):
    data = _request('track.search', {'track': query, 'limit': 8})
    if not data['ok']:
        return data
    matches = data['data'].get('results', {}).get('trackmatches', {}).get('track', [])
    return _ok({
        'type': 'search',
        'query': query,
        'results': [
            {
                'title': item.get('name', ''),
                'artist': item.get('artist', ''),
                'listeners': item.get('listeners', ''),
                'url': item.get('url', ''),
                'image': _largest_image(item.get('image', [])),
            }
            for item in _as_list(matches)
        ],
    })


def _request(method, params):
    if not settings.LASTFM_API_KEY:
        return _error('missing_api_key', 'LASTFM_API_KEY не задан. Last.fm данные недоступны.')

    clean_params = {key: str(value).strip() for key, value in params.items() if str(value).strip()}
    if not clean_params:
        return _error('bad_request', 'Пустой запрос к Last.fm.')

    cache_key = _cache_key(method, clean_params)
    cached = cache.get(cache_key)
    if cached:
        return cached

    try:
        response = requests.get(
            LASTFM_API_URL,
            params={
                'method': method,
                'api_key': settings.LASTFM_API_KEY,
                'format': 'json',
                **clean_params,
            },
            timeout=8,
        )
        response.raise_for_status()
        payload = response.json()
    except requests.Timeout:
        return _error('timeout', 'Last.fm не ответил вовремя.')
    except requests.RequestException:
        return _error('network_error', 'Last.fm временно недоступен.')
    except ValueError:
        return _error('invalid_json', 'Last.fm вернул некорректный ответ.')

    if payload.get('error'):
        code = str(payload.get('error'))
        message = payload.get('message', 'Last.fm вернул ошибку.')
        normalized = _error(_lastfm_error_code(code), message)
        cache.set(cache_key, normalized, 60)
        return normalized

    result = _ok(payload)
    cache.set(cache_key, result, CACHE_TIMEOUT)
    return result


def _cache_key(method, params):
    raw = method + ':' + '&'.join(f'{key}={params[key]}' for key in sorted(params))
    return 'lastfm:' + sha1(raw.lower().encode('utf-8')).hexdigest()


def _ok(data):
    return {'ok': True, 'error': None, 'message': '', 'data': data}


def _error(code, message):
    return {'ok': False, 'error': code, 'message': message, 'data': {}}


def _lastfm_error_code(code):
    mapping = {
        '6': 'not_found',
        '8': 'network_error',
        '9': 'invalid_session',
        '10': 'invalid_api_key',
        '11': 'service_offline',
        '16': 'service_unavailable',
        '29': 'rate_limited',
    }
    return mapping.get(code, 'lastfm_error')


def _as_list(value):
    if isinstance(value, list):
        return value
    if value:
        return [value]
    return []


def _largest_image(images):
    for item in reversed(_as_list(images)):
        url = item.get('#text', '')
        if url:
            return url
    return ''


def _tags(tags):
    return [item.get('name', '') for item in _as_list(tags) if item.get('name')]


def _summary(wiki_or_bio):
    return (wiki_or_bio or {}).get('summary', '').strip()


def _artist_name(value, fallback):
    if isinstance(value, dict):
        return value.get('name', fallback)
    return value or fallback
