from models import init_db, get_session, User, Team
from config.config import USER_ROLES
import logging

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def create_admin_user(session, telegram_id, username, full_name):
    """Создание администратора при первой инициализации"""
    try:
        existing_admin = session.query(User).filter(User.role == USER_ROLES['ADMIN']).first()
        if existing_admin:
            logger.info(f"Администратор уже существует: {existing_admin.full_name}")
            return existing_admin
        
        admin = User(
            telegram_id=telegram_id,
            username=username,
            full_name=full_name,
            role=USER_ROLES['ADMIN']
        )
        session.add(admin)
        session.commit()
        logger.info(f"Создан администратор: {admin.full_name}")
        return admin
    except Exception as e:
        session.rollback()
        logger.error(f"Ошибка при создании администратора: {e}")
        return None

def create_default_team(session, name="Общая команда", description="Команда по умолчанию"):
    """Создание команды по умолчанию"""
    try:
        existing_team = session.query(Team).filter(Team.name == name).first()
        if existing_team:
            logger.info(f"Команда по умолчанию уже существует: {existing_team.name}")
            return existing_team
        
        team = Team(
            name=name,
            description=description
        )
        session.add(team)
        session.commit()
        logger.info(f"Создана команда по умолчанию: {team.name}")
        return team
    except Exception as e:
        session.rollback()
        logger.error(f"Ошибка при создании команды по умолчанию: {e}")
        return None

def initialize_database():
    """Инициализация базы данных с начальными данными"""
    try:
        engine = init_db()
        session = get_session()
        logger.info("База данных успешно инициализирована")
        
        # Создание команды по умолчанию
        default_team = create_default_team(session)
        
        # Здесь можно создать администратора, если передать реальные данные
        # Например: create_admin_user(session, 123456789, "admin_username", "Администратор")
        
        session.close()
        return True
    except Exception as e:
        logger.error(f"Ошибка при инициализации базы данных: {e}")
        return False

if __name__ == "__main__":
    initialize_database() 