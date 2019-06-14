# -*- coding: utf-8 -*-
"""Build and Product forms."""
from flask_wtf import FlaskForm
from flask_login import current_user
from wtforms import StringField, RadioField, HiddenField
from wtforms.ext.sqlalchemy.fields import QuerySelectField
from wtforms.validators import DataRequired, Optional
from pid.common.models import Company, HardwareType, Project
from pid.vendorproduct.models import VendorProduct
from pid.user.models import User
from pid.vendorpart.models import VendorPart
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


class CreateVendorBuildForm(FlaskForm):
    product_type = RadioField('Product Type', choices=[('s/n', 'S/N record(s)'), ('lot', 'LOT record'), ('stock', 'STOCK record')], default='s/n')
    build_identifier = StringField('', validators=[Optional()])
    existing_build_id = HiddenField()
    serial_numbers = StringField('', validators=[Optional()])
    lot_record = StringField('', validators=[Optional()])
    hardware_type = QuerySelectField('Hardware Type', query_factory=get_hardware_types, get_label='name', validators=[DataRequired()])
    project = QuerySelectField('Project', query_factory=get_projects, get_label='name', validators=[DataRequired()])
    vendor = QuerySelectField('Vendor', query_factory=get_vendors, get_label='name', validators=[Optional()])
    manufacturer = QuerySelectField('Distributor', query_factory=get_vendors, get_label='name', validators=[DataRequired()])
    # TODO: Revision
    owner = QuerySelectField('Owner', query_factory=get_users, get_label='last_name_first_name', default=current_user)
    vendor_part_id = HiddenField('')

    def __init__(self, *args, **kwargs):
        """Create instance."""
        super(CreateVendorBuildForm, self).__init__(*args, **kwargs)
        settings = Settings.get_settings()
        if settings:
            self.owner.get_label = operator.attrgetter(settings.name_order)

    def validate(self):
        """Validate the form."""
        initial_validation = super(CreateVendorBuildForm, self).validate()
        errors = False
        data = {}
        if not initial_validation:
            errors = True

        vendor_part = VendorPart.get_by_id(self.vendor_part_id.data)
        existing_serial_numbers = VendorProduct.get_serial_numbers_for_vendor_part(vendor_part)

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
                    for sn in serial_numbers_array:
                        if sn in existing_serial_numbers:
                            self.serial_numbers.errors.append('S/N {0} already exists'.format(sn))
                            errors = True
                        else:
                            return_serial_numbers.append(sn)
                # Only one S/N present most likely, just append it
                else:
                    if serial_numbers in existing_serial_numbers:
                        self.serial_numbers.errors.append('S/N {0} already exists'.format(serial_numbers))
                        errors = True
                    else:
                        return_serial_numbers.append(serial_numbers)
            data['serial_numbers'] = return_serial_numbers
        elif self.product_type.data == 'lot':
            return_lot_record = None
            lot_record = self.lot_record.data.strip()
            if len(lot_record) == 0:
                self.lot_record.errors.append('No LOT record entered')
                errors = True
            else:
                return_lot_record = lot_record
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
