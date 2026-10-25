# Telegram Todo Bot Reminder

Telegram-бот для управления напоминаниями. На первом этапе реализованы
загрузка конфигурации, команда `/start`, базовое логирование и корректное
завершение приложения.

## Запуск

Требуется Python 3.12 или новее.

1. Установите зависимости:

   ```bash
   python -m pip install -e .
   ```

2. Создайте файл `.env` в корне проекта:

   ```dotenv
   BOT_TOKEN=your_telegram_bot_token
   ```

   Токен можно получить у [@BotFather](https://t.me/BotFather). Файл `.env`
   не должен добавляться в Git.

3. Запустите бота:

   ```bash
   python -m telegramtodobotreminder.main
   ```

   Также доступна установленная консольная команда:

   ```bash
   telegramtodobotreminder
   ```

Если `BOT_TOKEN` отсутствует или пуст, приложение завершится с понятным
сообщением об ошибке до создания подключения к Telegram.
