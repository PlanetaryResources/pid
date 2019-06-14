# -*- coding: utf-8 -*-
"""Anomaly forms."""
from flask_wtf import FlaskForm
from flask_login import current_user
from wtforms import StringField
from wtforms.ext.sqlalchemy.fields import QuerySelectField
from wtforms.validators import DataRequired
from pid.user.models import User
from pid.backend.models import Settings
import operator


def get_owners():
    return User.query.all()


class CreateECOForm(FlaskForm):
    designs = StringField('', validators=[DataRequired('At least one design is required.')])
    name = StringField('ECO Title', validators=[DataRequired('A name is required.')])
    owner = QuerySelectField(query_factory=get_owners, get_label='last_name_first_name', default=current_user)

    def __init__(self, *args, **kwargs):
        super(CreateECOForm, self).__init__(*args, **kwargs)
        settings = Settings.get_settings()
        if settings:
            self.owner.get_label = operator.attrgetter(settings.name_order)

    def validate(self):
        initial_validation = super(CreateECOForm, self).validate()
        return initial_validation
