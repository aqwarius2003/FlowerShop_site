from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from flowershopservice.admin_views import assign_deliverer_confirm

# Основные URL для сайта
urlpatterns = [
    path('admin/assign-deliverer-confirm/', 
         admin.site.admin_view(assign_deliverer_confirm),
         name='assign_deliverer_confirm'),
    path('admin/', admin.site.urls),
    path('', include('flowershopservice.urls')),  # все URL приложения
]

# Добавляем обработку статических файлов
if settings.DEBUG:
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    # Добавляем специальный обработчик для файлов в static/img/catalog/
    urlpatterns += static(
        '/static/img/catalog/', 
        document_root=settings.BASE_DIR / 'static' / 'img' / 'catalog'
    )
