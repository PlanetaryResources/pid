# -*- coding: utf-8 -*-
"""Flask Admin admins."""
from flask_admin.contrib.sqla import ModelView
from flask import redirect, request, url_for
from .models import Document, Image, Link
import flask_login as login


class APIManagementAdmin(ModelView):
    """Base Model for design management."""

    def is_accessible(self):
        """Need to make sure user is an admin to allow user management."""
        if login.current_user.is_authenticated:
            return login.current_user.is_admin()
        return False

    def inaccessible_callback(self, name, **kwargs):
        """What to do if user is not allowed to user manage."""
        return redirect(url_for('public.home', next=request.url))


class APIAdmin(APIManagementAdmin):
    """Design admin."""
    create_modal = True
    edit_modal = True
    can_export = True
    pass


def add_views(admin, db):
    """Add user admin views into views."""
    admin.add_view(APIAdmin(Document, db.session, endpoint='admin_documents', url='documents'))
    admin.add_view(APIAdmin(Image, db.session, endpoint='admin_images', url='images'))
    admin.add_view(APIAdmin(Link, db.session, endpoint='admin_links', url='links'))
    pass
