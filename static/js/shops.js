// Инициализация карты
let myMap = null;
let activeShopCard = null;
let placemarks = []; // Используем массив вместо Map для простоты
const shopCards = document.querySelectorAll('.shop-card');
const shopCarousel = document.querySelector('.shops-carousel');

// Функция инициализации карты
function initMap() {
    console.log('Инициализация карты...');
    
    // Создаем карту
    myMap = new ymaps.Map('map', {
        center: [56.0096, 92.8726], // Координаты центра Красноярска
        zoom: 12,
        controls: ['zoomControl']
    });

    console.log('Карта создана, добавляем метки...');
    
    // Добавляем метки на карту
    shopCards.forEach(function(card, index) {
        if (!card.dataset.lat || !card.dataset.lng) {
            console.log('Нет координат для:', card.querySelector('.shop-title').textContent);
            return;
        }
        
        // Создаем метку
        const coords = [
            parseFloat(card.dataset.lat),
            parseFloat(card.dataset.lng)
        ];
        
        console.log('Создаем метку:', coords, card.querySelector('.shop-title').textContent);
        
        const placemark = new ymaps.Placemark(coords, {
            balloonContentHeader: card.querySelector('.shop-title').textContent,
            balloonContentBody: `
                <div style="padding: 10px;">
                    <img src="${card.querySelector('.shop-image').dataset.src}" 
                         style="width: 200px; height: 150px; object-fit: cover; border-radius: 8px; margin-bottom: 10px;">
                    <p style="margin: 5px 0;"><strong>Адрес:</strong> ${card.querySelector('.shop-address').textContent}</p>
                    <p style="margin: 5px 0;"><strong>Телефон:</strong> ${card.querySelector('.shop-phone').textContent}</p>
                    <p style="margin: 5px 0;"><strong>Режим работы:</strong> ${card.querySelector('.shop-hours').textContent}</p>
                </div>
            `,
            hintContent: card.querySelector('.shop-title').textContent
        }, {
            preset: 'islands#greenDotIcon'
        });
        
        // Добавляем метку на карту
        myMap.geoObjects.add(placemark);
        
        // Сохраняем метку в массиве с индексом карточки
        placemarks[index] = placemark;
        
        // Добавляем обработчик клика по метке
        placemark.events.add('click', function() {
            console.log('Клик по метке:', index);
            activateShop(index);
        });
        
        // Добавляем обработчик клика по карточке
        card.addEventListener('click', function(e) {
            if (!e.target.classList.contains('shop-phone')) {
                e.preventDefault();
                console.log('Клик по карточке:', index);
                activateShop(index);
            }
        });
    });
    
    // Активируем первую карточку по умолчанию
    if (shopCards.length > 0) {
        shopCards[0].classList.add('active');
        activeShopCard = shopCards[0];
        
        if (placemarks[0]) {
            placemarks[0].options.set('preset', 'islands#greenIcon');
        }
    }
}

// Функция активации магазина
function activateShop(index) {
    console.log('Активация магазина по индексу:', index);
    
    if (!myMap || index === undefined || !placemarks[index]) {
        console.error('Невозможно активировать магазин:', index);
        return;
    }
    
    const card = shopCards[index];
    const placemark = placemarks[index];
    
    console.log('Найдена карточка и метка:', card.querySelector('.shop-title').textContent);
    
    // Закрываем все открытые балуны
    myMap.balloon.close();
    
    // Деактивируем предыдущую карточку
    if (activeShopCard) {
        activeShopCard.classList.remove('active');
        const oldIndex = Array.from(shopCards).indexOf(activeShopCard);
        if (oldIndex >= 0 && placemarks[oldIndex]) {
            placemarks[oldIndex].options.set('preset', 'islands#greenDotIcon');
        }
    }
    
    // Активируем новую карточку
    card.classList.add('active');
    activeShopCard = card;
    
    // Изменяем стиль метки
    placemark.options.set('preset', 'islands#greenIcon');
    
    // Получаем координаты
    const coords = [
        parseFloat(card.dataset.lat),
        parseFloat(card.dataset.lng)
    ];
    
    console.log('Перемещение к координатам:', coords);
    
    // Сначала устанавливаем центр карты
    myMap.setCenter(coords);
    
    // Затем устанавливаем зум
    myMap.setZoom(16);
    
    // С задержкой открываем балун
    setTimeout(function() {
        placemark.balloon.open();
    }, 300);
    
    // Прокручиваем к карточке
    card.scrollIntoView({ behavior: 'smooth', block: 'nearest' });
}

// Ленивая загрузка изображений
function lazyLoadImages() {
    const imageObserver = new IntersectionObserver((entries, observer) => {
        entries.forEach(entry => {
            if (entry.isIntersecting) {
                const img = entry.target;
                img.src = img.dataset.src;
                img.classList.add('loaded');
                observer.unobserve(img);
            }
        });
    });

    document.querySelectorAll('img.lazy').forEach(img => {
        imageObserver.observe(img);
    });
}

// Инициализация после загрузки Яндекс.Карт
ymaps.ready(function() {
    console.log('API Яндекс.Карт загружен');
    initMap();
});

// Инициализация при загрузке страницы
document.addEventListener('DOMContentLoaded', function() {
    console.log('DOM загружен');
    lazyLoadImages();
}); 