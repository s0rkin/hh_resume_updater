# HH Resume Updater

Утилита для автоматического поднятия резюме на hh.ru через официальное Android API.

За основу взят проект - https://github.com/s3rgeym/hh-applicant-tool 
Оттуда взяли Anroid ключи и заголовки. За что отдельное спасибо автору, если используете это приложение не забудьте поставить "звездочку" автору оригинала!

## 📋 Описание

Скрипт позволяет управлять резюме на hh.ru:
- просматривать список резюме,
- поднимать отдельное резюме,
- поднимать все резюме сразу.

Поддерживается OAuth 2.0 авторизация и имитация Android-клиента для корректной работы API.

### Основные возможности

- 🔐 OAuth 2.0 авторизация через Android-клиент
- 📝 Просмотр списка резюме
- ⬆️ Поднятие отдельных резюме или всех сразу
- 💾 Автоматическое сохранение и обновление токенов
- 📱 Рандомный User-Agent как в Android-приложении
- 🤖 Уведомления в Telegram (при настройке)

## 🚀 Установка

1. Клонируйте репозиторий:

```bash
git clone https://github.com/s0rkin/hh_resume_updater
cd hh_resume_updater
```

2. Установите зависимости:

```bash
pip install -r requirements.txt
```

3. Создайте конфигурацию:

```bash
cp expample.env .env
```

4. Заполните `.env` по шаблону.

## ⚙️ Конфигурация (.env)

Заполните следующие параметры в файле `.env`:

```dotenv
# Требуются для работы HH API
ANDROID_CLIENT_ID="Уже указан в примере"
ANDROID_CLIENT_SECRET="Уже указан в примере"
REDIRECT_URI=hhandroid://hh.ru/auth
TOKEN_FILE=token.json

# Опционально (для Telegram-уведомлений)
TELEGRAM_BOT_TOKEN=your_bot_token
TELEGRAM_CHAT_ID=your_chat_id
PROXY_HOST=http://proxy.example.com:8080
```

### Где взять данные

- `TELEGRAM_BOT_TOKEN` — в @BotFather.
- `TELEGRAM_CHAT_ID` — через @userinfobot.

## 🛠️ Использование

### Авторизация

```bash
python hh_resume_updater.py auth
```

При первом запуске или когда токен истёк, авторизация выполняется автоматически.

Вам нужно вставить в скрипт ссылку вида hhandroid://

### Список резюме

```bash
python hh_resume_updater.py list
```

### Поднять резюме

Поднять все:

```bash
python hh_resume_updater.py upgrade
```

Поднять конкретное по ID:

```bash
python hh_resume_updater.py upgrade <resume_id>
```

## 📌 Примеры

```bash
# Показать список резюме
python hh_resume_updater.py list

# Поднять резюме с ID
python hh_resume_updater.py upgrade 123456789

# Поднять все резюме
python hh_resume_updater.py upgrade
```

## 🔄 Автоматизация (cron)

Запустите по расписанию, например каждые 2 часа:

```cron
0 */2 * * * cd /path/to/project && python hh_resume_updater.py upgrade >> logs.txt 2>&1
```

## 📊 Логика работы с токенами

- Токен сохраняется в `TOKEN_FILE`.
- При истечении токена он обновляется через `refresh_token`.
- Если обновление не удалось, требуется повторная авторизация через `auth`.

## 📝 Примечания

- Имитируется поведение Android-приложения для стабильной работы API.
- Между поднятиями резюме скрипт делает паузу ~2 секунды (ограничения API).
- Ошибки логируются в консоль и отправляются в Telegram (если настроено).
- Успехи также отправляются в Telegram (если настроено).

## ⚠️ Важно

- Не передавайте `token.json` третьим лицам.
- Не публикуйте `.env` с реальными данными.
- Соблюдайте правила hh.ru и лимиты запросов.

## 📄 Лицензия

MIT

## 🤝 Вклад в проект

Предложения по улучшению приветствуются. Открывайте issue или pull request.
