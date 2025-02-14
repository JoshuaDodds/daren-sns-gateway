FROM python:3.10-alpine

ENV PYTHONUNBUFFERED=1

RUN mkdir /app

WORKDIR /app

RUN apk add --no-cache socat bash

COPY . /app/

RUN pip install --no-cache-dir -r requirements.txt

RUN chmod +x /app/entrypoint.sh

ENTRYPOINT ["/app/entrypoint.sh"]
