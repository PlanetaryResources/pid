# -*- coding: utf-8 -*-
"""User views."""
from flask import Blueprint, render_template
from flask_login import login_required, current_user

blueprint = Blueprint('user', __name__, url_prefix='/users', static_folder='../static')


@blueprint.before_app_request
def mark_current_user_online():
    if current_user and current_user.is_authenticated:
        current_user.mark_online()
