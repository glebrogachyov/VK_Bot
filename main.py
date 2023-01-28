from server import Bot
import requests
from settings.config import token, group_id

bot = Bot(token, group_id)

bot.start()

while True:
    try:
        print("Бот поднялся.")
        bot.start()
    except requests.exceptions.RequestException:
        print('ConnectionError')
        continue
    except Exception as e:
        print("Бот упал.\nОшибка: ", e)
