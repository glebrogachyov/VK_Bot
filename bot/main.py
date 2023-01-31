from server import Bot, logger
import requests
from storage.settings.config import token, group_id

bot = Bot(token, group_id)


@logger.catch
def main():
    while True:
        try:
            logger.info("Bot started.")
            bot.start()
        except requests.exceptions.RequestException:
            logger.error("Bot stopped. e: ConnectionError")
            continue
        except Exception as e:
            logger.error("Bot stopped. e: " + repr(e))
            continue
        except BaseException as be:
            logger.error("Bot stopped. be: " + repr(be))
            continue


if __name__ == '__main__':
    main()
