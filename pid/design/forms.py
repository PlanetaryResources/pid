# -*- coding: utf-8 -*-
"""Design forms."""
import operator
import string

from flask import flash, current_app
from flask_login import current_user
from flask_wtf import FlaskForm
from wtforms import StringField, IntegerField, RadioField, HiddenField
from wtforms.ext.sqlalchemy.fields import QuerySelectField
from wtforms.validators import DataRequired, Optional, ValidationError

from pid.backend.models import Settings
from pid.common.models import Project
from pid.globals import FORBIDDEN_REVISIONS
from pid.user.models import User
from .models import Design


# Helpers for query_factories in forms
def get_projects():
    return Project.query.all()


def get_owners():
    return User.query.all()


# From: https://stackoverflow.com/questions/16974047/efficient-way-to-find-missing-elements-in-an-integer-sequence
def missing_elements(L):
    start, end = L[0], L[-1]
    return sorted(set(range(start, end + 1)).difference(L))


class CreateDesignForm(FlaskForm):
    amount = StringField('Amount', validators=[DataRequired()], default='1')
    design_number_type = RadioField('Design Numbers', choices=[('lowest', 'Lowest unused numbers'),
                                                               ('range', 'Starting from:')], default='lowest')
    design_number = IntegerField('', validators=[Optional()])
    name = StringField('Name', validators=[DataRequired()])
    project = QuerySelectField(query_factory=get_projects, get_label='name', allow_blank=True,
                               blank_text='--- Select project ---', validators=[DataRequired()])
    revision = StringField('Revision', validators=[DataRequired()], default='A')
    owner = QuerySelectField(query_factory=get_owners, get_label='last_name_first_name', default=current_user)

    def __init__(self, *args, **kwargs):
        """Create instance."""
        super(CreateDesignForm, self).__init__(*args, **kwargs)
        settings = Settings.get_settings()
        if settings:
            self.owner.get_label = operator.attrgetter(settings.name_order)

    def validate_amount(self, field):
        # Check whether amount has anything besides a number in it
        if not field.data.isdigit():
            raise ValidationError('Amount must be a positive number.')
        # Check that amount is positive
        if int(field.data) <= 0:
            raise ValidationError('Amount must be 1 or more.')

    def validate_revision(self, field):
        revision = field.data.upper()
        if len(revision) > 3:
            field.errors.append('Revision can be maximum 3 letters.')
        if not all(c in string.ascii_uppercase for c in revision):
            field.errors.append('Revision can only contain letters.')
        if any(c in FORBIDDEN_REVISIONS for c in revision):
            field.errors.append('Revision can\'t contain any of: {0}.'.format(', '.join(FORBIDDEN_REVISIONS)))
        pass

    def validate(self):
        """Validate the form."""
        # TODO: Wish there was a better way than returning a tuple here, but then would need to grab
        #       from database again, and do all the calculation for design_numbers again in views.py
        initial_validation = super(CreateDesignForm, self).validate()
        errors = False
        if not initial_validation:
            errors = True

        if not self.amount.data or not self.amount.data.isdigit():
            amount = 0
        else:
            amount = int(self.amount.data)

        # Design numbers must be 7 digits long. They start on 1000000 and can go to 1999999
        design_numbers = []
        # For validating range data and verifying range is free
        if self.design_number_type.data == 'range':
            # First validate input
            if not self.design_number.data:
                self.design_number.errors.append('Required')
                return False, None
            elif len(str(self.design_number.data)) != 7:
                self.design_number.errors.append('Design numbers must be 7 digits long.')
                return False, None
            # Check if the desired number range is free
            design_number_start = self.design_number.data
            design_number_end = design_number_start + amount
            design_numbers = [i for i in range(design_number_start, design_number_end)]
            all_design_numbers = Design.find_all_design_numbers()
            clashing_numbers = list(set(design_numbers).intersection(all_design_numbers))
            if clashing_numbers:
                # Format the clashes a little bit prettier
                clashing_numbers = [str(x) for x in clashing_numbers]
                clashing_numbers = ', '.join(clashing_numbers)
                self.design_number.errors.append('The following design numbers clash: {0}.'.format(clashing_numbers))
                return False, None

        # The following portion is for finding the lowest free design numbers
        if self.design_number_type.data == 'lowest':
            all_design_numbers = Design.find_all_design_numbers()
            # TODO: Make these ranges configurable in GUI (lowest and highest design number)
            all_design_numbers.insert(0, 1999999)  # lower
            all_design_numbers.append(9999999)  # upper
            missing_design_numbers = missing_elements(all_design_numbers)
            try:
                for i in range(0, amount):
                    design_numbers.append(missing_design_numbers[i])
            except IndexError as error:
                # TODO: Make this check better in general
                current_app.logger.error(error)
                flash('WTF, we\'ve run out of design numbers! How is that even possible!', 'danger')
                return False, None

        if errors:
            return False, None

        # TODO: Do we need to worry about revisions in regards to design_numbers from this form?
        return True, design_numbers


class ReviseDesignForm(FlaskForm):
    design_id = HiddenField('')
    revision = StringField('New Revision', validators=[DataRequired()])
    revision_reason = StringField('Reason for Revision',
                                  validators=[DataRequired('A reason for revision is required.')])
    owner = QuerySelectField('New Owner', query_factory=get_owners, get_label='last_name_first_name')

    def __init__(self, *args, **kwargs):
        """Create instance."""
        super(ReviseDesignForm, self).__init__(*args, **kwargs)
        settings = Settings.get_settings()
        if settings:
            self.owner.get_label = operator.attrgetter(settings.name_order)

    def validate_revision(self, field):
        revision = field.data.upper()
        if len(revision) > 3:
            field.errors.append('Revision can be maximum 3 letters.')
        if not all(c in string.ascii_uppercase for c in revision):
            field.errors.append('Revision can only contain letters.')
        if any(c in FORBIDDEN_REVISIONS for c in revision):
            field.errors.append('Revision can\'t contain any of: {0}.'.format(', '.join(FORBIDDEN_REVISIONS)))
        pass

    def validate(self):
        initial_validation = super(ReviseDesignForm, self).validate()
        errors = False
        if not initial_validation:
            errors = True
        if errors:
            return False
        return True
