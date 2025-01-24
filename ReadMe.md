# Бот для проверки IMEI

Сервер и Telegram-бот на базе FastAPI для проверки IMEI и получения подробной информации об устройстве.

## Функции

- Проверка IMEI
- Интерфейс Telegram-бота
- Аутентификация на основе JWT

## Переменные среды

Создайте в корневом каталоге файл `.env` со следующими переменными:

```
# Конфигурация сервера
JWT_SECRET_KEY=jwt_секретный_ключ
IMEI_API_KEY=imei_api_ключ_для_imeichecknet

# Настройка Telegram-бота
BOT_TOKEN=телеграм_бот_токен
ADMIN_USER_ID=дмин_телеграм_id
```

## Установка
Клонировать репозиторий:

```cmd
 >> git clone https://github.com/optongroup/imei-checker.git 
 >> cd imei-checker
```

## Создание и активация виртуальной среды:

```cmd
 >> python -m venv .venv
 >> pip install -r requirements.txt
```

## Использование
Запуск сервера и бота
Выполните следующую команду, чтобы запустить как сервер FastAPI, так и Telegram-бота:

```cmd
python start.py
```

Сервер будет доступен по адресу http://localhost:8000

## Конечные точки API

Проверьте IMEI
```
GET /api/check-imei?imei={imei_number}
Header: Authorization: Bearer {token}
```

## Telegram Bot Commands
 - `/start` - Start the bot

 - `/help` - Show help message

 - `/auth` - Authorize user (admin only)

 - Отправить IMEI

## Проверка IMEI
Система проверяет номера IMEI с помощью:

 - Длина 15 символов

 - Только цифр

 - Проверка по алгоритму (Луна)[https://ru.wikipedia.org/wiki/%D0%90%D0%BB%D0%B3%D0%BE%D1%80%D0%B8%D1%82%D0%BC_%D0%9B%D1%83%D0%BD%D0%B0]