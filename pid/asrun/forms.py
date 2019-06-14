# -*- coding: utf-8 -*-
"""Procedure forms."""
from flask_wtf import FlaskForm
from flask_login import current_user
from wtforms.ext.sqlalchemy.fields import QuerySelectField
from pid.user.models import User
from pid.backend.models import Settings
import operator


# Helpers for query_factories in forms

def get_owners():
    return User.query.all()


class CreateAsRunForm(FlaskForm):
    owner = QuerySelectField(query_factory=get_owners, get_label='last_name_first_name', default=current_user)

    def __init__(self, *args, **kwargs):
        """Create instance."""
        super(CreateAsRunForm, self).__init__(*args, **kwargs)
        settings = Settings.get_settings()
        if settings:
            self.owner.get_label = operator.attrgetter(settings.name_order)

    def validate(self):
        initial_validation = super(CreateAsRunForm, self).validate()
        errors = False

        if not initial_validation:
            errors = True

        if errors:
            return False

        return True
