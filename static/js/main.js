/**
 * Инициализация всех обработчиков после загрузки DOM
 */
document.addEventListener('DOMContentLoaded', function() {
    // Инициализация всех форм
    initForms();
    // Инициализация квиза
    initQuiz();
    // Инициализация переключения видимости контактов
    initContactsToggle();
});

/**
 * Инициализирует переключение видимости секций контактов и консультации
 */
function initContactsToggle() {
    const contactLinks = document.querySelectorAll('.contact-link');
    contactLinks.forEach(link => {
        link.addEventListener('click', function(e) {
            e.preventDefault();
            const contactsSection = document.getElementById('contacts');
            const consultationSection = document.getElementById('consultation');

            contactsSection.classList.toggle('visible');
            consultationSection.classList.toggle('visible');

            // Плавная прокрутка к секции контактов
            if (contactsSection.classList.contains('visible')) {
                contactsSection.scrollIntoView({ behavior: 'smooth' });
            }
        });
    });
}

/**
 * Инициализация всех форм на странице
 * Добавляет обработчики событий отправки для каждой формы
 */
function initForms() {
    const forms = document.querySelectorAll('form');
    forms.forEach(form => {
        form.addEventListener('submit', handleFormSubmit);
    });
}

/**
 * Обработчик отправки формы
 * Предотвращает стандартную отправку, проводит валидацию
 * @param {Event} event - Событие отправки формы
 */
function getCookie(name) {
    let cookieValue = null;
    if (document.cookie && document.cookie !== '') {
        const cookies = document.cookie.split(';');
        for (let i = 0; i < cookies.length; i++) {
            const cookie = cookies[i].trim();
            if (cookie.startsWith(name + '=')) {
                cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                break;
            }
        }
    }
    return cookieValue;
}

function handleFormSubmit(event) {
    event.preventDefault();
    const form = event.target;

    if (!validateForm(form)) return;

    if (form.id === 'consultationForm') {
        const formData = new FormData(form);
        fetch(form.action, {
            method: 'POST',
            body: formData,
            headers: {
                'X-Requested-With': 'XMLHttpRequest',
                'X-CSRFToken': getCookie('csrftoken'),
            },
        })
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                showMessage(
                    `Спасибо, ${data.user_name}! Менеджер перезвонит на номер ${data.user_phone} в течение 20 минут`,
                    'success'
                );
                form.reset();
            } else {
                showMessage(data.error || 'Произошла ошибка', 'error');
            }
        })
        .catch(() => showMessage('Ошибка соединения', 'error'));
    }
}

/**
 * Валидация формы
 * Проверяет заполнение всех обязательных полей
 * @param {HTMLFormElement} form - Форма для валидации
 * @returns {boolean} - Результат валидации
 */
function validateForm(form) {
    let isValid = true;
    const requiredFields = form.querySelectorAll('[required]');

    requiredFields.forEach(field => {
        if (!field.value.trim()) {
            isValid = false;
            field.classList.add('error');
        } else {
            field.classList.remove('error');
        }

        // Проверка для поля имени: должно содержать только буквы
        if (field.name === 'fname') {
            const nameRegex = /^[А-Яа-яЁё\s]+$/; // разрешает только буквы и пробелы
            if (!nameRegex.test(field.value.trim())) {
                isValid = false;
                field.classList.add('error');
            } else {
                field.classList.remove('error');
            }
        }

        // Проверка для поля телефона: должно содержать только цифры и знак "+"
        if (field.name === 'tel') {
            const phoneRegex = /^[+]?[0-9\s()-]*$/; // разрешает только цифры и знаки
            if (!phoneRegex.test(field.value.trim())) {
                isValid = false;
                field.classList.add('error');
            } else {
                field.classList.remove('error');
            }
        }
    });

    return isValid;
}

/**
 * Инициализация "квиза"
 * Добавляет обработчики для кнопок навигации по квизу
 */
function initQuiz() {
    const nextButtons = document.querySelectorAll('.quiz-next');
    nextButtons.forEach(button => {
        button.addEventListener('click', handleQuizNext);
    });
}

/**
 * Обработчик перехода к следующему шагу квиза
 * @param {Event} event - Событие клика по кнопке
 */
function handleQuizNext(event) {
    event.preventDefault();
    // TODO: Здесь будет логика перехода между шагами квиза
    console.log('Следующий шаг квиза');
}

/**
 * Показывает временное сообщение пользователю
 * @param {string} message - Текст сообщения
 * @param {string} type - Тип сообщения ('success' или 'error')
 */
function showMessage(message, type = 'success') {
    const messageDiv = document.createElement('div');
    messageDiv.className = `message message-${type}`;
    messageDiv.textContent = message;

    document.body.appendChild(messageDiv);

    setTimeout(() => {
        messageDiv.remove();
    }, 3000);
}
