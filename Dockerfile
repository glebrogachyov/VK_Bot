FROM python:3.10-slim

WORKDIR /vk_bot

COPY ./requirements.txt /vk_bot/requirements.txt

RUN pip install --no-cache-dir --upgrade -r ./requirements.txt

COPY ./bot /vk_bot

CMD ["python", "-u", "./main.py"]