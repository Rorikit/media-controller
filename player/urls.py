from django.urls import path

from . import views

urlpatterns = [
    path('', views.index, name='index'),
    path('playlist/create/', views.create_playlist, name='create_playlist'),
    path('playlist/<int:pk>/', views.playlist_detail, name='playlist_detail'),
    path('playlist/<int:pk>/delete/', views.delete_playlist, name='delete_playlist'),
    path(
        'playlist/<int:playlist_pk>/add/<int:track_pk>/',
        views.add_track_to_playlist,
        name='add_track_to_playlist',
    ),
    path(
        'playlist/<int:playlist_pk>/remove/<int:track_pk>/',
        views.remove_track_from_playlist,
        name='remove_track_from_playlist',
    ),
    path('track/<int:track_pk>/add-to-playlist/', views.add_track_from_select, name='add_track_from_select'),
]
