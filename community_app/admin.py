from django.contrib import admin
from .models import FetishTag, Post
from .models import Category, Room, Message

admin.site.register(FetishTag)
admin.site.register(Post)
admin.site.register(Category)
admin.site.register(Room)
admin.site.register(Message)