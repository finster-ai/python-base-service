FROM python:3.10-slim

WORKDIR /python-docker

COPY requirements.txt requirements.txt
RUN apt-get update && apt-get install ffmpeg libsm6 libxext6 -y
RUN pip3 install -r requirements.txt

RUN apt install -y libreoffice-writer

COPY . .

ENV FLASK_APP=api_base_service.py

EXPOSE 8080

CMD exec gunicorn --bind :8080 --workers 1 --timeout 600 --threads 8 api_base_service:app
