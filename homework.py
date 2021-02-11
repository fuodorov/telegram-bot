import logging
import os
import time

import requests
import telegram
from dotenv import load_dotenv

load_dotenv()

PRAKTIKUM_TOKEN = os.getenv('PRAKTIKUM_TOKEN')
TELEGRAM_TOKEN = os.getenv('TELEGRAM_TOKEN')
CHAT_ID = os.getenv('TELEGRAM_CHAT_ID')
API_URL = 'https://praktikum.yandex.ru/api/'
API_METHODS = {'homework': 'user_api/homework_statuses/'}
STATUSES = {
    'rejected': 'К сожалению в работе нашлись ошибки.',
    'approved': ('Ревьюеру всё понравилось, можно приступать к следующему'
                 ' уроку.'),
    'reviewing': 'Работа взята в ревью.'
}

logging.basicConfig(
    level=logging.INFO,
    filename='bot.log',
    format='%(asctime)s, %(levelname)s, %(name)s, %(message)s'
)


class UndefinedStatusError(Exception):
    pass


def parse_homework_status(homework):
    homework_status = homework['status']
    if homework_status not in STATUSES:
        raise UndefinedStatusError('В ответе пришел неизвестный статус'
                                   f' {homework_status}')
    homework_name = homework['homework_name']
    verdict = STATUSES[homework_status]
    return f'У вас проверили работу "{homework_name}"!\n\n{verdict}'


def get_homework_statuses(current_timestamp):
    headers = {'Authorization': f'OAuth {PRAKTIKUM_TOKEN}'}
    params = {'from_date': current_timestamp}
    homework_statuses = requests.get(API_URL + API_METHODS['homework'],
                                     headers=headers, params=params)
    return homework_statuses.json()


def send_message(message, bot_client):
    return bot_client.send_message(chat_id='CHAT_ID', text=message)


def main():
    logging.debug('Работа началась')
    bot = telegram.Bot(token=TELEGRAM_TOKEN)
    current_timestamp = int(time.time())
    while True:
        try:
            new_homework = get_homework_statuses(current_timestamp)
            if new_homework.get('homeworks'):
                send_message(
                    parse_homework_status(new_homework.get('homeworks')[0]),
                    bot
                )
                logging.info('Отправлено сообщение')
            current_timestamp = new_homework.get('current_date')
            time.sleep(300)
        except Exception as e:
            logging.error(e, exc_info=True)
            send_message(f'Бот столкнулся с ошибкой: {e}', bot)
            time.sleep(5)


if __name__ == '__main__':
    main()
