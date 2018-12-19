FROM ubuntu:18.04

RUN apt-get update && apt-get install -y

RUN apt-get update && apt-get install -y \
    python3-pip \
    python3-dev \
    build-essential \
    libssl-dev \
    libffi-dev \
    python3-setuptools \
    cron

COPY requirements.txt /tmp/requirements.txt
RUN pip3 install -r /tmp/requirements.txt

COPY . /opt/app

RUN useradd --create-home --shell /bin/bash numu
RUN chown -R numu:numu /opt/app

ENV PYTHONIOENCODING utf-8
ENV LC_ALL C.UTF-8
ENV LANG C.UTF-8
ENV FLASK_ENV development
ENV FLASK_APP numu.py

EXPOSE 80

ADD crontab /etc/crontab
RUN chmod 0644 /etc/crontab
RUN touch /var/log/cron.log

WORKDIR /opt/app

RUN ["chmod", "+x", "/opt/app/run_devserver.sh"]
ENTRYPOINT ["sh", "run_devserver.sh"]