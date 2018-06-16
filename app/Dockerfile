FROM tiangolo/uwsgi-nginx-flask:python3.6

RUN apt-get update && apt-get install -y \
    python3 \
    python3-pip \
    git

ENV CELERY_BROKER_URL redis://:numu_tracker@redis:6379/0
ENV CELERY_RESULT_BACKEND redis://:numu_tracker@redis:6379/0

COPY requirements.txt /tmp/requirements.txt
RUN pip3 install -r /tmp/requirements.txt

COPY . /app

RUN adduser --disabled-password --gecos '' celery
RUN chown -R celery:celery /app
