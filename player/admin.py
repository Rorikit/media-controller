from django.contrib import admin

from .models import Playlist, Track


@admin.register(Track)
class TrackAdmin(admin.ModelAdmin):
    list_display = ('title', 'artist', 'duration', 'created_at')
    search_fields = ('title', 'artist')
    list_filter = ('created_at',)


@admin.register(Playlist)
class PlaylistAdmin(admin.ModelAdmin):
    list_display = ('name', 'track_count', 'created_at')
    search_fields = ('name',)
    filter_horizontal = ('tracks',)

    @admin.display(description='Количество треков')
    def track_count(self, obj):
        return obj.tracks.count()
