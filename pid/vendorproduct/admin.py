# -*- coding: utf-8 -*-
from flask_admin.contrib.sqla import ModelView
from flask import redirect, request, url_for
from .models import VendorBuild, VendorProduct
import flask_login as login


class BaseManagementAdmin(ModelView):

    def is_accessible(self):
        """Need to make sure user is an admin to allow management."""
        if login.current_user.is_authenticated:
            return login.current_user.is_admin()
        return False

    def inaccessible_callback(self, name, **kwargs):
        """What to do if user is not allowed."""
        return redirect(url_for('public.home', next=request.url))


class VendorBuildAdmin(BaseManagementAdmin):
    """Build admin."""
    create_modal = True
    edit_modal = True
    can_export = True
    column_list = ['id', 'vendor_part', 'build_number', 'owner', 'vendor', 'manufacturer']
    column_sortable_list = ['id', 'vendor_part', 'build_number', 'owner', 'vendor', 'manufacturer']
    column_default_sort = 'vendor_part.part_number'
    pass


class VendorProductAdmin(BaseManagementAdmin):
    """Product admin."""
    create_modal = True
    edit_modal = True
    can_export = True
    column_list = ['id', 'vendor_part', 'product_number', 'summary', 'owner']
    column_sortable_list = ['id', 'vendor_part', 'product_number', 'summary', 'owner']
    column_default_sort = 'vendor_part.part_number'
    pass


def add_views(admin, db):
    """Add admin views into views."""
    admin.add_view(VendorBuildAdmin(VendorBuild, db.session, endpoint='admin_vendor_builds', url='vendor_builds'))
    admin.add_view(VendorProductAdmin(VendorProduct, db.session, endpoint='admin_vendor_products', url='vendor_products'))
    pass
