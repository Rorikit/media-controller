from django.core.management import call_command
from django.test import TestCase, override_settings
from django.urls import reverse
from unittest.mock import Mock, patch

from .models import Playlist, Track
from .services import lastfm


class PlayerModelTests(TestCase):
    def test_track_str_contains_artist_and_title(self):
        track = Track.objects.create(
            title='High Voltage',
            artist='Linkin Park',
            audio_file='audio/Linkin Park - High Voltage.mp3',
        )

        self.assertEqual(str(track), 'Linkin Park - High Voltage')

    def test_playlist_str_returns_name(self):
        playlist = Playlist.objects.create(name='Workout')

        self.assertEqual(str(playlist), 'Workout')


class PlayerViewTests(TestCase):
    def setUp(self):
        self.track = Track.objects.create(
            title='Blackout',
            artist='Lokal',
            audio_file='audio/Lokal - Blackout.mp3',
        )
        self.other_track = Track.objects.create(
            title='Far Away',
            artist='Nickelback',
            audio_file='audio/Nickelback - Far Away.mp3',
        )
        self.playlist = Playlist.objects.create(name='Фитнес метал')

    def test_index_renders_tracks_and_global_player(self):
        response = self.client.get(reverse('index'))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Blackout')
        self.assertContains(response, 'global-player-bar')
        self.assertContains(response, 'data-global-audio')
        self.assertContains(response, 'globalPlayer.js')
        self.assertNotContains(response, 'data-audio')

    def test_playlist_detail_renders_playlist_tools(self):
        self.playlist.tracks.add(self.track)

        response = self.client.get(reverse('playlist_detail', args=[self.playlist.pk]))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, self.playlist.name)
        self.assertContains(response, 'На главную')
        self.assertContains(response, 'remove')
        self.assertContains(response, 'global-player-bar')

    def test_create_playlist_redirects_to_detail(self):
        response = self.client.post(reverse('create_playlist'), {
            'name': 'Road trip',
            'description': 'Tracks for a long drive',
        })

        playlist = Playlist.objects.get(name='Road trip')
        self.assertRedirects(response, reverse('playlist_detail', args=[playlist.pk]))

    def test_add_track_to_playlist_is_idempotent(self):
        url = reverse('add_track_to_playlist', args=[self.playlist.pk, self.track.pk])

        self.client.post(url, HTTP_REFERER=reverse('playlist_detail', args=[self.playlist.pk]))
        self.client.post(url, HTTP_REFERER=reverse('playlist_detail', args=[self.playlist.pk]))

        self.assertEqual(self.playlist.tracks.count(), 1)

    def test_add_track_from_select(self):
        response = self.client.post(
            reverse('add_track_from_select', args=[self.other_track.pk]),
            {'playlist_id': self.playlist.pk},
            HTTP_REFERER=reverse('index'),
        )

        self.assertRedirects(response, reverse('index'), fetch_redirect_response=False)
        self.assertTrue(self.playlist.tracks.filter(pk=self.other_track.pk).exists())

    def test_remove_track_from_playlist(self):
        self.playlist.tracks.add(self.track)

        response = self.client.post(
            reverse('remove_track_from_playlist', args=[self.playlist.pk, self.track.pk]),
            HTTP_REFERER=reverse('playlist_detail', args=[self.playlist.pk]),
        )

        self.assertRedirects(response, reverse('playlist_detail', args=[self.playlist.pk]), fetch_redirect_response=False)
        self.assertFalse(self.playlist.tracks.filter(pk=self.track.pk).exists())

    def test_delete_playlist(self):
        response = self.client.post(reverse('delete_playlist', args=[self.playlist.pk]))

        self.assertRedirects(response, reverse('index'))
        self.assertFalse(Playlist.objects.filter(pk=self.playlist.pk).exists())


class SeedTracksCommandTests(TestCase):
    def test_seed_tracks_creates_real_tracks_and_removes_placeholders(self):
        Track.objects.create(title='Morning Focus', artist='Demo Library', audio_file='audio/morning-focus.mp3')
        Track.objects.create(title='Frontend Groove', artist='Student Beats', audio_file='')

        call_command('seed_tracks')

        self.assertEqual(Track.objects.filter(artist__in=['Demo Library', 'Student Beats']).count(), 0)
        self.assertEqual(Track.objects.filter(audio_file='').count(), 0)
        self.assertGreaterEqual(Track.objects.count(), 11)
        self.assertTrue(Track.objects.filter(title="Nobody's Listening", artist='Linkin Park').exists())
        self.assertTrue(Track.objects.filter(title='Утренний рассвет', artist='Король и Шут').exists())


class LastFmServiceTests(TestCase):
    @override_settings(LASTFM_API_KEY='')
    def test_lastfm_service_gracefully_handles_missing_key(self):
        result = lastfm.get_track_info('Linkin Park', 'Numb')

        self.assertFalse(result['ok'])
        self.assertEqual(result['error'], 'missing_api_key')

    @override_settings(LASTFM_API_KEY='test-key')
    @patch('player.services.lastfm.requests.get')
    def test_lastfm_track_info_is_normalized(self, mocked_get):
        mocked_get.return_value = self._response({
            'track': {
                'name': 'Numb',
                'artist': {'name': 'Linkin Park'},
                'listeners': '100',
                'playcount': '250',
                'album': {'image': [{'#text': '', 'size': 'small'}, {'#text': 'https://img.test/cover.jpg', 'size': 'large'}]},
                'wiki': {'summary': 'Track summary'},
                'toptags': {'tag': [{'name': 'rock'}, {'name': 'nu metal'}]},
            }
        })

        result = lastfm.get_track_info('Linkin Park', 'Numb')

        self.assertTrue(result['ok'])
        self.assertEqual(result['data']['title'], 'Numb')
        self.assertEqual(result['data']['artist'], 'Linkin Park')
        self.assertEqual(result['data']['image'], 'https://img.test/cover.jpg')
        self.assertIn('rock', result['data']['tags'])

    def _response(self, payload):
        response = Mock()
        response.json.return_value = payload
        response.raise_for_status.return_value = None
        return response


class LastFmEndpointTests(TestCase):
    def test_lastfm_track_endpoint_validates_params(self):
        response = self.client.get(reverse('lastfm_track'))

        self.assertEqual(response.status_code, 400)
        self.assertFalse(response.json()['ok'])

    @patch('player.views.lastfm.get_similar_artists')
    @patch('player.views.lastfm.get_artist_top_tracks')
    @patch('player.views.lastfm.get_artist_info')
    @patch('player.views.lastfm.get_track_info')
    def test_lastfm_track_endpoint_returns_combined_payload(self, track_info, artist_info, top_tracks, similar):
        track_info.return_value = {'ok': True, 'error': None, 'message': '', 'data': {'title': 'Numb'}}
        artist_info.return_value = {'ok': True, 'error': None, 'message': '', 'data': {'artist': 'Linkin Park'}}
        top_tracks.return_value = {'ok': True, 'error': None, 'message': '', 'data': {'tracks': [{'title': 'Faint'}]}}
        similar.return_value = {'ok': True, 'error': None, 'message': '', 'data': {'artists': [{'name': 'Evanescence'}]}}

        response = self.client.get(reverse('lastfm_track'), {'artist': 'Linkin Park', 'track': 'Numb'})

        self.assertEqual(response.status_code, 200)
        payload = response.json()
        self.assertTrue(payload['ok'])
        self.assertEqual(payload['data']['track']['title'], 'Numb')
        self.assertEqual(payload['data']['top_tracks'][0]['title'], 'Faint')

    @patch('player.views.lastfm.search_tracks')
    def test_lastfm_search_endpoint_returns_results(self, search_tracks):
        search_tracks.return_value = {'ok': True, 'error': None, 'message': '', 'data': {'results': [{'title': 'Numb'}]}}

        response = self.client.get(reverse('lastfm_search'), {'q': 'numb'})

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()['data']['results'][0]['title'], 'Numb')
