# -*- coding: utf-8 -*-
"""Public section, including homepage and signup."""
from flask import Blueprint, flash, redirect, render_template, request, url_for
from flask_login import login_user, logout_user, current_user

from .forms import LoginForm
from pid.extensions import login_manager
from pid.utils import flash_errors
from pid.user.models import User

blueprint = Blueprint('public', __name__, static_folder='../static')


@login_manager.user_loader
def load_user(username):
    """Load user by usename."""
    return User.get_by_username(username)


@blueprint.route('/', methods=['GET', 'POST'])
def home():
    """Home page."""
    form = LoginForm(request.form)
    # Handle logging in
    if request.method == 'POST':
        if form.validate_on_submit():
            login_user(form.user)
            redirect_url = form.next.data or url_for('backend.dashboard')
            return redirect(redirect_url)
        else:
            flash_errors(form)
    return render_template('public/home.html', form=form)


@blueprint.route('/logout/')
def logout():
    """Logout."""
    if current_user.is_authenticated:
        logout_user()
        flash('You are logged out.', 'info')
    return redirect(url_for('public.home'))


#@blueprint.route('/about/')
#def about():
#    """About page."""
#    form = LoginForm(request.form)
#    return render_template('public/about.html', form=form)
