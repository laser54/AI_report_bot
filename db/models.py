from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey, Float, Enum
from sqlalchemy.orm import relationship
from datetime import datetime
import enum
from .database import Base

class UserRole(enum.Enum):
    EMPLOYEE = "employee"
    MANAGER = "manager"
    ADMIN = "admin"

class User(Base):
    """Модель пользователя системы"""
    __tablename__ = 'users'

    id = Column(Integer, primary_key=True)
    telegram_id = Column(Integer, unique=True, nullable=False)
    name = Column(String(100), nullable=False)
    role = Column(Enum(UserRole), default=UserRole.EMPLOYEE)
    team_id = Column(Integer, ForeignKey('teams.id'))
    registration_date = Column(DateTime, default=datetime.utcnow)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Отношения
    team = relationship("Team", back_populates="users")
    reports = relationship("Report", back_populates="user")
    tasks = relationship("Task", back_populates="user")

    def __repr__(self):
        return f"<User {self.name} ({self.role})>"

class Team(Base):
    """Модель команды/отдела"""
    __tablename__ = 'teams'

    id = Column(Integer, primary_key=True)
    name = Column(String(100), nullable=False)
    description = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Отношения
    users = relationship("User", back_populates="team")
    reports = relationship("Report", back_populates="team")
    tasks = relationship("Task", back_populates="team")

    def __repr__(self):
        return f"<Team {self.name}>"

class Task(Base):
    """Модель текущей задачи"""
    __tablename__ = 'tasks'
    
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('users.id'), nullable=False)
    team_id = Column(Integer, ForeignKey('teams.id'), nullable=False)
    description = Column(Text, nullable=False)
    metrics = Column(Text)  # JSON строка для хранения числовых показателей
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    user = relationship("User", back_populates="tasks")
    team = relationship("Team", back_populates="tasks")

    def __repr__(self):
        return f"<Task {self.id} by user {self.user_id}>"

class Report(Base):
    """Модель отчета о выполненной задаче"""
    __tablename__ = 'reports'

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('users.id'), nullable=True)
    team_id = Column(Integer, ForeignKey('teams.id'), nullable=True)
    description = Column(Text, nullable=False)
    metric_name = Column(String(100), nullable=True)
    metric_value = Column(Float, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Отношения
    user = relationship("User", back_populates="reports")
    team = relationship("Team", back_populates="reports")

    def __repr__(self):
        return f"<Report {self.id} created at {self.created_at}>" 