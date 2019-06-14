#!/bin/sh
# Use the exec command to start the app you want to run in this container.
# Don't let the app daemonize itself.

# Read more here: https://github.com/phusion/baseimage-docker#adding-additional-daemons
chdir /app
exec /app/venv/bin/gunicorn manage:app \
    -e PLAID_ENV=prod \
    --workers 4 \
    --log-level=warning \
    --bind 0.0.0.0:5000 \
    --access-logfile /var/log/plaid/gunicorn/access.log \
    --error-logfile /var/log/plaid/gunicorn/error.log
