from django.shortcuts import render, get_object_or_404
from django.http import JsonResponse
from django.template.loader import render_to_string
from .models import Product

# Create your views here.

def index(request):
    return render(request, 'index.html')

def catalog(request):
    # Получаем все активные букеты из базы данных
    bouquets = Product.objects.filter(status='active')
    
    # Для каждого букета модифицируем путь к изображению, убирая 'static/' из начала пути
    for bouquet in bouquets:
        if bouquet.image and str(bouquet.image).startswith('static/'):
            bouquet.image_url = str(bouquet.image)[7:]  # Убираем 'static/' из начала пути
        else:
            bouquet.image_url = str(bouquet.image)
    
    # Определяем начальное количество отображаемых букетов
    items_per_page = 6
    
    # Рассчитываем, нужно ли показывать кнопку "Показать еще"
    show_more_button = len(bouquets) > items_per_page
    
    # Передаем только первые N букетов в шаблон
    initial_bouquets = bouquets[:items_per_page]
    
    context = {
        'bouquets': initial_bouquets,
        'total_bouquets': len(bouquets),
        'show_more_button': show_more_button,
    }
    
    return render(request, 'catalog.html', context)

# Представление для загрузки дополнительных букетов
def load_more_bouquets(request):
    # Получаем количество уже загруженных букетов
    offset = int(request.GET.get('offset', 0))
    
    # Количество букетов, которые нужно загрузить
    limit = 3
    
    # Получаем все активные букеты из базы данных
    bouquets = Product.objects.filter(status='active')
    
    # Для каждого букета модифицируем путь к изображению, убирая 'static/' из начала пути
    for bouquet in bouquets:
        if bouquet.image and str(bouquet.image).startswith('static/'):
            bouquet.image_url = str(bouquet.image)[7:]  # Убираем 'static/' из начала пути
        else:
            bouquet.image_url = str(bouquet.image)
    
    # Получаем следующую порцию букетов
    more_bouquets = bouquets[offset:offset+limit]
    
    # Проверяем, есть ли еще букеты для загрузки
    has_more = len(bouquets) > offset + limit
    
    # Рендерим HTML для новых букетов
    html = render_to_string('bouquet_items.html', {'bouquets': more_bouquets}, request=request)
    
    # Возвращаем JSON с HTML и информацией о наличии дополнительных букетов
    return JsonResponse({
        'html': html,
        'has_more': has_more,
        'next_offset': offset + limit,
    })

def card(request, bouquet_id=None):
    # Получаем конкретный букет по id или используем заглушку
    if bouquet_id:
        bouquet = get_object_or_404(Product, id=bouquet_id)
    else:
        # Если id не указан, возвращаем первый букет из базы (временное решение)
        bouquet = Product.objects.filter(status='active').first()
    
    # Модифицируем путь к изображению
    if bouquet.image and str(bouquet.image).startswith('static/'):
        bouquet.image_url = str(bouquet.image)[7:]  # Убираем 'static/' из начала пути
    else:
        bouquet.image_url = str(bouquet.image)
    
    return render(request, 'card.html', {'bouquet': bouquet})

def consultation(request):
    return render(request, 'consultation.html')

def order(request):
    return render(request, 'order.html')

def order_step(request):
    return render(request, 'order-step.html')

def order_complete(request):
    # Здесь будет логика обработки заказа
    return render(request, 'order-step.html')

def quiz(request):
    return render(request, 'quiz.html')

def quiz_step(request):
    return render(request, 'quiz-step.html')

def result(request):
    # Получаем случайный активный букет
    random_bouquet = Product.objects.filter(status='active').order_by('?').first()
    
    # Модифицируем путь к изображению
    if random_bouquet and random_bouquet.image:
        if str(random_bouquet.image).startswith('static/'):
            random_bouquet.image_url = str(random_bouquet.image)[7:]
        else:
            random_bouquet.image_url = str(random_bouquet.image)
    
    return render(request, 'result.html', {'bouquet': random_bouquet})

def privacy(request):
    # Создайте шаблон privacy.html или перенаправляйте куда-то
    return render(request, 'privacy.html')
