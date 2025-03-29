from django.contrib import admin
from flowershopservice.models import ShopUser, Category, PriceRange, Product, \
    DeliveryTimeSlot, Order, \
    Consultation, DeliveryManagement, FlowerShop
from django.utils import timezone


@admin.register(ShopUser)
class ShopUserAdmin(admin.ModelAdmin):
    list_display = ['full_name', 'phone', 'status']
    list_filter = ['status']
    search_fields = ['full_name', 'phone']


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ['name']
    search_fields = ['name']


@admin.register(PriceRange)
class PriceRangeAdmin(admin.ModelAdmin):
    list_display = ['__str__', 'min_price', 'max_price']


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ['name', 'price', 'status']
    list_filter = ['status', 'categories']
    search_fields = ['name', 'description']
    filter_horizontal = ['categories']


@admin.register(DeliveryTimeSlot)
class DeliveryTimeSlotAdmin(admin.ModelAdmin):
    list_display = ['time_start', 'time_end', 'display_name', 'is_express',
                    'is_available_tomorrow']
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
    list_display = ['product', 'user', 'status', 'delivery_date', 'is_express_delivery',
                    'creation_date']
    list_filter = ['status', 'delivery_date', 'is_express_delivery', 'creation_date']
    search_fields = ['user__full_name', 'delivery_address', 'product__name']

    fieldsets = (
        ('Основная информация', {
            'fields': ('product', 'user', 'comment', 'status')
        }),
        ('Информация о доставке', {
            'fields': ('delivery_address', 'delivery_date', 'is_express_delivery',
                       'delivery_time_from', 'delivery_time_to', 'actual_delivery_time')
        }),
        ('Исполнители', {
            'fields': ('manager', 'delivery_person', 'delivery_comments')
        }),
    )


@admin.register(Consultation)
class ConsultationAdmin(admin.ModelAdmin):
    list_display = ['user', 'get_phone', 'creation_date', 'status_display', 'processed']
    list_filter = ['processed', 'creation_date']
    ordering = ['creation_date']  # Сортировка от старых к новым

    def get_phone(self, obj):
        return obj.user.phone

    get_phone.short_description = 'Телефон'

    def status_display(self, obj):
        if obj.processed:
            return 'Обработано'
        now = timezone.now()
        delta = now - obj.creation_date
        if delta.total_seconds() > 20 * 60:  # Проверка на 20 минут
            return 'Просрочено'
        return 'Не обработано'

    status_display.short_description = 'Статус заявки'


@admin.register(DeliveryManagement)
class DeliveryManagementAdmin(admin.ModelAdmin):
    list_display = ['delivery_person', 'working_date', 'shift_start', 'shift_end',
                    'is_available', 'current_orders_count', 'max_orders_per_day']
    list_filter = ['working_date', 'is_available', 'delivery_person']
    search_fields = ['delivery_person__full_name']


@admin.register(FlowerShop)
class FlowerShopAdmin(admin.ModelAdmin):
    list_display = ("name", "city", "address", "phone")
    search_fields = ("name", "city")
