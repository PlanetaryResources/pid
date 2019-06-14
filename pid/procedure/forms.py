# -*- coding: utf-8 -*-
"""Procedure forms."""
from flask_wtf import FlaskForm
from flask_login import current_user
from wtforms import StringField, TextAreaField
from wtforms.ext.sqlalchemy.fields import QuerySelectField
from wtforms.validators import DataRequired
from pid.user.models import User
from pid.common.models import Project
from pid.backend.models import Settings
import operator


# Helpers for query_factories in forms
def get_owners():
    return User.query.all()


def get_projects():
    return Project.query.all()


class CreateProcedureForm(FlaskForm):
    name = StringField('Procedure Title', validators=[DataRequired('A title is required.')])
    project = QuerySelectField(query_factory=get_projects, get_label='name', allow_blank=True,
                               blank_text='--- Select project ---', validators=[DataRequired()])
    owner = QuerySelectField(query_factory=get_owners, get_label='last_name_first_name', default=current_user)

    def __init__(self, *args, **kwargs):
        """Create instance."""
        super(CreateProcedureForm, self).__init__(*args, **kwargs)
        settings = Settings.get_settings()
        if settings:
            self.owner.get_label = operator.attrgetter(settings.name_order)

    def validate(self):
        initial_validation = super(CreateProcedureForm, self).validate()
        errors = False
        if not initial_validation:
            errors = True
        if errors:
            return False
        return True


class ReviseProcedureForm(FlaskForm):
    revision_reason = TextAreaField('Reason for Revision', validators=[DataRequired('A reason for revision is required.')])

    def __init__(self, *args, **kwargs):
        """Create instance."""
        super(ReviseProcedureForm, self).__init__(*args, **kwargs)

    def validate(self):
        initial_validation = super(ReviseProcedureForm, self).validate()
        errors = False
        if not initial_validation:
            errors = True
        if errors:
            return False
        return True
