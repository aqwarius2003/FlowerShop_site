from django.db import models
from phone_field import PhoneField
import datetime


class ShopUser(models.Model):
    """
    Модель пользователя магазина.
    """
    user_id = models.CharField(max_length=20, unique=True, verbose_name='ID Телеграма')
    full_name = models.CharField(max_length=100, verbose_name='ФИО')
    phone = PhoneField(blank=True, help_text='Телефон')
    address = models.CharField(max_length=200, null=True, blank=True, verbose_name='Адрес')
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
    product_price = models.DecimalField(max_digits=10, decimal_places=2, verbose_name='Цена букета')
    product_image = models.CharField(max_length=255, null=True, blank=True, verbose_name='Изображение букета')
    product_composition = models.TextField(null=True, blank=True, verbose_name='Состав букета')
    
    user = models.ForeignKey(ShopUser, on_delete=models.CASCADE,
                             related_name='user_orders', verbose_name='Пользователь')
    comment = models.TextField(max_length=300, verbose_name='Комментарий к заказу', null=True, blank=True)
    delivery_address = models.CharField(max_length=200, verbose_name='Адрес доставки')
    
    # Поля для доставки
    delivery_date = models.DateField(verbose_name='Дата доставки', null=True)
    is_express_delivery = models.BooleanField(default=False, verbose_name='Доставка как можно скорее')
    delivery_time_from = models.TimeField(verbose_name='Доставка с', null=True, blank=True)
    delivery_time_to = models.TimeField(verbose_name='Доставка до', null=True, blank=True)
    actual_delivery_time = models.DateTimeField(verbose_name='Фактическое время доставки', null=True, blank=True)
    
    creation_date = models.DateTimeField(auto_now_add=True, verbose_name='Дата и время создания заказа')
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