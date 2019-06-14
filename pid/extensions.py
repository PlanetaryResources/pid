# -*- coding: utf-8 -*-
"""Extensions module. Each extension is initialized in the app factory located in app.py."""
import os

from celery import Celery
from flasgger import Swagger
from flask_admin import Admin, AdminIndexView, expose
from flask_caching import Cache
from flask_debugtoolbar import DebugToolbarExtension
from flask_htmlmin import HTMLMIN
from flask_ldap3_login import LDAP3LoginManager
from flask_login import LoginManager, login_required
from flask_mail import Mail
from flask_migrate import Migrate
from flask_moment import Moment
from flask_restful import Api
from flask_sqlalchemy import SQLAlchemy
from flask_whooshee import Whooshee
from flask_wtf.csrf import CSRFProtect

from pid.settings import DevConfig, ProdConfig, StagingConfig
from pid.utils import admin_required, admin_or_superuser_required


# Block access to /admin unless logged in
class FlaskAdminBlockedAdminIndex(AdminIndexView):

    @login_required
    @admin_required
    @expose('/')
    def index(self):
        return self.render('admin/index.html')


class FlaskAdminBlockedSuperuserIndex(AdminIndexView):

    @login_required
    @admin_or_superuser_required
    @expose('/')
    def index(self):
        return self.render('admin/index.html')


# Workaround to use PostgreSQL's native autocommit. If using SQLALchemy's standard way of doing everything
# in a transaction, PGSQL might be blocked from autovacuum etc. This way we have more of a manual control if needed.
# http://oddbird.net/2014/06/14/sqlalchemy-postgres-autocommit/
# https://github.com/mitsuhiko/flask-sqlalchemy/issues/120
# https://stackoverflow.com/a/12417346
class SQLAlchemyAutoCommit(SQLAlchemy):
    def apply_driver_hacks(self, app, info, options):
        if not 'isolation_level' in options:
            options['isolation_level'] = 'AUTOCOMMIT'
        return super(SQLAlchemyAutoCommit, self).apply_driver_hacks(app, info, options)


config = DevConfig
if os.environ.get('PLAID_ENV') == 'prod':
    config = ProdConfig
elif os.environ.get('PLAID_ENV') == 'staging':
    config = StagingConfig


csrf_protect = CSRFProtect()
login_manager = LoginManager()
db = SQLAlchemyAutoCommit()
migrate = Migrate()
cache = Cache()
debug_toolbar = DebugToolbarExtension()
admin = Admin(template_mode='bootstrap3', index_view=FlaskAdminBlockedAdminIndex())
superuser = Admin(template_mode='bootstrap3', index_view=FlaskAdminBlockedSuperuserIndex(
    url='/superuser', endpoint='superuser'))
restful_api = Api()
ldap_manager = LDAP3LoginManager()
swagger = Swagger()
moment = Moment()
whooshee = Whooshee()
htmlmin = HTMLMIN()
mail = Mail()
celery = Celery(__name__, broker=config.CELERY_BROKER_URL)
