# -*- coding: utf-8 -*-
"""VendorPart forms."""
import operator
from flask_login import current_user
from flask_wtf import FlaskForm
from wtforms import StringField
from wtforms.ext.sqlalchemy.fields import QuerySelectField
from wtforms.validators import DataRequired
from pid.backend.models import Settings
from pid.common.models import Project, Company
from pid.user.models import User
from .models import VendorPart


# Helpers for query_factories in forms
def get_projects():
    return Project.query.all()


def get_owners():
    return User.query.all()


def get_vendors():
    return Company.get_all_with_pri_on_top()


class CreateVendorPartForm(FlaskForm):
    part_number = StringField('Part Number', validators=[DataRequired('A part number is required.')])
    name = StringField('Name/Description', validators=[DataRequired('A name/description is required')])
    vendor = QuerySelectField(query_factory=get_vendors, get_label='name', allow_blank=True,
                              blank_text='--- Select vendor ---', validators=[DataRequired('A vendor is required.')])
    project = QuerySelectField(query_factory=get_projects, get_label='name', allow_blank=True,
                               blank_text='--- Select project ---', validators=[DataRequired()])
    owner = QuerySelectField(query_factory=get_owners, get_label='last_name_first_name', default=current_user)

    def __init__(self, *args, **kwargs):
        """Create instance."""
        super(CreateVendorPartForm, self).__init__(*args, **kwargs)
        settings = Settings.get_settings()
        if settings:
            self.owner.get_label = operator.attrgetter(settings.name_order)

    def validate(self):
        """Validate the form."""
        initial_validation = super(CreateVendorPartForm, self).validate()
        errors = False

        if not initial_validation:
            errors = True

        vendor_part = VendorPart.get_by_part_number(self.part_number.data)

        if self.part_number.data and vendor_part:
            self.part_number.errors.append('Vendor Part number already exists.')
            errors = True

        if errors:
            return False

        return True
