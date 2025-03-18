from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey, create_engine, Float
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship, sessionmaker
from datetime import datetime
import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config.config import DATABASE_URL

Base = declarative_base()

class User(Base):
    """Модель пользователя системы"""
    __tablename__ = 'users'

    id = Column(Integer, primary_key=True)
    telegram_id = Column(Integer, unique=True, nullable=False)
    username = Column(String(100))
    full_name = Column(String(100))
    role = Column(String(20), default='employee')  # employee, manager, admin
    team_id = Column(Integer, ForeignKey('teams.id'), nullable=True)
    created_at = Column(DateTime, default=datetime.now)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now)

    # Отношения
    team = relationship("Team", back_populates="users")
    reports = relationship("Report", back_populates="user")

    def __repr__(self):
        return f"<User {self.full_name} ({self.role})>"

class Team(Base):
    """Модель команды/отдела"""
    __tablename__ = 'teams'

    id = Column(Integer, primary_key=True)
    name = Column(String(100), nullable=False)
    description = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.now)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now)

    # Отношения
    users = relationship("User", back_populates="team")
    reports = relationship("Report", back_populates="team")

    def __repr__(self):
        return f"<Team {self.name}>"

class Report(Base):
    """Модель отчета о выполненной задаче"""
    __tablename__ = 'reports'

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('users.id'), nullable=False)
    team_id = Column(Integer, ForeignKey('teams.id'), nullable=False)
    description = Column(Text, nullable=False)
    metric_value = Column(Float, nullable=True)  # Числовой показатель, если есть
    metric_name = Column(String(100), nullable=True)  # Название показателя
    report_date = Column(DateTime, default=datetime.now)  # Дата отчета
    created_at = Column(DateTime, default=datetime.now)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now)

    # Отношения
    user = relationship("User", back_populates="reports")
    team = relationship("Team", back_populates="reports")

    def __repr__(self):
        return f"<Report {self.id} by {self.user.full_name} at {self.report_date}>"

def init_db():
    """Инициализация базы данных"""
    engine = create_engine(DATABASE_URL)
    Base.metadata.create_all(engine)
    return engine

def get_session():
    """Получение сессии для работы с базой данных"""
    engine = create_engine(DATABASE_URL)
    Session = sessionmaker(bind=engine)
    return Session() 