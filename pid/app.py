# -*- coding: utf-8 -*-
"""The app module, containing the app factory function."""
import logging
import os

from flask import Flask, render_template, send_from_directory
from flask_wtf.csrf import CSRFError

from pid import (api, backend, common, design, part, product, public, user,
                 anomaly, eco, specification, procedure, asrun, task, vendorpart, vendorproduct)
from pid.assets import assets
from pid.extensions import (admin, cache, csrf_protect, db, debug_toolbar, ldap_manager, login_manager,
                            migrate, moment, restful_api, superuser, swagger, whooshee, htmlmin, mail, celery)
from pid.settings import ProdConfig
from pid.utils import convert_utc_to_local, get_text, prettify_log, sql_debug, filter_supress_none, pad_with_zeros


# TODO: Consider SSL:
# http://flask.pocoo.org/snippets/111/
# https://stackoverflow.com/questions/28579142/attributeerror-context-object-has-no-attribute-wrap-socket/28590266#28590266


def create_app(config_object=ProdConfig):
    """An application factory, as explained here: http://flask.pocoo.org/docs/patterns/appfactories/.

    :param config_object: The configuration object to use.
    """
    app = Flask(__name__)
    app.config.from_object(config_object)
    register_extensions(app)
    register_celery(app)
    register_blueprints(app)
    register_errorhandlers(app)
    register_loggers(app)
    register_admin_views()
    register_superuser_views()

    # In case we want to use line statements for jinja2 templates:
    # http://jinja.pocoo.org/docs/2.9/templates/#line-statements
    app.jinja_env.line_statement_prefix = '#'
    app.jinja_env.filters['sn'] = filter_supress_none  # Filter to suppress 'None' string in Jinja2 templates, use like: {{value|sn}}

    # This is where we inject various variables to all Jinja2 templates
    @app.context_processor
    def inject_jinja_variables():
        variables = {
            'VERSION': config_object.PLAID_VERSION,
            'get_text': get_text,
            'convert_utc_to_local': convert_utc_to_local,
            'pad_with_zeros': pad_with_zeros,
            'online_users': user.models.User.get_online_users()
        }
        return dict(**variables)

    # Convoluted way of displaying a favicon, for legacy browsers which people probably don't use.
    @app.route('/favicon.ico')
    def favicon():
        return send_from_directory(os.path.join(app.root_path, 'static'), 'images/favicon.ico', mimetype='image/vnd.microsoft.icon')

    # Send all WTForm CSRF errors to the following page
    @app.errorhandler(CSRFError)
    def handle_csrf_error(e):
        return render_template('csrf_error.html', reason=e.description), 400

    return app


def register_extensions(app):
    """Register Flask extensions."""
    admin.init_app(app)
    assets.init_app(app)
    cache.init_app(app)
    csrf_protect.init_app(app)
    db.init_app(app)
    debug_toolbar.init_app(app)
    ldap_manager.init_app(app)
    login_manager.init_app(app)
    login_manager.login_view = 'public.home'
    moment.init_app(app)
    migrate.init_app(app, db)
    restful_api.init_app(api.views.blueprint)
    superuser.init_app(app)
    swagger.init_app(app)
    whooshee.init_app(app)
    htmlmin.init_app(app)
    mail.init_app(app)
    return None


def register_celery(app):
    celery.conf.update(app.config)
    TaskBase = celery.Task

    class ContextTask(TaskBase):
        abstract = True

        def __call__(self, *args, **kwargs):
            with app.app_context():
                return TaskBase.__call__(self, *args, **kwargs)

    celery.Task = ContextTask


def register_blueprints(app):
    """Register Flask blueprints."""
    app.register_blueprint(api.views.blueprint)
    app.register_blueprint(backend.views.blueprint)
    app.register_blueprint(common.views.blueprint)
    app.register_blueprint(design.views.blueprint)
    app.register_blueprint(part.views.blueprint)
    app.register_blueprint(product.views.blueprint)
    app.register_blueprint(public.views.blueprint)
    app.register_blueprint(user.views.blueprint)
    app.register_blueprint(anomaly.views.blueprint)
    app.register_blueprint(eco.views.blueprint)
    app.register_blueprint(specification.views.blueprint)
    app.register_blueprint(procedure.views.blueprint)
    app.register_blueprint(asrun.views.blueprint)
    app.register_blueprint(task.views.blueprint)
    app.register_blueprint(vendorpart.views.blueprint)
    app.register_blueprint(vendorproduct.views.blueprint)
    return None


def register_loggers(app):
    # Define our logger and formatting
    formatter = logging.Formatter('[%(asctime)s] %(levelname)s %(pathname)s:%(lineno)d - %(message)s', '%Y-%m-%d %H:%M:%S')
    rotating_handler = logging.handlers.RotatingFileHandler(os.getenv('PLAID_LOG_FILE', 'plaid.log'), maxBytes=10000000, backupCount=5)
    rotating_handler.setLevel(logging.DEBUG)
    rotating_handler.setFormatter(formatter)
    # Add third-party loggers to handler
    log = logging.getLogger('flask_ldap3_login')
    log.setLevel(logging.ERROR)
    log.addHandler(rotating_handler)
    # Set werkzeug logging to ERROR to filter out all the GET messages
    # log = logging.getLogger('werkzeug')
    # log.setLevel(logging.ERROR)
    # log.addHandler(handler)
    app.logger.addHandler(rotating_handler)  # Add handler to app logger
    if app.config['PRETTIFY_STDOUT']:
        prettify_log(app)  # Prettify and condense HTTP log output
    if app.config['PRINT_SQL_STATEMENTS']:
        app.after_request(sql_debug)  # Print out all SQL queries for response
    # Send error emails to admins in production
    if not app.debug:
        smtp_server = app.config['MAIL_SERVER']
        from_email = app.config['MAIL_DEFAULT_SENDER']
        admins = app.config['ADMINS']
        mail_handler = logging.handlers.SMTPHandler(mailhost=smtp_server, fromaddr=from_email, toaddrs=admins, subject='Error with PLAID')
        mail_handler.setLevel(logging.ERROR)
        app.logger.addHandler(mail_handler)
    return None


def register_admin_views():
    """Register admin views."""
    # Arranged by importance. Earlier will show up more to left in navbar
    design.admin.add_views(admin, db)
    vendorpart.admin.add_views(admin, db)
    part.admin.add_views(admin, db)
    product.admin.add_views(admin, db)
    vendorproduct.admin.add_views(admin, db)
    api.admin.add_views(admin, db)
    common.admin.add_views(admin, db)
    user.admin.add_views(admin, db)
    anomaly.admin.add_views(admin, db)
    eco.admin.add_views(admin, db)
    task.admin.add_views(admin, db)
    return None


def register_superuser_views():
    """Register superuser views."""
    common.superuser.add_views(superuser, db)
    return None


def register_errorhandlers(app):
    """Register error handlers."""
    def render_error(error):
        """Render error template."""
        # If a HTTPException, pull the `code` attribute; default to 500
        error_code = getattr(error, 'code', 500)
        return render_template('{0}.html'.format(error_code)), error_code
    for errcode in [401, 404, 500]:
        app.errorhandler(errcode)(render_error)
    return None
