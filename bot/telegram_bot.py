import sys
import os
import logging
from telebot import TeleBot, types
from datetime import datetime

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config.config import TELEGRAM_TOKEN, USER_ROLES, BOT_COMMANDS
from services.user_service import UserService
from services.team_service import TeamService
from services.report_service import ReportService

# Настройка логирования
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Инициализация бота
bot = TeleBot(TELEGRAM_TOKEN)

# Хранилище состояний пользователей
user_states = {}

# Состояния пользователя
class UserState:
    IDLE = 'idle'  # Начальное состояние
    AWAITING_TEAM_SELECTION = 'awaiting_team_selection'  # Ожидание выбора команды
    AWAITING_REGISTER_CONFIRMATION = 'awaiting_register_confirmation'  # Ожидание подтверждения регистрации
    AWAITING_REPORT_DESCRIPTION = 'awaiting_report_description'  # Ожидание описания задачи
    AWAITING_REPORT_METRIC = 'awaiting_report_metric'  # Ожидание числового показателя
    AWAITING_REPORT_METRIC_NAME = 'awaiting_report_metric_name'  # Ожидание названия показателя
    AWAITING_ADMIN_ACTION = 'awaiting_admin_action'  # Ожидание действия администратора

# Временное хранилище данных пользователей
user_data = {}

# Функции-хелперы
def get_user_state(user_id):
    """Получение текущего состояния пользователя"""
    return user_states.get(user_id, UserState.IDLE)

def set_user_state(user_id, state):
    """Установка состояния пользователя"""
    user_states[user_id] = state

def reset_user_state(user_id):
    """Сброс состояния пользователя"""
    if user_id in user_states:
        user_states.pop(user_id)
    if user_id in user_data:
        user_data.pop(user_id)

def get_markup_for_teams():
    """Создание клавиатуры с доступными командами"""
    markup = types.InlineKeyboardMarkup(row_width=2)
    teams = TeamService.get_all_teams()
    
    for team in teams:
        markup.add(types.InlineKeyboardButton(
            team.name, 
            callback_data=f"select_team_{team.id}"
        ))
    
    markup.add(types.InlineKeyboardButton("Создать новую команду", callback_data="create_new_team"))
    return markup

def get_main_menu_markup(user_id):
    """Создание основного меню в зависимости от роли пользователя"""
    user = UserService.get_user_by_telegram_id(user_id)
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
    
    # Общие кнопки для всех пользователей
    markup.add(types.KeyboardButton('📝 Отправить отчет'))
    markup.add(types.KeyboardButton('📋 Мои отчеты'))
    markup.add(types.KeyboardButton('ℹ️ Помощь'))
    
    # Дополнительные кнопки для руководителей и администраторов
    if user and (user.role == USER_ROLES['MANAGER'] or user.role == USER_ROLES['ADMIN']):
        markup.add(types.KeyboardButton('📊 Получить отчет за неделю'))
    
    # Дополнительные кнопки только для администраторов
    if user and user.role == USER_ROLES['ADMIN']:
        markup.add(types.KeyboardButton('👥 Управление пользователями'))
        markup.add(types.KeyboardButton('🏢 Управление командами'))
    
    return markup

# Обработчики команд
@bot.message_handler(commands=[BOT_COMMANDS['START']])
def handle_start(message):
    """Обработка команды /start"""
    user_id = message.from_user.id
    reset_user_state(user_id)
    
    user = UserService.get_user_by_telegram_id(user_id)
    
    if user:
        # Пользователь уже зарегистрирован
        bot.send_message(
            user_id, 
            f"Привет, {user.full_name}! Вы уже зарегистрированы в системе.\nВаша роль: {user.role}\nВаша команда: {user.team.name if user.team else 'Не указана'}",
            reply_markup=get_main_menu_markup(user_id)
        )
    else:
        # Новый пользователь
        bot.send_message(
            user_id, 
            f"Добро пожаловать, {message.from_user.first_name}! Вы еще не зарегистрированы в системе. Используйте команду /register для регистрации."
        )

@bot.message_handler(commands=[BOT_COMMANDS['REGISTER']])
def handle_register(message):
    """Обработка команды /register"""
    user_id = message.from_user.id
    user = UserService.get_user_by_telegram_id(user_id)
    
    if user:
        # Пользователь уже зарегистрирован
        bot.send_message(
            user_id, 
            f"Вы уже зарегистрированы в системе.\nВаша роль: {user.role}\nВаша команда: {user.team.name if user.team else 'Не указана'}",
            reply_markup=get_main_menu_markup(user_id)
        )
        return
    
    # Запрос выбора команды
    bot.send_message(
        user_id, 
        "Для регистрации выберите вашу команду:",
        reply_markup=get_markup_for_teams()
    )
    
    # Сохранение информации о пользователе
    user_data[user_id] = {
        'telegram_id': user_id,
        'username': message.from_user.username,
        'full_name': f"{message.from_user.first_name} {message.from_user.last_name if message.from_user.last_name else ''}"
    }
    
    set_user_state(user_id, UserState.AWAITING_TEAM_SELECTION)

@bot.message_handler(commands=[BOT_COMMANDS['REPORT']])
def handle_report_command(message):
    """Обработка команды /report для создания отчета"""
    user_id = message.from_user.id
    user = UserService.get_user_by_telegram_id(user_id)
    
    if not user:
        bot.send_message(
            user_id, 
            "Вы не зарегистрированы в системе. Используйте команду /register для регистрации."
        )
        return
    
    # Запрос описания задачи
    bot.send_message(
        user_id, 
        "Введите описание выполненной задачи:"
    )
    
    # Инициализация данных отчета
    user_data[user_id] = {
        'user_id': user.id,
        'team_id': user.team_id
    }
    
    set_user_state(user_id, UserState.AWAITING_REPORT_DESCRIPTION)

@bot.message_handler(commands=[BOT_COMMANDS['HELP']])
def handle_help(message):
    """Обработка команды /help"""
    help_text = """
📌 *Список доступных команд:*

/start - Начало работы с ботом
/register - Регистрация в системе
/report - Отправка отчета о выполненной задаче
/help - Показать справку

*Описание бота:*
Этот бот помогает сотрудникам отправлять отчеты о выполненных задачах, а руководителям получать сводную информацию по отделам.
    """
    bot.send_message(message.chat.id, help_text, parse_mode='Markdown')

@bot.message_handler(commands=[BOT_COMMANDS['ADMIN']])
def handle_admin(message):
    """Обработка команды /admin для администраторов"""
    user_id = message.from_user.id
    
    if not UserService.is_admin(user_id):
        bot.send_message(
            user_id, 
            "У вас нет прав администратора."
        )
        return
    
    markup = types.InlineKeyboardMarkup(row_width=2)
    markup.add(
        types.InlineKeyboardButton("Управление пользователями", callback_data="admin_manage_users"),
        types.InlineKeyboardButton("Управление командами", callback_data="admin_manage_teams")
    )
    
    bot.send_message(
        user_id, 
        "Выберите действие:",
        reply_markup=markup
    )
    
    set_user_state(user_id, UserState.AWAITING_ADMIN_ACTION)

# Обработчики текстовых сообщений
@bot.message_handler(func=lambda message: get_user_state(message.from_user.id) == UserState.AWAITING_REPORT_DESCRIPTION)
def handle_report_description(message):
    """Обработка ввода описания задачи"""
    user_id = message.from_user.id
    description = message.text.strip()
    
    if not description:
        bot.send_message(
            user_id, 
            "Описание не может быть пустым. Пожалуйста, введите описание выполненной задачи:"
        )
        return
    
    # Сохранение описания
    user_data[user_id]['description'] = description
    
    # Запрос ввода числового показателя (опционально)
    markup = types.InlineKeyboardMarkup()
    markup.add(
        types.InlineKeyboardButton("Да", callback_data="report_add_metric"),
        types.InlineKeyboardButton("Нет", callback_data="report_no_metric")
    )
    
    bot.send_message(
        user_id, 
        "Хотите добавить числовой показатель к отчету?",
        reply_markup=markup
    )

@bot.message_handler(func=lambda message: get_user_state(message.from_user.id) == UserState.AWAITING_REPORT_METRIC_NAME)
def handle_report_metric_name(message):
    """Обработка ввода названия показателя"""
    user_id = message.from_user.id
    metric_name = message.text.strip()
    
    if not metric_name:
        bot.send_message(
            user_id, 
            "Название показателя не может быть пустым. Пожалуйста, введите название:"
        )
        return
    
    # Сохранение названия показателя
    user_data[user_id]['metric_name'] = metric_name
    
    # Запрос ввода значения показателя
    bot.send_message(
        user_id, 
        f"Введите значение для показателя '{metric_name}':"
    )
    
    set_user_state(user_id, UserState.AWAITING_REPORT_METRIC)

@bot.message_handler(func=lambda message: get_user_state(message.from_user.id) == UserState.AWAITING_REPORT_METRIC)
def handle_report_metric_value(message):
    """Обработка ввода значения показателя"""
    user_id = message.from_user.id
    metric_value_text = message.text.strip()
    
    try:
        metric_value = float(metric_value_text.replace(',', '.'))
        user_data[user_id]['metric_value'] = metric_value
        
        # Создание отчета
        report = ReportService.create_report(
            user_id=user_data[user_id]['user_id'],
            team_id=user_data[user_id]['team_id'],
            description=user_data[user_id]['description'],
            metric_name=user_data[user_id]['metric_name'],
            metric_value=metric_value
        )
        
        if report:
            bot.send_message(
                user_id, 
                f"Отчет успешно создан!\n\nОписание: {report.description}\nПоказатель: {report.metric_name}: {report.metric_value}",
                reply_markup=get_main_menu_markup(user_id)
            )
        else:
            bot.send_message(
                user_id, 
                "Произошла ошибка при создании отчета. Пожалуйста, попробуйте снова.",
                reply_markup=get_main_menu_markup(user_id)
            )
        
        reset_user_state(user_id)
    except ValueError:
        bot.send_message(
            user_id, 
            "Неверный формат числа. Пожалуйста, введите числовое значение (например, 42 или 3.14):"
        )

# Обработчики нажатий на кнопки
@bot.callback_query_handler(func=lambda call: call.data.startswith("select_team_"))
def handle_team_selection(call):
    """Обработка выбора команды при регистрации"""
    user_id = call.from_user.id
    team_id = int(call.data.split("_")[2])
    
    if get_user_state(user_id) != UserState.AWAITING_TEAM_SELECTION:
        return
    
    team = TeamService.get_team_by_id(team_id)
    if not team:
        bot.send_message(
            user_id, 
            "Выбранная команда не найдена. Пожалуйста, выберите другую команду."
        )
        return
    
    # Сохранение выбранной команды
    user_data[user_id]['team_id'] = team_id
    
    # Создание пользователя
    user = UserService.create_user(
        telegram_id=user_data[user_id]['telegram_id'],
        username=user_data[user_id]['username'],
        full_name=user_data[user_id]['full_name'],
        role=USER_ROLES['EMPLOYEE'],  # По умолчанию все новые пользователи - сотрудники
        team_id=team_id
    )
    
    if user:
        bot.edit_message_text(
            chat_id=call.message.chat.id,
            message_id=call.message.message_id,
            text=f"Регистрация успешно завершена!\n\nВаша роль: {user.role}\nВаша команда: {team.name}"
        )
        
        bot.send_message(
            user_id,
            "Теперь вы можете отправлять отчеты о выполненных задачах с помощью команды /report или нажав на соответствующую кнопку в меню.",
            reply_markup=get_main_menu_markup(user_id)
        )
    else:
        bot.edit_message_text(
            chat_id=call.message.chat.id,
            message_id=call.message.message_id,
            text="Произошла ошибка при регистрации. Пожалуйста, попробуйте снова позже."
        )
    
    reset_user_state(user_id)

@bot.callback_query_handler(func=lambda call: call.data == "create_new_team")
def handle_create_new_team(call):
    """Обработка создания новой команды"""
    user_id = call.from_user.id
    
    bot.edit_message_text(
        chat_id=call.message.chat.id,
        message_id=call.message.message_id,
        text="Функция создания новой команды доступна только администраторам. Пожалуйста, обратитесь к администратору системы."
    )
    
    bot.send_message(
        user_id,
        "Выберите существующую команду для регистрации:",
        reply_markup=get_markup_for_teams()
    )

@bot.callback_query_handler(func=lambda call: call.data == "report_add_metric")
def handle_add_metric(call):
    """Обработка добавления числового показателя"""
    user_id = call.from_user.id
    
    bot.edit_message_text(
        chat_id=call.message.chat.id,
        message_id=call.message.message_id,
        text="Введите название числового показателя (например, 'Количество обработанных заявок'):"
    )
    
    set_user_state(user_id, UserState.AWAITING_REPORT_METRIC_NAME)

@bot.callback_query_handler(func=lambda call: call.data == "report_no_metric")
def handle_no_metric(call):
    """Обработка отказа от добавления числового показателя"""
    user_id = call.from_user.id
    
    # Создание отчета без числового показателя
    report = ReportService.create_report(
        user_id=user_data[user_id]['user_id'],
        team_id=user_data[user_id]['team_id'],
        description=user_data[user_id]['description']
    )
    
    if report:
        bot.edit_message_text(
            chat_id=call.message.chat.id,
            message_id=call.message.message_id,
            text="Отчет успешно создан!"
        )
        
        bot.send_message(
            user_id,
            f"Описание: {report.description}",
            reply_markup=get_main_menu_markup(user_id)
        )
    else:
        bot.edit_message_text(
            chat_id=call.message.chat.id,
            message_id=call.message.message_id,
            text="Произошла ошибка при создании отчета. Пожалуйста, попробуйте снова."
        )
    
    reset_user_state(user_id)

# Обработчики текстовых кнопок в главном меню
@bot.message_handler(func=lambda message: message.text == '📝 Отправить отчет')
def handle_send_report_button(message):
    """Обработка нажатия на кнопку отправки отчета"""
    handle_report_command(message)

@bot.message_handler(func=lambda message: message.text == '📋 Мои отчеты')
def handle_my_reports_button(message):
    """Обработка нажатия на кнопку просмотра своих отчетов"""
    user_id = message.from_user.id
    user = UserService.get_user_by_telegram_id(user_id)
    
    if not user:
        bot.send_message(
            user_id, 
            "Вы не зарегистрированы в системе. Используйте команду /register для регистрации."
        )
        return
    
    reports = ReportService.get_user_reports(user.id)
    
    if not reports:
        bot.send_message(
            user_id, 
            "У вас еще нет отчетов."
        )
        return
    
    # Отображение последних 5 отчетов
    response = "Ваши последние отчеты:\n\n"
    
    for i, report in enumerate(reports[:5], 1):
        response += f"{i}. Дата: {report.report_date.strftime('%d.%m.%Y')}\n"
        response += f"   Описание: {report.description}\n"
        
        if report.metric_name and report.metric_value:
            response += f"   {report.metric_name}: {report.metric_value}\n"
        
        response += "\n"
    
    bot.send_message(user_id, response)

@bot.message_handler(func=lambda message: message.text == '📊 Получить отчет за неделю')
def handle_weekly_report_button(message):
    """Обработка нажатия на кнопку получения недельного отчета"""
    user_id = message.from_user.id
    user = UserService.get_user_by_telegram_id(user_id)
    
    if not user or (user.role != USER_ROLES['MANAGER'] and user.role != USER_ROLES['ADMIN']):
        bot.send_message(
            user_id, 
            "У вас нет доступа к этой функции."
        )
        return
    
    # Получение еженедельного отчета для команды руководителя
    team_id = user.team_id if user.role == USER_ROLES['MANAGER'] else None  # Для админа - все команды
    summary = ReportService.generate_weekly_summary(team_id)
    
    bot.send_message(user_id, summary)

@bot.message_handler(func=lambda message: message.text == 'ℹ️ Помощь')
def handle_help_button(message):
    """Обработка нажатия на кнопку помощи"""
    handle_help(message)

# Обработчик неизвестных команд
@bot.message_handler(func=lambda message: True)
def handle_unknown(message):
    """Обработка всех остальных сообщений"""
    user_id = message.from_user.id
    user = UserService.get_user_by_telegram_id(user_id)
    
    if not user:
        bot.send_message(
            user_id, 
            "Вы не зарегистрированы в системе. Используйте команду /register для регистрации."
        )
        return
    
    bot.send_message(
        user_id, 
        "Не понимаю эту команду. Используйте кнопки меню или команду /help для получения списка доступных команд.",
        reply_markup=get_main_menu_markup(user_id)
    )

def start_bot():
    """Запуск бота"""
    logger.info("Запуск бота...")
    bot.polling(none_stop=True, interval=0)

if __name__ == "__main__":
    start_bot() 