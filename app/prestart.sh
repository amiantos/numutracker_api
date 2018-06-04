#! /usr/bin/env bash

# Let the DB start
sleep 10;
# Run migrations
flask db upgrade