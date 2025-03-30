from django.apps import AppConfig
import logging

logger = logging.getLogger(__name__)


class FlowershopserviceConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'flowershopservice'

    def ready(self):
        logger.info("Initializing signals...")
        # Импорт сигналов для их регистрации
        import flowershopservice.signals  # noqa
        logger.info("Signals initialized")
