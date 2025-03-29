from django.contrib import admin
from .models import ShopUser, Category, PriceRange, Product, DeliveryTimeSlot, Order, Consultation, DeliveryManagement
from django.utils.html import mark_safe, format_html
from django.db import models
from django.utils import timezone
from django.utils.formats import date_format
from django import forms
from django.core.validators import RegexValidator

@admin.register(ShopUser)
class ShopUserAdmin(admin.ModelAdmin):
    list_display = ['full_name', 'phone', 'status']
    list_filter = ['status']
    search_fields = ['full_name', 'phone']

    # Добавляем форму для кастомизации полей
    class ShopUserAdminForm(forms.ModelForm):
        phone = forms.CharField(
            max_length=20,
            validators=[
                RegexValidator(
                    regex=r'^\+?1?\d{9,15}$',
                    message="Номер телефона должен быть в формате: '+999999999'. До 15 цифр."
                )
            ],
            widget=forms.TextInput(attrs={'placeholder': '+7 (999) 999-99-99'})
        )

        class Meta:
            model = ShopUser
            fields = '__all__'

    form = ShopUserAdminForm

@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ['name']
    search_fields = ['name']

@admin.register(PriceRange)
class PriceRangeAdmin(admin.ModelAdmin):
    list_display = ['__str__', 'min_price', 'max_price']

@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ('admin_image_preview', 'name', 'price', 'status')
    list_display_links = ('admin_image_preview', 'name')
    search_fields = ('name', 'description')
    list_filter = ('status', 'categories', 'is_featured')
    filter_horizontal = ['categories']

    # Настраиваем размеры текстовых полей
    formfield_overrides = {
        models.TextField: {'widget': admin.widgets.AdminTextareaWidget(attrs={'rows': 3})},
    }

    # Добавляем CSS для уменьшения высоты виджета с категориями
    class Media:
        css = {
            'all': (
                'admin/css/custom.css',
            )
        }

    def formfield_for_manytomany(self, db_field, request, **kwargs):
        if db_field.name == "categories":
            kwargs['widget'] = admin.widgets.FilteredSelectMultiple(
                db_field.verbose_name,
                is_stacked=False,
            )
        return super().formfield_for_manytomany(db_field, request, **kwargs)

    def get_image_preview(self, obj):
        if obj.image:
            return mark_safe(f'<img src="{obj.image.url}" width="50" height="50" style="object-fit: cover; vertical-align: middle; margin-right: 10px;" />')
        return "Нет фото"
    get_image_preview.short_description = 'Текущее фото'

    readonly_fields = ('get_image_preview',)

    fieldsets = (
        (None, {
            'fields': (
                ('name', 'price'),
                ('get_image_preview', 'image'),  # Добавляем превью рядом с полем загрузки
                'description',
                'composition',
                'categories',
                ('status', 'is_featured'),
            ),
            'classes': ('wide',)
        }),
    )

@admin.register(DeliveryTimeSlot)
class DeliveryTimeSlotAdmin(admin.ModelAdmin):
    list_display = ['time_start', 'time_end', 'display_name', 'is_express', 'is_available_tomorrow']
    list_filter = ['is_express', 'is_available_tomorrow']
    list_editable = ['display_name', 'is_available_tomorrow']
    
    def get_fieldsets(self, request, obj=None):
        return [
            (None, {
                'fields': ('time_start', 'time_end', 'display_name')
            }),
            ('Настройки доступности', {
                'fields': ('is_express', 'is_available_tomorrow')
            })
        ]

@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    def get_phone(self, obj):
        return obj.user.phone if obj.user else '-'
    get_phone.short_description = 'Телефон'

    def get_delivery_time(self, obj):
        if obj.is_express_delivery:
            return format_html(
                '<span style="color: red;"><b>СРОЧНЫЙ</b></span><br>'
                '<small>Создан: {}</small>',
                timezone.localtime(obj.creation_date).strftime('%H:%M') if obj.creation_date else 'Неизвестно'
            )
        return f"{obj.delivery_time_from.strftime('%H:%M')}-{obj.delivery_time_to.strftime('%H:%M')}" if obj.delivery_time_from and obj.delivery_time_to else 'Неизвестно'
    get_delivery_time.short_description = "Время доставки"
    get_delivery_time.allow_tags = True

    list_display = (
        'get_bouquet_preview', 
        'product',
        'user',
        'get_phone',
        'get_delivery_time',
        'status',
        'delivery_date',
        'display_creation_date'
    )
    list_display_links = ('get_bouquet_preview', 'product')
    search_fields = (
        'product__name', 
        'user__full_name', 
        'user__phone', 
        'delivery_address'
    )
    list_filter = ('status', 'delivery_date', 'is_express_delivery')
    list_editable = ('status',)
    
    # Уменьшаем высоту поля комментария
    formfield_overrides = {
        models.TextField: {'widget': admin.widgets.AdminTextareaWidget(attrs={'rows': 3})},
    }

    def get_bouquet_preview(self, obj):
        if obj.product and obj.product.image:
            return mark_safe(f'<img src="{obj.product.image.url}" width="50" height="50" style="object-fit: cover;" />')
        return "Нет фото"
    get_bouquet_preview.short_description = 'Фото'

    # Настройка полей формы
    fieldsets = (
        ('Основная информация', {
            'fields': ('product', 'user', 'status', 'creation_date'),
        }),
        ('Информация о доставке', {
            'fields': ('delivery_date', 'delivery_address', 'is_express_delivery', 
                      'delivery_time_from', 'delivery_time_to'),
        }),
        ('Комментарии', {
            'fields': ('comment', 'delivery_comments'),
            'classes': ('collapse',),  # Делаем секцию сворачиваемой
        }),
    )

    # Делаем поле creation_date только для чтения
    readonly_fields = ('creation_date',)

    # Метод для форматирования времени создания с учетом часового пояса
    def display_creation_date(self, obj):
        """Отображение даты создания с учетом часового пояса"""
        if obj.creation_date:
            # Преобразуем время UTC в локальное время с учетом часового пояса из settings.py
            local_time = timezone.localtime(obj.creation_date)
            # Форматируем время согласно локализации
            return date_format(local_time, format='SHORT_DATETIME_FORMAT')
        return "-"
    display_creation_date.short_description = "Создан"

@admin.register(Consultation)
class ConsultationAdmin(admin.ModelAdmin):
    list_display = ['user', 'creation_date', 'processed']
    list_filter = ['processed', 'creation_date']

@admin.register(DeliveryManagement)
class DeliveryManagementAdmin(admin.ModelAdmin):
    list_display = ['delivery_person', 'working_date', 'shift_start', 'shift_end', 'is_available', 'current_orders_count', 'max_orders_per_day']
    list_filter = ['working_date', 'is_available', 'delivery_person']
    search_fields = ['delivery_person__full_name']
