from django.urls import path
from . import views

urlpatterns = [
    path('gender_select/', views.gender_select, name='gender_select'),
    path('register/', views.register, name='register'),
    path('profile/setup/', views.profile_setup, name='profile_setup'),
    path('login/', views.login_view, name='login'),
    path('payment/start/', views.payment_start, name='payment_start'),
    

    # ログイン後のトップページ
    #path('home/', views.home, name='home'),


    # ここから課金ページ
    #path('payment/', views.payment, name='payment'),
    path('webhook/stripe/', views.stripe_webhook, name='stripe_webhook'),
    path('create-checkout-session/', views.create_checkout_session, name='create_checkout_session'),
    path('payment/success/', views.payment_success, name='payment_success'),
    path('payment/cancel/', views.payment_cancel, name='payment_cancel'),

    path('profile/<int:user_id>/', views.profile_view, name='profile'),
    path('profile/edit/', views.profile_edit, name='profile_edit'),

    path('billing/', views.billing_portal, name='billing_portal'),
    path('cancel/', views.cancel_subscription, name='cancel_subscription'),

    path('delete/confirm/', views.account_delete_confirm, name='account_delete_confirm'),
    path('delete/', views.account_delete, name='account_delete'),

    path('contact/', views.contact, name='contact'),
    path('contact/done/', views.contact_done, name='contact_done'),
    path("terms/", views.terms, name="terms"),

    path('password-reset/', views.password_reset_request, name='password_reset_request'),
    path('password-reset/confirm/<int:user_id>/', views.password_reset_confirm, name='password_reset_confirm'),
    path('password-reset/done/', views.password_reset_done, name='password_reset_done'),
]