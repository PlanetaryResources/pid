# -*- coding: utf-8 -*-
"""Part forms."""
from flask_wtf import FlaskForm
from wtforms import StringField, IntegerField
from wtforms.compat import string_types
from wtforms.validators import DataRequired, StopValidation
from pid.design.models import Design


class CorrectDataRequired(DataRequired):
    '''
    This class allows DataRequired fields to have "0" as a valid input.
    See: https://github.com/wtforms/wtforms/issues/100
    '''
    def __call__(self, form, field):
        if field.data is None or isinstance(field.data, string_types) and not field.data.strip():
            if self.message is None:
                message = field.gettext('This field is required.')
            else:
                message = self.message

            field.errors[:] = []
            raise StopValidation(message)


class CreatePartForm(FlaskForm):
    design_id = StringField('')
    part_identifier = IntegerField('', validators=[CorrectDataRequired('A part identifier is required.')])
    name = StringField('Part Name', validators=[DataRequired('A name is required.')])

    def __init__(self, *args, **kwargs):
        """Create instance."""
        super(CreatePartForm, self).__init__(*args, **kwargs)

    def validate(self):
        initial_validation = super(CreatePartForm, self).validate()
        errors = False

        if not initial_validation:
            errors = True

        design_id = self.design_id.data
        part_identifier = self.part_identifier.data
        design = Design.get_by_id(design_id)
        for part in design.parts:
            if part.part_identifier == part_identifier:
                self.part_identifier.errors.append('This part number ({0}) is already in use. Used the number filled in now instead.'.format(part_identifier))
                errors = True

        if errors:
            return False

        return True
