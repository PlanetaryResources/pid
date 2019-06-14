# -*- coding: utf-8 -*-
"""Build and Product forms."""
from flask_wtf import FlaskForm
from flask_login import current_user
from wtforms import StringField, RadioField, HiddenField, IntegerField
from wtforms.ext.sqlalchemy.fields import QuerySelectField
from wtforms.validators import DataRequired, Optional
from pid.common.models import Company, HardwareType, Project
from pid.part.models import Part
from pid.product.models import Product
from pid.user.models import User
from pid.backend.models import Settings
import operator


# Helpers for query_factories in forms
def get_hardware_types():
    return HardwareType.query.all()


def get_projects():
    return Project.query.all()


def get_vendors():
    return Company.get_all_with_pri_on_top()


def get_users():
    return User.query.all()


class CreateBuildForm(FlaskForm):
    product_type = RadioField('Product Type', choices=[('s/n', 'S/N record(s)'), ('lot', 'LOT record'), ('stock', 'STOCK record')], default='s/n')
    build_identifier = StringField('', validators=[Optional()])
    existing_build_id = HiddenField()
    serial_numbers = StringField('', validators=[Optional()])
    lot_record = StringField('', validators=[Optional()])
    hardware_type = QuerySelectField('Hardware Type', query_factory=get_hardware_types, get_label='name', validators=[DataRequired()])
    project = QuerySelectField('Project', query_factory=get_projects, get_label='name', validators=[DataRequired()])
    vendor = QuerySelectField('Vendor', query_factory=get_vendors, get_label='name', validators=[DataRequired()])
    # TODO: Revision
    owner = QuerySelectField('Owner', query_factory=get_users, get_label='last_name_first_name', default=current_user)
    part_id = HiddenField('')

    def __init__(self, *args, **kwargs):
        """Create instance."""
        super(CreateBuildForm, self).__init__(*args, **kwargs)
        settings = Settings.get_settings()
        if settings:
            self.owner.get_label = operator.attrgetter(settings.name_order)

    def validate(self):
        """Validate the form."""
        initial_validation = super(CreateBuildForm, self).validate()
        errors = False
        data = {}
        if not initial_validation:
            errors = True

        part = Part.get_by_id(self.part_id.data)
        existing_serial_numbers = Product.get_serial_numbers_for_design_number_and_part_identifier(part.design.design_number, part.part_identifier)

        if self.product_type.data == 's/n':
            # TODO: Try to move some of this to an external function, very messy now
            return_serial_numbers = []
            # TODO: Improve these replaces
            serial_numbers = self.serial_numbers.data.strip().replace(' , ', ',').replace(', ', ',').replace(' ,', ',').replace(' ', ',')  # In case user uses space instead of comma
            if len(serial_numbers) == 0:
                self.serial_numbers.errors.append('No S/N(s) entered')
                errors = True
            else:
                # First check for comma separated serial_numbers
                if ',' in serial_numbers:
                    serial_numbers_array = serial_numbers.split(',')
                    # In these, check for ranges and validate and append
                    for sn in serial_numbers_array:
                        if '-' in sn:
                            serial_numbers_range_low = sn.split('-')[0]
                            serial_numbers_range_high = sn.split('-')[1]
                            validated_low = self.validate_serial_number(serial_numbers_range_low)
                            validated_high = self.validate_serial_number(serial_numbers_range_high)
                            if validated_low and validated_high:
                                for i in range(int(validated_low), int(validated_high) + 1):
                                    validated_sn = self.validate_serial_number(i)
                                    if validated_sn in existing_serial_numbers:
                                        self.serial_numbers.errors.append('S/N {0} already exists'.format(validated_sn))
                                        errors = True
                                    else:
                                        return_serial_numbers.append(validated_sn)
                            else:
                                self.serial_numbers.errors.append('Invalid S/N(s) entered')
                                errors = True
                        # If not range, append the validated values
                        else:
                            validated_sn = self.validate_serial_number(sn)
                            if validated_sn:
                                if validated_sn in existing_serial_numbers:
                                    self.serial_numbers.errors.append('S/N {0} already exists'.format(validated_sn))
                                    errors = True
                                else:
                                    return_serial_numbers.append(validated_sn)
                            else:
                                self.serial_numbers.errors.append('Invalid S/N(s) entered')
                                errors = True
                # Only range present
                elif '-' in serial_numbers:
                    serial_numbers_range_low = serial_numbers.split('-')[0]
                    serial_numbers_range_high = serial_numbers.split('-')[1]
                    validated_low = self.validate_serial_number(serial_numbers_range_low)
                    validated_high = self.validate_serial_number(serial_numbers_range_high)
                    if validated_low and validated_high:
                        for i in range(int(validated_low), int(validated_high) + 1):
                            validated_sn = self.validate_serial_number(i)
                            if validated_sn in existing_serial_numbers:
                                self.serial_numbers.errors.append('S/N {0} already exists'.format(validated_sn))
                                errors = True
                            else:
                                return_serial_numbers.append(validated_sn)
                    else:
                        self.serial_numbers.errors.append('Invalid S/N(s) entered')
                        errors = True
                    pass
                # Only one S/N present most likely, just append it after validating
                else:
                    validated_sn = self.validate_serial_number(serial_numbers)
                    if validated_sn:
                        if validated_sn in existing_serial_numbers:
                            self.serial_numbers.errors.append('S/N {0} already exists'.format(validated_sn))
                            errors = True
                        else:
                            return_serial_numbers.append(validated_sn)
                    else:
                        self.serial_numbers.errors.append('Invalid S/N(s) entered')
                        errors = True
            data['serial_numbers'] = return_serial_numbers
        elif self.product_type.data == 'lot':
            return_lot_record = None
            lot_record = self.lot_record.data.strip()
            if len(lot_record) == 0:
                self.lot_record.errors.append('No LOT record entered')
                errors = True
            else:
                if lot_record[0] != 'L':
                    # No biggie, just need to append L to beginning of number
                    validated_lot_record = self.validate_serial_number(lot_record)
                    if validated_lot_record:
                        return_lot_record = 'L{0}'.format(validated_lot_record)
                    else:
                        self.lot_record.errors.append('Invalid LOT record entered')
                        errors = True
                else:
                    # Remove 'L' from beginning before validating, then add again.
                    validated_lot_record = self.validate_serial_number(lot_record[1:])
                    if validated_lot_record:
                        return_lot_record = 'L{0}'.format(validated_lot_record)
                    else:
                        self.lot_record.errors.append('Invalid LOT record entered')
                        errors = True
            if lot_record in existing_serial_numbers:
                self.lot_record.errors.append('LOT record {0} already exists'.format(lot_record))
                errors = True
            else:
                data['lot_record'] = return_lot_record
        elif self.product_type.data == 'stock':
            # TODO: Check if STCK already exists
            if 'STCK' in existing_serial_numbers:
                self.product_type.errors.append('STCK already exists')
                errors = True
            else:
                data['is_stock'] = True

        if errors:
            return False, None

        return True, data

    def validate_serial_number(self, serial_number):
        try:
            sn = '{0:03d}'.format(int(serial_number))
            if len(sn) > 3:
                return False
            return sn
        except ValueError:
            # In case unable to parse to number
            return False


class AddExtraProductComponentForm(FlaskForm):
    product_id = HiddenField('')
    part_id = HiddenField('')
    part_group = HiddenField('')
    quantity = IntegerField('', validators=[DataRequired('You must enter a number.')])

    def __init__(self, *args, **kwargs):
        """Create instance."""
        super(AddExtraProductComponentForm, self).__init__(*args, **kwargs)

    def validate(self):
        initial_validation = super(AddExtraProductComponentForm, self).validate()
        errors = False
        if not initial_validation:
            errors = True
        if errors:
            return False
        return True
