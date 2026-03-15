from django.contrib import admin
from django.urls import path, include
from django.shortcuts import redirect
from django.conf import settings
from django.conf.urls.static import static
from community_app import views   # ← API 用に追加

def root_redirect(request):
    return redirect('login')

urlpatterns = [
    path('', root_redirect, name='root'),
    path('admin/', admin.site.urls),

    # accounts アプリ
    path('accounts/', include('accounts.urls')),

    # community_app（投稿機能）
    path('', include('community_app.urls')),

    # ★ API（ここに追加）
    #path("api/post/create/", views.api_post_create, name="api_post_create"),
]

urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)