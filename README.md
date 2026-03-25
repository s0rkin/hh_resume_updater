# HH Resume Updater

A utility for automatically updating resumes on hh.ru using the official Android API.

This project is based on https://github.com/s3rgeym/hh-applicant-tool.
Android keys and headers were taken from there. Big thanks to the author; if you use this app, don’t forget to star the original project.

## 📋 Description

The script allows you to manage resumes on hh.ru:
- list resumes,
- bump a single resume,
- bump all resumes at once.

OAuth 2.0 authorization is supported, and an Android client is emulated for proper API behavior.

### Main features

- 🔐 OAuth 2.0 authorization through Android client
- 📝 List resumes
- ⬆️ Bump individual resume or all resumes
- 💾 Automatic token save and refresh
- 📱 Random User-Agent like Android app
- 🤖 Telegram notifications (optional)

## 🚀 Installation

1. Clone the repository:

```bash
git clone https://github.com/s0rkin/hh_resume_updater
cd hh_resume_updater
```

2. Install dependencies:

```bash
pip install -r requirements.txt
```

3. Create configuration:

```bash
cp example.env .env
```

4. Fill in `.env` according to the template.

## ⚙️ Configuration (.env)

Fill in the following parameters in `.env`:

```dotenv
# Required for HH API
ANDROID_CLIENT_ID="Already in example"
ANDROID_CLIENT_SECRET="Already in example"
REDIRECT_URI=hhandroid://hh.ru/auth
TOKEN_FILE=settings.json

# Optional (for Telegram notifications)
TELEGRAM_BOT_TOKEN=your_bot_token
TELEGRAM_CHAT_ID=your_chat_id
PROXY_HOST=http://proxy.example.com:8080
```

### Where to get values

- `TELEGRAM_BOT_TOKEN` from @BotFather.
- `TELEGRAM_CHAT_ID` from @userinfobot.

## 🛠️ Usage

### Authorization

```bash
python main.py auth
```

On first run or if token expired, authorization is performed automatically.

A link of the form `hhandroid://` should be inserted into the script.

### List resumes

```bash
python main.py list
```

### Bump resume

Bump all:

```bash
python main.py upgrade
```

Bump specific resume by ID:

```bash
python main.py upgrade <resume_id>
```

## 📌 Examples

```bash
# List resumes
python main.py list

# Bump resume by ID
python main.py upgrade 123456789

# Bump all resumes
python main.py upgrade
```

## 🔄 Automation (cron)

Schedule with cron, e.g., every 5 hours:

```cron
0 */5 * * * cd /path/to/project && python main.py upgrade >> logs.txt 2>&1
```

## 📊 Token handling

- Token is saved in `TOKEN_FILE`.
- If token is expired, it is refreshed using `refresh_token`.
- If refresh fails, re-authorization with `auth` is required.

## 📝 Notes

- Android app behavior is emulated for stable API operation.
- There is a ~2 seconds delay between bump operations to respect API limits.
- Errors are logged to console and sent to Telegram (if configured).
- Success notifications are also sent to Telegram (if configured).

## ⚠️ Important

- Do not share `settings.json` with third parties.
- Do not publish `.env` with real credentials.
- Respect hh.ru rules and rate limits.

## 📄 License

MIT

## 🤝 Contribution

Suggestions are welcome. Open an issue or pull request.
