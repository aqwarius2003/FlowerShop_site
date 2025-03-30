import logging
import requests
from django.conf import settings
import time

logger = logging.getLogger(__name__)

class TelegramNotifier:
    @staticmethod
    def send_message(text: str):
        """Отправка сообщения в общий чат Telegram."""
        token = settings.TELEGRAM_BOT_TOKEN
        chat_id = settings.TELEGRAM_CHAT_ID
        
        if not token or not chat_id:
            logger.error("Telegram credentials not configured!")
            return False

        url = f"https://api.telegram.org/bot{token}/sendMessage"
        payload = {
            "chat_id": chat_id,
            "text": text,
            "parse_mode": "HTML"
        }

        try:
            response = requests.post(url, json=payload, timeout=10)
            response.raise_for_status()
            return True
        except Exception as e:
            logger.error(f"Telegram send error: {str(e)}")
            return False
    
    @staticmethod
    def send_to_user(telegram_id: str, text: str):
        """Отправка сообщения пользователю по его Telegram ID."""
        if not telegram_id:
            logger.warning("Telegram ID not provided for message")
            return False
            
        token = settings.TELEGRAM_BOT_TOKEN
        
        if not token:
            logger.error("Telegram BOT TOKEN not configured!")
            return False

        url = f"https://api.telegram.org/bot{token}/sendMessage"
        payload = {
            "chat_id": telegram_id,
            "text": text,
            "parse_mode": "HTML"
        }

        try:
            response = requests.post(url, json=payload, timeout=10)
            response.raise_for_status()
            return True
        except Exception as e:
            logger.error(
                f"Telegram send error to user {telegram_id}: {e}"
            )
            return False
    
    @staticmethod
    def send_to_multiple_users(
        telegram_ids: list, 
        text: str, 
        delay: float = 0.5
    ):
        """
        Отправка сообщения нескольким пользователям с задержкой.
        
        Args:
            telegram_ids: Список Telegram ID получателей
            text: Текст сообщения
            delay: Задержка между отправками в секундах (по умолчанию 0.5 сек)
        
        Returns:
            dict: Словарь с результатами отправки для каждого получателя
        """
        if not telegram_ids:
            logger.warning("No Telegram IDs provided for messages")
            return {}
            
        results = {}
        
        for tid in telegram_ids:
            if not tid:
                continue
                
            # Отправляем сообщение текущему получателю
            success = TelegramNotifier.send_to_user(tid, text)
            results[tid] = success
            
            # Делаем задержку если это не последний получатель
            if tid != telegram_ids[-1]:
                time.sleep(delay)
        
        return results