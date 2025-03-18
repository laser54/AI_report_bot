/**
 * Основные функции для работы с Telegram Mini App
 */

// Инициализация при загрузке DOM
document.addEventListener('DOMContentLoaded', function() {
    // Инициализация Telegram Mini App
    const webapp = window.Telegram.WebApp;
    
    // Установка темы в соответствии с Telegram
    applyTelegramTheme();
    
    // Вызов метода расширения экрана мини-приложения
    webapp.expand();
    
    // Добавление обработчика событий для адаптивного дизайна
    webapp.onEvent('viewportChanged', applyTelegramTheme);
});

/**
 * Применение темы Telegram к приложению
 */
function applyTelegramTheme() {
    const webapp = window.Telegram.WebApp;
    
    // Применение темной/светлой темы
    if (webapp.colorScheme === 'dark') {
        document.body.classList.add('dark-theme');
    } else {
        document.body.classList.remove('dark-theme');
    }
    
    // Установка основного цвета из Telegram
    if (webapp.themeParams && webapp.themeParams.button_color) {
        document.documentElement.style.setProperty('--tg-theme-button-color', webapp.themeParams.button_color);
    }
}

/**
 * Показать уведомление пользователю
 * @param {string} message - Текст уведомления
 * @param {string} type - Тип уведомления (success, error, warning, info)
 */
function showNotification(message, type = 'info') {
    // Создание элемента уведомления
    const notification = document.createElement('div');
    notification.className = `alert alert-${type} alert-dismissible fade show`;
    notification.setAttribute('role', 'alert');
    notification.innerHTML = `
        ${message}
        <button type="button" class="btn-close" data-bs-dismiss="alert" aria-label="Close"></button>
    `;
    
    // Добавление уведомления в DOM
    const container = document.querySelector('.container');
    container.insertBefore(notification, container.firstChild);
    
    // Автоматическое скрытие уведомления через 5 секунд
    setTimeout(() => {
        const bsAlert = new bootstrap.Alert(notification);
        bsAlert.close();
    }, 5000);
} 