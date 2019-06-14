# -*- coding: utf-8 -*-
"""Specification forms."""
from flask_wtf import FlaskForm
from flask_login import current_user
from wtforms import StringField, TextAreaField
from wtforms.ext.sqlalchemy.fields import QuerySelectField
from wtforms.validators import DataRequired
from pid.user.models import User
from pid.backend.models import Settings
import operator


# Helpers for query_factories in forms
def get_owners():
    return User.query.all()


class CreateSpecificationForm(FlaskForm):
    name = StringField('Specification Title', validators=[DataRequired('A name is required.')])
    owner = QuerySelectField(query_factory=get_owners, get_label='last_name_first_name', default=current_user)

    def __init__(self, *args, **kwargs):
        """Create instance."""
        super(CreateSpecificationForm, self).__init__(*args, **kwargs)
        settings = Settings.get_settings()
        if settings:
            self.owner.get_label = operator.attrgetter(settings.name_order)

    def validate(self):
        initial_validation = super(CreateSpecificationForm, self).validate()
        errors = False
        if not initial_validation:
            errors = True
        if errors:
            return False
        return True


class ReviseSpecificationForm(FlaskForm):
    revision_reason = TextAreaField('Reason for Revision', validators=[DataRequired('A reason for revision is required.')])
    owner = QuerySelectField(query_factory=get_owners, get_label='last_name_first_name', default=current_user)

    def __init__(self, *args, **kwargs):
        """Create instance."""
        super(ReviseSpecificationForm, self).__init__(*args, **kwargs)
        settings = Settings.get_settings()
        if settings:
            self.owner.get_label = operator.attrgetter(settings.name_order)

    def validate(self):
        initial_validation = super(ReviseSpecificationForm, self).validate()
        errors = False
        if not initial_validation:
            errors = True
        if errors:
            return False
        return True
