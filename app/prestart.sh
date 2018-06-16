#! /usr/bin/env bash

# Run migrations
flask db upgrade

su -m celery -c "celery -A tasks beat --loglevel=info --pidfile='/tmp/celerybeat.pid'" &
#su -m celery -c "celery -A tasks worker --loglevel=info"