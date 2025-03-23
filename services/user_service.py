import sys
import os
import logging
from datetime import datetime

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from db.models import User
from db.database import get_session
from config.config import USER_ROLES

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class UserService:
    """Сервис для работы с пользователями"""

    @staticmethod
    def get_user_by_telegram_id(telegram_id):
        """Получение пользователя по Telegram ID"""
        session = get_session()
        try:
            user = session.query(User).filter(User.telegram_id == telegram_id).first()
            return user
        except Exception as e:
            logger.error(f"Ошибка при получении пользователя: {e}")
            return None
        finally:
            session.close()

    @staticmethod
    def create_user(telegram_id, username, full_name, role=USER_ROLES['EMPLOYEE'], team_id=None):
        """Создание нового пользователя"""
        session = get_session()
        try:
            # Проверка существования пользователя
            existing_user = UserService.get_user_by_telegram_id(telegram_id)
            if existing_user:
                logger.info(f"Пользователь уже существует: {existing_user.full_name}")
                return existing_user

            # Создание нового пользователя
            user = User(
                telegram_id=telegram_id,
                username=username,
                full_name=full_name,
                role=role,
                team_id=team_id
            )
            session.add(user)
            session.commit()
            logger.info(f"Создан новый пользователь: {user.full_name}")
            return user
        except Exception as e:
            session.rollback()
            logger.error(f"Ошибка при создании пользователя: {e}")
            return None
        finally:
            session.close()

    @staticmethod
    def update_user(telegram_id, **kwargs):
        """Обновление данных пользователя"""
        session = get_session()
        try:
            user = session.query(User).filter(User.telegram_id == telegram_id).first()
            if not user:
                logger.warning(f"Пользователь с Telegram ID {telegram_id} не найден")
                return None

            # Обновление полей
            for key, value in kwargs.items():
                if hasattr(user, key):
                    setattr(user, key, value)
            
            user.updated_at = datetime.now()
            session.commit()
            logger.info(f"Данные пользователя {user.full_name} обновлены")
            return user
        except Exception as e:
            session.rollback()
            logger.error(f"Ошибка при обновлении пользователя: {e}")
            return None
        finally:
            session.close()

    @staticmethod
    def get_all_users(role=None, team_id=None):
        """Получение списка пользователей с возможностью фильтрации"""
        session = get_session()
        try:
            query = session.query(User)
            
            if role:
                query = query.filter(User.role == role)
            
            if team_id:
                query = query.filter(User.team_id == team_id)
            
            users = query.all()
            return users
        except Exception as e:
            logger.error(f"Ошибка при получении списка пользователей: {e}")
            return []
        finally:
            session.close()

    @staticmethod
    def delete_user(telegram_id):
        """Удаление пользователя"""
        session = get_session()
        try:
            user = session.query(User).filter(User.telegram_id == telegram_id).first()
            if not user:
                logger.warning(f"Пользователь с Telegram ID {telegram_id} не найден")
                return False

            session.delete(user)
            session.commit()
            logger.info(f"Пользователь {user.full_name} удален")
            return True
        except Exception as e:
            session.rollback()
            logger.error(f"Ошибка при удалении пользователя: {e}")
            return False
        finally:
            session.close()

    @staticmethod
    def is_admin(telegram_id):
        """Проверка является ли пользователь администратором"""
        user = UserService.get_user_by_telegram_id(telegram_id)
        return user and user.role == USER_ROLES['ADMIN']

    @staticmethod
    def is_manager(telegram_id):
        """Проверка является ли пользователь руководителем"""
        user = UserService.get_user_by_telegram_id(telegram_id)
        return user and user.role == USER_ROLES['MANAGER'] 