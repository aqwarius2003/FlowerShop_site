from django.contrib import admin
from .models import ShopUser, Category, PriceRange, Product, DeliveryTimeSlot, Order, Consultation, DeliveryManagement, Shop
from django.utils.html import mark_safe, format_html
from django.db import models
from django.utils import timezone
from django.utils.formats import date_format
from django import forms
from django.core.validators import RegexValidator
from django.conf import settings
from django.contrib import messages

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
        'delivery_person',
        'display_creation_date'
    )
    list_display_links = ('get_bouquet_preview', 'product')
    search_fields = (
        'product__name', 
        'user__full_name', 
        'user__phone', 
        'delivery_address'
    )
    list_filter = ('status', 'delivery_date', 'is_express_delivery', 'delivery_person')
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

    # Добавляем действия для быстрого назначения доставщика
    actions = ['assign_to_delivery']
    
    def assign_to_delivery(self, request, queryset):
        # Получаем всех доставщиков
        deliverers = ShopUser.objects.filter(status='delivery')
        
        # Если нет доставщиков, выдаем ошибку
        if not deliverers.exists():
            self.message_user(request, "Нет доступных доставщиков в системе!", level='ERROR')
            return
            
        # Если выбрано несколько заказов
        if queryset.count() > 1:
            self.message_user(request, "Выберите только один заказ для назначения доставщика", level='WARNING')
            return
            
        # Получаем единственный выбранный заказ
        order = queryset.first()
        
        # Если заказ уже в доставке и имеет доставщика
        if order.status == 'inDelivery' and order.delivery_person:
            self.message_user(request, 
                f"Заказ уже в доставке и назначен на {order.delivery_person.full_name}", 
                level='WARNING')
            return
            
        # Формируем HTML для выпадающего списка
        select_html = '<select name="deliverer" required style="margin: 10px 0;">'
        select_html += '<option value="">-- Выберите доставщика --</option>'
        
        for deliverer in deliverers:
            has_telegram = 'да' if deliverer.telegram_id else 'нет'
            select_html += f'<option value="{deliverer.id}">{deliverer.full_name} (TG: {has_telegram})</option>'
            
        select_html += '</select>'
        
        # Создаем форму выбора доставщика
        from django.http import HttpResponse
        from django.template.response import TemplateResponse
        
        context = {
            'title': f'Назначить доставщика для заказа #{order.id}',
            'select_html': select_html,
            'orders': queryset,
            'opts': self.model._meta,
            'app_label': self.model._meta.app_label,
            'order_id': order.id,
            'action_checkbox_name': admin.helpers.ACTION_CHECKBOX_NAME,
        }
        
        # Рендерим шаблон с формой
        return TemplateResponse(request, 
                                'admin/assign_deliverer.html', 
                                context)
    
    assign_to_delivery.short_description = "Назначить доставщика и отправить в доставку"

    # Настройка полей формы
    fieldsets = (
        ('Основная информация', {
            'fields': ('product', 'user', 'status', 'creation_date'),
        }),
        ('Информация о доставке', {
            'fields': ('delivery_date', 'delivery_address', 'is_express_delivery', 
                      'delivery_time_from', 'delivery_time_to', 'delivery_person'),
        }),
        ('Комментарии', {
            'fields': ('comment', 'delivery_comments'),
            'classes': ('collapse',),  # Делаем секцию сворачиваемой
        }),
    )

    # Делаем поле creation_date только для чтения
    readonly_fields = ('creation_date', 'user')
    
    # Фильтруем список доставщиков - показываем только пользователей со статусом 'delivery'
    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        if db_field.name == "delivery_person":
            kwargs["queryset"] = ShopUser.objects.filter(status='delivery')
        return super().formfield_for_foreignkey(db_field, request, **kwargs)

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

    # Автоматически меняем статус заказа на "В доставке" при назначении доставщика
    def save_model(self, request, obj, form, change):
        """
        Переопределяем метод сохранения модели, чтобы автоматически менять статус
        заказа на "В доставке" при назначении доставщика
        """
        # Получаем предыдущее состояние объекта (если он существует)
        if change and obj.pk:
            try:
                old_obj = self.model.objects.get(pk=obj.pk)
                old_delivery_person = old_obj.delivery_person
                
                # Если доставщик был изменен или назначен
                if obj.delivery_person and (not old_delivery_person or old_delivery_person.id != obj.delivery_person.id):
                    # Меняем статус на "В доставке" если он не был еще установлен
                    if obj.status != 'inDelivery':
                        obj.status = 'inDelivery'
                        messages.info(request, f"Статус заказа автоматически изменён на 'В доставке' при назначении доставщика.")
                    
            except self.model.DoesNotExist:
                pass
                
        # Если это новый заказ и сразу назначается доставщик
        elif not change and obj.delivery_person:
            obj.status = 'inDelivery'
        
        # Сохраняем модель
        super().save_model(request, obj, form, change)

@admin.register(Consultation)
class ConsultationAdmin(admin.ModelAdmin):
    list_display = ['user', 'creation_date', 'processed']
    list_filter = ['processed', 'creation_date']

@admin.register(DeliveryManagement)
class DeliveryManagementAdmin(admin.ModelAdmin):
    list_display = ['delivery_person', 'working_date', 'shift_start', 'shift_end', 'is_available', 'current_orders_count', 'max_orders_per_day']
    list_filter = ['working_date', 'is_available', 'delivery_person']
    search_fields = ['delivery_person__full_name']

@admin.register(Shop)
class ShopAdmin(admin.ModelAdmin):
    list_display = ('admin_image_preview', 'title', 'address', 'phone', 'working_hours', 'order', 'is_active')
    list_editable = ('order', 'is_active')
    search_fields = ('title', 'address')
    list_filter = ('is_active',)
    prepopulated_fields = {'slug': ('title',)}
    readonly_fields = ('coord_x', 'coord_y', 'get_map_preview', 'get_image_preview')
    
    fieldsets = (
        ('Основная информация', {
            'fields': (
                'title',
                'slug',
                ('get_image_preview', 'image'),
                'address',
                ('coord_x', 'coord_y'),
                'get_map_preview',
                'phone',
                'working_hours',
                'description',
            )
        }),
        ('SEO', {
            'fields': ('meta_title', 'meta_description'),
            'classes': ('collapse',),
        }),
        ('Настройки', {
            'fields': ('order', 'is_active'),
        }),
    )
    
    def get_map_preview(self, obj):
        if obj.coord_x and obj.coord_y:
            return mark_safe(f'''
                <div style="width: 100%; max-width: 800px; min-width: 400px;">
                    <div id="map_{obj.id}" style="width: 100%; aspect-ratio: 1; margin: 10px 0; background-color: #f5f5f5; border: 1px solid #ddd;"></div>
                </div>
                <script>
                    (function() {{
                        function waitForYMaps() {{
                            if (typeof ymaps !== 'undefined') {{
                                ymaps.ready(function() {{
                                    try {{
                                        console.log('Инициализация карты для {obj.id}...');
                                        var mapElement = document.getElementById("map_{obj.id}");
                                        
                                        if (!mapElement) {{
                                            console.error('Элемент карты не найден');
                                            return;
                                        }}

                                        var map = new ymaps.Map(mapElement, {{
                                            center: [{obj.coord_x}, {obj.coord_y}],
                                            zoom: 16,
                                            controls: ['zoomControl', 'fullscreenControl']
                                        }});

                                        var placemark = new ymaps.Placemark(
                                            [{obj.coord_x}, {obj.coord_y}],
                                            {{ balloonContent: "{obj.title}" }},
                                            {{ preset: 'islands#redDotIcon' }}
                                        );

                                        map.geoObjects.add(placemark);
                                        
                                        // Принудительно обновляем размер карты
                                        setTimeout(function() {{
                                            map.container.fitToViewport();
                                        }}, 100);

                                        console.log('Карта успешно создана');
                                    }} catch (e) {{
                                        console.error('Ошибка при создании карты:', e);
                                        var mapElement = document.getElementById("map_{obj.id}");
                                        if (mapElement) {{
                                            mapElement.innerHTML = '<div style="color: red; padding: 20px; text-align: center;">Ошибка загрузки карты: ' + e.message + '</div>';
                                        }}
                                    }}
                                }});
                            }} else {{
                                console.log('Ожидание загрузки API...');
                                setTimeout(waitForYMaps, 100);
                            }}
                        }}

                        if (document.readyState === 'loading') {{
                            document.addEventListener('DOMContentLoaded', waitForYMaps);
                        }} else {{
                            waitForYMaps();
                        }}
                    }})();
                </script>
            ''')
        return "Координаты не указаны"
    get_map_preview.short_description = 'Предпросмотр на карте'
    
    def admin_image_preview(self, obj):
        if obj.image:
            return mark_safe(f'<img src="{obj.image.url}" width="50" height="50" style="object-fit: cover;" />')
        return "Нет изображения"
    admin_image_preview.short_description = 'Фото'
    
    def get_image_preview(self, obj):
        if obj.image:
            return mark_safe(f'<img src="{obj.image.url}" width="200" style="max-height: 200px; object-fit: cover;" />')
        return "Нет изображения"
    get_image_preview.short_description = 'Текущее фото'

    class Media:
        js = (
            f'https://api-maps.yandex.ru/2.1/?apikey={settings.YANDEX_MAPS_API_KEY}&lang=ru_RU&load=package.full',
        )
        css = {
            'all': ('admin/css/custom.css',)
        }
