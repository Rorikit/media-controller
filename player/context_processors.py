from django.conf import settings


def lastfm_settings(request):
    return {
        'LASTFM_API_KEY': settings.LASTFM_API_KEY,
    }
