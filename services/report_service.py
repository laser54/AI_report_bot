import sys
import os
import logging
from datetime import datetime, timedelta

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from db.models import Report, User, Team
from db.database import get_session

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class ReportService:
    """Сервис для работы с отчетами сотрудников"""

    @staticmethod
    def create_report(user_id, team_id, description, metric_value=None, metric_name=None, report_date=None):
        """Создание нового отчета"""
        session = get_session()
        try:
            # Создание отчета
            report = Report(
                user_id=user_id,
                team_id=team_id,
                description=description,
                metric_value=metric_value,
                metric_name=metric_name,
                report_date=report_date or datetime.now()
            )
            session.add(report)
            session.commit()
            logger.info(f"Создан новый отчет: ID={report.id}")
            return report
        except Exception as e:
            session.rollback()
            logger.error(f"Ошибка при создании отчета: {e}")
            return None
        finally:
            session.close()

    @staticmethod
    def get_report_by_id(report_id):
        """Получение отчета по ID"""
        session = get_session()
        try:
            report = session.query(Report).filter(Report.id == report_id).first()
            return report
        except Exception as e:
            logger.error(f"Ошибка при получении отчета: {e}")
            return None
        finally:
            session.close()

    @staticmethod
    def update_report(report_id, **kwargs):
        """Обновление данных отчета"""
        session = get_session()
        try:
            report = session.query(Report).filter(Report.id == report_id).first()
            if not report:
                logger.warning(f"Отчет с ID {report_id} не найден")
                return None

            # Обновление полей
            for key, value in kwargs.items():
                if hasattr(report, key):
                    setattr(report, key, value)
            
            report.updated_at = datetime.now()
            session.commit()
            logger.info(f"Данные отчета ID={report.id} обновлены")
            return report
        except Exception as e:
            session.rollback()
            logger.error(f"Ошибка при обновлении отчета: {e}")
            return None
        finally:
            session.close()

    @staticmethod
    def delete_report(report_id):
        """Удаление отчета"""
        session = get_session()
        try:
            report = session.query(Report).filter(Report.id == report_id).first()
            if not report:
                logger.warning(f"Отчет с ID {report_id} не найден")
                return False

            session.delete(report)
            session.commit()
            logger.info(f"Отчет ID={report_id} удален")
            return True
        except Exception as e:
            session.rollback()
            logger.error(f"Ошибка при удалении отчета: {e}")
            return False
        finally:
            session.close()

    @staticmethod
    def get_user_reports(user_id, start_date=None, end_date=None):
        """Получение отчетов пользователя за период"""
        session = get_session()
        try:
            query = session.query(Report).filter(Report.user_id == user_id)
            
            if start_date:
                query = query.filter(Report.report_date >= start_date)
            
            if end_date:
                query = query.filter(Report.report_date <= end_date)
            
            reports = query.order_by(Report.report_date.desc()).all()
            return reports
        except Exception as e:
            logger.error(f"Ошибка при получении отчетов пользователя: {e}")
            return []
        finally:
            session.close()

    @staticmethod
    def get_team_reports(team_id, start_date=None, end_date=None):
        """Получение отчетов команды за период"""
        session = get_session()
        try:
            query = session.query(Report).filter(Report.team_id == team_id)
            
            if start_date:
                query = query.filter(Report.report_date >= start_date)
            
            if end_date:
                query = query.filter(Report.report_date <= end_date)
            
            reports = query.order_by(Report.report_date.desc()).all()
            return reports
        except Exception as e:
            logger.error(f"Ошибка при получении отчетов команды: {e}")
            return []
        finally:
            session.close()

    @staticmethod
    def get_weekly_reports(team_id=None):
        """Получение отчетов за последнюю неделю"""
        end_date = datetime.now()
        start_date = end_date - timedelta(days=7)
        
        session = get_session()
        try:
            query = session.query(Report).filter(
                Report.report_date >= start_date,
                Report.report_date <= end_date
            )
            
            if team_id:
                query = query.filter(Report.team_id == team_id)
            
            reports = query.order_by(Report.report_date.desc()).all()
            return reports
        except Exception as e:
            logger.error(f"Ошибка при получении еженедельных отчетов: {e}")
            return []
        finally:
            session.close()

    @staticmethod
    def generate_weekly_summary(team_id=None):
        """Генерация сводки за неделю"""
        reports = ReportService.get_weekly_reports(team_id)
        
        if not reports:
            return "Нет отчетов за последнюю неделю."
        
        # Группировка отчетов по командам
        teams_data = {}
        session = get_session()
        
        try:
            for report in reports:
                team = session.query(Team).filter(Team.id == report.team_id).first()
                if not team:
                    continue
                
                team_name = team.name
                if team_name not in teams_data:
                    teams_data[team_name] = []
                
                teams_data[team_name].append(report)
            
            # Формирование текстового отчета
            summary = "Еженедельный отчет:\n\n"
            
            for team_name, team_reports in teams_data.items():
                summary += f"Команда: {team_name}\n"
                summary += f"Количество отчетов: {len(team_reports)}\n"
                summary += "Описание выполненных задач:\n"
                
                for report in team_reports:
                    summary += f"- {report.description}\n"
                    if report.metric_value and report.metric_name:
                        summary += f"  {report.metric_name}: {report.metric_value}\n"
                
                summary += "\n"
            
            return summary
        except Exception as e:
            logger.error(f"Ошибка при генерации сводки: {e}")
            return "Произошла ошибка при генерации сводки."
        finally:
            session.close() 