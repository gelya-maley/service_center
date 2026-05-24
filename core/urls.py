from django.urls import path, re_path
from . import views

urlpatterns = [
    path('', views.home, name='home'),
    path('services/', views.service_list, name='service_list'),
    path('services/<int:pk>/', views.service_detail, name='service_detail'),
    path('about/', views.about, name='about'),
    path('contacts/', views.contacts, name='contacts'),
    path('faq/', views.faq, name='faq'),
    path('vacancies/', views.vacancies, name='vacancies'),
    path('reviews/', views.reviews, name='reviews'),
    path('reviews/add/', views.add_review, name='add_review'),
    path('promocodes/', views.promocodes, name='promocodes'),
    path('statistics/', views.statistics, name='statistics'),
    path('privacy/', views.privacy_policy, name='privacy_policy'),
    
    re_path(r'^order/(?P<order_id>\d+)/$', views.order_detail, name='order_detail'),
    
    path('search/', views.search_orders, name='search_orders'),
    path('cabinet/', views.cabinet, name='cabinet'),
    
    # API endpoints - только для авторизованных пользователей
    path('api/weather/', views.api_weather, name='api_weather'),
    path('api/exchange/', views.api_exchange, name='api_exchange'),
]