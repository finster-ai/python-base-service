# Stage 1: Build environment
FROM python:3.10-alpine AS build-env
WORKDIR /python-docker
COPY requirements.txt requirements.txt

# Install build dependencies and gunicorn, then install Python packages
RUN apk add --no-cache gcc musl-dev libffi-dev openssl-dev && \
    pip install --no-cache-dir gunicorn && \
    pip install --no-cache-dir -r requirements.txt && \
    apk del gcc musl-dev

# Stage 2: Production environment
FROM python:3.10-alpine
WORKDIR /python-docker

# Install runtime dependencies
RUN apk add --no-cache libffi openssl

# Copy installed Python packages from the build environment
COPY --from=build-env /usr/local/lib/python3.10/site-packages /usr/local/lib/python3.10/site-packages
COPY --from=build-env /usr/local/bin/gunicorn /usr/local/bin/gunicorn
COPY . .

ENV FLASK_APP=main.py
EXPOSE 8080

CMD ["gunicorn", "--config", "gunicorn.conf.py", "--workers=1", "--bind=0.0.0.0:8080", "--timeout=600", "--threads=8", "api_base_service:app"]


#FROM python:3.10-slim
#
#WORKDIR /python-docker
#
## Combine apt-get install commands and clean up the apt cache
#RUN apt-get update && \
#    apt-get install -y --no-install-recommends ffmpeg libsm6 libxext6 libreoffice-writer && \
#    apt-get clean && rm -rf /var/lib/apt/lists/*
#
#COPY requirements.txt requirements.txt
#
## Install Python dependencies without cache
#RUN pip3 install --no-cache-dir -r requirements.txt
#
#COPY . .
#
#ENV FLASK_APP=main.py
#
#EXPOSE 8080
#
## Use Gunicorn to serve the application
##CMD exec gunicorn --log-config gunicorn_logging.conf --bind :8080 --workers 1 --timeout 600 --threads 8 api_base_service:app
#CMD ["gunicorn", "--config", "gunicorn.conf.py", "--workers=1", "--bind=0.0.0.0:8080", "--timeout=600", "--threads=8", "api_base_service:app"]
