import html
import os
import sys

import requests

sys.path.append('.')
sys.path.append('..')
from app.settings import TG_ALERTS_CHANNEL, TG_BOT_TOKEN


def telegram_command(name: str, data: dict, **kwargs):
    api_url = 'https://api.telegram.org/bot{token}/{method}'.format
    url = api_url(token=TG_BOT_TOKEN, method=name)
    return requests.post(url=url, data=data, **kwargs)


def tg_send_message(text: str, chat_id: str, notify=True):
    return telegram_command(
        'sendMessage',
        {
            'text': text,
            'chat_id': chat_id,
            'parse_mode': 'html',
			'disable_notification': not notify,
            'disable_web_page_preview': True,
        },
    )

if __name__ == '__main__':
    r = tg_send_message('Hello', TG_ALERTS_CHANNEL)
    print(r)
    print(123)