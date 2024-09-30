import telebot
from telebot import types
import requests
import logging
import sqlite3
from datetime import datetime, timedelta
import threading
from time import sleep

# Настройка логгера
logging.basicConfig(level=logging.INFO,
                    format='%(asctime)s - %(levelname)s - %(message)s',
                    filename='bot.log')

# URL для получения курса доллара (Центробанк России)
DOLLAR_URL = "https://www.cbr.ru/currency_base/dynamics/?json"


def get_dollar_rate():
    try:
        response = requests.get(DOLLAR_URL)
        response.raise_for_status()
        data = response.json()

        today_date = datetime.now().strftime('%Y-%m-%d')
        dollar_rates = data[today_date]

        usd_rub = next((rate for currency, rate in dollar_rates.items() if currency == 'USD'), None)
        return float(usd_rub) if usd_rub else None
    except Exception as e:
        logging.error(f"Ошибка при получении курса доллара: {e}")
        return None


def get_currency_rate(base_currency):
    try:
        response = requests.get(DOLLAR_URL)
        response.raise_for_status()
        data = response.json()

        today_date = datetime.now().strftime('%Y-%m-%d')
        rates = data[today_date]

        base_rate = next((rate for currency, rate in rates.items() if currency == base_currency), None)
        return float(base_rate) if base_rate else None
    except Exception as e:
        logging.error(f"Ошибка при получении курса валюты {base_currency}: {e}")
        return None


def start_message():
    return """Добрый день! Как вас зовут?"""


def greeting(name):
    message = f"Рад знакомству, {name}!"

    # Получаем список доступных валют из базы данных
    currencies = get_currencies_from_db()

    keyboard = types.InlineKeyboardMarkup()
    for currency in currencies:
        callback_button = types.InCallbackButton(text=currency, callback_data=f"{currency}_rate")
        keyboard.add(callback_button)

    message += "\n\nВыберите валюту для получения курса:"
    message += "\n\n" + str(keyboard)

    return message


def handle_callback(query):
    callback_data = query.data.split('_')[0]
    currency = callback_data.upper()

    rate = get_currency_rate(currency)
    message = f"Курс {currency} сегодня {rate:.2f} рублей."

    # Обновляем данные в базе данных
    update_exchange_rate_in_db(currency, rate)

    return message


def main():
    bot = telebot.TeleBot("YOUR_BOT_TOKEN")  # Замените на ваш токен бота

    @bot.message_handler(commands=['start'])
    def send_welcome(message):
        chat_id = message.chat.id
        bot.send_message(chat_id, start_message())

    @bot.message_handler(func=lambda message: True)
    def echo_all(message):
        chat_id = message.chat.id
        name = message.text.strip()
        bot.send_message(chat_id, greeting(name))

    @bot.callback_query_handler(func=lambda call: True)
    def callback_query(call):
        bot.answer_callback_query(call.id)
        chat_id = call.message.chat.id
        message_id = call.message.message_id
        bot.edit_message_text(handle_callback(call.data), chat_id=chat_id, message_id=message_id)

    # Запуск потока для периодического обновления курсов
    threading.Thread(target=update_exchange_rates_periodically).start()

    bot.polling()


def create_tables():
    conn = sqlite3.connect('exchange_rates.db')
    cursor = conn.cursor()

    cursor.execute('''CREATE TABLE IF NOT EXISTS users
                      (id INTEGER PRIMARY KEY, username TEXT)''')

    cursor.execute('''CREATE TABLE IF NOT EXISTS exchange_rates
                      (currency TEXT PRIMARY KEY, last_update TIMESTAMP DEFAULT CURRENT_TIMESTAMP)''')

    conn.commit()
    conn.close()


def add_user(user_id, username):
    conn = sqlite3.connect('exchange_rates.db')
    cursor = conn.cursor()
    cursor.execute("INSERT OR REPLACE INTO users VALUES (?, ?)", (user_id, username))
    conn.commit()
    conn.close()


def get_currencies_from_db():
    conn = sqlite3.connect('exchange_rates.db')
    cursor = conn.cursor()
    cursor.execute("SELECT currency FROM exchange_rates")
    currencies = [row[0] for row in cursor.fetchall()]
    conn.close()
    return currencies


def update_exchange_rate_in_db(currency, rate):
    conn = sqlite3.connect('exchange_rates.db')
    cursor = conn.cursor()
    cursor.execute("UPDATE exchange_rates SET last_update = CURRENT_TIMESTAMP WHERE currency = ?", (currency,))
    conn.commit()
    conn.close()


def update_exchange_rates_periodically():
    while True:
        for currency in ['USD', 'EUR', 'GBP']:  # Добавьте другие нужные вам валюты
            rate = get_currency_rate(currency)
            if rate is not None:
                update_exchange_rate_in_db(currency, rate)
        sleep(3600)  # Обновляем каждые час


if __name__ == '__main__':
    create_tables()  # Создаем таблицы в базе данных при первом запуске
    main()
