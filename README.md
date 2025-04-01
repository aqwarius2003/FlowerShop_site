# 🌸 FlowerShop — «Интернет-магазин цветов на Django»

**Добро пожаловать в FlowerShop!**

## 📌 Описание проекта

Этот проект представляет собой полноценный интернет-магазин цветов с админ-панелью, каталогом, управлением заказами и интеграцией с Telegram.

![Видео-30-03-2025 203048](https://github.com/user-attachments/assets/eeeb4f3b-8171-4fe7-b853-89f26d296bc7)

## 🚀 Особенности

- **Каталог товаров** с фильтрацией по категориям и ценам.
- **Система заказов** с выбором слотов доставки.
- **Telegram-бот** для уведомлений.
- **Админ-панель** для управления товарами, заказами и пользователями.
- **Интеграция с медиафайлами**(изображения цветов).
- **Поддержка фикстур** (`fill_database.py`, `fill_db_addreses.py`).

![](https://i.postimg.cc/6qX1fh50/image.jpg)  ![](https://i.postimg.cc/m2T5cVnZ/image.jpg)

![](https://i.postimg.cc/Hn9vZ7rC/image.jpg)  ![](https://i.postimg.cc/kMQHXLfh/image.jpg)

## 🛠 Установка и запуск

### 🔧 Предварительные требования:

- Python 3.10 или выше
- СУБД по вашему выбору
- Виртуальное окружение (рекомендуется)

### Настройка проекта

1. 📌 **Клонируйте репозиторий:**

```bash
git clone https://github.com/AndreyBychenkow/FlowerShop.git
cd FlowerShop
```

2. 📌 **Создайте виртуальное окружение:**

```bash
python -m venv venv
source venv/bin/activate  # Для Linux/Mac
venv\Scripts\activate     # Для Windows
```

3. 📌 **Установите зависимости:**

   ```bash
   pip install -r requirements.txt   
   ```
4. 📌 **Настройка переменных окружения:**

**Создайте файл .env в корне проекта и добавьте необходимые переменные окружения:**

```bash
DEBUG='True'
SECRET_KEY='your-secret-key'
ALLOWED_HOSTS='localhost,127.0.0.1'
YANDEX_GEOCODER_API_KEY='your-secret_GEOCODER_API_KEY'
YANDEX_MAPS_API_KEY='your-secret_MAPS_API_KEY'
TELEGRAM_BOT_TOKEN='your_TELEGRAM_BOT_TOKEN'
```

5. 📌 **Примените миграции:**

   ```bash
   python manage.py migrate   
   ```
6. 📌 **Создайте суперпользователя для работы с админ-панелью:**

   ```bash
   python manage.py createsuperuser   
   ```
7. 📌 **Запустите сервер:**

   ```bash
   python manage.py runserver   
   ```

Теперь вы можете открыть приложение в браузере по [адресу](http://127.0.0.1:8000/) и зайти в [админку](http://127.0.0.1:8000/admin/)

![](https://i.postimg.cc/wT9Bb81X/image.jpg)
![](https://i.postimg.cc/6qhwrqw8/consultacii.jpg)
![](https://i.postimg.cc/DyBnmSBD/magazins.jpg)

![](https://i.postimg.cc/HspTpw4X/image.jpg)
![](https://i.postimg.cc/fW7wn2XM/image.jpg)
![](https://i.postimg.cc/NjFYXQn0/image.jpg)

## 📬 Контакты:

### Авторы:

**Виктор Рыков**
Telegram:  **@aqwarius2003**

**Андрей Быченков**
Telegram:  **@decebell032**
