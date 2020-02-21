# Dockerfile specifically for kubernetes
FROM python:3.6-slim

RUN apt update && apt install -y build-essential curl gunicorn
RUN pip install pipenv

WORKDIR /app

COPY . /app
RUN pipenv install --deploy --system

EXPOSE 8082
CMD ["gunicorn", "app.app:create_app()", "--workers 4", "--bind 0.0.0.0:$PORT", "--worker-class", "aiohttp.worker.GunicornWebWorker"]
