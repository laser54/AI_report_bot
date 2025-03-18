import sys
import os
import logging
from flask import Flask, request, render_template, jsonify, redirect, url_for, session
import json
import hmac
import hashlib
from datetime import datetime

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config.config import TELEGRAM_TOKEN, APP_HOST, APP_PORT
from db.models import init_db
from services.user_service import UserService
from services.team_service import TeamService
from services.report_service import ReportService

# Инициализация базы данных
init_db()

# Настройка логирования
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Инициализация Flask приложения
app = Flask(__name__, 
            template_folder=os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'templates'),
            static_folder=os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'static'))

app.secret_key = TELEGRAM_TOKEN  # Используем токен бота в качестве секретного ключа для сессий

# Middleware для проверки Telegram данных
def verify_telegram_data(data):
    """Проверка подписи данных от Telegram"""
    if not data:
        return False
    
    received_hash = data.get('hash')
    auth_date = data.get('auth_date')
    
    if not received_hash or not auth_date:
        return False
    
    # Удаление хеша из данных для проверки
    data_check = {k: v for k, v in data.items() if k != 'hash'}
    
    # Создание строки для проверки
    data_check_string = '\n'.join([f"{k}={v}" for k, v in sorted(data_check.items())])
    
    # Создание секретного ключа
    secret_key = hashlib.sha256(TELEGRAM_TOKEN.encode()).digest()
    
    # Вычисление хеша
    computed_hash = hmac.new(secret_key, data_check_string.encode(), hashlib.sha256).hexdigest()
    
    # Сравнение хешей
    return computed_hash == received_hash

# Главная страница
@app.route('/')
def index():
    """Отображение главной страницы"""
    return render_template('index.html')

# Авторизация через Telegram Login Widget
@app.route('/auth', methods=['POST'])
def auth():
    """Авторизация пользователя через Telegram Login Widget"""
    data = request.form.to_dict()
    
    if not verify_telegram_data(data):
        return jsonify({'status': 'error', 'message': 'Недействительные данные аутентификации'}), 403
    
    telegram_id = int(data.get('id'))
    username = data.get('username', '')
    first_name = data.get('first_name', '')
    last_name = data.get('last_name', '')
    full_name = f"{first_name} {last_name}".strip()
    
    # Получение пользователя
    user = UserService.get_user_by_telegram_id(telegram_id)
    
    if not user:
        # Перенаправление на страницу регистрации, если пользователь не зарегистрирован
        session['telegram_data'] = data
        return redirect(url_for('register'))
    
    # Сохранение данных пользователя в сессию
    session['user_id'] = user.id
    session['telegram_id'] = telegram_id
    session['username'] = username
    session['full_name'] = full_name
    session['role'] = user.role
    
    # Перенаправление на панель управления
    return redirect(url_for('dashboard'))

# Регистрация пользователя
@app.route('/register', methods=['GET', 'POST'])
def register():
    """Страница регистрации пользователя"""
    if 'telegram_data' not in session:
        return redirect(url_for('index'))
    
    if request.method == 'POST':
        team_id = request.form.get('team_id')
        
        if not team_id:
            return render_template('register.html', 
                                 teams=TeamService.get_all_teams(),
                                 error="Выберите команду")
        
        # Получение данных пользователя из сессии
        data = session['telegram_data']
        telegram_id = int(data.get('id'))
        username = data.get('username', '')
        first_name = data.get('first_name', '')
        last_name = data.get('last_name', '')
        full_name = f"{first_name} {last_name}".strip()
        
        # Создание пользователя
        user = UserService.create_user(
            telegram_id=telegram_id,
            username=username,
            full_name=full_name,
            team_id=team_id
        )
        
        if user:
            # Сохранение данных пользователя в сессию
            session['user_id'] = user.id
            session['telegram_id'] = telegram_id
            session['username'] = username
            session['full_name'] = full_name
            session['role'] = user.role
            
            # Удаление временных данных из сессии
            session.pop('telegram_data', None)
            
            # Перенаправление на панель управления
            return redirect(url_for('dashboard'))
        else:
            return render_template('register.html', 
                                 teams=TeamService.get_all_teams(),
                                 error="Ошибка при регистрации пользователя")
    
    # GET запрос - отображение формы регистрации
    return render_template('register.html', teams=TeamService.get_all_teams())

# Панель управления
@app.route('/dashboard')
def dashboard():
    """Панель управления пользователя"""
    if 'telegram_id' not in session:
        return redirect(url_for('index'))
    
    user_id = session.get('user_id')
    user = UserService.get_user_by_telegram_id(session.get('telegram_id'))
    
    if not user:
        session.clear()
        return redirect(url_for('index'))
    
    # Получение отчетов пользователя
    reports = ReportService.get_user_reports(user.id)
    
    return render_template('dashboard.html', 
                         user=user,
                         reports=reports)

# Создание отчета
@app.route('/report/create', methods=['GET', 'POST'])
def create_report():
    """Страница создания отчета"""
    if 'telegram_id' not in session:
        return redirect(url_for('index'))
    
    user = UserService.get_user_by_telegram_id(session.get('telegram_id'))
    
    if not user:
        session.clear()
        return redirect(url_for('index'))
    
    if request.method == 'POST':
        description = request.form.get('description', '').strip()
        metric_name = request.form.get('metric_name', '').strip()
        metric_value_str = request.form.get('metric_value', '').strip()
        
        if not description:
            return render_template('create_report.html', 
                                 user=user,
                                 error="Описание не может быть пустым")
        
        metric_value = None
        if metric_name and metric_value_str:
            try:
                metric_value = float(metric_value_str.replace(',', '.'))
            except ValueError:
                return render_template('create_report.html', 
                                     user=user,
                                     error="Неверный формат числового показателя")
        
        # Создание отчета
        report = ReportService.create_report(
            user_id=user.id,
            team_id=user.team_id,
            description=description,
            metric_name=metric_name if metric_name else None,
            metric_value=metric_value
        )
        
        if report:
            return redirect(url_for('dashboard'))
        else:
            return render_template('create_report.html', 
                                 user=user,
                                 error="Ошибка при создании отчета")
    
    # GET запрос - отображение формы создания отчета
    return render_template('create_report.html', user=user)

# Выход из системы
@app.route('/logout')
def logout():
    """Выход из системы"""
    session.clear()
    return redirect(url_for('index'))

# API для получения отчетов за неделю (для руководителей и администраторов)
@app.route('/api/reports/weekly', methods=['GET'])
def api_weekly_reports():
    """API для получения еженедельных отчетов"""
    if 'telegram_id' not in session:
        return jsonify({'status': 'error', 'message': 'Unauthorized'}), 401
    
    user = UserService.get_user_by_telegram_id(session.get('telegram_id'))
    
    if not user or (user.role != 'manager' and user.role != 'admin'):
        return jsonify({'status': 'error', 'message': 'Недостаточно прав'}), 403
    
    # Получение еженедельного отчета
    team_id = user.team_id if user.role == 'manager' else None
    weekly_summary = ReportService.generate_weekly_summary(team_id)
    
    return jsonify({
        'status': 'success',
        'data': weekly_summary
    })

def run_app():
    """Запуск Flask приложения"""
    app.run(host=APP_HOST, port=APP_PORT, debug=True)

if __name__ == "__main__":
    run_app() 