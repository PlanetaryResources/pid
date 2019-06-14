# -*- coding: utf-8 -*-
"""Application configuration."""
import os


class Config(object):
    """Base configuration."""
    SECRET_KEY = os.environ.get('PID_SECRET', 'this-is-going-to-be-the-best-spacecraft-database-ever')
    APP_DIR = os.path.abspath(os.path.dirname(__file__))  # This directory
    PROJECT_ROOT = os.path.abspath(os.path.join(APP_DIR, os.pardir))
    ASSETS_DEBUG = False
    DEBUG_TB_ENABLED = False  # Disable Debug toolbar
    DEBUG_TB_INTERCEPT_REDIRECTS = False
    CACHE_TYPE = 'simple'  # Can be "memcached", "redis", etc.
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    # LDAP settings
    LDAP_HOST = 'ldap.planetaryresources.com'
    LDAP_BASE_DN = 'DC=planetaryresources,DC=com'
    LDAP_USER_DN = 'CN=Users'
    LDAP_GROUP_DN = 'CN=Users'
    LDAP_USER_LOGIN_ATTR = 'sAMAccountName'
    # TODO: Change user and password to something specific for PID
    LDAP_BIND_USER_DN = 's-chatLDAP'
    LDAP_BIND_USER_PASSWORD = 'YOUR_LDAP_BIND_USER_PASSWORD_HERE'
    LDAP_SEARCH_FOR_GROUPS = True
    # LDAP_USER_SEARCH_SCOPE = 'SEARCH_SCOPE_WHOLE_SUBTREE'
    # LDAP_GROUP_SEARCH_SCOPE = 'SEARCH_SCOPE_WHOLE_SUBTREE'  # SEARCH_SCOPE_BASE_OBJECT, SEARCH_SCOPE_SINGLE_LEVEL, SEARCH_SCOPE_WHOLE_SUBTREE
    # LDAP_USER_OBJECT_FILTER = '(&(objectCategory=person)(objectClass=user)(!(userAccountControl=66050)))'
    # LDAP_GROUP_OBJECT_FILTER = '(&(objectCategory=Group)(objectClass=group)(!(userAccountControl=66050)))'
    LDAP_GROUP_MEMBERS_ATTR = 'member'
    PLAID_USERS_GROUP = 'plaid-users'  # Group that allows users access
    PLAID_VERSION = '1.0.0'  # http://semver.org/spec/v2.0.0.html
    UPLOAD_FOLDER = PROJECT_ROOT + '/uploads'
    ALLOWED_IMAGE_EXTENSIONS = ['png', 'jpg', 'jpeg', 'gif', 'bmp', 'tiff']
    MAX_CONTENT_LENGTH = 256 * 1024 * 1024  # 256 MB upload limit, should be reflected in NGINX on prod as well
    PRINT_SQL_STATEMENTS = False  # Do not print out debug SQL statements
    PRETTIFY_STDOUT = False  # Do not prettify log output
    MAIL_SERVER = 'smtp.planetaryresources.com'
    MAIL_PORT = 25
    MAIL_DEFAULT_SENDER = 'PLAID <plaid.noreply@planetaryresources.com>'
    ADMINS = ['jarle@planetaryresources.com', 'haggartplaid@gmail.com']  # TODO: Have these in settings page instead
    CELERY_BROKER_URL = 'amqp://plaid_dev_rabbit:complicated-password-here@localhost/plaid_dev_amqp'
    CELERY_RESULT_BACKEND = 'amqp://plaid_dev_rabbit:complicated-password-here@localhost/plaid_dev_amqp'
    MIGRATIONS_DIR = 'migrations'  # This should be overwritten by other configs


class ProdConfig(Config):
    """Production configuration."""
    ENV = 'prod'
    TESTING = False
    DEBUG = False
    SQLALCHEMY_DATABASE_URI = 'postgresql://plaid_user:complicated-password-here@prd-db:5433/plaid_db'
    DEBUG_TB_ENABLED = False  # Disable Debug toolbar
    MINIFY_PAGE = True  # Minify HTML (remove comments, whitespace, etc)
    CELERY_BROKER_URL = 'amqp://plaid_rabbit:complicated-password-here@rabbitmq/plaid_amqp'
    CELERY_RESULT_BACKEND = 'amqp://plaid_rabbit:complicated-password-here@rabbitmq/plaid_amqp'
    MIGRATIONS_DIR = 'migrations_prod'


class DevConfig(Config):
    """Development configuration."""
    ENV = 'dev'
    DEBUG = True
    DB_NAME = 'pid_db'
    SQLALCHEMY_DATABASE_URI = 'postgresql://localhost/{0}'.format(DB_NAME)
    # SQLALCHEMY_ECHO = True  # Print out SQL statements via SQLAlchemy
    PRINT_SQL_STATEMENTS = True  # Print out SQL statements via our own method
    DEBUG_TB_ENABLED = True
    DEBUG_TB_PROFILER_ENABLED = True
    ASSETS_DEBUG = True  # Don't bundle/minify static assets
    CACHE_TYPE = 'simple'  # Can be "memcached", "redis", etc.
    MINIFY_PAGE = False  # Don't minify HTML
    PRETTIFY_STDOUT = True  # Prettify and condense HTTP log output
    TESTING = False
    MAIL_SUPPRESS_SEND = False  # Send emails even in dev environment
    DEV_EMAIL = 'jarle@planetaryresources.com'  # Remember to change this for yourself
    MIGRATIONS_DIR = 'migrations_dev'


class StagingConfig(Config):
    ENV = 'staging'
    TESTING = False
    DEBUG = False
    DEBUG_TB_ENABLED = False
    MINIFY_PAGE = True
    # MAIL_SUPPRESS_SEND = True  # Don't send emails, would conflict with emails from production app.
    SQLALCHEMY_DATABASE_URI = 'postgresql://plaid_staging_user:complicated-password-here@prd-db:5433/plaid_staging_db'
    CELERY_BROKER_URL = 'amqp://plaid_staging_rabbit:complicated-password-here@rabbitmq_staging/plaid_staging_amqp'
    CELERY_RESULT_BACKEND = 'amqp://plaid_staging_rabbit:complicated-password-here@rabbitmq_staging/plaid_staging_amqp'
    MIGRATIONS_DIR = 'migrations_staging'
    PLAID_USERS_GROUP = 'employees'  # Allow anyone in company access to staging server
    MAIL_DEFAULT_SENDER = 'PLAID Staging <plaid.stagingy@planetaryresources.com>'


class TestConfig(Config):
    """Test configuration."""
    TESTING = True
    DEBUG = True
    SQLALCHEMY_DATABASE_URI = 'sqlite://'
    WTF_CSRF_ENABLED = False  # Allows form testing
