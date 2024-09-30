import telebot
import requests


# URL для получения курса доллара (Центробанк России)
DOLLAR_URL = "https://www.cbr.ru/currency_base/dynamics/?json"


def get_dollar_rate():
    response = requests.get(DOLLAR_URL)
    data = response.json()

    # Извлекаем курс доллара по дате текущего дня
    today_date = data['Date']
    dollar_rates = data[today_date]

    # Найдем курс доллара
    usd_rub = next((rate for currency, rate in dollar_rates.items() if currency == 'USD'), None)

    return float(usd_rub) if usd_rub else None


def start_message():
    return """Добрый день! Как вас зовут?"""


def greeting(name):
    rate = get_dollar_rate()
    message = f"Рад знакомству, {name}! Курс доллара сегодня "
    if rate is not None:
        message += f"{rate:.2f} рублей."
    else:
        message += "не доступна на данный момент."
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
        bot.send_message(chat_id, greeting(message.text))

    bot.polling()


if __name__ == '__main__':
    main()
