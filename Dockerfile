# Stage 1: Build environment
FROM python:3.10-alpine AS build-env
WORKDIR /python-docker
COPY requirements.txt requirements.txt

RUN apk add --no-cache gcc musl-dev libffi-dev openssl-dev && \
    pip install --no-cache-dir uvicorn && \
    pip install --no-cache-dir -r requirements.txt && \
    apk del gcc musl-dev

# Stage 2: Production environment
FROM python:3.10-alpine
WORKDIR /python-docker

RUN apk add --no-cache libffi openssl

# Copy installed Python packages and Uvicorn binary
COPY --from=build-env /usr/local/lib/python3.10/site-packages /usr/local/lib/python3.10/site-packages
COPY --from=build-env /usr/local/bin/uvicorn /usr/local/bin/uvicorn
COPY . .

EXPOSE 8080

CMD ["uvicorn", "python_base_service:app", "--host", "0.0.0.0", "--port", "8080", "--workers", "1", "--timeout-keep-alive", "600"]
