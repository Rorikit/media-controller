from django import forms

from .models import Playlist


class PlaylistForm(forms.ModelForm):
    class Meta:
        model = Playlist
        fields = ['name', 'description']
        widgets = {
            'name': forms.TextInput(attrs={
                'placeholder': 'Например: Учёба, вечер, фокус',
                'class': 'field',
            }),
            'description': forms.Textarea(attrs={
                'placeholder': 'Короткое описание плейлиста',
                'class': 'field field-area',
                'rows': 3,
            }),
        }
