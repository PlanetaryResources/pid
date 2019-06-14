# -*- coding: utf-8 -*-
"""Anomaly forms."""
from flask_wtf import FlaskForm
from flask_login import current_user
from wtforms import StringField, IntegerField, RadioField, HiddenField
from wtforms.ext.sqlalchemy.fields import QuerySelectField
from wtforms.validators import DataRequired
from pid.common.models import Criticality
from pid.user.models import User
from pid.design.models import Design
from pid.vendorpart.models import VendorPart
from pid.asrun.models import AsRun
from pid.backend.models import Settings
import operator

# Helpers for query_factories in forms


def get_owners():
    return User.query.all()


def get_criticality():
    return Criticality.query.all()


class CreateAnomalyForm(FlaskForm):
    affected = RadioField('Against', choices=[('design', 'DESIGN'), ('asrun', 'AS-RUN'), ('other', 'OTHER')]
                          , default='design')
    designs = StringField('')
    vendor_parts = StringField('')
    as_runs = StringField('')
    name = StringField('Anomaly Title', validators=[DataRequired('A name is required.')])
    criticality = QuerySelectField(query_factory=get_criticality, get_label='name')
    owner = QuerySelectField(query_factory=get_owners, get_label='last_name_first_name', default=current_user)

    def __init__(self, *args, **kwargs):
        """Create instance."""
        super(CreateAnomalyForm, self).__init__(*args, **kwargs)
        settings = Settings.get_settings()
        if settings:
            self.owner.get_label = operator.attrgetter(settings.name_order)

    def validate(self):
        initial_validation = super(CreateAnomalyForm, self).validate()
        errors = False

        if not initial_validation:
            errors = True

        if self.affected.data == 'design':
            if not self.designs.data and not self.vendor_parts.data:
                self.designs.errors.append("You must add at least one design, vendor part, as-run, or choose 'Other'")
                self.as_runs.errors.append("You must add at least one design, vendor part, as-run, or choose 'Other'")
                errors = True
        elif self.affected.data == 'asrun':
            if not self.as_runs.data:
                self.designs.errors.append("You must add at least one design, as-run, or choose 'Other'")
                self.as_runs.errors.append("You must add at least one design, vendor part, as-run, or choose 'Other'")
                errors = True

        if errors:
            return False

        return True
