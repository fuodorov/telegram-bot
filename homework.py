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
REQUEST_TIMEOUT = 10
BOT_TIMEOUT = 300
TIMEOUT = 5

logging.basicConfig(
    level=logging.INFO,
    filename='bot.log',
    format='%(asctime)s, %(levelname)s, %(name)s, %(message)s'
)


class UndefinedStatusError(Exception):
    pass


def parse_homework_status(homework):
    try:
        homework_status = homework.get('status')
        if homework_status not in STATUSES:
            raise UndefinedStatusError('The response with an unknown status'
                                       f' {homework_status}')
        homework_name = homework.get('homework_name')
    except KeyError as e:
        logging.error(e, exc_info=True)
    verdict = STATUSES[homework_status]
    logging.info(f'homework_name = "{homework_name}", verdict = "{verdict}"')
    return f'У вас проверили работу "{homework_name}"!\n\n{verdict}'


def get_homework_statuses(current_timestamp):
    if current_timestamp is None:
        current_timestamp = int(time.time())
    headers = {'Authorization': f'OAuth {PRAKTIKUM_TOKEN}'}
    params = {'from_date': current_timestamp}
    try:
        homework_statuses = requests.get(f'{API_URL}{API_METHODS["homework"]}',
                                         headers=headers, params=params,
                                         timeout=REQUEST_TIMEOUT)
    except requests.HTTPError as e:
        logging.error(e, exc_info=True)
    except requests.ConnectionError as e:
        logging.error(e, exc_info=True)
    except requests.Timeout as e:
        logging.error(e, exc_info=True)
    except requests.RequestException as e:
        logging.error(e, exc_info=True)
    return homework_statuses.json()


def send_message(message, bot_client):
    return bot_client.send_message(chat_id='CHAT_ID', text=message)


def main():
    logging.debug('Running')
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
                logging.info('Sent message')
            current_timestamp = new_homework.get('current_date')
            time.sleep(BOT_TIMEOUT)
        except Exception as e:
            logging.error(e, exc_info=True)
            send_message(f'Бот столкнулся с ошибкой: {e}', bot)
            time.sleep(TIMEOUT)


if __name__ == '__main__':
    main()
