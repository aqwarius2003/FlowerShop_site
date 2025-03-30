import requests
from django.conf import settings
from typing import Optional, Tuple
import logging
from urllib.parse import urlencode
import re

logger = logging.getLogger(__name__)

def get_coordinates_by_address(address: str) -> Optional[Tuple[float, float]]:
    """
    Получает координаты по адресу используя API Яндекс.Геокодера
    
    Args:
        address: Адрес для геокодирования
        
    Returns:
        Tuple[float, float]: Кортеж (широта, долгота) или None в случае ошибки
    """
    try:
        logger.info(f"Запрос координат: {address}")
        
        base_url = "https://geocode-maps.yandex.ru/1.x/"
        params = {
            "apikey": settings.YANDEX_GEOCODER_API_KEY,
            "format": "json",
            "geocode": address
        }
        
        debug_params = params.copy()
        debug_params["apikey"] = "HIDDEN"
        debug_url = f"{base_url}?{urlencode(debug_params)}"
        logger.debug(f"Запрос к API: {debug_url}")
        
        response = requests.get(base_url, params=params)
        
        if response.status_code == 403:
            logger.error("Ошибка авторизации API (403)")
            logger.error(f"Ответ API: {response.text}")
            return None
            
        if response.status_code != 200:
            logger.error(f"Ошибка API: {response.status_code}")
            logger.error(f"Ответ: {response.text}")
            return None
            
        data = response.json()
        features = data["response"]["GeoObjectCollection"]["featureMember"]
        
        if not features:
            logger.warning(f"Адрес не найден: {address}")
            return None
            
        coords_str = features[0]["GeoObject"]["Point"]["pos"]
        longitude, latitude = map(float, coords_str.split())
        
        logger.info(f"Найдены координаты: {latitude}, {longitude}")
        return latitude, longitude
        
    except Exception as e:
        logger.error(f"Ошибка геокодирования: {str(e)}")
        return None 

def validate_russian_phone(phone_number: str) -> tuple:
    """
    Валидирует и форматирует российский номер телефона
    
    Args:
        phone_number: Номер телефона в произвольном формате
        
    Returns:
        Tuple[bool, str]: (успех, результат)
            - Если успех=True, результат содержит отформатированный номер
            - Если успех=False, результат содержит сообщение об ошибке
    """
    # Удаляем все нецифровые символы кроме +
    cleaned = re.sub(r'[^\d+]', '', phone_number)
    
    # Если номер начинается с 8, заменяем на +7
    if cleaned.startswith('8') and len(cleaned) == 11:
        cleaned = '+7' + cleaned[1:]
    
    # Если номер начинается с 7, добавляем +
    elif cleaned.startswith('7') and len(cleaned) == 11:
        cleaned = '+' + cleaned
    
    # Проверяем, что номер соответствует российскому формату +7XXXXXXXXXX
    pattern = r'^\+7\d{10}$'
    if not re.match(pattern, cleaned):
        return False, "Номер телефона должен быть в формате +7XXXXXXXXXX или 8XXXXXXXXXX"
    
    return True, cleaned 