import os
from dotenv import load_dotenv

# Загрузка переменных окружения из файла .env
load_dotenv()

# Telegram Bot API
TELEGRAM_TOKEN = os.getenv('TELEGRAM_BOT_TOKEN')
if not TELEGRAM_TOKEN:
    raise ValueError('TELEGRAM_BOT_TOKEN не найден в .env файле')

# Webhook настройки
WEBHOOK_URL = os.getenv('WEBHOOK_URL')

# База данных
DATABASE_URL = os.getenv('DATABASE_URL', 'sqlite:///database.db')

# Роли пользователей
USER_ROLES = {
    'EMPLOYEE': 'employee',  # Сотрудник
    'MANAGER': 'manager',    # Руководитель
    'ADMIN': 'admin'         # Администратор
}

# Команды бота
BOT_COMMANDS = {
    'START': 'start',
    'REGISTER': 'register',
    'REPORT': 'report',
    'ADMIN': 'admin',
    'HELP': 'help'
}

# Настройки веб-приложения
APP_HOST = os.getenv('APP_HOST', '0.0.0.0')
APP_PORT = int(os.getenv('APP_PORT', 5000)) 