from django.contrib import messages
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_POST

from .forms import PlaylistForm
from .models import Playlist, Track
from .services import lastfm


def _back_or_index(request):
    """Возвращаем пользователя туда, откуда была отправлена форма."""
    return request.META.get('HTTP_REFERER') or 'index'


def index(request):
    # На главной странице JS получает треки прямо из HTML-карточек.
    tracks = Track.objects.all()
    playlists = Playlist.objects.prefetch_related('tracks')
    return render(request, 'player/index.html', {
        'tracks': tracks,
        'playlists': playlists,
        'playlist_form': PlaylistForm(),
    })


def playlist_detail(request, pk):
    playlist = get_object_or_404(Playlist.objects.prefetch_related('tracks'), pk=pk)
    tracks = Track.objects.all()
    playlists = Playlist.objects.prefetch_related('tracks')
    return render(request, 'player/playlist_detail.html', {
        'playlist': playlist,
        'tracks': tracks,
        'playlists': playlists,
        'playlist_form': PlaylistForm(),
    })


@require_POST
def create_playlist(request):
    form = PlaylistForm(request.POST)
    if form.is_valid():
        playlist = form.save()
        messages.success(request, f'Плейлист "{playlist.name}" создан.')
        return redirect('playlist_detail', pk=playlist.pk)

    messages.error(request, 'Проверьте название плейлиста.')
    return redirect(_back_or_index(request))


@require_POST
def delete_playlist(request, pk):
    playlist = get_object_or_404(Playlist, pk=pk)
    playlist.delete()
    messages.success(request, 'Плейлист удалён.')
    return redirect('index')


@require_POST
def add_track_to_playlist(request, playlist_pk, track_pk):
    playlist = get_object_or_404(Playlist, pk=playlist_pk)
    track = get_object_or_404(Track, pk=track_pk)
    if playlist.tracks.filter(pk=track.pk).exists():
        messages.info(request, f'Трек "{track.title}" уже есть в плейлисте.')
    else:
        playlist.tracks.add(track)
        messages.success(request, f'Трек "{track.title}" добавлен.')
    return redirect(_back_or_index(request))


@require_POST
def add_track_from_select(request, track_pk):
    track = get_object_or_404(Track, pk=track_pk)
    playlist = get_object_or_404(Playlist, pk=request.POST.get('playlist_id'))
    if playlist.tracks.filter(pk=track.pk).exists():
        messages.info(request, f'Трек "{track.title}" уже есть в плейлисте "{playlist.name}".')
    else:
        playlist.tracks.add(track)
        messages.success(request, f'Трек "{track.title}" добавлен в "{playlist.name}".')
    return redirect(_back_or_index(request))


@require_POST
def remove_track_from_playlist(request, playlist_pk, track_pk):
    playlist = get_object_or_404(Playlist, pk=playlist_pk)
    track = get_object_or_404(Track, pk=track_pk)
    playlist.tracks.remove(track)
    messages.success(request, f'Трек "{track.title}" удалён из плейлиста.')
    return redirect(_back_or_index(request))


def lastfm_track(request):
    artist = request.GET.get('artist', '').strip()
    track = request.GET.get('track', '').strip()
    if not artist or not track:
        return JsonResponse({'ok': False, 'error': 'bad_request', 'message': 'artist и track обязательны.', 'data': {}}, status=400)

    track_info = lastfm.get_track_info(artist, track)
    artist_info = lastfm.get_artist_info(artist)
    top_tracks = lastfm.get_artist_top_tracks(artist)
    similar_artists = lastfm.get_similar_artists(artist)
    return JsonResponse({
        'ok': track_info['ok'],
        'error': track_info['error'],
        'message': track_info['message'],
        'data': {
            'track': track_info.get('data', {}),
            'artist': artist_info.get('data', {}),
            'top_tracks': top_tracks.get('data', {}).get('tracks', []),
            'similar_artists': similar_artists.get('data', {}).get('artists', []),
        },
    })


def lastfm_artist(request):
    artist = request.GET.get('artist', '').strip()
    if not artist:
        return JsonResponse({'ok': False, 'error': 'bad_request', 'message': 'artist обязателен.', 'data': {}}, status=400)

    artist_info = lastfm.get_artist_info(artist)
    top_tracks = lastfm.get_artist_top_tracks(artist)
    similar_artists = lastfm.get_similar_artists(artist)
    return JsonResponse({
        'ok': artist_info['ok'],
        'error': artist_info['error'],
        'message': artist_info['message'],
        'data': {
            'artist': artist_info.get('data', {}),
            'top_tracks': top_tracks.get('data', {}).get('tracks', []),
            'similar_artists': similar_artists.get('data', {}).get('artists', []),
        },
    })


def lastfm_search(request):
    query = request.GET.get('q', '').strip()
    if not query:
        return JsonResponse({'ok': False, 'error': 'bad_request', 'message': 'q обязателен.', 'data': {}}, status=400)
    return JsonResponse(lastfm.search_tracks(query))
