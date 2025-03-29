from .models import Shop


def shops_context(request):
    """
    Контекстный процессор для получения списка активных магазинов
    """
    return {
        'shops': Shop.objects.get_active_shops(),  # Получаем все активные магазины
        'initial_center': {  # Начальный центр карты (центр Красноярска)
            'lat': 56.0096,  # Широта центра Красноярска
            'lng': 92.8726   # Долгота центра Красноярска
        }
    }