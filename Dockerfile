FROM python:3.10-slim

WORKDIR /python-docker

# Combine apt-get install commands and clean up the apt cache
RUN apt-get update && \
    apt-get install -y --no-install-recommends ffmpeg libsm6 libxext6 libreoffice-writer && \
    apt-get clean && rm -rf /var/lib/apt/lists/*

COPY requirements.txt requirements.txt

# Install Python dependencies without cache
RUN pip3 install --no-cache-dir -r requirements.txt

COPY . .

ENV FLASK_APP=main.py

EXPOSE 8080

# Use Gunicorn to serve the application
#CMD exec gunicorn --log-config gunicorn_logging.conf --bind :8080 --workers 1 --timeout 600 --threads 8 api_base_service:app
CMD ["gunicorn", "--log-config", "gunicorn_logging.conf", "--config", "gunicorn.conf.py", "api_base_service:app"]
