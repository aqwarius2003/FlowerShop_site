from django.core.cache import cache
from django.db import models

class ShopManager(models.Manager):
    def get_active_shops(self):
        cache_key = 'active_shops'
        shops = cache.get(cache_key)
        
        if not shops:
            shops = list(self.filter(is_active=True).order_by('order'))
            cache.set(cache_key, shops, 60*60*24)  # Кэш на 24 часа
        
        return shops