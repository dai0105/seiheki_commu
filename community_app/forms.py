from django import forms
from .models import Post, Room

class PostForm(forms.ModelForm):
    class Meta:
        model = Post
        fields = ['content', 'tags']  # ← image/video は絶対に入れない
        widgets = {
            'content': forms.Textarea(attrs={'rows': 3}),
            'tags': forms.CheckboxSelectMultiple(),
        }

class RoomForm(forms.ModelForm):
    class Meta:
        model = Room
        fields = ['category', 'name', 'max_members', 'description']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'input-field'}),
            'max_members': forms.NumberInput(attrs={'class': 'input-field', 'min': 4, 'max': 10}),
            'description': forms.Textarea(attrs={'class': 'input-field', 'rows': 3}),
            'category': forms.Select(attrs={'class': 'input-field'}),
        }