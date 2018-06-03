FROM tiangolo/uwsgi-nginx-flask:python3.6

RUN apt-get update && apt-get install -y \
    python3 \
    python3-pip \
    git

COPY requirements.txt /tmp/requirements.txt
RUN pip3 install -r /tmp/requirements.txt

COPY ./app /app
