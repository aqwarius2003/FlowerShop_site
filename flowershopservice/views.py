from django.shortcuts import get_object_or_404
from django.template.loader import render_to_string
from .models import Product, DeliveryTimeSlot, Category, PriceRange
import datetime
from django.shortcuts import render, redirect

from django.http import JsonResponse
from django.views.decorators.http import require_POST
from .models import ShopUser, Consultation, Order
import uuid
import logging
from django.utils import timezone  # Добавляем импорт timezone

logger = logging.getLogger(__name__)


def index(request):
    # Получаем рекомендуемые товары
    featured_products = Product.get_featured_products()
    
    return render(request, 'index.html', {
        'featured_products': featured_products
    })


def catalog(request):
    # Получаем все активные букеты из базы данных
    bouquets = Product.objects.filter(status='active')

    # Для каждого букета модифицируем путь к изображению, убирая 'static/' из начала пути
    for bouquet in bouquets:
        if bouquet.image and str(bouquet.image).startswith('static/'):
            bouquet.image_url = str(bouquet.image)[
                                7:]  # Убираем 'static/' из начала пути
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
            bouquet.image_url = str(bouquet.image)[
                                7:]  # Убираем 'static/' из начала пути
        else:
            bouquet.image_url = str(bouquet.image)

    # Получаем следующую порцию букетов
    more_bouquets = bouquets[offset:offset + limit]

    # Проверяем, есть ли еще букеты для загрузки
    has_more = len(bouquets) > offset + limit

    # Рендерим HTML для новых букетов
    html = render_to_string('bouquet_items.html', {'bouquets': more_bouquets},
                            request=request)

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


def show_consultation(request):
    return render(request, 'consultation.html')


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
                'full_name': name,
                'status': 'user',
            }
        )
        Consultation.objects.create(user=user)
        return JsonResponse({
            'success': True,
            'message': 'Спасибо за обращение! Мы свяжемся с вами в ближайшее время.',
            'user_name': name,
            'user_phone': phone,
        })
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)})


def order(request):
    # Получаем ID букета из параметров URL
    bouquet_id = request.GET.get('bouquet_id')
    
    if bouquet_id:
        # Получаем букет и сохраняем его данные в сессии
        try:
            bouquet = Product.objects.get(id=bouquet_id)
            request.session['bouquet_data'] = {
                'id': bouquet.id,
                'name': bouquet.name,
                'price': str(bouquet.price),
                'composition': bouquet.composition
            }
        except Product.DoesNotExist:
            pass

    # Получаем текущую дату и время
    current_date = datetime.date.today()
    current_time = datetime.datetime.now().time()

    # Специальный слот "Как можно скорее"
    express_slot = DeliveryTimeSlot.objects.filter(is_express=True).first()
    
    # Получаем обычные слоты (не экспресс)
    regular_slots = DeliveryTimeSlot.objects.filter(is_express=False).order_by(
        'time_start')

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
    
    # Проверяем доступность экспресс-слота
    express_available = False
    express_message = None
    if express_slot:
        # Проверяем время с учетом 30-минутного интервала
        time_diff = datetime.datetime.combine(datetime.date.today(), express_slot.time_end) - datetime.datetime.combine(datetime.date.today(), current_time)
        if time_diff.total_seconds() > 1800:  # Более 30 минут до конца слота
            express_available = True
    
    context = {
        'express_slot': express_slot if express_available else None,
        'express_message': express_message,
        'today_slots': today_slots,
        'tomorrow_slots': tomorrow_slots,
        'current_date': current_date,
        'tomorrow_date': current_date + datetime.timedelta(days=1)
    }

    return render(request, 'order.html', context)


def order_step(request):
    if request.method == 'POST':
        # Обработка данных формы
        name = request.POST.get('fname', '')
        phone = request.POST.get('tel', '')
        address = request.POST.get('adres', '')
        order_time = request.POST.get('orderTime', '')

        # Логирование для отладки
        logger.info(f"Order form data: name={name}, phone={phone}, address={address}, time={order_time}")

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
                    logger.info(f"Express delivery: {delivery_time_from} - {delivery_time_to}")
            except Exception as e:
                logger.error(f"Error getting express time slot: {str(e)}")
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
                logger.info(f"Today delivery: {delivery_time_from} - {delivery_time_to}")
            except DeliveryTimeSlot.DoesNotExist:
                logger.error(f"Time slot not found: {slot_id}")
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
                logger.info(f"Tomorrow delivery: {delivery_time_from} - {delivery_time_to}")
            except DeliveryTimeSlot.DoesNotExist:
                logger.error(f"Time slot not found: {slot_id}")
                pass

        # Сохраняем информацию в сессии для последующего создания заказа
        request.session['order_data'] = {
            'name': name,
            'phone': phone,
            'address': address,
            'delivery_date': delivery_date.isoformat(),
            'is_express': is_express,
            'delivery_time_from': delivery_time_from.strftime(
                '%H:%M:%S') if delivery_time_from else None,
            'delivery_time_to': delivery_time_to.strftime(
                '%H:%M:%S') if delivery_time_to else None
        }
        logger.info(f"Saved order data to session: {request.session['order_data']}")

    return render(request, 'order-step.html')


# def order_complete(request):
#     # Здесь будет логика обработки заказа
#     return render(request, 'order-step.html')

def order_complete(request):
    if request.method == 'POST':
        # Обработка данных формы и создание заказа
        return JsonResponse({
            'success': True,
            'message': 'Заказ успешно оформлен!',
        })
    return render(request, 'order-step.html')


def quiz(request):
    # Получаем все категории из базы данных
    categories = Category.objects.all().order_by('name')
    return render(request, 'quiz.html', {'categories': categories})


def quiz_step(request, category_id):
    # Получаем выбранную категорию
    category = get_object_or_404(Category, id=category_id)
    
    # Получаем все ценовые диапазоны
    price_ranges = PriceRange.objects.all().order_by('min_price')
    
    context = {
        'category': category,
        'price_ranges': price_ranges
    }
    
    return render(request, 'quiz-step.html', context)


def result(request):
    """Показывает случайный букет из всего каталога"""
    # Получаем случайный активный букет
    random_bouquet = Product.objects.filter(status='active').order_by('?').first()

    # Модифицируем путь к изображению
    if random_bouquet and random_bouquet.image:
        if str(random_bouquet.image).startswith('static/'):
            random_bouquet.image_url = str(random_bouquet.image)[7:]
        else:
            random_bouquet.image_url = str(random_bouquet.image)

    return render(request, 'result.html', {'bouquet': random_bouquet})


def result_filtered(request, category_id, price_range_id):
    """Показывает букет, отфильтрованный по категории и ценовому диапазону"""
    # Получаем выбранную категорию и ценовой диапазон
    category = get_object_or_404(Category, id=category_id)
    price_range = get_object_or_404(PriceRange, id=price_range_id)
    
    # Получаем букеты, соответствующие критериям
    # Сначала фильтрация по категории
    bouquets = Product.objects.filter(
        categories=category,
        status='active'
    )
    
    # Затем по ценовому диапазону
    if price_range.min_price and price_range.max_price:
        bouquets = bouquets.filter(price__gte=price_range.min_price, price__lte=price_range.max_price)
    elif price_range.min_price:
        bouquets = bouquets.filter(price__gte=price_range.min_price)
    elif price_range.max_price:
        bouquets = bouquets.filter(price__lte=price_range.max_price)
    
    # Если нет подходящих букетов, берем все активные
    if not bouquets.exists():
        bouquets = Product.objects.filter(status='active')
    
    # Берем случайный букет из отфильтрованного списка
    random_bouquet = bouquets.order_by('?').first()
    
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

def process_order(request):
    if request.method == 'POST':
        # Получаем данные заказа и букета из сессии
        order_data = request.session.get('order_data', {})
        bouquet_data = request.session.get('bouquet_data', {})
        
        # Логирование для отладки
        logger.info(f"Order data from session: {order_data}")
        logger.info(f"Bouquet data from session: {bouquet_data}")
        
        if not order_data:
            logger.error("Order data not found in session")
            return JsonResponse({'success': False, 'error': 'Данные заказа не найдены'})
        
        if not bouquet_data:
            logger.error("Bouquet data not found in session")
            return JsonResponse({'success': False, 'error': 'Данные букета не найдены'})
        
        try:
            # Получаем букет
            bouquet = Product.objects.get(id=bouquet_data['id'])
            logger.info(f"Found product: {bouquet.name}, ID: {bouquet.id}")
            
            # Создаем или получаем пользователя
            user, created = ShopUser.objects.get_or_create(
                phone=order_data['phone'],
                defaults={
                    # Удаляем поле user_id, так как его нет в модели
                    'full_name': order_data['name'],
                    'status': 'user',
                    'address': order_data['address']
                }
            )
            logger.info(f"User: {user.full_name}, Created: {created}")

            # Создаем заказ с информацией о букете
            order = Order.objects.create(
                user=user,
                product=bouquet,
                product_name=bouquet.name,
                product_price=bouquet.price,
                product_composition=bouquet.composition,
                delivery_address=order_data['address'],
                delivery_date=datetime.datetime.strptime(order_data['delivery_date'], '%Y-%m-%d').date(),
                is_express_delivery=order_data['is_express'],
                status='created',
                creation_date=timezone.now()  # Явно указываем текущее время с учетом часового пояса
            )
            logger.info(f"Created order with ID: {order.id}")

            # Добавляем время доставки, если оно есть
            if order_data.get('delivery_time_from'):
                order.delivery_time_from = datetime.datetime.strptime(
                    order_data['delivery_time_from'], '%H:%M:%S').time()
            if order_data.get('delivery_time_to'):
                order.delivery_time_to = datetime.datetime.strptime(
                    order_data['delivery_time_to'], '%H:%M:%S').time()
            
            order.save()
            logger.info(f"Order saved: {order.id}")

            # Очищаем данные из сессии
            del request.session['order_data']
            del request.session['bouquet_data']
            
            return JsonResponse({
                'success': True,
                'message': 'Мы свяжемся с Вами в ближайшее время для уточнения заказа',
                'order_id': order.id
            })
            
        except Exception as e:
            logger.error(f"Error creating order: {str(e)}", exc_info=True)
            return JsonResponse({'success': False, 'error': str(e)})
    
    return JsonResponse({'success': False, 'error': 'Неверный метод запроса'})


def contacts(request):
    return render(request, 'contacts.html')
