from django.db.models.signals import post_save
from django.dispatch import receiver
from .models import Order, Consultation, ShopUser
from .telegram_service import TelegramNotifier
import logging

logger = logging.getLogger(__name__)

@receiver(post_save, sender=Order)
def notify_order_created(sender, instance, created, **kwargs):
    """Обработчик сигнала создания нового заказа."""
    logger.info(f"Signal received for Order. Created: {created}")
    if created:
        logger.info("Сработал сигнал для нового заказа")
        message = (
            f"🛒 Новый заказ #{instance.id}\n"
            f"Клиент: {instance.user.full_name}\n"
            f"Телефон: {instance.user.phone}\n"
            f"Букет: {instance.product_name}\n"
            f"Адрес: {instance.delivery_address}"
        )
        
        # # Отправка в общий чат (закомментировано)
        # result = TelegramNotifier.send_message(message)
        # logger.info(f"Message sent to main channel: {result}")
        
        # Индивидуальные уведомления менеджерам
        send_to_managers(message)

@receiver(post_save, sender=Consultation)
def notify_consultation_created(sender, instance, created, **kwargs):
    """Обработчик сигнала создания новой заявки на консультацию."""
    logger.info(f"Signal received for Consultation. Created: {created}")
    if created:
        message = (
            f"📞 Новая заявка на консультацию\n"
            f"Клиент: {instance.user.full_name}\n"
            f"Телефон: {instance.user.phone}\n"
            f"Время: {instance.creation_date.strftime('%d.%m.%Y %H:%M')}"
        )
        
        # # Отправка в общий чат (закомментировано)
        # result = TelegramNotifier.send_message(message)
        # logger.info(f"Message sent to main channel: {result}")
        
        # Индивидуальные уведомления менеджерам
        send_to_managers(message)

def send_to_managers(message, delay=0.5):
    """
    Отправляет уведомления всем менеджерам с telegram_id.
    
    Args:
        message: Текст сообщения
        delay: Задержка между отправками в секундах (не используется)
    """
    # Получаем всех менеджеров с указанным telegram_id
    managers = ShopUser.objects.filter(
        status='manager',
        telegram_id__isnull=False
    ).exclude(telegram_id='')
    
    if not managers.exists():
        logger.warning("No managers with Telegram ID found")
        return
    
    logger.info(f"Sending notifications to {managers.count()} managers")
    
    # Отправка индивидуальных сообщений каждому менеджеру
    for manager in managers:
        personal_message = (
            f"👋 {manager.full_name}, у вас новое уведомление!\n\n{message}"
        )
        
        try:
            result = TelegramNotifier.send_to_user(
                manager.telegram_id, 
                personal_message
            )
            
            if result:
                logger.info(
                    f"Notification sent to {manager.full_name}"
                )
            else:
                logger.warning(
                    f"Failed to send to {manager.full_name}"
                )
        except Exception as e:
            logger.error(
                f"Error sending to {manager.full_name}: {str(e)}"
            )
            
    # # Групповая рассылка (закомментирована)
    # telegram_ids = [m.telegram_id for m in managers]
    # try:
    #     group_message = f"📢 Групповое уведомление для менеджеров!\n\n{message}"
    #     results = TelegramNotifier.send_to_multiple_users(
    #         telegram_ids, group_message, delay
    #     )
    #     success = sum(1 for r in results.values() if r)
    #     logger.info(f"Group message: {success}/{len(telegram_ids)} sent")
    # except Exception as e:
    #     logger.error(f"Error in group message: {str(e)}")