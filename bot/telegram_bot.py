import os
import logging
import hashlib
import hmac
from urllib.parse import parse_qs
from telebot import TeleBot
from telebot.handler_backends import State, StatesGroup
from telebot.storage import StateMemoryStorage
from dotenv import load_dotenv
from db.database import get_session
from db.models import User, UserRole, Report
from telebot import types
from flask import Flask, request, abort, render_template, jsonify

# Настройка логирования
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Загрузка переменных окружения
load_dotenv()

# Инициализация Flask приложений
webhook_app = Flask(__name__)  # Для вебхуков
template_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), 'templates'))
webapp = Flask(__name__, template_folder=template_dir)  # Для веб-интерфейса

# Инициализация бота с хранилищем состояний
state_storage = StateMemoryStorage()
bot = TeleBot(os.getenv('TELEGRAM_BOT_TOKEN'), state_storage=state_storage)

# Порты для разных сервисов
WEBHOOK_PORT = 8443  # Порт для вебхуков бота
APP_PORT = 8000     # Порт для веб-приложения

# Получаем URL для вебхука
WEBHOOK_HOST = os.getenv('WEBHOOK_HOST', 'https://sguevents.help')
WEBHOOK_PATH = f"/webhook/{os.getenv('TELEGRAM_BOT_TOKEN')}"
WEBHOOK_URL = f"{WEBHOOK_HOST}{WEBHOOK_PATH}"

# Путь для веб-приложения
WEBAPP_URL = f"{WEBHOOK_HOST}/report"

# Определение состояний для регистрации
class RegistrationStates(StatesGroup):
    waiting_for_name = State()
    waiting_for_role = State()

# Удаляем неиспользуемые состояния для отчетов
class ReportStates(StatesGroup):
    pass  # Больше не используется, так как отчеты создаются через веб-интерфейс

@bot.message_handler(commands=['start'])
def start(message):
    """Обработчик команды /start"""
    session = get_session()
    try:
        # Проверяем, зарегистрирован ли пользователь
        user = session.query(User).filter_by(telegram_id=message.from_user.id).first()
        
        if user:
            bot.reply_to(message, 
                        f"С возвращением, {user.name}!\n"
                        "Доступные команды:\n"
                        "/start - показать это сообщение\n"
                        "/help - показать справку\n"
                        "/report - создать отчет")
        else:
            bot.reply_to(message, 
                        "Добро пожаловать! Для начала работы необходимо зарегистрироваться.\n"
                        "Используйте команду /register для регистрации.")
    finally:
        session.close()

@bot.message_handler(commands=['help'])
def help(message):
    """Обработчик команды /help"""
    session = get_session()
    try:
        user = session.query(User).filter_by(telegram_id=message.from_user.id).first()
        
        if user:
            if user.role == UserRole.ADMIN:
                help_text = ("Справка по использованию бота:\n"
                           "1. /report - создать отчет\n"
                           "2. /stats - просмотр статистики\n"
                           "3. /manage_users - управление пользователями\n"
                           "4. /settings - настройки системы")
            elif user.role == UserRole.MANAGER:
                help_text = ("Справка по использованию бота:\n"
                           "1. /report - создать отчет\n"
                           "2. /stats - просмотр статистики по команде\n"
                           "3. /team - управление командой")
            else:
                help_text = ("Справка по использованию бота:\n"
                           "1. /report - создать отчет\n"
                           "2. /my_stats - просмотр личной статистики")
        else:
            help_text = ("Справка по использованию бота:\n"
                        "1. /register - зарегистрироваться в системе\n"
                        "2. /help - показать эту справку")
        
        bot.reply_to(message, help_text)
    finally:
        session.close()

@bot.message_handler(commands=['register'])
def register(message):
    """Начало процесса регистрации"""
    session = get_session()
    try:
        # Проверяем, не зарегистрирован ли уже пользователь
        user = session.query(User).filter_by(telegram_id=message.from_user.id).first()
        if user:
            bot.reply_to(message, "Вы уже зарегистрированы в системе!")
            return

        # Запрашиваем имя
        bot.set_state(message.from_user.id, RegistrationStates.waiting_for_name, message.chat.id)
        bot.reply_to(message, "Пожалуйста, введите ваше имя:")
    finally:
        session.close()

@bot.message_handler(state=RegistrationStates.waiting_for_name)
def process_name(message):
    """Обработка введенного имени"""
    # Сохраняем имя
    bot.set_state(message.from_user.id, RegistrationStates.waiting_for_role, message.chat.id)
    bot.add_data(message.from_user.id, message.chat.id, name=message.text)
    
    # Запрашиваем роль
    bot.reply_to(message, 
                "Выберите вашу роль:\n"
                "1 - Сотрудник\n"
                "2 - Руководитель\n"
                "3 - Администратор")

@bot.message_handler(state=RegistrationStates.waiting_for_role)
def process_role(message):
    """Обработка выбранной роли"""
    try:
        role_num = int(message.text)
        if role_num not in [1, 2, 3]:
            raise ValueError()
            
        # Получаем сохраненное имя
        with bot.retrieve_data(message.from_user.id, message.chat.id) as data:
            name = data['name']
        
        # Определяем роль
        role_map = {
            1: UserRole.EMPLOYEE,
            2: UserRole.MANAGER,
            3: UserRole.ADMIN
        }
        role = role_map[role_num]
        
        # Создаем пользователя
        session = get_session()
        try:
            new_user = User(
                telegram_id=message.from_user.id,
                name=name,
                role=role
            )
            session.add(new_user)
            session.commit()
            
            # Сбрасываем состояние
            bot.delete_state(message.from_user.id, message.chat.id)
            
            bot.reply_to(message, 
                        f"Регистрация успешно завершена!\n"
                        f"Имя: {name}\n"
                        f"Роль: {role.value}\n\n"
                        "Используйте /help для просмотра доступных команд.")
        finally:
            session.close()
            
    except (ValueError, TypeError):
        bot.reply_to(message, "Пожалуйста, выберите роль цифрой от 1 до 3")

@bot.message_handler(commands=['report'])
def report_command(message):
    """Обработчик команды /report"""
    with get_session() as session:
        user = session.query(User).filter_by(telegram_id=message.from_user.id).first()
        if not user:
            bot.reply_to(message, "Пожалуйста, сначала зарегистрируйтесь с помощью команды /register")
            return
            
        bot.reply_to(message, "Нажмите кнопку меню в нижней части экрана, чтобы создать отчет")

# Удаляем старые обработчики отчетов, так как теперь используется веб-интерфейс
@bot.message_handler(state=ReportStates.waiting_for_description)
def process_description(message):
    pass  # Оставляем пустую функцию для обратной совместимости

@bot.message_handler(state=ReportStates.waiting_for_metric_name)
def process_metric_name(message):
    pass  # Оставляем пустую функцию для обратной совместимости

@bot.message_handler(state=ReportStates.waiting_for_metric_value)
def process_metric_value(message):
    pass  # Оставляем пустую функцию для обратной совместимости

def create_report_in_db(message):
    pass  # Оставляем пустую функцию для обратной совместимости

# Обработчик всех остальных сообщений должен быть последним
@bot.message_handler(func=lambda message: True, state=None)
def echo_all(message):
    """Обработчик всех остальных сообщений"""
    bot.reply_to(message, "Извините, я понимаю только команды. Используйте /help для справки")

@webhook_app.route(WEBHOOK_PATH, methods=['POST'])
def webhook():
    if request.headers.get('content-type') == 'application/json':
        json_string = request.get_data().decode('utf-8')
        update = types.Update.de_json(json_string)
        bot.process_new_updates([update])
        return ''
    else:
        abort(403)

def setup_webhook():
    """Настройка вебхука"""
    # Удаляем старый вебхук
    bot.remove_webhook()
    
    # Устанавливаем новый
    bot.set_webhook(url=WEBHOOK_URL)
    logger.info(f"Webhook установлен на {WEBHOOK_URL}")
    
    # Устанавливаем команды бота
    commands = [
        types.BotCommand("start", "Начать работу"),
        types.BotCommand("help", "Показать справку"),
        types.BotCommand("register", "Зарегистрироваться")
    ]
    bot.set_my_commands(commands)
    
    # Создаем кнопку меню для веб-приложения
    menu_button = types.MenuButtonWebApp(
        type="web_app",
        text="Создать отчет", 
        web_app=types.WebAppInfo(url=f"{WEBHOOK_HOST}/report")
    )
    bot.set_chat_menu_button(menu_button=menu_button)

def start_bot():
    """Запуск бота"""
    logger.info("Бот запущен")
    setup_webhook()
    
    # Запускаем оба приложения в разных потоках
    from threading import Thread
    
    def run_webhook_app():
        webhook_app.run(host='0.0.0.0', port=WEBHOOK_PORT)
        
    def run_webapp():
        webapp.run(host='0.0.0.0', port=APP_PORT)
    
    webhook_thread = Thread(target=run_webhook_app)
    webapp_thread = Thread(target=run_webapp)
    
    webhook_thread.start()
    webapp_thread.start()
    
    webhook_thread.join()
    webapp_thread.join()

def validate_telegram_data(init_data):
    """Проверка данных от Telegram Web App"""
    try:
        # Разбираем строку init_data
        parsed_data = dict(parse_qs(init_data))
        
        # Получаем хэш
        received_hash = parsed_data.get('hash', [None])[0]
        if not received_hash:
            return False
            
        # Удаляем хэш из данных для проверки
        del parsed_data['hash']
        
        # Сортируем оставшиеся параметры
        data_check_string = '\n'.join(f"{k}={v[0]}" for k, v in sorted(parsed_data.items()))
        
        # Создаем хэш
        secret_key = hmac.new(b"WebAppData", os.getenv('TELEGRAM_BOT_TOKEN').encode(), hashlib.sha256).digest()
        calculated_hash = hmac.new(secret_key, data_check_string.encode(), hashlib.sha256).hexdigest()
        
        return calculated_hash == received_hash
    except Exception as e:
        logger.error(f"Error validating Telegram data: {e}")
        return False

@webapp.route('/report')
def report_form():
    """Страница с формой отчета"""
    logger.info("Accessing /report endpoint")
    try:
        return render_template('report.html')
    except Exception as e:
        logger.error(f"Error rendering template: {e}")
        return str(e), 500

@webapp.route('/submit_report', methods=['POST'])
def submit_report():
    """Обработка отправки отчета"""
    logger.info("Submitting report")
    try:
        # Проверяем данные от Telegram
        init_data = request.headers.get('X-Telegram-Init-Data')
        if not init_data or not validate_telegram_data(init_data):
            logger.error("Invalid Telegram data")
            return jsonify({'error': 'Invalid Telegram data'}), 403
            
        data = request.get_json()
        if not data:
            logger.error("Invalid data received")
            return jsonify({'error': 'Invalid data'}), 400
            
        description = data.get('description', '')
        metric_name = data.get('metric_name')
        metric_value = data.get('metric_value')
        user_id = data.get('user_id')
        
        if not description:
            logger.error("Description is required")
            return jsonify({'error': 'Description is required'}), 400
            
        if not user_id:
            logger.error("User ID is required")
            return jsonify({'error': 'User ID is required'}), 400
        
        # Получаем пользователя
        session = get_session()
        try:
            user = session.query(User).filter_by(telegram_id=user_id).first()
            if not user:
                logger.error(f"User not found: {user_id}")
                return jsonify({'error': 'User not found'}), 404
                
            # Создаем отчет
            report = Report(
                user_id=user.id,
                team_id=user.team_id,
                description=description,
                metric_name=metric_name,
                metric_value=metric_value
            )
            session.add(report)
            session.commit()
            logger.info(f"Report created successfully: {report}")
            return jsonify({'success': True, 'message': 'Report created successfully'})
        finally:
            session.close()
    except Exception as e:
        logger.error(f"Error creating report: {e}")
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    start_bot() 