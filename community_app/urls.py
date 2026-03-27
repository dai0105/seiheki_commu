from django.urls import path
from . import views
from django.urls import path, include
from . import views


urlpatterns = [
    #path('accounts/', include('accounts.urls')),
    path('post/create/', views.post_create, name='post_create'),
    path('post/<int:post_id>/delete/', views.post_delete, name='post_delete'),
    path('timeline/', views.timeline, name='timeline'),
    path('post/<int:post_id>/delete/', views.post_delete, name='post_delete'),
    path('community/rooms/', views.room_list, name='room_list'),
    path('rooms/load_more/', views.load_more_rooms, name='load_more_rooms'),
    path('community/rooms/create/', views.room_create, name='room_create'),
    path('community/rooms/<int:room_id>/', views.room_detail, name='room_detail'),
    path('rooms/<int:room_id>/join/', views.join_room, name='join_room'),
    path('rooms/<int:room_id>/leave/', views.leave_room, name='leave_room'),
    path('rooms/<int:room_id>/delete/', views.room_delete, name='room_delete'),
    path('dm/start/<int:user_id>/', views.dm_start, name='dm_start'),
    path('dm/<int:room_id>/', views.dm_detail, name='dm_detail'),
    path('dm/', views.dm_list, name='dm_list'),
    path('block/<int:user_id>/', views.block_user, name='block_user'),
    path('qa/', views.qa_page, name='qa_page'),
]