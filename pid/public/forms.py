# -*- coding: utf-8 -*-
"""Public forms."""
from flask import current_app, flash
from flask_wtf import FlaskForm
from wtforms import PasswordField, StringField, HiddenField
from wtforms.validators import DataRequired
from flask_ldap3_login import AuthenticationResponseStatus
from pid.user.models import User
from pid.extensions import ldap_manager


# Inspired by:
# https://github.com/nickw444/flask-ldap3-login/blob/master/flask_ldap3_login/forms.py
@ldap_manager.save_user
def save_user(username, first_name, last_name, email, roles):
    # First check if user is already in DB, and create if not, and update if is
    user = User.get_by_username(username)
    if not user:
        # Create new user if not in database
        user = User.create(username=username, first_name=first_name, last_name=last_name, email=email, roles=roles)
    elif user.first_name != first_name or user.last_name != last_name or user.email != email or user.roles != roles:
        # Update user if details have changed. Username should never change
        user.first_name = first_name
        user.last_name = last_name
        user.email = email
        user.roles = roles
        user = User.update(user)
    return user


class LoginForm(FlaskForm):
    """Login form."""

    username = StringField('Username', validators=[DataRequired()])
    password = PasswordField('Password', validators=[DataRequired()])
    next = HiddenField('Next')

    def __init__(self, *args, **kwargs):
        """Create instance."""
        super(LoginForm, self).__init__(*args, **kwargs)
        self.user = None

    def validate(self):
        """Validate the form."""
        initial_validation = super(LoginForm, self).validate()
        if not initial_validation:
            return False

        # current_app.logger.debug('User attempting to log in')

        user = self.authenticate(self.username.data, self.password.data)

        if user is None:
            return False
        else:
            self.user = user
            return True

    def authenticate(self, username, password):
        # TODO: Check if app is able to reach LDAP server
        # TODO: Check if user is active in AD
        # Try to authenticate user via AD
        result = ldap_manager.authenticate(username, password)
        if result.status == AuthenticationResponseStatus.success:
            # Grab relevant roles for PID (users, superusers, admin)
            roles = ['employees']  # Add employees for staging server purposes. TODO: Find a better way to manage
            for group in result.user_groups:
                if group['name'].startswith('plaid-'):
                    roles.append(group['name'])


            # Check if user is part of plaid-users (required to access app)
            if current_app.config['PLAID_USERS_GROUP'] not in roles:
                flash('You are not part of PLAID users group, contact Sean or Jarle if you should have access', 'warning')
                return None

            user = ldap_manager._save_user(
                result.user_id,
                result.user_info['givenName'],
                result.user_info['sn'],
                result.user_info['mail'],
                ', '.join(roles)
            )
            return user
        else:
            # Query local SQLite DB in DEV
            if current_app.config['ENV'] is 'dev':
                user = User.get_by_username(username)
                if user is None:
                    flash('Could not authenticate with AD or find a local user', 'warning')
                    return None
                flash('Logged in as local user', 'info')
                return user
            else:
                flash('Could not authenticate your username ({0}) with AD, did you enter correct password?'.format(self.username.data), 'warning')
                return None
        return None
