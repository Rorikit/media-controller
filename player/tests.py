from django.core.management import call_command
from django.test import TestCase
from django.urls import reverse

from .models import Playlist, Track


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
