import os
import django
import json
import random
import shutil
from django.conf import settings
from django.core.exceptions import ValidationError

# Установите переменную окружения для настроек Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'flowershop.settings')

# Инициализируйте Django
django.setup()

from flowershopservice.models import Shop

# Пути к данным
RAW_BASE_PATH = 'raw_base'
IMAGE_SOURCE_FOLDER = os.path.join(RAW_BASE_PATH, 'addresses')
SHOPS_JSON_PATH = os.path.join(RAW_BASE_PATH, 'shops.json')

def main():
    print("\nЗагрузка магазинов...")
    
    # Проверка папки с изображениями
    if not os.path.exists(IMAGE_SOURCE_FOLDER):
        print(f"Папка {IMAGE_SOURCE_FOLDER} не найдена!")
        return

    # Загрузка данных магазинов
    try:
        with open(SHOPS_JSON_PATH, 'r', encoding='utf-8') as f:
            shops_data = json.load(f)
    except FileNotFoundError:
        print("Файл shops.json не найден!")
        return

    # Получение списка доступных изображений
    image_files = [
        f for f in os.listdir(IMAGE_SOURCE_FOLDER) 
        if f.lower().endswith(('.png', '.jpg', '.jpeg'))
    ]
    if not image_files:
        print("Нет доступных изображений в папке addresses!")
        return

    # Создание директории для медиа
    os.makedirs(os.path.join(settings.MEDIA_ROOT, 'shops'), exist_ok=True)

    for shop_data in shops_data:
        fields = shop_data['fields']
        
        # Копирование случайного изображения
        try:
            image_file = random.choice(image_files)
            source_path = os.path.join(IMAGE_SOURCE_FOLDER, image_file)
            dest_path = os.path.join('shops', image_file)
            full_dest_path = os.path.join(settings.MEDIA_ROOT, dest_path)
            
            if not os.path.exists(full_dest_path):
                shutil.copy(source_path, full_dest_path)
        except Exception as e:
            print(f"Ошибка копирования изображения: {str(e)}")
            dest_path = None

        # Создание объекта магазина
        try:
            Shop.objects.update_or_create(
                title=fields['title'],
                defaults={
                    'address': fields['address'],
                    'phone': fields['phone'],
                    'image': dest_path,
                    'working_hours': fields.get('working_hours', '10:00-20:00'),
                    'description': fields.get('description', ''),
                    'slug': fields['slug'],
                    'meta_title': fields.get('meta_title', ''),
                    'meta_description': fields.get('meta_description', ''),
                    'order': fields.get('order', 0),
                    'is_active': fields.get('is_active', True)
                }
            )
            print(f"Обработан магазин: {fields['title']}")
        except ValidationError as e:
            print(f"Ошибка валидации для {fields['title']}: {str(e)}")

if __name__ == '__main__':
    main()
