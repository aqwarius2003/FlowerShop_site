#!/usr/bin/env python
"""
Инструмент для отладки отправки сообщений доставщикам.
Позволяет проверить отправку сообщений в Telegram для конкретного заказа
или протестировать отправку сообщений произвольному доставщику.
"""

import os
import sys
import django

# Добавляем путь к проекту Django
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'flowershop.settings')
django.setup()

from flowershopservice.models import Order, ShopUser
from flowershopservice.telegram_service import TelegramNotifier
from flowershopservice.signals import send_to_delivery_person

def main():
    """Основная функция скрипта"""
    print("\n=== Отладчик отправки сообщений доставщикам ===\n")
    
    # Выбор действия
    print("Выберите действие:")
    print("1. Проверить отправку сообщения для существующего заказа")
    print("2. Отправить тестовое сообщение произвольному доставщику")
    choice = input("Ваш выбор (1/2): ")
    
    if choice == '1':
        test_existing_order()
    elif choice == '2':
        test_delivery_person()
    else:
        print("Неверный выбор")

def test_existing_order():
    """Проверка отправки сообщения для существующего заказа"""
    # Список заказов с назначенными доставщиками
    orders = Order.objects.filter(delivery_person__isnull=False).order_by('-id')[:10]
    
    if not orders:
        print("Не найдено заказов с назначенными доставщиками.")
        return
    
    print("\nПоследние заказы с назначенными доставщиками:")
    for i, order in enumerate(orders, 1):
        print(f"{i}. Заказ #{order.id} - {order.product_name} - Доставщик: {order.delivery_person.full_name}")
    
    try:
        choice = int(input("\nВыберите номер заказа для тестирования: "))
        if 1 <= choice <= len(orders):
            order = orders[choice-1]
            
            # Формируем текст уведомления для доставщика
            message = (
                f"🚚 Заказ #{order.id} готов к доставке!\n"
                f"Клиент: {order.user.full_name}\n"
                f"Телефон: {order.user.phone}\n"
                f"Букет: {order.product_name}\n"
                f"Адрес: {order.delivery_address}\n"
                f"Доставка: {order.delivery_date.strftime('%d.%m.%Y')}, "
                f"{order.delivery_time_from.strftime('%H:%M') if order.delivery_time_from else '-'} - "
                f"{order.delivery_time_to.strftime('%H:%M') if order.delivery_time_to else '-'}"
            )
            
            deliverer = order.delivery_person
            print(f"\nОтправка сообщения доставщику {deliverer.full_name} (Telegram ID: {deliverer.telegram_id})")
            
            # Проверка telegram_id
            if not deliverer.telegram_id:
                print("ОШИБКА: У доставщика не указан Telegram ID!")
                return
            
            # Отправляем через функцию из signals
            print("\nОтправка через функцию send_to_delivery_person из signals.py...")
            send_to_delivery_person(deliverer, message)
            
            # Отправляем напрямую через TelegramNotifier
            print("\nОтправка напрямую через TelegramNotifier...")
            direct_message = f"👋 {deliverer.full_name}, тестовое сообщение!\n\n{message}"
            result = TelegramNotifier.send_to_user(deliverer.telegram_id, direct_message)
            
            if result:
                print("✅ Сообщение успешно отправлено!")
            else:
                print("❌ Ошибка при отправке сообщения.")
        else:
            print("Неверный выбор")
    except ValueError:
        print("Пожалуйста, введите число.")

def test_delivery_person():
    """Отправка тестового сообщения произвольному доставщику"""
    # Список доставщиков с telegram_id
    deliverers = ShopUser.objects.filter(
        status='delivery', 
        telegram_id__isnull=False
    ).exclude(telegram_id='')
    
    if not deliverers:
        print("Не найдено доставщиков с указанным Telegram ID.")
        return
    
    print("\nДоступные доставщики:")
    for i, deliverer in enumerate(deliverers, 1):
        print(f"{i}. {deliverer.full_name} (Telegram ID: {deliverer.telegram_id})")
    
    try:
        choice = int(input("\nВыберите номер доставщика для тестирования: "))
        if 1 <= choice <= len(deliverers):
            deliverer = deliverers[choice-1]
            
            # Формируем тестовое сообщение
            message = (
                f"🚚 ТЕСТОВОЕ СООБЩЕНИЕ\n"
                f"Это проверка системы уведомлений.\n"
                f"Если вы получили это сообщение, значит система работает правильно."
            )
            
            print(f"\nОтправка тестового сообщения доставщику {deliverer.full_name}")
            
            # Проверяем telegram_id еще раз
            if not deliverer.telegram_id:
                print("ОШИБКА: У доставщика не указан Telegram ID!")
                return
                
            # Отправляем сообщение
            personal_message = f"👋 {deliverer.full_name}, это тестовое сообщение!\n\n{message}"
            result = TelegramNotifier.send_to_user(deliverer.telegram_id, personal_message)
            
            if result:
                print("✅ Тестовое сообщение успешно отправлено!")
            else:
                print("❌ Ошибка при отправке тестового сообщения.")
        else:
            print("Неверный выбор")
    except ValueError:
        print("Пожалуйста, введите число.")

if __name__ == "__main__":
    main() 