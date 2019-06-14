# -*- coding: utf-8 -*-
from flask_admin.contrib.sqla import ModelView
from flask import redirect, request, url_for
from .models import Build, Product, ProductComponent
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


class BuildAdmin(BaseManagementAdmin):
    """Build admin."""
    create_modal = True
    edit_modal = True
    can_export = True
    column_list = ['id', 'part', 'build_number', 'owner', 'vendor']
    column_sortable_list = ['id', 'part', 'build_number', 'owner', 'vendor']
    column_default_sort = 'part.design.design_number'
    pass


class ProductAdmin(BaseManagementAdmin):
    """Product admin."""
    create_modal = True
    edit_modal = True
    can_export = True
    column_list = ['id', 'part', 'product_number', 'revision', 'summary', 'owner']
    column_sortable_list = ['id', 'part', 'product_number', 'revision', 'summary', 'owner']
    column_default_sort = 'part.design.design_number'
    pass


class ProductComponentAdmin(BaseManagementAdmin):
    create_modal = True
    edit_modal = True
    can_export = True
    pass


def add_views(admin, db):
    """Add admin views into views."""
    admin.add_view(BuildAdmin(Build, db.session, endpoint='admin_builds', url='builds'))
    admin.add_view(ProductAdmin(Product, db.session, endpoint='admin_products', url='products'))
    admin.add_view(ProductComponentAdmin(ProductComponent, db.session, endpoint='admin_product_components', url='product_components'))
    pass
