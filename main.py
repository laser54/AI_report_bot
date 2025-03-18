import os
import logging
import threading
from dotenv import load_dotenv

# Настройка логирования
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Загрузка переменных окружения
load_dotenv()

# Проверка наличия токена бота
TELEGRAM_TOKEN = os.getenv('TELEGRAM_BOT_TOKEN')
if not TELEGRAM_TOKEN:
    logger.error("Переменная окружения TELEGRAM_BOT_TOKEN не найдена")
    logger.info("Создайте файл .env на основе .env.example и укажите в нем токен бота")
    exit(1)

# Импорт после проверки наличия переменных окружения
from bot.telegram_bot import start_bot
from app.webapp import run_app
from db.init_db import initialize_database

def main():
    """Основная функция запуска приложения"""
    try:
        # Инициализация базы данных
        if not initialize_database():
            logger.error("Не удалось инициализировать базу данных")
            return
        
        # Запуск Flask-приложения в отдельном потоке
        flask_thread = threading.Thread(target=run_app)
        flask_thread.daemon = True
        flask_thread.start()
        logger.info("Веб-приложение запущено в отдельном потоке")
        
        # Запуск Telegram-бота в основном потоке
        logger.info("Запуск Telegram-бота")
        start_bot()
    except KeyboardInterrupt:
        logger.info("Приложение остановлено пользователем")
    except Exception as e:
        logger.error(f"Ошибка при запуске приложения: {e}")

if __name__ == "__main__":
    main() 