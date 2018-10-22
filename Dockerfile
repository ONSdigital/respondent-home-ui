FROM python:3.6

RUN mkdir -p /usr/src/app
WORKDIR /usr/src/app

# TODO Get the Pipfile working.
RUN pip install aiodns
RUN pip install aiohttp
RUN pip install aiohttp_session[secure]
RUN pip install aiohttp-jinja2
RUN pip install aiohttp-utils
RUN pip install cchardet
RUN pip install envparse
RUN pip install gevent
RUN pip install gunicorn
RUN pip install invoke
RUN pip install iso8601
RUN pip install requests
RUN pip install retrying
RUN pip install sdc-cryptography
RUN pip install structlog

EXPOSE 9092

ENTRYPOINT ["sh", "docker-entrypoint.sh"]

COPY . /usr/src/app
