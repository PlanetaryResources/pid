# -*- coding: utf-8 -*-
"""Flask Admin admins."""
from flask_admin.contrib.sqla import ModelView
from flask import redirect, request, url_for
from .models import ECO
import flask_login as login


class ECOManagementAdmin(ModelView):
    """Base Model for eco management."""

    def is_accessible(self):
        """Need to make sure user is an admin to allow anomaly management."""
        if login.current_user.is_authenticated:
            return login.current_user.is_admin()
        return False

    def inaccessible_callback(self, name, **kwargs):
        """What to do if user is not allowed to user manage."""
        return redirect(url_for('public.home', next=request.url))


class ECOAdmin(ECOManagementAdmin):
    """ECO admin."""
    create_modal = True
    edit_modal = True
    can_export = True
    pass


def add_views(admin, db):
    """Add user admin views into views."""
    admin.add_view(ECOAdmin(ECO, db.session, endpoint='admin_ecos',
                            url='ecos'))
    pass
