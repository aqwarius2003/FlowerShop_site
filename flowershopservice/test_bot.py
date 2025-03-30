import os
import sys
import requests
import logging
from django.conf import settings

# Настраиваем логирование
logging.basicConfig(level=logging.INFO, 
                   format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Добавляем путь к проекту для импорта настроек
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "flowershop.settings")

# Импортируем Django и настраиваем
import django
django.setup()

# Импортируем после настройки Django
from flowershopservice.telegram_service import TelegramNotifier
from flowershopservice.models import ShopUser

def test_send_to_chat():
    """Тест отправки сообщения в общий чат"""
    logger.info("Тестирование отправки сообщения в общий чат")
    result = TelegramNotifier.send_message("Тестовое сообщение в общий чат")
    logger.info(f"Результат отправки в общий чат: {result}")
    return result

def test_send_to_user(telegram_id):
    """Тест отправки сообщения конкретному пользователю"""
    logger.info(f"Тестирование отправки сообщения пользователю {telegram_id}")
    result = TelegramNotifier.send_to_user(
        telegram_id, 
        f"Тестовое сообщение для пользователя {telegram_id}"
    )
    logger.info(f"Результат отправки пользователю: {result}")
    return result

def test_direct_api():
    """Тест прямого обращения к API Telegram"""
    logger.info("Тестирование прямого обращения к API Telegram")
    token = settings.TELEGRAM_BOT_TOKEN
    chat_id = settings.TELEGRAM_CHAT_ID
    
    if not token or not chat_id:
        logger.error("Не настроены учетные данные Telegram")
        return False
        
    url = f"https://api.telegram.org/bot{token}/sendMessage"
    payload = {
        "chat_id": chat_id,
        "text": "Тестовое сообщение через прямой API запрос",
        "parse_mode": "HTML"
    }
    
    try:
        response = requests.post(url, json=payload, timeout=10)
        logger.info(f"Статус ответа: {response.status_code}")
        logger.info(f"Ответ API: {response.json()}")
        return response.status_code == 200
    except Exception as e:
        logger.error(f"Ошибка при прямом обращении к API: {e}")
        return False

def test_delivery_person():
    """Тест отправки сообщения доставщикам"""
    logger.info("Тестирование отправки сообщений доставщикам")
    
    # Получаем всех доставщиков с telegram_id
    delivery_users = ShopUser.objects.filter(
        status='delivery', 
        telegram_id__isnull=False
    ).exclude(telegram_id='')
    
    if not delivery_users.exists():
        logger.warning("Не найдено доставщиков с Telegram ID")
        return
        
    logger.info(f"Найдено доставщиков: {delivery_users.count()}")
    
    for user in delivery_users:
        logger.info(f"Отправка тестового сообщения доставщику: {user.full_name} (ID: {user.telegram_id})")
        
        # Проверяем валидность telegram_id - должен быть числом
        try:
            int(user.telegram_id)
        except ValueError:
            logger.error(f"Неправильный формат Telegram ID: {user.telegram_id}")
            continue
        
        result = TelegramNotifier.send_to_user(
            user.telegram_id, 
            f"Тестовое сообщение для доставщика {user.full_name}"
        )
        
        logger.info(f"Результат отправки: {result}")

def test_specific_delivery_person():
    """Тест отправки сообщения конкретному доставщику по имени"""
    delivery_name = input("Введите имя доставщика для тестирования или нажмите Enter для пропуска: ")
    
    if not delivery_name:
        logger.info("Тестирование конкретного доставщика пропущено")
        return
        
    try:
        user = ShopUser.objects.filter(
            status='delivery', 
            full_name__icontains=delivery_name
        ).first()
        
        if not user:
            logger.warning(f"Доставщик с именем '{delivery_name}' не найден")
            return
            
        if not user.telegram_id:
            logger.warning(f"У доставщика {user.full_name} не указан Telegram ID")
            return
            
        logger.info(f"Найден доставщик: {user.full_name} (ID: {user.telegram_id})")
        
        # Отправляем тестовое сообщение
        result = TelegramNotifier.send_to_user(
            user.telegram_id, 
            f"🧪 Тестовое сообщение для доставщика {user.full_name}"
        )
        
        logger.info(f"Результат отправки тестового сообщения: {result}")
    except Exception as e:
        logger.error(f"Ошибка при тестировании конкретного доставщика: {e}")

if __name__ == "__main__":
    logger.info("Запуск тестирования Telegram бота")
    
    # Тестируем отправку в общий чат
    test_send_to_chat()
    
    # Тестируем прямое обращение к API
    test_direct_api()
    
    # Тестируем отправку доставщикам
    test_delivery_person()
    
    # Тестируем отправку конкретному доставщику
    test_specific_delivery_person()
    
    logger.info("Тестирование завершено") 