from django.core.management.base import BaseCommand

from player.models import Track


class Command(BaseCommand):
    help = 'Creates real demo tracks for the media player course project.'

    def handle(self, *args, **options):
        tracks = [
            (
                'CAFé CON RON',
                'Bad Bunny, Los Pleneros de la Cresta',
                'audio/Bad Bunny, Los Pleneros de la Cresta - CAFé CON RON.mp3',
            ),
            (
                'Ganga Riddim (ft. Mehdi Nassouli)',
                'Jarreau Vandal, Dave Nunes',
                'audio/Jarreau Vandal, Dave Nunes - Ganga Riddim (ft. Mehdi Nassouli).mp3',
            ),
            ('Ultrasound', 'Arcando x Pirapus', 'audio/Arcando x Pirapus - Ultrasound.mp3'),
            ('Blackout', 'Lokal', 'audio/Lokal - Blackout.mp3'),
            ("Nobody's Listening", 'Linkin Park', "audio/Linkin Park - Nobody's Listening.mp3"),
            ('Till I Collapse', 'Eminem feat. Nate Dogg', 'audio/Eminem feat. Nate Dogg - Till I Collapse.mp3'),
            ('Утренний рассвет', 'Король и Шут', 'audio/Король и Шут - Утренний рассвет.mp3'),
            ('Far Away', 'Nickelback', 'audio/Nickelback - Far Away.mp3'),
            ('VICTIMIZED', 'LINKIN PARK', 'audio/LINKIN PARK - VICTIMIZED.mp3'),
            ('High Voltage', 'Linkin Park', 'audio/Linkin Park - High Voltage.mp3'),
            ('Something In The Way', 'Nirvana', 'audio/Nirvana - Something In The Way.mp3'),
        ]

        # Старые учебные заглушки удаляются, чтобы в интерфейсе оставались только реальные файлы.
        Track.objects.filter(artist__in=['Demo Library', 'Student Beats']).delete()
        Track.objects.filter(audio_file='').delete()

        saved = 0
        for title, artist, audio_file in tracks:
            Track.objects.update_or_create(
                title=title,
                artist=artist,
                defaults={
                    'audio_file': audio_file,
                    'duration': '',
                },
            )
            saved += 1

        self.stdout.write(self.style.SUCCESS(f'Tracks ready. Saved: {saved}.'))
