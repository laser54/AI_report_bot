import os
import sys
from bot.telegram_bot import start_bot
from db.database import init_db

if __name__ == '__main__':
    # Инициализируем базу данных
    init_db()
    # Запускаем бота
    start_bot() 