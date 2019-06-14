# -*- coding: utf-8 -*-
"""Procedure forms."""
from flask_wtf import FlaskForm
from wtforms import SelectField
from wtforms.ext.sqlalchemy.fields import QuerySelectField
from pid.user.models import User
from .models import Settings
import operator


# Helpers for query_factories in forms

def get_users():
    return User.query.all()


class SettingsForm(FlaskForm):
    efab_user = QuerySelectField('EFAB User', query_factory=get_users, get_label='last_name_first_name')
    mfab_user = QuerySelectField('MFAB User', query_factory=get_users, get_label='last_name_first_name')
    plaid_admin = QuerySelectField('PLAID Admin', query_factory=get_users, get_label='last_name_first_name')
    name_order = SelectField('Name Order', choices=Settings.name_order_options)

    def __init__(self, *args, **kwargs):
        """Create instance."""
        super(SettingsForm, self).__init__(*args, **kwargs)
        settings = Settings.get_settings()
        if settings:
            self.efab_user.get_label = operator.attrgetter(settings.name_order)
            self.mfab_user.get_label = operator.attrgetter(settings.name_order)
            self.plaid_admin.get_label = operator.attrgetter(settings.name_order)

    def validate(self):
        initial_validation = super(SettingsForm, self).validate()
        errors = False

        if not initial_validation:
            errors = True

        if errors:
            return False

        return True
