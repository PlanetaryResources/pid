#!/bin/sh
# Use the exec command to start the app you want to run in this container.
# Don't let the app daemonize itself.

# Read more here: https://github.com/phusion/baseimage-docker#adding-additional-daemons
chdir /app
exec /sbin/setuser www-data /app/venv/bin/celery -A celery_worker.celery worker \
    -f /var/log/plaid/celery/worker.log -l WARNING
