#!/usr/bin/env python3

import requests
import urllib.parse
import json
import os
import sys
import time
import argparse
import random
import uuid
from datetime import datetime, timedelta
import telebot
from telebot import apihelper

#load file .env config
from dotenv import load_dotenv
load_dotenv()

# Данные от Android-приложения
ANDROID_CLIENT_ID = os.getenv("ANDROID_CLIENT_ID")
ANDROID_CLIENT_SECRET = os.getenv("ANDROID_CLIENT_SECRET")
REDIRECT_URI = os.getenv("REDIRECT_URI")
TOKEN_FILE = os.getenv("TOKEN_FILE")

# Telegram (если не заданы, уведомления не отправляются)
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")

if TELEGRAM_BOT_TOKEN and TELEGRAM_CHAT_ID:
    apihelper.proxy = {
        "http": os.getenv("PROXY_HOST"),
        "https": os.getenv("PROXY_HOST"),
    }

# ----------------------------------------------------------------------
# Генерация User-Agent как в Android-приложении
# ----------------------------------------------------------------------

def generate_android_useragent() -> str:
    """Генерирует случайный User-Agent, похожий на официальное Android-приложение."""
    devices = (
        "23053RN02A, 23053RN02Y, 23053RN02I, 23053RN02L, 23077RABDC".split(", ")
    )
    device = random.choice(devices)
    minor = random.randint(100, 150)
    patch = random.randint(10000, 15000)
    android = random.randint(11, 15)
    return (
        f"ru.hh.android/7.{minor}.{patch}, Device: {device}, "
        f"Android OS: {android} (UUID: {uuid.uuid4()})"
    )

# ----------------------------------------------------------------------
# Отправка уведомлений в Telegram (через telebot)
# ----------------------------------------------------------------------

def send_telegram_message(text: str) -> bool:
    """Отправляет сообщение в Telegram через библиотеку telebot."""
    if not TELEGRAM_BOT_TOKEN or not TELEGRAM_CHAT_ID:
        print("Telegram не настроен, сообщение не отправлено.")
        return False
    try:
        bot = telebot.TeleBot(TELEGRAM_BOT_TOKEN)
        bot.send_message(TELEGRAM_CHAT_ID, text, parse_mode='HTML')
        return True
    except Exception as e:
        print(f"Исключение при отправке в Telegram: {e}")
        return False

# ----------------------------------------------------------------------
# Авторизация с ручным вводом URI (для сервера)
# ----------------------------------------------------------------------

def get_authorization_code():
    """Выводит ссылку для авторизации, ждёт ввода полного URI с кодом."""
    auth_url = (f"https://hh.ru/oauth/authorize"
                f"?client_id={ANDROID_CLIENT_ID}"
                f"&response_type=code"
                f"&redirect_uri={REDIRECT_URI}")

    print("\n" + "="*60)
    print("Для авторизации перейдите по ссылке (можно на любом устройстве):")
    print(auth_url)
    print("\nПосле подтверждения доступа браузер перенаправит вас на адрес")
    print(f"{REDIRECT_URI}?code=... (страница не найдётся, это нормально).")
    print("Скопируйте ПОЛНЫЙ URI из адресной строки браузера (начинается с hhandroid://)")
    print("и вставьте его сюда.")
    print("="*60 + "\n")

    while True:
        user_input = input("Вставьте URI: ").strip()
        if not user_input:
            continue
        parsed = urllib.parse.urlparse(user_input)
        params = urllib.parse.parse_qs(parsed.query)
        if 'code' in params:
            return params['code'][0]
        else:
            print("Не удалось найти код в URI. Попробуйте ещё раз.")

def exchange_code_for_token(code):
    """Обменивает код на access_token и refresh_token."""
    token_data = {
        'grant_type': 'authorization_code',
        'client_id': ANDROID_CLIENT_ID,
        'client_secret': ANDROID_CLIENT_SECRET,
        'code': code,
        'redirect_uri': REDIRECT_URI
    }
    headers = {'User-Agent': generate_android_useragent()}
    resp = requests.post("https://hh.ru/oauth/token", data=token_data, headers=headers)
    if resp.status_code != 200:
        raise Exception(f"Ошибка получения токена: {resp.text}")
    token_json = resp.json()
    token_json['expires_at'] = (datetime.now() + timedelta(seconds=token_json['expires_in'])).isoformat()
    return token_json

def authorize():
    """Запрашивает код через ручной ввод URI и возвращает полный токен."""
    code = get_authorization_code()
    return exchange_code_for_token(code)

# ----------------------------------------------------------------------
# Работа с сохранённым токеном
# ----------------------------------------------------------------------

def load_token():
    """Загружает токен из файла, если он ещё не истёк."""
    if not os.path.exists(TOKEN_FILE):
        return None
    with open(TOKEN_FILE, 'r') as f:
        data = json.load(f)
    expires_at = datetime.fromisoformat(data['expires_at'])
    if datetime.now() >= expires_at:
        return None
    return data

def save_token(token):
    with open(TOKEN_FILE, 'w') as f:
        json.dump(token, f, indent=2)

def refresh_token(refresh_token_value):
    """Обновляет токен по refresh_token."""
    data = {
        'grant_type': 'refresh_token',
        'refresh_token': refresh_token_value,
        'client_id': ANDROID_CLIENT_ID,
        'client_secret': ANDROID_CLIENT_SECRET
    }
    headers = {'User-Agent': generate_android_useragent()}
    
    try:
        resp = requests.post("https://hh.ru/oauth/token", data=data, headers=headers)
        
        print(f"Refresh token response status: {resp.status_code}")
        
        if resp.status_code != 200:
            print(f"Refresh token error response: {resp.text}")
            return None
            
        token_json = resp.json()
        
        if 'access_token' not in token_json:
            print("No access_token in refresh response")
            return None
            
        token_json['expires_at'] = (datetime.now() + timedelta(seconds=token_json.get('expires_in', 3600))).isoformat()
        
        if 'refresh_token' not in token_json:
            token_json['refresh_token'] = refresh_token_value
            print("Using old refresh_token")
            
        return token_json
        
    except Exception as e:
        print(f"Exception during token refresh: {e}")
        return None

def get_valid_token(force_auth=False):
    """
    Возвращает действующий access_token.
    Если force_auth=True, игнорирует сохранённый токен и запускает новую авторизацию.
    """
    if force_auth:
        print("Force auth requested, authorizing...")
        token = authorize()
        save_token(token)
        return token['access_token']

    token = load_token()
    if token:
        expires_at = datetime.fromisoformat(token['expires_at'])
        current_time = datetime.now()
        
        # Обновляем токен ТОЛЬКО если он истек
        if current_time >= expires_at:
            print("Token expired, refreshing...")
            new_token = refresh_token(token['refresh_token'])
            if new_token:
                save_token(new_token)
                print("Token refreshed successfully")
                return new_token['access_token']
            else:
                print("Failed to refresh token, need new authorization")
                if os.path.exists(TOKEN_FILE):
                    os.remove(TOKEN_FILE)
                token = authorize()
                save_token(token)
                return token['access_token']
        else:
            # Токен еще действителен
            time_left = expires_at - current_time
            print(f"Token is valid, expires in {time_left}")
            return token['access_token']
    else:
        print("Token not found, authorizing...")
        token = authorize()
        save_token(token)
        return token['access_token']

# ----------------------------------------------------------------------
# API запросы
# ----------------------------------------------------------------------

def api_request(method, url, token, data=None):
    headers = {
        'Authorization': f'Bearer {token}',
        'User-Agent': generate_android_useragent()
    }
    
    print(f"Making {method} request to {url}")
    
    if method.upper() == 'GET':
        resp = requests.get(url, headers=headers)
    elif method.upper() == 'POST':
        resp = requests.post(url, headers=headers, data=data)
    else:
        raise ValueError(f"Unsupported method: {method}")
    
    # 204 - успешный ответ без содержимого
    if resp.status_code == 204:
        print(f"✅ Request successful (204 No Content)")
    elif resp.status_code != 200:
        print(f"❌ API error {resp.status_code}: {resp.text[:500]}")
    else:
        print(f"✅ Request successful (200 OK)")
    
    return resp

def get_resumes(token):
    """Возвращает список резюме пользователя."""
    resp = api_request('GET', 'https://api.hh.ru/resumes/mine', token)
    if resp.status_code == 200:
        return resp.json().get('items', [])
    else:
        print(f"Ошибка получения списка резюме: {resp.status_code} {resp.text}", file=sys.stderr)
        return []

def publish_resume(token, resume_id):
    """Поднимает резюме."""
    resp = api_request('POST', f'https://api.hh.ru/resumes/{resume_id}/publish', token)
    # 204 - успешный ответ
    return resp.status_code == 204

# ----------------------------------------------------------------------
# CLI команды
# ----------------------------------------------------------------------

def cmd_auth(args):
    """Принудительная авторизация (получение нового токена)."""
    try:
        token = get_valid_token(force_auth=True)
        # Проверим информацию о пользователе
        resp = api_request('GET', 'https://api.hh.ru/me', token)
        if resp.status_code == 200:
            me = resp.json()
            msg = f"✅ Авторизация выполнена успешно.\nВы: {me.get('first_name')} {me.get('last_name')} (id: {me.get('id')})"
        else:
            msg = "✅ Авторизация выполнена, но не удалось получить данные пользователя."
        print(msg)
        send_telegram_message(msg)
    except Exception as e:
        error_msg = f"❌ Ошибка авторизации: {e}"
        print(error_msg)
        send_telegram_message(error_msg)

def cmd_list(args):
    """Показать список резюме."""
    try:
        token = get_valid_token()
        resumes = get_resumes(token)
        if not resumes:
            print("У вас нет резюме.")
            return
        print("Ваши резюме:")
        for i, r in enumerate(resumes, 1):
            print(f"{i}. {r.get('title')} (ID: {r['id']})")
            updated = r.get('updated_at', '')
            if updated:
                print(f"   Обновлено: {updated}")
    except Exception as e:
        print(f"Ошибка при получении списка резюме: {e}")

def cmd_upgrade(args):
    """Поднять одно или все резюме."""
    results = []
    error_occurred = False
    try:
        token = get_valid_token()
        resumes = get_resumes(token)
        if not resumes:
            msg = "Нет резюме для поднятия."
            print(msg)
            send_telegram_message(msg)
            return

        if args.resume_id:
            # Поднимаем конкретное
            found = False
            for r in resumes:
                if r['id'] == args.resume_id:
                    found = True
                    print(f"Поднимаем: {r.get('title')} ({r['id']})")
                    success = publish_resume(token, r['id'])
                    if success:
                        status = "✅ Успешно"
                        results.append(f"{status} {r.get('title')} (ID: {r['id']})")
                    else:
                        status = "❌ Ошибка"
                        results.append(f"{status} {r.get('title')} (ID: {r['id']})")
                        error_occurred = True
                    break
            if not found:
                msg = f"Резюме с ID {args.resume_id} не найдено."
                print(msg)
                send_telegram_message(msg)
                return
        else:
            # Поднимаем все
            for r in resumes:
                print(f"Поднимаем: {r.get('title')} ({r['id']})")
                success = publish_resume(token, r['id'])
                if success:
                    status = "✅ Успешно"
                    results.append(f"{status} {r.get('title')} (ID: {r['id']})")
                else:
                    status = "❌ Ошибка"
                    results.append(f"{status} {r.get('title')} (ID: {r['id']})")
                    error_occurred = True
                time.sleep(2)  # Пауза между поднятиями
    except Exception as e:
        error_msg = f"❌ Критическая ошибка при выполнении: {e}"
        print(error_msg)
        send_telegram_message(error_msg)
        return

    # Отправляем итоговый отчёт
    if results:
        report = f"📊 Результаты поднятия резюме {datetime.now().strftime('%d.%m.%Y %H:%M')}\n\n"
        report += "\n".join(results)
        if error_occurred:
            report += "\n\n⚠️ Некоторые резюме не удалось поднять."
        print(report)
        send_telegram_message(report)
    else:
        msg = "⚠️ Не удалось поднять резюме (нет результатов)."
        print(msg)
        send_telegram_message(msg)

def main():
    parser = argparse.ArgumentParser(description='Утилита для поднятия резюме на hh.ru (консольная авторизация)')
    subparsers = parser.add_subparsers(dest='command', required=True, help='Команда')

    parser_auth = subparsers.add_parser('auth', help='Авторизоваться (получить новый токен)')
    parser_list = subparsers.add_parser('list', help='Показать список резюме')
    parser_upgrade = subparsers.add_parser('upgrade', help='Поднять резюме')
    parser_upgrade.add_argument('resume_id', nargs='?', help='ID резюме (если не указан, поднимаются все)')

    args = parser.parse_args()

    if args.command == 'auth':
        cmd_auth(args)
    elif args.command == 'list':
        cmd_list(args)
    elif args.command == 'upgrade':
        cmd_upgrade(args)
    else:
        parser.print_help()

if __name__ == '__main__':
    main()