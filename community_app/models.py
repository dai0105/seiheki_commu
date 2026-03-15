from django.db import models
from django.contrib.auth.models import User
from accounts.models import Tag
from django.contrib.auth import get_user_model

class FetishTag(models.Model):
    name = models.CharField(max_length=50, unique=True)

    def __str__(self):
        return self.name


class Post(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    content = models.TextField(max_length=500, blank=True)
    tags = models.ManyToManyField(Tag, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    image = models.CharField(max_length=500, blank=True, null=True)
    video = models.CharField(max_length=500, blank=True, null=True)

    def __str__(self):
        return f"{self.user.username} - {self.content[:20]}"


class Category(models.Model):
    name = models.CharField(max_length=50)

    def __str__(self):
        return self.name

class Room(models.Model):
    category = models.ForeignKey(Category, on_delete=models.CASCADE)
    name = models.CharField(max_length=50)
    description = models.TextField(blank=True)
    max_members = models.IntegerField(default=5)
    created_by = models.ForeignKey(User, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.category.name} - {self.name}"
    

User = get_user_model()
class Message(models.Model):
    room = models.ForeignKey(Room, on_delete=models.CASCADE, related_name='messages')
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    content = models.TextField(blank=True)
    image = models.ImageField(upload_to='room_images/', blank=True, null=True)
    video = models.FileField(upload_to='room_videos/', blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

class RoomMember(models.Model):
    room = models.ForeignKey(Room, on_delete=models.CASCADE, related_name='members')
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    joined_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('room', 'user')

class DMRoom(models.Model):
    user1 = models.ForeignKey(User, related_name='dm_user1', on_delete=models.CASCADE)
    user2 = models.ForeignKey(User, related_name='dm_user2', on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('user1', 'user2')

    def __str__(self):
        return f"{self.user1.username} - {self.user2.username}"

    def get_partner(self, user):
        return self.user2 if self.user1 == user else self.user1

    @property
    def latest_message(self):
        return self.messages.order_by('-created_at').first()
    
class DMMessage(models.Model):
    room = models.ForeignKey(
        DMRoom,
        on_delete=models.CASCADE,
        related_name='messages'
    )
    sender = models.ForeignKey(User, on_delete=models.CASCADE)
    content = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    image = models.ImageField(upload_to='dm_images/', blank=True, null=True)
    video = models.FileField(upload_to='dm_videos/', blank=True, null=True)

class Block(models.Model):
    blocker = models.ForeignKey(User, related_name='blocking', on_delete=models.CASCADE)
    blocked = models.ForeignKey(User, related_name='blocked_by', on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('blocker', 'blocked')

    def __str__(self):
        return f"{self.blocker} → {self.blocked}"