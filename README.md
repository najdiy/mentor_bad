# Mentor Bads Bot

Telegram-бот для отслеживания приёма БАД от бренда **Mentor Bads**.

## Возможности

- Добавление БАД с расписанием приёмов
- Ежедневные напоминания в нужное время (с учётом часового пояса)
- Кнопки "Принял / Пропустить / Напомнить позже (+30 мин, +1 час)"
- Отслеживание остатков с автоматическим декрементом
- Алерты при низком запасе с кнопкой подтверждения заказа
- Статистика приёмов за 7 и 30 дней
- Пауза/возобновление напоминаний
- Рассылка от администратора

## Быстрый старт

### 1. Создайте бота

Напишите [@BotFather](https://t.me/BotFather) в Telegram, создайте бота и скопируйте токен.

### 2. Установка

```bash
python3 -m venv .venv
source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

### 3. Конфигурация

Скопируйте `.env.example` в `.env` и заполните:

```env
BOT_TOKEN=ваш_токен_от_BotFather
ADMIN_IDS=ваш_telegram_id     # Несколько через запятую: 123,456
DATABASE_URL=sqlite+aiosqlite:///mentor_bads.db
SCHEDULER_DB=scheduler.db
```

Узнать свой Telegram ID: напишите [@userinfobot](https://t.me/userinfobot)

### 4. Запуск

```bash
python -m bot.main
```

## Команды бота

| Команда | Описание |
|---|---|
| `/start` | Регистрация и главное меню |
| `/add_supplement` | Добавить новый БАД |
| `/supplements` | Список ваших БАД |
| `/my_schedule` | Расписание приёмов на сегодня |
| `/stock` | Остатки |
| `/update_stock` | Обновить количество |
| `/stats` | Статистика (неделя / месяц) |
| `/timezone` | Сменить часовой пояс |
| `/pause` | Приостановить напоминания |
| `/resume` | Возобновить напоминания |

## Структура проекта

```
bot/
├── main.py              # Точка входа
├── config.py            # Настройки из .env
├── database/            # ORM-модели и репозитории
├── handlers/            # Обработчики команд и кнопок
├── keyboards/           # Клавиатуры Telegram
├── scheduler/           # APScheduler — напоминания
├── middlewares/         # DB-сессия, rate limiting
├── filters/             # Фильтр IsAdmin
├── states/              # FSM-состояния
└── utils/               # Форматтеры, timezone-хелперы
```

## Стек

- **aiogram 3.x** — Telegram Bot framework
- **APScheduler 3.x** + SQLiteJobStore — планировщик напоминаний
- **SQLAlchemy 2.x** async + **aiosqlite** — база данных
- **pydantic-settings** — конфигурация

## Деплой на сервер (опционально)

Для постоянной работы используйте systemd, Docker или любой PaaS (Railway, Render).

Пример `systemd` unit-файла (`/etc/systemd/system/mentor-bads-bot.service`):

```ini
[Unit]
Description=Mentor Bads Telegram Bot
After=network.target

[Service]
WorkingDirectory=/opt/mentor-bads
ExecStart=/opt/mentor-bads/.venv/bin/python -m bot.main
Restart=always

[Install]
WantedBy=multi-user.target
```
