document.addEventListener('DOMContentLoaded', function() {
    // Обработка ссылок на контакты
    document.querySelectorAll('.contact-link').forEach(function(link) {
        link.addEventListener('click', function(e) {
            e.preventDefault();
            const contactsSection = document.getElementById('contacts');
            contactsSection.classList.add('visible');
            contactsSection.scrollIntoView({ behavior: 'smooth' });
        });
    });

    // Ленивая загрузка Яндекс.Карты
    const mapContainer = document.querySelector('.contacts__map');
    let mapLoaded = false;

    // Функция для загрузки карты
    function loadMap() {
        if (mapLoaded) return;
        
        // Создаем iframe для загрузки карты
        const iframe = document.createElement('iframe');
        iframe.width = '100%';
        iframe.height = '316';
        iframe.frameBorder = '0';
        iframe.allow = 'geolocation';
        iframe.src = 'https://yandex.ru/map-widget/v1/?um=constructor%3Af39d7a7f1829359b6ffe21ab6356fcaeace17d528d6522dba8772f885c8b1a7d&amp;width=398&amp;height=316&amp;lang=ru_RU&amp;scroll=false';
        iframe.title = 'Яндекс Карта';
        
        // Очищаем контейнер и добавляем iframe
        mapContainer.innerHTML = '';
        mapContainer.appendChild(iframe);
        mapLoaded = true;
    }
    
    // Функция для проверки видимости элемента на экране
    function isElementInViewport(el) {
        if (!el) return false;
        
        const rect = el.getBoundingClientRect();
        return (
            rect.top <= (window.innerHeight || document.documentElement.clientHeight) && 
            rect.bottom >= 0 &&
            rect.left <= (window.innerWidth || document.documentElement.clientWidth) && 
            rect.right >= 0
        );
    }
    
    // Проверка видимости и загрузка карты при необходимости
    function checkMapVisibility() {
        if (isElementInViewport(mapContainer) && !mapLoaded) {
            loadMap();
        }
    }
    
    // Проверка при прокрутке и изменении размера окна
    window.addEventListener('scroll', checkMapVisibility, { passive: true });
    window.addEventListener('resize', checkMapVisibility, { passive: true });
    
    // Проверяем после загрузки страницы
    // Делаем это с небольшой задержкой, чтобы страница полностью отрисовалась
    setTimeout(checkMapVisibility, 500);
    
    // Если контакты видны сразу (например, на главной странице)
    if (document.body.classList.contains('home') || 
        document.getElementById('contacts').classList.contains('visible')) {
        setTimeout(checkMapVisibility, 1000);
    }
}); 