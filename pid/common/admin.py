# -*- coding: utf-8 -*-
"""Flask Admin admins."""
from flask_admin.contrib.sqla import ModelView
from flask import redirect, request, url_for
from .models import (Company, Criticality, Disposition, HardwareType,
                     Material, MaterialSpecification, Project)
import flask_login as login


class CommonManagementAdmin(ModelView):
    """Base Model for user management."""

    def is_accessible(self):
        """Need to make sure user is an admin to allow user management."""
        if login.current_user.is_authenticated:
            return login.current_user.is_admin()
        return False

    def inaccessible_callback(self, name, **kwargs):
        """What to do if user is not allowed to user manage."""
        return redirect(url_for('public.home', next=request.url))


class CommonAdmin(CommonManagementAdmin):
    """Common admin."""
    create_modal = True
    edit_modal = True
    can_export = True
    pass


class CompanyView(CommonAdmin):
    column_editable_list = ['name', 'website', 'address', 'notes']
    list_template = 'admin/list_with_csrf_token.html'
    pass


class CriticalityView(CommonAdmin):
    column_editable_list = ['name', 'description', 'ordering']
    # See: https://github.com/flask-admin/flask-admin/issues/998
    list_template = 'admin/admin_list_with_reorder_column.html'
    pass


class DispositionView(CommonAdmin):
    column_editable_list = ['name', 'description', 'ordering']
    list_template = 'admin/admin_list_with_reorder_column.html'
    pass


class HardwareTypeView(CommonAdmin):
    column_editable_list = ['name', 'description', 'ordering']
    list_template = 'admin/admin_list_with_reorder_column.html'
    pass


class MaterialView(CommonAdmin):
    column_editable_list = ['name', 'description']
    column_auto_select_related = True
    inline_models = (MaterialSpecification,)
    list_template = 'admin/list_with_csrf_token.html'


class ProjectView(CommonAdmin):
    column_editable_list = ['name', 'description']
    list_template = 'admin/list_with_csrf_token.html'
    pass


def add_views(admin, db):
    """Add common admin views into views."""
    admin.add_view(CompanyView(Company, db.session, endpoint='admin_companies', url='companies'))
    admin.add_view(CriticalityView(Criticality, db.session, endpoint='admin_criticalities', url='criticalities'))
    admin.add_view(DispositionView(Disposition, db.session, endpoint='admin_dispositions', url='dispositions'))
    admin.add_view(HardwareTypeView(HardwareType, db.session, endpoint='admin_hardwaretypes', url='hardwaretypes'))
    admin.add_view(MaterialView(Material, db.session, endpoint='admin_materials', url='materials'))
    admin.add_view(ProjectView(Project, db.session, endpoint='admin_projects', url='projects'))
    pass
