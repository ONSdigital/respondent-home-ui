FROM python:3.6

WORKDIR /app
COPY . /app
EXPOSE 8085
RUN pip3 install pipenv && pipenv install --deploy --system

CMD ["python3", "run.py"]
