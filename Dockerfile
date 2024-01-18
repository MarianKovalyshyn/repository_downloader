FROM python:3.11.4-slim-buster
LABEL maintainer="mariankovalishin12345@gmail.com"

ENV PYTHONUNBUFFERED 1

WORKDIR /app

COPY requirements.txt requirements.txt

RUN apt-get update && apt-get -y install gcc

RUN pip install -r requirements.txt

COPY . .

CMD ["python", "main.py"]
