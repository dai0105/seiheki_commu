from django.db import models
from django.contrib.auth.models import User
from django import forms

class Tag(models.Model):
    name = models.CharField(max_length=50, unique=True)

    def __str__(self):
        return self.name


AGE_CHOICES = [
    ('18-22', '18〜22歳'),
    ('23-27', '23〜27歳'),
    ('28-32', '28〜32歳'),
    ('33-37', '33〜37歳'),
    ('38-42', '38〜42歳'),
    ('43-47', '43〜47歳'),
    ('48-52', '48〜52歳'),
    ('53+', '53歳以上'),
]

AGE_RANGE_CHOICES = [
    ('18-22', '18〜22歳'),
    ('23-27', '23〜27歳'),
    ('28-32', '28〜32歳'),
    ('33-37', '33〜37歳'),
    ('38-42', '38〜42歳'),
    ('43-47', '43〜47歳'),
    ('48-52', '48〜52歳'),
    ('53+', '53歳以上'),
]

class Profile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    nickname = models.CharField(max_length=50)
    age_range = models.CharField(max_length=10, choices=AGE_RANGE_CHOICES)
    gender = models.CharField(max_length=10)
    bio = models.TextField(blank=True)
    icon = models.ImageField(upload_to='icons/', blank=True, null=True)
    tags = models.ManyToManyField(Tag, blank=True)
    stripe_customer_id = models.CharField(max_length=255, null=True, blank=True)
    def __str__(self):
        return self.nickname
    


class ProfileForm(forms.ModelForm):
    class Meta:
        model = Profile
        fields = ['nickname', 'age_range', 'bio', 'icon', 'tags']

class Contact(models.Model):
    name = models.CharField(max_length=100, blank=True)
    email = models.EmailField(blank=True)
    message = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.name or '匿名'} - {self.created_at}"