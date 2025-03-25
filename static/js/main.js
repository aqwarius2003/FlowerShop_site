/**
 * Инициализация всех обработчиков после загрузки DOM
 */
document.addEventListener('DOMContentLoaded', function() {
    // Инициализация всех форм
    initForms();
    // Инициализация квиза
    initQuiz();
});

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
function handleFormSubmit(event) {
    event.preventDefault();
    const form = event.target;
    
    // Базовая валидация
    if (!validateForm(form)) {
        return;
    }

    // TODO: Здесь будет отправка формы
    console.log('Форма отправлена:', form.id);
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