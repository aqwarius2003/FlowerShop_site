from django.shortcuts import get_object_or_404, redirect
from django.contrib import messages
from .models import Order, ShopUser
from .telegram_service import TelegramNotifier
import logging

logger = logging.getLogger(__name__)

def assign_deliverer_confirm(request):
    """
    Обработчик подтверждения назначения доставщика.
    Получает данные из формы, обновляет заказ и отправляет уведомления.
    """
    if request.method != 'POST':
        messages.error(request, "Недопустимый метод запроса")
        return redirect('admin:flowershopservice_order_changelist')
    
    order_id = request.POST.get('order_id')
    deliverer_id = request.POST.get('deliverer')
    should_notify_managers = request.POST.get('notify_manager') == 'on'
    
    # Проверка данных формы
    if not order_id or not deliverer_id:
        messages.error(request, "Не указан заказ или доставщик")
        return redirect('admin:flowershopservice_order_changelist')
    
    try:
        # Получаем объекты заказа и доставщика
        order = get_object_or_404(Order, id=order_id)
        deliverer = get_object_or_404(
            ShopUser, id=deliverer_id, status='delivery'
        )
        
        # Обновляем заказ
        order.delivery_person = deliverer
        order.status = 'inDelivery'
        order.save()
        
        # Логирование успешного действия
        logger.info(
            f"Заказ #{order.id} назначен на доставщика {deliverer.full_name} "
            f"и переведен в статус 'В доставке'"
        )
        
        # Сообщение об успехе для админа
        messages.success(
            request, 
            f"Заказ №{order.id} назначен на доставщика {deliverer.full_name} "
            f"и переведен в статус 'В доставке'"
        )
        
        # Проверяем наличие Telegram ID и отправляем уведомление
        if deliverer.telegram_id:
            # Формируем текст уведомления для доставщика
            message = (
                f"🚚 Заказ #{order.id} готов к доставке!\n"
                f"Клиент: {order.user.full_name}\n"
                f"Телефон: {order.user.phone}\n"
                f"Букет: {order.product_name}\n"
                f"Адрес: {order.delivery_address}\n"
            )
            
            # Добавляем информацию о времени доставки
            if order.delivery_date:
                message += f"Дата: {order.delivery_date.strftime('%d.%m.%Y')}\n"
                
            if order.is_express_delivery:
                message += "⚡ СРОЧНАЯ доставка!"
            elif order.delivery_time_from and order.delivery_time_to:
                from_time = order.delivery_time_from.strftime('%H:%M')
                to_time = order.delivery_time_to.strftime('%H:%M')
                message += f"Время: с {from_time} до {to_time}"
            
            # Отправляем уведомление доставщику
            delivery_message = (
                f"👋 {deliverer.full_name}, "
                f"у вас новый заказ на доставку!\n\n{message}"
            )
            success = TelegramNotifier.send_to_user(
                deliverer.telegram_id,
                delivery_message
            )
            
            if success:
                logger.info(
                    f"Уведомление о заказе #{order.id} отправлено "
                    f"доставщику {deliverer.full_name}"
                )
                messages.success(
                    request, "Уведомление отправлено доставщику."
                )
            else:
                logger.warning(
                    f"Не удалось отправить уведомление доставщику "
                    f"{deliverer.full_name} о заказе #{order.id}"
                )
                messages.warning(
                    request, "Не удалось отправить уведомление доставщику."
                )
        else:
            messages.warning(
                request,
                f"У доставщика {deliverer.full_name} не указан Telegram ID. "
                f"Уведомление не отправлено!"
            )
            
        # Уведомление менеджеров (если включено)
        if should_notify_managers:
            from .signals import send_to_managers
            
            manager_message = (
                f"📋 Заказ #{order.id} передан в доставку\n"
                f"Доставщик: {deliverer.full_name}\n"
                f"Клиент: {order.user.full_name}\n"
                f"Букет: {order.product_name}"
            )
            
            send_to_managers(manager_message)
            
            logger.info(
                f"Уведомление об изменении статуса заказа #{order.id} "
                f"отправлено менеджерам"
            )
        
        return redirect('admin:flowershopservice_order_changelist')
        
    except Exception as e:
        logger.error(f"Ошибка при назначении доставщика: {str(e)}")
        messages.error(request, f"Произошла ошибка: {str(e)}")
        return redirect('admin:flowershopservice_order_changelist') 