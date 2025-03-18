# AI Report Bot - Система отчетности с Telegram-ботом

Система для сбора и агрегации отчетов сотрудников через Telegram-бота с интегрированным мини-приложением.

## Функциональность

- **Telegram-бот**: Команды для регистрации, создания отчетов и администрирования
- **Мини-приложение**: Удобный интерфейс для отправки отчетов о выполненных задачах
- **Ролевая система доступа**: Три роли пользователей (Сотрудник, Руководитель, Администратор)
- **Еженедельные отчеты**: Сводные отчеты для руководителей
- **Возможность экспорта**: Генерация текстовых отчетов

## Архитектура системы

- **Backend**: Python с Flask для веб-сервера
- **Frontend**: HTML, CSS, JavaScript для Telegram Mini App
- **База данных**: SQLite (разработка) / PostgreSQL (продакшн)
- **Интеграции**: Telegram Bot API

## Структура проекта

```
AI_report_bot/
├── bot/                  # Код Telegram-бота
├── app/                  # Код мини-приложения
├── db/                   # Модели базы данных и миграции
├── services/             # Сервисы бизнес-логики
├── config/               # Конфигурационные файлы
├── static/               # Статические файлы для мини-приложения
├── templates/            # HTML шаблоны
└── utils/                # Вспомогательные функции
```

## Подробная инструкция по установке и запуску

### Предварительные требования

1. Python 3.8 или выше
2. Токен Telegram-бота (можно получить у [@BotFather](https://t.me/BotFather))
3. Зарегистрированное мини-приложение в Telegram (для полной функциональности)

### Шаг 1: Клонирование репозитория

```bash
git clone https://github.com/ваш-username/AI_report_bot.git
cd AI_report_bot
```

### Шаг 2: Создание виртуального окружения и установка зависимостей

```bash
# Создание виртуального окружения
python -m venv venv

# Активация виртуального окружения
# Для Windows:
venv\Scripts\activate
# Для macOS/Linux:
source venv/bin/activate

# Установка зависимостей
pip install -r requirements.txt
```

### Шаг 3: Настройка конфигурации

1. Создайте файл `.env` на основе `.env.example`:
   ```bash
   # Для Windows:
   copy .env.example .env
   # Для macOS/Linux:
   cp .env.example .env
   ```

2. Отредактируйте файл `.env` и укажите свои значения:
   ```
   # Токен вашего Telegram бота (получите у @BotFather)
   TELEGRAM_BOT_TOKEN=your_telegram_bot_token_here

   # URL-адрес вашего веб-приложения (используется для вебхука)
   WEBHOOK_URL=https://your-app-domain.com

   # Настройки базы данных
   DATABASE_URL=sqlite:///database.db
   ```

### Шаг 4: Инициализация базы данных

База данных будет автоматически инициализирована при первом запуске приложения. По умолчанию используется SQLite, но вы можете настроить PostgreSQL, изменив `DATABASE_URL` в файле `.env`.

### Шаг 5: Запуск приложения

```bash
python main.py
```

После запуска бот будет готов принимать команды, а мини-приложение будет доступно по указанному URL-адресу.

## Использование

### Команды бота

- `/start` - Начало работы с ботом
- `/register` - Регистрация в системе
- `/report` - Создание нового отчета
- `/help` - Справка по командам
- `/admin` - Панель администратора (только для администраторов)

### Роли пользователей

1. **Сотрудник**:
   - Может создавать отчеты о выполненных задачах
   - Может просматривать свои отчеты

2. **Руководитель**:
   - Все возможности Сотрудника
   - Может получать еженедельные сводные отчеты по своей команде

3. **Администратор**:
   - Все возможности Руководителя
   - Управление пользователями и командами
   - Доступ ко всем отчетам

### Мини-приложение Telegram

Мини-приложение предоставляет удобный веб-интерфейс для:
- Создания отчетов
- Просмотра истории отчетов
- Получения еженедельных сводок (для руководителей и администраторов)

## Устранение проблем

### Проблема: Бот не запускается

Решение:
- Проверьте правильность токена бота в файле `.env`
- Убедитесь, что все зависимости установлены: `pip install -r requirements.txt`
- Проверьте отсутствие ошибок в логах

### Проблема: Не работает мини-приложение

Решение:
- Убедитесь, что URL вебхука настроен правильно
- Проверьте доступность мини-приложения по указанному URL
- Для локальной разработки используйте тунелирование (например, ngrok)