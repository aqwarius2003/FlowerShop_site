from django.db import models
from phone_field import PhoneField
import datetime
from django.utils.html import mark_safe
from django.utils import timezone
import random
from django.core.cache import cache
from .managers import ShopManager
from django.utils.text import slugify
from .utils import get_coordinates_by_address
from django.conf import settings
import logging


class ShopUser(models.Model):
    """
    Модель пользователя магазина.
    """
    full_name = models.CharField(max_length=100, verbose_name='ФИО')
    phone = PhoneField(blank=True, help_text='Телефон', unique=True)
    address = models.CharField(max_length=200, null=True, blank=True, verbose_name='Адрес')
    telegram_id = models.CharField(
        'Telegram ID',
        max_length=50,
        blank=True,  # Разрешаем пустое значение в форме
        null=True    # Разрешаем NULL в базе данных
    )
    STATUS_CHOICES = [
        ('owner', 'Владелец сервиса'),
        ('user', 'Пользователь'),
        ('admin', 'Админ'),
        ('manager', 'Менеджер'),
        ('delivery', 'Доставщик'),
    ]
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='user', verbose_name='Статус')

    def __str__(self):
        return self.full_name

    class Meta:
        verbose_name = "Пользователь"
        verbose_name_plural = "Пользователи"


class Category(models.Model):
    """
    Модель категорий букетов.
    """
    name = models.CharField(max_length=50, verbose_name='Название категории')

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = "Категория"
        verbose_name_plural = "Категории"
        ordering = ['name']


class PriceRange(models.Model):
    """
    Модель ценовых категорий
    """
    min_price = models.DecimalField(max_digits=8, decimal_places=2, null=True, blank=True,
                                    verbose_name='Минимальная цена')
    max_price = models.DecimalField(max_digits=8, decimal_places=2, null=True, blank=True,
                                    verbose_name='Максимальная цена')

    def __str__(self):
        if self.min_price and self.max_price:
            return f"{self.min_price} - {self.max_price} руб"
        elif self.min_price:
            return f"от {self.min_price} руб"
        elif self.max_price:
            return f"до {self.max_price} руб"
        else:
            return "Без ограничения"

    class Meta:
        verbose_name = "Ценовой диапазон"
        verbose_name_plural = "Ценовые диапазоны"

    def get_products(self):
        if self.min_price and self.max_price:
            return Product.objects.filter(price__gte=self.min_price, price__lte=self.max_price)
        elif self.min_price:
            return Product.objects.filter(price__gte=self.min_price)
        elif self.max_price:
            return Product.objects.filter(price__lte=self.max_price)
        else:
            return Product.objects.all()


class Product(models.Model):
    """
    Модель букета.
    """
    id = models.AutoField(primary_key=True, editable=False)
    name = models.CharField(max_length=30, verbose_name='Название')
    description = models.TextField(max_length=300, verbose_name='Описание')
    composition = models.TextField(verbose_name='Состав букета')
    price = models.DecimalField(max_digits=8, decimal_places=2, verbose_name='Цена')
    categories = models.ManyToManyField(Category, verbose_name='Категории')
    image = models.ImageField(upload_to='img/catalog/', verbose_name='Изображение')
    STATUS_CHOICES = [
        ('active', 'Актуальный'),
        ('archived', 'Архивный'),
    ]
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='active', verbose_name='Статус')
    is_featured = models.BooleanField(default=False, verbose_name='Показывать на главной')
    is_bestseller = models.BooleanField(default=False, verbose_name='Хит продаж')

    def __str__(self):
        return self.name

    def admin_image_preview(self):
        if self.image:
            return mark_safe(f'<img src="{self.image.url}" width="50" height="50" style="object-fit: cover;" />')
        return "Нет изображения"
    
    admin_image_preview.short_description = 'Превью'

    @classmethod
    def get_featured_products(cls):
        """Получение рекомендуемых товаров с кэшированием"""
        # Ключ для кэширования
        cache_key = 'featured_products'
        
        # Пробуем получить данные из кэша
        featured_products = cache.get(cache_key)
        
        if featured_products is None:
            # Получаем все активные товары с предзагрузкой изображений
            featured = cls.objects.filter(status='active', is_featured=True).select_related()
            non_featured = cls.objects.filter(status='active', is_featured=False).select_related()
            
            featured_count = featured.count()
            
            if featured_count >= 3:
                # Если отмеченных товаров больше 3, берем случайные 3
                featured_products = random.sample(list(featured), 3)
            else:
                # Если отмеченных товаров меньше 3, добавляем случайные неотмеченные
                featured_products = list(featured)
                needed_count = 3 - featured_count
                if needed_count > 0 and non_featured.exists():
                    random_products = random.sample(list(non_featured), min(needed_count, non_featured.count()))
                    featured_products.extend(random_products)
            
            # Кэшируем результат на 1 час
            cache.set(cache_key, featured_products, 60 * 60)
        
        return featured_products

    def save(self, *args, **kwargs):
        """Переопределяем метод save для инвалидации кэша при изменении товара"""
        cache.delete('featured_products')
        super().save(*args, **kwargs)

    class Meta:
        verbose_name = "Букет"
        verbose_name_plural = "Букеты"


class DeliveryTimeSlot(models.Model):
    """
    Модель временных слотов доставки
    """
    time_start = models.TimeField(verbose_name='Время начала')
    time_end = models.TimeField(verbose_name='Время окончания')
    display_name = models.CharField(max_length=100, blank=True, verbose_name='Название слота на сайте')
    is_available_tomorrow = models.BooleanField(default=True, verbose_name='Доступен для доставки на завтра')
    is_express = models.BooleanField(default=False, verbose_name='"Как можно скорее"')
    
    class Meta:
        verbose_name = "Слот доставки"
        verbose_name_plural = "Слоты доставки"
        ordering = ['time_start']

    def __str__(self):
        if self.display_name:
            return self.display_name
        return f"с {self.time_start.strftime('%H:%M')} до {self.time_end.strftime('%H:%M')}"
    
    def save(self, *args, **kwargs):
        # Автоматически генерируем название слота, если оно не задано
        if not self.display_name:
            self.display_name = f"с {self.time_start.strftime('%H:%M')} до {self.time_end.strftime('%H:%M')}"
        super().save(*args, **kwargs)
    
    def is_available_today(self):
        """Проверяет, доступен ли слот на сегодня (не истек)"""
        now = datetime.datetime.now().time()
        # Если текущее время меньше времени окончания слота, то слот доступен
        return now < self.time_end


class Order(models.Model):
    """
    Модель заказа.
    """
    # Связь с товаром (может быть null, если товар удален)
    product = models.ForeignKey(Product, on_delete=models.SET_NULL, null=True, blank=True, verbose_name='Букет')
    
    # Дублирующие поля для сохранения исторических данных
    product_name = models.CharField(max_length=200, verbose_name='Название букета')
    product_price = models.DecimalField(max_digits=10, decimal_places=2,
                                        verbose_name='Цена букета', default=0.0)
    product_image = models.CharField(max_length=255, null=True, blank=True, verbose_name='Изображение букета')
    product_composition = models.TextField(null=True, blank=True, verbose_name='Состав букета')
    
    user = models.ForeignKey(ShopUser, on_delete=models.CASCADE,
                             related_name='user_orders', verbose_name='Пользователь')
    comment = models.TextField(max_length=300, verbose_name='Комментарий к заказу', null=True, blank=True)
    delivery_address = models.CharField(max_length=200, verbose_name='Адрес доставки')
    
    # Поля для доставки
    delivery_date = models.DateField(verbose_name='Дата доставки', null=True)
    is_express_delivery = models.BooleanField(
        default=False, 
        verbose_name='Экспресс-доставка'
    )
    delivery_time_from = models.TimeField(verbose_name='Доставка с', null=True, blank=True)
    delivery_time_to = models.TimeField(verbose_name='Доставка до', null=True, blank=True)
    actual_delivery_time = models.DateTimeField(verbose_name='Фактическое время доставки', null=True, blank=True)
    
    creation_date = models.DateTimeField(
        default=timezone.now,
        verbose_name='Создан'
    )
    STATUS_CHOICES = [
        ('created', 'Создан'),
        ('inWork', 'В работе'),
        ('inDelivery', 'В доставке'),
        ('delivered', 'Выдан клиенту'),
        ('cancelled', 'Отменен'),
    ]
    status = models.CharField(max_length=12, choices=STATUS_CHOICES, default='created', verbose_name='Статус заказа')
    manager = models.ForeignKey(ShopUser, on_delete=models.CASCADE,
                                related_name='managed_orders', null=True, blank=True, verbose_name='Менеджер')
    delivery_person = models.ForeignKey(ShopUser, on_delete=models.CASCADE,
                                        related_name='delivery_orders', null=True, blank=True, verbose_name='Доставщик')
    delivery_comments = models.TextField(null=True, blank=True, verbose_name='Комментарии к доставке')

    def __str__(self):
        return f'Заказ {self.product_name} для {self.user.full_name}'

    class Meta:
        verbose_name = "Заказ"
        verbose_name_plural = "Заказы"


# Черновик модели для менеджмента доставки
class DeliveryManagement(models.Model):
    """
    Модель для управления доставщиками и их графиком
    """
    delivery_person = models.ForeignKey(ShopUser, on_delete=models.CASCADE, 
                                      related_name='delivery_schedule', 
                                      verbose_name='Доставщик')
    working_date = models.DateField(verbose_name='Рабочий день')
    shift_start = models.TimeField(verbose_name='Начало смены')
    shift_end = models.TimeField(verbose_name='Конец смены')
    max_orders_per_day = models.PositiveIntegerField(default=10, verbose_name='Максимум заказов в день')
    current_orders_count = models.PositiveIntegerField(default=0, verbose_name='Текущее количество заказов')
    is_available = models.BooleanField(default=True, verbose_name='Доступен для назначения')
    
    class Meta:
        verbose_name = "График доставщика"
        verbose_name_plural = "Графики доставщиков"
        unique_together = ['delivery_person', 'working_date']
    
    def __str__(self):
        return f"{self.delivery_person.full_name} на {self.working_date}"
    
    def has_capacity(self):
        """Проверяет, может ли доставщик взять еще заказы"""
        return self.current_orders_count < self.max_orders_per_day and self.is_available


class Consultation(models.Model):
    """
    Модель заявки на консультацию
    """
    user = models.ForeignKey(ShopUser, on_delete=models.CASCADE, 
                           related_name='consultations',
                           verbose_name='Пользователь')
    creation_date = models.DateTimeField(auto_now_add=True, verbose_name='Дата создания')
    processed = models.BooleanField(default=False, verbose_name='Статус заявки')
    manager = models.ForeignKey(ShopUser, on_delete=models.SET_NULL, 
                               null=True, blank=True, 
                               related_name='managed_consultations',
                               verbose_name='Менеджер')

    class Meta:
        verbose_name = "Консультация"
        verbose_name_plural = "Консультации"

    def __str__(self):
         return f'Консультация для {self.user.full_name} ({self.user.phone})'
    

class Shop(models.Model):
    title = models.CharField('Название', max_length=100)
    address = models.CharField('Адрес', max_length=200)
    phone = models.CharField('Телефон', max_length=20)
    coord_x = models.FloatField('Координата X (широта)', null=True, blank=True)
    coord_y = models.FloatField('Координата Y (долгота)', null=True, blank=True)
    image = models.ImageField('Фото салона', upload_to='shops/')
    order = models.PositiveIntegerField('Порядок', default=0)
    is_active = models.BooleanField('Активен', default=True)
    working_hours = models.CharField('Часы работы', max_length=100, default='10:00-20:00')
    description = models.TextField('Описание', blank=True)
    slug = models.SlugField('URL', unique=True)
    meta_title = models.CharField('Meta Title', max_length=150, blank=True)
    meta_description = models.TextField('Meta Description', blank=True)
    last_address = models.CharField(max_length=200, editable=False, null=True)

    class Meta:
        ordering = ['order']
        verbose_name = 'Магазин'
        verbose_name_plural = 'Магазины'
    
    objects = ShopManager()

    def __str__(self):
        return self.title

    def save(self, *args, **kwargs):
        from .utils import get_coordinates_by_address
        logger = logging.getLogger(__name__)
 
        if not self.slug:
            self.slug = slugify(self.title)

        # Проверяем, изменился ли адрес
        logger.info(f"Сохранение магазина {self.title}")
        logger.info(f"Текущий адрес: {self.address}")
        logger.info(f"Предыдущий адрес: {self.last_address}")

        if self.address != self.last_address:
            logger.info(f"Адрес изменился, получаем новые координаты")
            # Получаем координаты только если адрес изменился
            coordinates = get_coordinates_by_address(self.address)
            if coordinates:
                self.coord_x, self.coord_y = coordinates
                self.last_address = self.address
                logger.info(f"Получены новые координаты: широта={self.coord_x}, долгота={self.coord_y}")
            else:
                logger.warning(f"Не удалось получить координаты для адреса: {self.address}")
     
        super().save(*args, **kwargs)
        # Инвалидируем кэш при сохранении
        cache.delete('active_shops')
        logger.info(f"Магазин {self.title} сохранен")

    def admin_image_preview(self):
        """Метод для отображения превью в списке магазинов"""
        if self.image:
            return mark_safe(f'<img src="{self.image.url}" width="50" height="50" style="object-fit: cover;" />')
        return "Нет изображения"
    admin_image_preview.short_description = 'Фото'

    def get_image_preview(self):
        print(f"Image URL: {self.image.url if self.image else None}")  # Для отладки
        if self.image:
            return mark_safe(f'<img src="{self.image.url}" width="150" height="150" style="object-fit: cover;" />')
        return 'Нет изображения'
    get_image_preview.short_description = 'Превью изображения'

    def get_map_preview(self):
        """Метод для отображения карты в форме редактирования"""
        if self.coord_x and self.coord_y:
            map_id = f'map_{self.id}'
            return mark_safe(f'''
                <div id="{map_id}" style="width: 100%; height: 400px; margin-top: 10px;"></div>
                <script>
                    (function() {{
                        var mapElement = document.getElementById("{map_id}");
                        if (!mapElement) return;

                        function initMap() {{
                            try {{
                                var map = new ymaps.Map(mapElement, {{
                                    center: [{self.coord_x}, {self.coord_y}],
                                    zoom: 16,
                                    controls: ['zoomControl', 'fullscreenControl']
                                }});

                                var placemark = new ymaps.Placemark(
                                    [{self.coord_x}, {self.coord_y}],
                                    {{ balloonContent: "{self.title}" }}
                                );
                                map.geoObjects.add(placemark);
                                map.container.fitToViewport();
                            }} catch (e) {{
                                console.error('Ошибка при инициализации карты:', e);
                                mapElement.innerHTML = 'Ошибка загрузки карты: ' + e.message;
                            }}
                        }}

                        if (typeof ymaps !== 'undefined') {{
                            ymaps.ready(initMap);
                        }} else {{
                            console.error('API Яндекс.Карт не загружен');
                            mapElement.innerHTML = 'Ошибка: API Яндекс.Карт не загружен';
                        }}
                    }})();
                </script>
            ''')
        return "Координаты не указаны"
    get_map_preview.short_description = 'Предпросмотр на карте'
