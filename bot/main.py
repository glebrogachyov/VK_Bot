from server import Bot
import requests
from settings.config import token, group_id

bot = Bot(token, group_id)

# bot.start()

while True:
    try:
        print("Bot started.")
        bot.start()
    except requests.exceptions.RequestException:
        print('ConnectionError')
        continue
    except Exception as e:
        print("Bot stopped.\nError: ", e)
        continue
    except BaseException as be:
        print("Bot stopped on BaseException.\nError: ", be)
        continue
