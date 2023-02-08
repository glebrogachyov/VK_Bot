from server import Bot, logger
import requests
import time
from storage.settings.config import token, group_id


@logger.catch
def main():
    while True:
        try:
            bot = Bot(token, group_id)
            logger.info("Bot starting...")
            bot.start()
        except requests.exceptions.RequestException:
            logger.error("Bot stopped. e: ConnectionError")
            time.sleep(2)
            continue
        except Exception as e:
            time.sleep(2)
            logger.error("Bot stopped. e: " + repr(e))
            continue
        except BaseException as be:
            time.sleep(2)
            logger.error("Bot stopped. be: " + repr(be))
            continue


if __name__ == '__main__':
    main()
