from loguru import logger
from sys import stdout

logger.remove(0)
logger.add(stdout, format="{time} {level} {message}", level="INFO")
logger.add("storage/log/bot_log.log", format="{time} {level} {message}",
           level="DEBUG", rotation="06:00", retention="3 days")
