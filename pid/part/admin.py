# -*- coding: utf-8 -*-
"""Flask Admin admins."""
from flask_admin.contrib.sqla import ModelView
from flask import redirect, request, url_for
from .models import Part, PartComponent
import flask_login as login


class PartManagementAdmin(ModelView):
    """Base Model for design management."""

    def is_accessible(self):
        """Need to make sure user is an admin to allow user management."""
        if login.current_user.is_authenticated:
            return login.current_user.is_admin()
        return False

    def inaccessible_callback(self, name, **kwargs):
        """What to do if user is not allowed to user manage."""
        return redirect(url_for('public.home', next=request.url))


class PartAdmin(PartManagementAdmin):
    """Part admin."""
    create_modal = True
    edit_modal = True
    can_export = True
    column_list = ['id', 'design', 'part_identifier', 'components', 'current_best_estimate', 'uncertainty', 'predicted_best_estimate']
    column_sortable_list = column_list
    column_default_sort = 'design.design_number'
    pass


class PartComponentAdmin(PartManagementAdmin):
    """Part admin."""
    create_modal = True
    edit_modal = True
    can_export = True
    column_list = ['id', 'parent', 'part', 'vendor_part', 'quantity', 'ordering']
    column_sortable_list = column_list
    column_default_sort = 'parent.design.design_number'
    pass


def add_views(admin, db):
    """Add user admin views into views."""
    admin.add_view(PartAdmin(Part, db.session, endpoint='admin_parts', url='parts'))
    admin.add_view(PartComponentAdmin(PartComponent, db.session, endpoint='admin_part_components', url='part_components'))
    pass
