import logging
import requests
from django.conf import settings

logger = logging.getLogger(__name__)

class TelegramNotifier:
    @staticmethod
    def send_message(text: str):
        """Отправка сообщения в Telegram."""
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