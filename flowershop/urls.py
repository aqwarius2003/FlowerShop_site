from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', include('flowershopservice.urls')),  # все URL приложения
]

# Добавляем обработку статических файлов
if settings.DEBUG:
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    # Добавляем специальный обработчик для файлов в static/img/catalog/
    urlpatterns += static('/static/img/catalog/', document_root=settings.BASE_DIR / 'static' / 'img' / 'catalog')
