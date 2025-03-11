# BloggerAI

BloggerAI - это Telegram-бот, предназначенный для мониторинга каналов, обработки постов и публикации измененного контента в целевой канал. Бот использует библиотеку Pyrogram для взаимодействия с Telegram и OpenAI для изменения содержимого постов.

## Возможности

- Мониторинг исходного канала на наличие новых постов
- Изменение постов на основе инструкций пользователя
- Публикация измененных постов в целевой канал
- Обработка взаимодействий с пользователем и управление состоянием

## Требования

- Python 3.8+
- Токен API Telegram Bot
- Ключ API OpenAI

## Установка

1. Клонируйте репозиторий:

    ```bash
    git clone https://github.com/yourusername/bloggerAI.git
    cd bloggerAI
    ```

2. Создайте виртуальное окружение и активируйте его:

    ```bash
    python -m venv .venv
    source .venv/bin/activate  # В Windows используйте `.venv\Scripts\activate`
    ```

3. Установите необходимые пакеты:

    ```bash
    pip install -r requirements.txt
    ```

4. Настройте переменные окружения для вашего токена API Telegram Bot и ключа API OpenAI:

    ```bash
    export TELEGRAM_BOT_TOKEN='your-telegram-bot-token'
    export OPENAI_API_KEY='your-openai-api-key'
    ```

## Использование

1. Запустите бота:

    ```bash
    python main.py
    ```

2. Взаимодействуйте с ботом в Telegram, чтобы настроить исходные и целевые каналы, а также предоставить инструкции для изменения постов.

## Структура проекта

- `main.py`: Точка входа для бота.
- `services/bot/handlers/`: Содержит обработчики для различных команд и сообщений бота.
- `services/bot/bot_utils.py`: Вспомогательные функции для бота.
- `services/pyrogram_service/pyrogram_client.py`: Настройка и методы клиента Pyrogram.
- `services/database/dao.py`: Объекты доступа к данным для взаимодействия с базой данных.
- `services/shared/logger.py`: Настройка логгера.



