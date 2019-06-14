#!/bin/bash

mkdir -p /opt/pr/pid
cd /opt/pr/pid
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
deactivate

# sudo steps to be done manually
# cp /opt/pr/pid/deployment/pid.gunicorn.service /etc/systemd/system/gunicorn.service
# cp /opt/pr/pid/deployment/pid.conf.nginx /etc/nginx/sites-available/pid.planetaryresources.com
# ln -s /etc/nginx/sites-available/pid.planetaryresources.com /etc/nginx/sites-enabled/pid.planetaryresources.com
# chown -R www-data:www-data /opt/pr/pid
# service nginx restart
# systemctl daemon-reload
# systemctl start gunicorn
# systemctl enable gunicorn
