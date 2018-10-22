#!/bin/bash
gunicorn -w 3 --worker-class aiohttp.worker.GunicornWebWorker -b 0.0.0.0:9092 "app.app:create_app()"
