from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, scoped_session
from sqlalchemy.ext.declarative import declarative_base
import os
from dotenv import load_dotenv

# Загрузка переменных окружения
load_dotenv()

# Создание директории для базы данных, если её нет
os.makedirs('db', exist_ok=True)

# Получение URL базы данных из переменных окружения
DATABASE_URL = os.getenv('DATABASE_URL', 'sqlite:///db/database.db')

# Создание движка базы данных
engine = create_engine(DATABASE_URL)

# Создание фабрики сессий
session_factory = sessionmaker(bind=engine)
Session = scoped_session(session_factory)

# Базовый класс для моделей
Base = declarative_base()

def init_db():
    """Инициализация базы данных"""
    # Импорт моделей для создания таблиц
    from .models import User, Team, Task, Report
    
    # Создание таблиц
    Base.metadata.create_all(engine)
    
def get_session():
    """Получение сессии базы данных"""
    return Session() 