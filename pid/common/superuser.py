# -*- coding: utf-8 -*-
"""Flask Admin superuser."""
from flask_admin.contrib.sqla import ModelView
from flask import redirect, request, url_for
from .models import (Company, Criticality, Disposition, HardwareType,
                     Material, MaterialSpecification, Project)
import flask_login as login


class CommonManagementSuperuser(ModelView):
    """Base Model for common management."""

    def is_accessible(self):
        """Need to make sure user is a superuser to allow common management."""
        if login.current_user.is_authenticated:
            return login.current_user.is_admin_or_superuser()
        return False

    def inaccessible_callback(self, name, **kwargs):
        """What to do if user is not allowed to manage."""
        return redirect(url_for('public.home', next=request.url))


class CommonSuperuser(CommonManagementSuperuser):
    """Common superuser."""
    create_modal = True
    edit_modal = True
    details_modal = True
    can_export = True
    can_delete = False
    pass


class CompanyView(CommonSuperuser):
    column_editable_list = ['name', 'website', 'address', 'notes']
    list_template = 'admin/list_with_csrf_token.html'
    pass


class CriticalityView(CommonSuperuser):
    column_editable_list = ['name', 'description', 'ordering']
    list_template = 'admin/superuser_list_with_reorder_column.html'
    pass


class DispositionView(CommonSuperuser):
    column_editable_list = ['name', 'description', 'ordering']
    list_template = 'admin/superuser_list_with_reorder_column.html'
    pass


class HardwareTypeView(CommonSuperuser):
    column_editable_list = ['name', 'description', 'ordering']
    list_template = 'admin/superuser_list_with_reorder_column.html'
    pass


class MaterialView(CommonSuperuser):
    column_editable_list = ['name', 'description']
    column_auto_select_related = True
    # TODO: Figure out how to prevent deletion of MaterialSpecifications for superusers
    inline_models = (MaterialSpecification,)
    list_template = 'admin/list_with_csrf_token.html'
    pass


class ProjectView(CommonSuperuser):
    column_editable_list = ['name', 'description']
    list_template = 'admin/list_with_csrf_token.html'
    pass


def add_views(superuser, db):
    """Add common superuser views into views."""
    superuser.add_view(CompanyView(Company, db.session, endpoint='superuser_companies', url='companies'))
    superuser.add_view(CriticalityView(Criticality, db.session, endpoint='superuser_criticalities', url='criticalities'))
    superuser.add_view(DispositionView(Disposition, db.session, endpoint='superuser_dispositions', url='dispositions'))
    superuser.add_view(HardwareTypeView(HardwareType, db.session, endpoint='superuser_hardwaretypes', url='hardwaretypes'))
    superuser.add_view(MaterialView(Material, db.session, endpoint='superuser_materials', url='materials'))
    superuser.add_view(ProjectView(Project, db.session, endpoint='superuser_projects', url='projects'))
    pass
