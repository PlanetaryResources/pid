# -*- coding: utf-8 -*-
"""Flask Admin admins."""
from flask_admin.contrib.sqla import ModelView
from flask import redirect, request, url_for
from .models import VendorPart
import flask_login as login


class BaseManagementAdmin(ModelView):
    """Base Model for design management."""

    def is_accessible(self):
        """Need to make sure user is an admin to allow user management."""
        if login.current_user.is_authenticated:
            return login.current_user.is_admin()
        return False

    def inaccessible_callback(self, name, **kwargs):
        """What to do if user is not allowed to user manage."""
        return redirect(url_for('public.home', next=request.url))


class VendorPartAdmin(BaseManagementAdmin):
    """VendorPart admin."""
    create_modal = True
    edit_modal = True
    can_export = True
    column_list = ['id', 'part_number', 'name', 'vendor', 'state', 'owner']
    column_sortable_list = column_list
    column_default_sort = 'part_number'
    pass


def add_views(admin, db):
    """Add user admin views into views."""
    admin.add_view(VendorPartAdmin(VendorPart, db.session, endpoint='admin_vendor_parts', url='vendorparts'))
    pass
