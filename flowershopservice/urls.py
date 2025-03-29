from django.urls import path
from flowershopservice import views

urlpatterns = [
    path('', views.index, name='index'),
    path('catalog/', views.catalog, name='catalog'),
    path('catalog/load-more/', views.load_more_bouquets, name='load_more_bouquets'),
    path('card/', views.card, name='card'),
    path('card/<int:bouquet_id>/', views.card, name='bouquet_detail'),
    path('consultation/', views.consultation, name='consultation'),
    path("contacts/", views.contacts, name="contacts"),
    path('order/', views.order, name='order'),
    path('order-step/', views.order_step, name='order_step'),
    path('order-complete/', views.order_complete, name='order_complete'),
    path('quiz/', views.quiz, name='quiz'),
    path('quiz-step/', views.quiz_step, name='quiz_step'),
    path('result/', views.result, name='result'),
    path('privacy/', views.privacy, name='privacy'),
]
