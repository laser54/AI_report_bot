import sys
import os
import logging
from datetime import datetime

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from db.models import Team, get_session

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class TeamService:
    """Сервис для работы с командами/отделами"""

    @staticmethod
    def get_team_by_id(team_id):
        """Получение команды по ID"""
        session = get_session()
        try:
            team = session.query(Team).filter(Team.id == team_id).first()
            return team
        except Exception as e:
            logger.error(f"Ошибка при получении команды: {e}")
            return None
        finally:
            session.close()

    @staticmethod
    def get_team_by_name(name):
        """Получение команды по названию"""
        session = get_session()
        try:
            team = session.query(Team).filter(Team.name == name).first()
            return team
        except Exception as e:
            logger.error(f"Ошибка при получении команды по названию: {e}")
            return None
        finally:
            session.close()

    @staticmethod
    def create_team(name, description=None):
        """Создание новой команды"""
        session = get_session()
        try:
            # Проверка существования команды с таким названием
            existing_team = TeamService.get_team_by_name(name)
            if existing_team:
                logger.info(f"Команда с названием '{name}' уже существует")
                return existing_team

            # Создание новой команды
            team = Team(
                name=name,
                description=description
            )
            session.add(team)
            session.commit()
            logger.info(f"Создана новая команда: {name}")
            return team
        except Exception as e:
            session.rollback()
            logger.error(f"Ошибка при создании команды: {e}")
            return None
        finally:
            session.close()

    @staticmethod
    def update_team(team_id, **kwargs):
        """Обновление данных команды"""
        session = get_session()
        try:
            team = session.query(Team).filter(Team.id == team_id).first()
            if not team:
                logger.warning(f"Команда с ID {team_id} не найдена")
                return None

            # Обновление полей
            for key, value in kwargs.items():
                if hasattr(team, key):
                    setattr(team, key, value)
            
            team.updated_at = datetime.now()
            session.commit()
            logger.info(f"Данные команды '{team.name}' обновлены")
            return team
        except Exception as e:
            session.rollback()
            logger.error(f"Ошибка при обновлении команды: {e}")
            return None
        finally:
            session.close()

    @staticmethod
    def get_all_teams():
        """Получение списка всех команд"""
        session = get_session()
        try:
            teams = session.query(Team).all()
            return teams
        except Exception as e:
            logger.error(f"Ошибка при получении списка команд: {e}")
            return []
        finally:
            session.close()

    @staticmethod
    def delete_team(team_id):
        """Удаление команды"""
        session = get_session()
        try:
            team = session.query(Team).filter(Team.id == team_id).first()
            if not team:
                logger.warning(f"Команда с ID {team_id} не найдена")
                return False

            session.delete(team)
            session.commit()
            logger.info(f"Команда '{team.name}' удалена")
            return True
        except Exception as e:
            session.rollback()
            logger.error(f"Ошибка при удалении команды: {e}")
            return False
        finally:
            session.close() 