#!/bin/bash

service cron start &&
flask run -h 0.0.0.0 -p 80 --with-threads