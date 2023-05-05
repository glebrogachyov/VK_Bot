from services.utilities import get_correct_datetime

from loguru import logger
from sys import stdout

fmt = "- %d.%m.%Y %H:%M:%S"


def set_datetime(record):
    record["extra"]["datetime"] = get_correct_datetime().strftime(fmt)


output_format = '{extra[datetime]} | {level:5} | {message}'

logger.configure(patcher=set_datetime)
logger.remove(0)

logger.add(stdout, format=output_format, level="INFO")
logger.add("storage/log/bot_log.log", format=output_format, level="DEBUG", rotation="06:00", retention="3 days")
