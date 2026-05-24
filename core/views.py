import json
import logging
import requests
from django.shortcuts import render, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.db.models import Count, Sum
from django.db.models.functions import TruncMonth
from django.http import JsonResponse

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import io
import base64

logger = logging.getLogger(__name__)

from .models import (
    Order, Service, EmployeeProfile, Client, 
    OrderService, ServiceType, DeviceType, SparePart
)

def get_weather():
    try:
        url = "https://api.open-meteo.com/v1/forecast?latitude=53.9&longitude=27.5667&current_weather=true"
        response = requests.get(url, timeout=5)
        if response.status_code == 200:
            return response.json()['current_weather']['temperature']
    except Exception as e:
        logger.error(f"Weather API error: {e}")
    return "N/A"

def get_exchange_rate():
    try:
        url = "https://api.nbrb.by/exrates/rates/USD?parammode=2"
        response = requests.get(url, timeout=5)
        if response.status_code == 200:
            return response.json()['Cur_OfficialRate']
    except Exception as e:
        logger.error(f"Exchange rate API error: {e}")
    return "N/A"

def home(request):
    latest_service = Service.objects.order_by('-id').first()
    weather = get_weather()
    usd_rate = get_exchange_rate()
    logger.info(f"Home page viewed, weather: {weather}, USD: {usd_rate}")
    return render(request, 'core/home.html', {
        'latest_service': latest_service,
        'weather': weather,
        'usd_rate': usd_rate
    })

def service_list(request):
    services = Service.objects.select_related('service_type').all()
    return render(request, 'core/service_list.html', {'services': services})

def service_detail(request, pk):
    service = get_object_or_404(Service, pk=pk)
    return render(request, 'core/service_detail.html', {'service': service})

def about(request):
    return render(request, 'core/about.html')

def contacts(request):
    employees = EmployeeProfile.objects.select_related('user').all()
    return render(request, 'core/contacts.html', {'employees': employees})

def faq(request):
    return render(request, 'core/faq.html')

def vacancies(request):
    return render(request, 'core/vacancies.html')

def reviews(request):
    reviews_list = [
        {'name': 'Анна', 'rating': 5, 'text': 'Отличный сервис! Быстро починили ноутбук, спасибо!', 'date': '15/01/2025'},
        {'name': 'Дмитрий', 'rating': 4, 'text': 'Хорошо сделали, но долго ждал запчасть.', 'date': '10/01/2025'},
        {'name': 'Екатерина', 'rating': 5, 'text': 'Профессиональный подход. Рекомендую!', 'date': '05/01/2025'},
    ]
    return render(request, 'core/reviews.html', {'reviews': reviews_list})

def add_review(request):
    if request.method == 'POST':
        name = request.POST.get('name')
        rating = request.POST.get('rating')
        text = request.POST.get('text')
        
        errors = {}
        
        if not name or len(name) < 2 or len(name) > 100:
            errors['name'] = 'Имя должно быть от 2 до 100 символов'
        
        if not rating or rating not in ['1', '2', '3', '4', '5']:
            errors['rating'] = 'Выберите корректную оценку'
        
        if not text or len(text) < 10 or len(text) > 1000:
            errors['text'] = 'Текст отзыва должен быть от 10 до 1000 символов'
        
        if errors:
            return render(request, 'core/add_review.html', {'errors': errors, 'form_data': request.POST})
        else:
            return render(request, 'core/add_review.html', {'success': True})
    
    return render(request, 'core/add_review.html')

def promocodes(request):
    return render(request, 'core/promocodes.html')

def privacy_policy(request):
    """Страница политики конфиденциальности"""
    return render(request, 'core/privacy_policy.html')

@login_required
def order_detail(request, order_id):
    order = get_object_or_404(Order, id=order_id)
    return render(request, 'core/order_detail.html', {'order': order})

def search_orders(request):
    query = request.GET.get('q')
    sort_by = request.GET.get('sort', '-order_date')
    orders = Order.objects.select_related('client', 'master').all()
    if query:
        orders = orders.filter(client__full_name__icontains=query)
    orders = orders.order_by(sort_by)
    return render(request, 'core/search.html', {'orders': orders, 'query': query})

@login_required
def cabinet(request):
    if hasattr(request.user, 'client_profile') and request.user.client_profile:
        orders = request.user.client_profile.orders.all()
        return render(request, 'core/client_cabinet.html', {'orders': orders})
    elif hasattr(request.user, 'employee_profile') and request.user.employee_profile:
        orders = request.user.employee_profile.orders.all()
        return render(request, 'core/master_cabinet.html', {'orders': orders})
    else:
        return render(request, 'core/cabinet.html')

def generate_statistics_chart():
    orders_by_month = Order.objects.annotate(
        month=TruncMonth('order_date')
    ).values('month').annotate(
        count=Count('id')
    ).order_by('month')
    
    if not orders_by_month:
        months = []
        counts = []
    else:
        months = [item['month'].strftime('%b %Y') for item in orders_by_month if item['month']]
        counts = [item['count'] for item in orders_by_month]
    
    plt.figure(figsize=(10, 5))
    plt.plot(months, counts, marker='o', linestyle='-', color='royalblue', linewidth=2, markersize=8)
    plt.title('Динамика количества заказов по месяцам', fontsize=14, fontweight='bold')
    plt.xlabel('Месяц', fontsize=12)
    plt.ylabel('Количество заказов', fontsize=12)
    plt.grid(True, linestyle='--', alpha=0.7)
    plt.xticks(rotation=45, ha='right')
    plt.tight_layout()
    
    buffer = io.BytesIO()
    plt.savefig(buffer, format='png', dpi=100)
    buffer.seek(0)
    image_base64 = base64.b64encode(buffer.getvalue()).decode()
    plt.close()
    
    return image_base64

def statistics(request):
    all_orders = Order.objects.all()
    total_orders = all_orders.count()
    
    total_sum = sum(o.total_cost() for o in all_orders)
    avg_cost = total_sum / total_orders if total_orders > 0 else 0
    
    costs_list = sorted([float(o.total_cost()) for o in all_orders])
    if costs_list:
        n = len(costs_list)
        if n % 2 == 0:
            median_cost = (costs_list[n//2 - 1] + costs_list[n//2]) / 2
        else:
            median_cost = costs_list[n//2]
    else:
        median_cost = 0
    
    popular_service = OrderService.objects.values('service__name').annotate(
        total=Sum('quantity')
    ).order_by('-total').first()
    
    profitable_service = OrderService.objects.values('service__name', 'service__price').annotate(
        total_quantity=Sum('quantity')
    ).order_by('-total_quantity')
    
    if profitable_service:
        for item in profitable_service:
            item['total_revenue'] = float(item['service__price']) * item['total_quantity']
        most_profitable = max(profitable_service, key=lambda x: x['total_revenue'])
        most_profitable_name = most_profitable['service__name']
        most_profitable_revenue = most_profitable['total_revenue']
    else:
        most_profitable_name = "Нет данных"
        most_profitable_revenue = 0
    
    chart_base64 = generate_statistics_chart()
    services_alpha = Service.objects.select_related('service_type').all().order_by('name')
    
    context = {
        'total_orders': total_orders,
        'avg_cost': round(avg_cost, 2),
        'median_cost': round(median_cost, 2),
        'popular_service': popular_service['service__name'] if popular_service else "Нет данных",
        'most_profitable_name': most_profitable_name,
        'most_profitable_revenue': round(most_profitable_revenue, 2),
        'chart_base64': chart_base64,
        'services_alpha': services_alpha,
    }
    return render(request, 'core/statistics.html', context)

# API endpoints - только для авторизованных пользователей
@login_required
def api_weather(request):
    """API погоды - доступ только для авторизованных пользователей"""
    weather = get_weather()
    return JsonResponse({
        'temperature': weather,
        'unit': 'celsius',
        'status': 'success'
    })

@login_required
def api_exchange(request):
    """API курса валют - доступ только для авторизованных пользователей"""
    rate = get_exchange_rate()
    return JsonResponse({
        'usd_rate': rate,
        'currency': 'USD',
        'status': 'success'
    })