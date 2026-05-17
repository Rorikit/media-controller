from django.db import migrations


def create_tracks(apps, schema_editor):
    Track = apps.get_model('player', 'Track')
    demo_tracks = [
        {
            'title': 'Morning Focus',
            'artist': 'Demo Library',
            'audio_file': 'audio/morning-focus.mp3',
            'duration': '03:12',
        },
        {
            'title': 'Night Drive',
            'artist': 'Demo Library',
            'audio_file': 'audio/night-drive.mp3',
            'duration': '02:48',
        },
        {
            'title': 'Soft Coding',
            'artist': 'Demo Library',
            'audio_file': 'audio/soft-coding.mp3',
            'duration': '04:05',
        },
        {
            'title': 'Lecture Break',
            'artist': 'Demo Library',
            'audio_file': 'audio/lecture-break.mp3',
            'duration': '01:56',
        },
    ]

    for track in demo_tracks:
        Track.objects.get_or_create(
            title=track['title'],
            artist=track['artist'],
            defaults={
                'audio_file': track['audio_file'],
                'duration': track['duration'],
            },
        )


def remove_tracks(apps, schema_editor):
    Track = apps.get_model('player', 'Track')
    Track.objects.filter(artist='Demo Library').delete()


class Migration(migrations.Migration):
    dependencies = [
        ('player', '0001_initial'),
    ]

    operations = [
        migrations.RunPython(create_tracks, remove_tracks),
    ]
