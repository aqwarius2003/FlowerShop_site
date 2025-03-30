import os
import django
import json
import random
import shutil
import datetime
from decimal import Decimal

# Установите переменную окружения для настроек Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'flowershop.settings')

# Инициализируйте Django
django.setup()

from flowershopservice.models import Product, Category, PriceRange, DeliveryTimeSlot
from django.conf import settings

# Определяем базовый путь к папке raw_base
RAW_BASE_PATH = 'raw_base'

print("Начинаем импорт данных...")

# ==================== СОЗДАНИЕ ЦЕНОВЫХ ДИАПАЗОНОВ ====================
print("\nСоздание ценовых диапазонов...")

try:
    with open(os.path.join(RAW_BASE_PATH, 'price_ranges.json'), 'r', encoding='utf-8') as file:
        price_ranges_data = json.load(file)
    
    for price_range in price_ranges_data:
        min_price = Decimal(price_range["min_price"]) if price_range["min_price"] is not None else None
        max_price = Decimal(price_range["max_price"]) if price_range["max_price"] is not None else None
        
        obj, created = PriceRange.objects.get_or_create(
            min_price=min_price,
            max_price=max_price
        )
        if created:
            print(f"Создан ценовой диапазон: {obj}")
        else:
            print(f"Ценовой диапазон уже существует: {obj}")
except FileNotFoundError:
    print("Файл price_ranges.json не найден!")
    exit(1)

# ==================== СОЗДАНИЕ СЛОТОВ ДОСТАВКИ ====================
print("\nСоздание слотов доставки...")

try:
    with open(os.path.join(RAW_BASE_PATH, 'delivery_slots.json'), 'r', encoding='utf-8') as file:
        delivery_slots_data = json.load(file)
    
    for slot in delivery_slots_data:
        time_start = datetime.datetime.strptime(slot["time_start"], "%H:%M").time()
        time_end = datetime.datetime.strptime(slot["time_end"], "%H:%M").time()
        
        obj, created = DeliveryTimeSlot.objects.get_or_create(
            time_start=time_start,
            time_end=time_end,
            defaults={
                "display_name": slot["display_name"],
                "is_available_tomorrow": slot["is_available_tomorrow"],
                "is_express": slot["is_express"]
            }
        )
        if created:
            print(f"Создан слот доставки: {obj}")
        else:
            print(f"Слот доставки уже существует: {obj}")
except FileNotFoundError:
    print("Файл delivery_slots.json не найден!")
    exit(1)

# ==================== ЗАГРУЗКА БУКЕТОВ ====================
print("\nЗагрузка букетов...")

try:
    # Загрузка данных из JSON файла
    with open(os.path.join(RAW_BASE_PATH, 'raw_base.json'), 'r', encoding='utf-8') as file:
        bouquets_data = json.load(file)

    # Определяем пути
    SOURCE_IMAGE_FOLDER = os.path.join(RAW_BASE_PATH, 'flower_img')
    
    # Проверяем наличие папки с изображениями
    if not os.path.exists(SOURCE_IMAGE_FOLDER):
        print(f"Папка {SOURCE_IMAGE_FOLDER} не найдена!")
        exit(1)
    
    # Создаем директорию для каталога, если её нет
    os.makedirs(os.path.join(settings.MEDIA_ROOT, 'catalog'), exist_ok=True)

    # Создание категорий
    categories_set = set()
    for bouquet in bouquets_data:
        for category in bouquet['fields']['categories']:
            categories_set.add(category)

    for category_name in categories_set:
        Category.objects.get_or_create(name=category_name)
        print(f"Категория '{category_name}' добавлена или уже существует")

    # Получаем список всех изображений
    image_files = os.listdir(SOURCE_IMAGE_FOLDER)
    random.shuffle(image_files)

    # Добавляем букеты
    for i, bouquet in enumerate(bouquets_data):
        if i >= len(image_files):
            print("Недостаточно изображений для всех букетов!")
            break

        fields = bouquet['fields']
        name = fields['name']
        
        # Проверяем существование букета
        if Product.objects.filter(name=name).exists():
            print(f'Букет "{name}" уже существует, пропускаем.')
            continue
        
        # Копируем изображение
        image_file = image_files[i]
        source_image_path = os.path.join(SOURCE_IMAGE_FOLDER, image_file)
        relative_image_path = os.path.join('catalog', image_file)
        destination_image_path = os.path.join(settings.MEDIA_ROOT, 'catalog', image_file)

        shutil.copy(source_image_path, destination_image_path)

        # Создаем продукт
        product = Product(
            name=name,
            description=fields['description'],
            composition=fields['composition'],
            price=fields['price'],
            image=relative_image_path,
            status='active'
        )
        
        product.save()

        # Добавляем категории
        for category_name in fields['categories']:
            category = Category.objects.get(name=category_name)
            product.categories.add(category)

        print(f'Добавлен букет: {name} (цена: {fields["price"]} руб.)')

except FileNotFoundError:
    print("Файл raw_base.json не найден!")
    exit(1)
except Exception as e:
    print(f"Произошла ошибка: {str(e)}")
    exit(1)

print("\nИмпорт данных успешно завершен!")