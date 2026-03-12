from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User
from django import forms
from .models import Profile

class CustomUserCreationForm(UserCreationForm):
    username = forms.EmailField(label='メールアドレス')

    class Meta:
        model = User
        fields = ("username", "password1", "password2")


class ProfileForm(forms.ModelForm):
    class Meta:
        model = Profile
        fields = ['nickname', 'age_range', 'bio', 'icon', 'tags']
        labels = {
            'nickname': 'ニックネーム',
            'age_range': '年齢帯',
            'bio': '自己紹介',
            'icon': 'アイコン画像',
            'tags': 'タグ',
        }
        widgets = {
            'tags': forms.CheckboxSelectMultiple(),
        }

class ContactForm(forms.Form):
    name = forms.CharField(label='お名前', required=False)
    email = forms.EmailField(label='メールアドレス', required=False)
    message = forms.CharField(
        label='お問い合わせ内容',
        widget=forms.Textarea,
        required=True
    )