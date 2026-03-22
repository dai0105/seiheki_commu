from django.urls import path
from . import views

urlpatterns = [
    path('gender_select/', views.gender_select, name='gender_select'),
    path('register/', views.register, name='register'),
    path('profile/setup/', views.profile_setup, name='profile_setup'),
    path('login/', views.login_view, name='login'),
    



    path('profile/<int:user_id>/', views.profile_view, name='profile'),
    path('profile/edit/', views.profile_edit, name='profile_edit'),

  

    path('delete/confirm/', views.account_delete_confirm, name='account_delete_confirm'),
    path('delete/', views.account_delete, name='account_delete'),

    path('contact/', views.contact, name='contact'),
    path('contact/done/', views.contact_done, name='contact_done'),
    path("terms/", views.terms, name="terms"),

    path('password-reset/', views.password_reset_request, name='password_reset_request'),
    path('password-reset/confirm/<int:user_id>/', views.password_reset_confirm, name='password_reset_confirm'),
    path('password-reset/done/', views.password_reset_done, name='password_reset_done'),
]