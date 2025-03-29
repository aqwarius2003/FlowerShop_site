# FlowerShop

Веб-сайт цветочного магазина на Django.

## Установка и запуск

### Предварительные требования

1. Установите UV (быстрая альтернатива pip):
```bash
pip install uv
```

### Настройка проекта

1. Клонируйте репозиторий:
```bash
git clone <url-репозитория>
cd flowershop
```

2. Создайте виртуальное окружение с UV:
```bash
uv venv
```

3. Активируйте виртуальное окружение:
- Windows:
```bash
.venv\Scripts\activate
```
- Linux/MacOS:
```bash
source .venv/bin/activate
```

4. Установите зависимости:
```bash
uv pip install -r requirements.txt
```

5. Создайте файл `.env` в корневой директории проекта:
```env
SECRET_KEY=your-secret-key
DEBUG=True
ALLOWED_HOSTS=localhost,127.0.0.1
```

6. Примените миграции:
```bash
python manage.py migrate
```

7. Запустите сервер разработки:
```bash
python manage.py runserver
```

Сайт будет доступен по адресу: http://127.0.0.1:8000/

## Структура проекта

- `flowershop/` - основной проект Django
- `flowershopservice/` - основное приложение
- `static/` - статические файлы (CSS, изображения)
- `templates/` - HTML шаблоны 





Получить API ключ Яндекс.Карт:
Зайдите на https://developer.tech.yandex.ru/
Создайте новое приложение
Получите API ключ для JavaScript API