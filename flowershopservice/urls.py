from django.urls import path
from . import views


urlpatterns = [
    path('', views.index, name='index'),
    path('catalog/', views.catalog, name='catalog'),
    path('catalog/load-more/', views.load_more_bouquets, name='load_more_bouquets'),
    path('card/', views.card, name='card'),
    path('card/<int:bouquet_id>/', views.card, name='bouquet_detail'),
    path('consultation/', views.consultation, name='consultation'),
    path('order/', views.order, name='order'),
    path('order-step/', views.order_step, name='order_step'),
    path('order-complete/', views.order_complete, name='order_complete'),
    path('quiz/', views.quiz, name='quiz'),
    path('quiz-step/<int:category_id>/', views.quiz_step, name='quiz_step'),
    path('result/', views.result, name='result'),
    path('result/<int:category_id>/<int:price_range_id>/', views.result_filtered, name='result_filtered'),
    path('privacy/', views.privacy, name='privacy'),
    path('process-order/', views.process_order, name='process_order'),
]