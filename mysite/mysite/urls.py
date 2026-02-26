
from django.contrib import admin
from django.urls import path, include
from django.conf.urls.static import static, settings

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', include('booklist.urls')),
    path('accounts/', include('django.contrib.auth.urls')),
] + (static(settings.STATIC_URL, document_root=settings.STATIC_ROOT) +
    static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT))

