from django.shortcuts import get_object_or_404
from django.template.loader import render_to_string
from .models import Product, DeliveryTimeSlot
import datetime
from django.shortcuts import render, redirect

from django.http import JsonResponse
from django.views.decorators.http import require_POST
from .models import ShopUser, Consultation
import uuid


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

@require_POST
def consultation(request):
    name = request.POST.get('fname', '').strip()
    phone = request.POST.get('tel', '').strip()

    if not name or not phone:
        return JsonResponse({'success': False, 'error': 'Заполните все поля'})

    try:
        user, created = ShopUser.objects.get_or_create(
            phone=phone,
            defaults={
                'user_id': str(uuid.uuid4()),
                'full_name': name,
                'status': 'user',
            }
        )
        Consultation.objects.create(user=user)
        return JsonResponse({
            'success': True,
            'user_name': name,
            'user_phone': phone,
        })
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)})

def order(request):
    # Получаем текущую дату и время
    current_date = datetime.date.today()
    current_time = datetime.datetime.now().time()
    
    # Специальный слот "Как можно скорее"
    express_slot = DeliveryTimeSlot.objects.filter(is_express=True).first()
    
    # Получаем обычные слоты (не экспресс)
    regular_slots = DeliveryTimeSlot.objects.filter(is_express=False).order_by('time_start')
    
    # Разделяем слоты на доступные сегодня и завтра
    today_slots = []
    tomorrow_slots = []
    
    for slot in regular_slots:
        # Слот доступен сегодня, если текущее время меньше времени окончания слота
        # и не слишком близко к времени окончания (мин. 30 минут до конца)
        time_diff = datetime.datetime.combine(datetime.date.today(), slot.time_end) - datetime.datetime.combine(datetime.date.today(), current_time)
        if time_diff.total_seconds() > 1800:  # Более 30 минут до конца слота
            today_slots.append(slot)
            
        # Если слот доступен для доставки завтра
        if slot.is_available_tomorrow:
            tomorrow_slots.append(slot)
    
    # Для отладки
    print(f"Express slot: {express_slot}")
    print(f"Today slots: {today_slots}")
    print(f"Tomorrow slots: {tomorrow_slots}")
    
    context = {
        'express_slot': express_slot,
        'today_slots': today_slots,
        'tomorrow_slots': tomorrow_slots,
        'current_date': current_date,
        'tomorrow_date': current_date + datetime.timedelta(days=1)
    }
    
    return render(request, 'order.html', context)

def order_step(request):
    if request.method == 'GET':
        # Получаем данные из формы
        order_time = request.GET.get('orderTime', '')
        
        # Обрабатываем выбранный слот доставки
        delivery_date = datetime.date.today()
        is_express = False
        delivery_time_from = None
        delivery_time_to = None
        
        if order_time.startswith('express'):
            # Это экспресс-доставка
            is_express = True
            # Если для экспресс-доставки нужно указать время, получаем экспресс-слот
            try:
                express_slot = DeliveryTimeSlot.objects.filter(is_express=True).first()
                if express_slot:
                    delivery_time_from = express_slot.time_start
                    delivery_time_to = express_slot.time_end
            except:
                pass
        elif order_time.startswith('today'):
            # Доставка сегодня
            _, slot_id = order_time.split('-')
            slot_id = int(slot_id)
            # Получаем слот доставки
            try:
                time_slot = DeliveryTimeSlot.objects.get(id=slot_id)
                delivery_time_from = time_slot.time_start
                delivery_time_to = time_slot.time_end
            except DeliveryTimeSlot.DoesNotExist:
                pass
        elif order_time.startswith('tomorrow'):
            # Доставка завтра
            delivery_date = datetime.date.today() + datetime.timedelta(days=1)
            _, slot_id = order_time.split('-')
            slot_id = int(slot_id)
            # Получаем слот доставки
            try:
                time_slot = DeliveryTimeSlot.objects.get(id=slot_id)
                delivery_time_from = time_slot.time_start
                delivery_time_to = time_slot.time_end
            except DeliveryTimeSlot.DoesNotExist:
                pass
        
        # Сохраняем информацию в сессии для последующего создания заказа
        request.session['order_data'] = {
            'name': request.GET.get('fname', ''),
            'phone': request.GET.get('tel', ''),
            'address': request.GET.get('adres', ''),
            'delivery_date': delivery_date.isoformat(),
            'is_express': is_express,
            'delivery_time_from': delivery_time_from.strftime('%H:%M:%S') if delivery_time_from else None,
            'delivery_time_to': delivery_time_to.strftime('%H:%M:%S') if delivery_time_to else None
        }
        
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
