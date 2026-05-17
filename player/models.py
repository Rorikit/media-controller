from django.db import models


class Track(models.Model):
    # Модель трека хранит данные, которые нужны и серверу, и JS-плееру на странице.
    title = models.CharField(max_length=120, verbose_name='Название')
    artist = models.CharField(max_length=120, blank=True, verbose_name='Исполнитель')
    audio_file = models.FileField(upload_to='audio/', blank=True, verbose_name='Аудиофайл')
    duration = models.CharField(max_length=16, blank=True, verbose_name='Длительность')
    cover_image = models.FileField(upload_to='covers/', blank=True, verbose_name='Обложка')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['title']
        verbose_name = 'Трек'
        verbose_name_plural = 'Треки'

    def __str__(self):
        if self.artist:
            return f'{self.artist} - {self.title}'
        return self.title


class Playlist(models.Model):
    # ManyToManyField позволяет одному треку находиться в нескольких плейлистах.
    name = models.CharField(max_length=120, unique=True, verbose_name='Название')
    description = models.TextField(blank=True, verbose_name='Описание')
    tracks = models.ManyToManyField(Track, blank=True, related_name='playlists', verbose_name='Треки')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Плейлист'
        verbose_name_plural = 'Плейлисты'

    def __str__(self):
        return self.name
