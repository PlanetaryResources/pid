#!/usr/bin/env python

# Only purpose of this file is to start a Celery worker:
# celery -A celery_worker.celery worker
# See https://blog.miguelgrinberg.com/post/celery-and-the-flask-application-factory-pattern

__author__ = 'Jarle Hakas <jarle@planetaryresources.com>'
__copyright__ = 'Copyright 2017 Planetary Resources, Inc., 2019 ConsenSys, Inc.'

import os

from pid.app import create_app, celery  # noqa
from pid.settings import DevConfig, ProdConfig, StagingConfig

config = None
if os.environ.get('PLAID_ENV') == 'prod':
    config = ProdConfig
elif os.environ.get('PLAID_ENV') == 'staging':
    config = StagingConfig
else:
    config = DevConfig

app = create_app(config)
app.app_context().push()
