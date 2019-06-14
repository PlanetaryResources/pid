# -*- coding: utf-8 -*-
"""Helper utilities and decorators."""
from functools import wraps
from itertools import product
from string import ascii_uppercase as AUC

import pytz
import socket
from flask import flash, abort
from flask_login import current_user
from flask_sqlalchemy import get_debug_queries

import pid.globals as GLOBAL


def flash_errors(form, category='warning'):
    """Flash all errors for a form."""
    for field, errors in form.errors.items():
        for error in errors:
            flash('{0} - {1}'.format(getattr(form, field).label.text, error), category)


# Modified from this extension: https://github.com/Frozenball/flask-color
def prettify_log(app):
    import werkzeug.serving
    import re
    # from datetime import datetime
    hidePattern = app.config.get('COLOR_PATTERN_HIDE', r'/^$/')
    WSGIRequestHandler = werkzeug.serving.WSGIRequestHandler

    class TerminalColors:
        HEADER = '\033[95m'
        OKBLUE = '\033[94m'
        OKGREEN = '\033[92m'
        GRAY = '\033[1;30m'
        LITTLEGRAY = '\033[1;30m'
        WARNING = '\033[93m'
        FAIL = '\033[91m'
        ENDC = '\033[0m'

    def log_request(self, code='-', size='-'):
        url = self.requestline.split(" ")[1]
        method = self.requestline.split(" ")[0]

        if code == 200:
            statusColor = TerminalColors.OKGREEN
        elif str(code)[0] in ['4', '5']:
            statusColor = TerminalColors.FAIL
        else:
            statusColor = TerminalColors.ENDC

        if re.search(hidePattern, url):
            return

        print("{statusColor}{status}{colorEnd} {method} {url}".format(
            # time=datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            status=code,
            method=method,
            url=url,
            statusColor=statusColor,
            colorEnd=TerminalColors.ENDC
        ))

    WSGIRequestHandler.log_request = log_request
    werkzeug.serving.WSGIRequestHandler = WSGIRequestHandler


# Modified from https://gist.github.com/dhrrgn/6022858
def sql_debug(response):
    if 'text/html' not in response.headers['Content-Type']:
        return response
    queries = list(get_debug_queries())
    query_str = ''
    total_duration = 0.0
    for q in queries:
        total_duration += q.duration
        if type(q.parameters) is tuple:
            for p in q.parameters:
                stmt = str(q.statement % p).replace('\n', '\n       ')
                query_str += 'Query: {0}\nDuration: {1}ms\n\n'.format(stmt, round(q.duration * 1000, 2))
        else:
            stmt = str(q.statement % q.parameters).replace('\n', '\n       ')
            query_str += 'Query: {0}\nDuration: {1}ms\n\n'.format(stmt, round(q.duration * 1000, 2))

    print('=' * 80)
    print(' SQL Queries - {0} Queries Executed in {1}ms'.format(len(queries), round(total_duration * 1000, 2)))
    print('=' * 80)
    print(query_str.rstrip('\n'))
    print('=' * 80 + '\n')

    return response


# ===== DECORATORS BELOW HERE ===== #

# Use where only an admin is allowed to access a function or view
def admin_required(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        if not current_user.is_admin():
            abort(401)
        return func(*args, **kwargs)
    return wrapper


# Use where only a superuser is allowed to access a function or view
def superuser_required(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        if not current_user.is_superuser():
            abort(401)
        return func(*args, **kwargs)
    return wrapper


# Use where a superuser or admin is allowed to access a function or view
def admin_or_superuser_required(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        if not current_user.is_admin_or_superuser():
            abort(401)
        return func(*args, **kwargs)
    return wrapper


# ===== JINJA2 FUNCTIONS ===== #

def convert_utc_to_local(utc_time):
    # TODO: Add timezone to current_user preferences
    # timezone = current_user.preferences.timezone
    timezone = 'America/Los_Angeles'
    local_time = utc_time.astimezone(pytz.timezone(timezone))
    return local_time


def get_text(key):
    ''' Return the text for a given key to the view, or if not found, return the key itself '''
    return GLOBAL.TEXT.get(key, key)


def filter_supress_none(val):
    if val is not None:
        return val
    else:
        return ''


# ===== MISC ===== #

def find_all_revisions(results):
    # Sort them first alphabetically, then by length
    results.sort(key=lambda x: (len(x.revision), x.revision))
    return results


def find_latest_revision(results):
    resultset = [row[0] for row in results]
    resultset.sort(key=lambda x: (len(x), x), reverse=True)
    return resultset[0]


def find_next_revision(results):
    used_revisions = [str(row[0]) for row in results]
    # Doing separate lists that we then concat, due to sorting issues
    all_possible_single_revisions = []
    all_possible_double_revisions = []
    # See: https://stackoverflow.com/questions/23686398/iterate-a-to-zzz-in-python
    for chars in AUC:
        all_possible_single_revisions.append(''.join(chars))
    for chars in product(AUC, repeat=2):
        all_possible_double_revisions.append(''.join(chars))

    free_single_revisions = list(set(all_possible_single_revisions) - set(used_revisions) - set(GLOBAL.FORBIDDEN_REVISIONS))
    free_double_revisions = list(set(all_possible_double_revisions) - set(used_revisions))
    return (sorted(free_single_revisions) + sorted(free_double_revisions))[0]


def pad_with_zeros(value, length):
    return value.zfill(length)


def format_match_query(type, query):
    if type == 'ends-with':
        formatted_query = '{0}{1}'.format('%', query)
    elif type == 'starts-with':
        formatted_query = '{0}{1}'.format(query, '%')
    else:
        formatted_query = '{0}{1}{2}'.format('%', query, '%')
    return formatted_query


def check_connection(server, port):
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    try:
        result = sock.connect_ex((server, port))
    except socket.gaierror:
        # Could not reach server
        result = 1

    if result == 0:
        return True
    else:
        return False
