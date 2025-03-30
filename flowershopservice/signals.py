from django.db.models.signals import post_save, pre_save
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

@receiver(pre_save, sender=Order)
def notify_order_status_changed(sender, instance, **kwargs):
    """
    Обработчик сигнала изменения статуса заказа.
    Отправляет уведомление доставщику, когда заказ переходит в статус "В доставке".
    """
    # Получаем текущий заказ из базы данных
    try:
        # Проверяем, существует ли заказ в базе данных
        if instance.pk:
            # Получаем текущее состояние заказа из базы данных
            current_order = Order.objects.get(pk=instance.pk)
            
            # Логируем подробную информацию о заказе
            logger.info(f"Сигнал pre_save для заказа #{instance.id}")
            logger.info(f"Текущий статус заказа: {current_order.status}")
            logger.info(f"Новый статус заказа: {instance.status}")
            logger.info(f"Текущий доставщик: {current_order.delivery_person.full_name if current_order.delivery_person else 'не назначен'}")
            logger.info(f"Новый доставщик: {instance.delivery_person.full_name if instance.delivery_person else 'не назначен'}")
            
            # Проверяем изменение статуса на "В доставке" или изменение доставщика вместе со статусом "В доставке"
            # Первое условие - если статус заказа изменился на "inDelivery"
            # Второе условие - если одновременно назначается доставщик и устанавливается статус "inDelivery"
            if ((current_order.status != 'inDelivery' and instance.status == 'inDelivery' and instance.delivery_person is not None) or
                (instance.status == 'inDelivery' and
                 instance.delivery_person is not None and
                 (current_order.delivery_person is None or current_order.delivery_person.id != instance.delivery_person.id))):
                
                logger.info(
                    f"Order #{instance.id} status changed to 'inDelivery'. "
                    f"Sending notification to delivery person: {instance.delivery_person.full_name}"
                )
                
                # Формируем текст уведомления для доставщика
                message = (
                    f"🚚 Заказ #{instance.id} готов к доставке!\n"
                    f"Клиент: {instance.user.full_name}\n"
                    f"Телефон: {instance.user.phone}\n"
                    f"Букет: {instance.product_name}\n"
                    f"Адрес: {instance.delivery_address}\n"
                    f"Доставка: {instance.delivery_date.strftime('%d.%m.%Y')}, "
                    f"{instance.delivery_time_from.strftime('%H:%M') if instance.delivery_time_from else '-'} - "
                    f"{instance.delivery_time_to.strftime('%H:%M') if instance.delivery_time_to else '-'}"
                )
                
                # Отправляем уведомление доставщику
                send_to_delivery_person(instance.delivery_person, message)
                
                # Уведомляем также менеджеров, что заказ передан в доставку
                manager_message = (
                    f"📋 Заказ #{instance.id} передан в доставку\n"
                    f"Доставщик: {instance.delivery_person.full_name}\n"
                    f"Клиент: {instance.user.full_name}\n"
                    f"Букет: {instance.product_name}"
                )
                send_to_managers(manager_message)
    except Order.DoesNotExist:
        # Заказ новый, ничего не делаем
        pass
    except Exception as e:
        logger.error(f"Error in order status change signal: {str(e)}")

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
    #     group_message = f"📢 Групповое уведомление!\n\n{message}"
    #     results = TelegramNotifier.send_to_multiple_users(
    #         telegram_ids, group_message, delay
    #     )
    #     success = sum(1 for r in results.values() if r)
    #     logger.info(f"Group message: {success}/{len(telegram_ids)} sent")
    # except Exception as e:
    #     logger.error(f"Error in group message: {str(e)}")

def send_to_delivery_person(delivery_person, message):
    """
    Отправляет уведомление доставщику о новом заказе на доставку.
    
    Args:
        delivery_person: Объект ShopUser с ролью доставщика
        message: Текст сообщения
    """
    if not delivery_person:
        logger.warning("No delivery person specified for notification")
        return
    
    logger.info(f"Подготовка отправки уведомления доставщику {delivery_person.full_name}")
    logger.info(f"Telegram ID доставщика: {delivery_person.telegram_id}")
    
    if not delivery_person.telegram_id:
        logger.warning(
            f"Delivery person {delivery_person.full_name} has no Telegram ID"
        )
        return
    
    # Проверяем валидность telegram_id - должен быть числом
    try:
        int(delivery_person.telegram_id)
    except ValueError:
        logger.error(f"Неправильный формат Telegram ID: {delivery_person.telegram_id}")
        return
    
    personal_message = (
        f"👋 {delivery_person.full_name}, у вас новый заказ на доставку!\n\n"
        f"{message}"
    )
    
    logger.info(f"Отправка сообщения доставщику {delivery_person.full_name} (ID: {delivery_person.telegram_id})")
    
    try:
        result = TelegramNotifier.send_to_user(
            delivery_person.telegram_id, personal_message
        )
        
        if result:
            logger.info(
                f"✅ Delivery notification sent to {delivery_person.full_name}"
            )
        else:
            logger.warning(
                f"❌ Failed to send delivery notification to "
                f"{delivery_person.full_name}"
            )
    except Exception as e:
        logger.error(
            f"❌ Error sending to delivery person {delivery_person.full_name}: "
            f"{str(e)}"
        )