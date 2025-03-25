from django.contrib import admin
from .models import ShopUser, Category, PriceRange, Product, DeliveryTimeSlot, Order, Consultation

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
    list_display = ['date', 'time_start', 'time_end', 'max_deliveries', 'current_deliveries']
    list_filter = ['date']

@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ['product', 'user', 'status', 'creation_date']
    list_filter = ['status', 'creation_date']
    search_fields = ['user__full_name', 'delivery_address']

@admin.register(Consultation)
class ConsultationAdmin(admin.ModelAdmin):
    list_display = ['user', 'creation_date', 'processed']
    list_filter = ['processed', 'creation_date']
