#! /usr/bin/env bash

# Run migrations
flask db upgrade

su -m celery -c "celery -A tasks beat --loglevel=info" &
#su -m celery -c "celery -A tasks worker --loglevel=info"