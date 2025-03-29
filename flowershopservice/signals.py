from django.db.models.signals import post_save
from django.dispatch import receiver
from .models import Order, Consultation, ShopUser
from .telegram_service import TelegramNotifier
import logging

logger = logging.getLogger(__name__)

@receiver(post_save, sender=Order)
def notify_order_created(sender, instance, created, **kwargs):
    logger.info(f"Signal received for Order. Created: {created}")
    if created:
        logger.info("Сработал сигнал для нового заказа")
        message = (
            f"🛒 Новый заказ #{instance.id}\n"
            f"Клиент: {instance.user.full_name}\n"
            f"Адрес: {instance.delivery_address}"
        )
        result = TelegramNotifier.send_message(message)
        logger.info(f"Message sent to Telegram: {result}")
        
        # Уведомление для менеджеров
        managers = ShopUser.objects.filter(status='manager')
        for manager in managers:
            TelegramNotifier.send_message(f"Менеджеру: {manager.full_name}\n{message}")

@receiver(post_save, sender=Consultation)
def notify_consultation_created(sender, instance, created, **kwargs):
    logger.info(f"Signal received for Consultation. Created: {created}")
    if created:
        message = (
            f"📞 Новая заявка на консультацию\n"
            f"Телефон: {instance.user.phone}\n"
            f"Время: {instance.creation_date}"
        )
        result = TelegramNotifier.send_message(message)
        logger.info(f"Message sent to Telegram: {result}")
        
        # Уведомление для менеджеров
        managers = ShopUser.objects.filter(status='manager')
        for manager in managers:
            TelegramNotifier.send_message(f"Менеджеру: {manager.full_name}\n{message}")