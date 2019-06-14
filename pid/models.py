# -*- coding: utf-8 -*-
"""Base models, most classes will inherit from some of these."""

import datetime
from flask import url_for
from flask_login import current_user
from sqlalchemy.ext.declarative import declared_attr
from sqlalchemy.orm import validates
from pid.common.models import Approver, ChangeLog, RevisionLog, WorkflowLog, Reference
from pid.database import Model, SurrogatePK, Column, db, reference_col, relationship


class ThumbnailMixin(object):

    @declared_attr
    def thumbnail_id(cls):
        return reference_col('images', nullable=True)

    @declared_attr
    def thumbnail(cls):
        return relationship('Image')

    def get_thumbnail_url(self):
        if self.thumbnail:
            return self.thumbnail.get_url()
        return None


class ChangeLogMixin(object):

    @declared_attr
    def change_log_id(cls):
        return reference_col('change_logs')

    @declared_attr
    def change_log(cls):
        return relationship('ChangeLog')

    def __init__(self):
        self.change_log = ChangeLog.create()  # Creates first entry in __init__

    def add_change_log_entry(self, changed_by=current_user, **kwargs):
        self.change_log.add_entry(changed_by=changed_by, **kwargs)


class RevisionLogMixin(object):
    __abstract__ = True

    revision = Column(db.String, nullable=False, default='A')

    @declared_attr
    def revision_log_id(cls):
        return reference_col('revision_logs')

    @declared_attr
    def revision_log(cls):
        return relationship('RevisionLog')

    @validates('revision')
    def convert_upper(self, key, value):
        return value.upper()

    def __init__(self):
        self.revision_log = RevisionLog.create()
        revision = self.revision if self.revision else 'A'
        self.revision_log.add_entry(revision=revision, reason='Initial Release', revisioned_by=current_user)

    def add_revision_log_entry(self, changed_by=current_user, **kwargs):
        self.revision.add_entry(changed_by=changed_by, **kwargs)

    def get_latest_revision_unique_identifier(self):
        raise NotImplementedError

    def get_latest_revision_url(self):
        raise NotImplementedError


class WorkflowLogMixin(object):
    __abstract__ = True

    self_approved = Column(db.Boolean(), default=False)

    @declared_attr
    def workflow_log_id(cls):
        return reference_col('workflow_logs')

    @declared_attr
    def workflow_log(cls):
        return relationship('WorkflowLog')

    def __init__(self):
        self.workflow_log = WorkflowLog.create()  # Creates first entry in WorkflowLog __init__
        if current_user.padawan:
            approver = Approver.create(approver_id=current_user.supervisor_id, capacity='Supervisor')
            self.approvers.append(approver)

    def add_workflow_log_entry(self, changed_by=current_user, **kwargs):
        self.workflow_log.add_entry(changed_by=changed_by, **kwargs)

    def is_open(self):
        return True if self.state in self.workflow.open_states else False

    def get_approvers(self):
        approvers = []
        for approver in self.approvers:
            if not approver.approved_at:
                approvers.append(approver.approver)
        return approvers

    def get_approval_errors(self):
        raise NotImplementedError


class BaseRecord(ChangeLogMixin, SurrogatePK, Model):
    __abstract__ = True

    created_at = Column(db.DateTime, nullable=False, default=datetime.datetime.utcnow)

    @declared_attr
    def owner_id(cls):
        return reference_col('users')

    @declared_attr
    def owner(cls):
        return relationship('User', foreign_keys=cls.owner_id)

    @declared_attr
    def created_by_id(cls):
        return reference_col('users')

    @declared_attr
    def created_by(cls):
        return relationship('User', foreign_keys=cls.created_by_id)

    @classmethod
    def advanced_search(cls, params):
        raise NotImplementedError

    def __init__(self):
        ChangeLogMixin.__init__(self)
        self.created_by = current_user

    def can_user_edit(self, field_name):
        if current_user.is_admin():
            return True  # Admins can do anything always
        role = 'all'
        if current_user == self.owner:
            role = 'owner'
        elif current_user.is_superuser():
            role = 'superuser'
        state = 'closed'
        if self.is_open():
            state = 'open'
        elif self.state == self.workflow.released_state:
            state = 'released'
        return self.permissions.get_permissions().get(state, False).get(role, False).get(field_name)

    def get_unique_identifier(self):
        raise NotImplementedError

    def get_name(self):
        return self.name

    def get_url(self):
        raise NotImplementedError

    def get_descriptive_url(self):
        return '<a href="{0}">{1} - {2}</a>'.format(self.get_url(), self.get_unique_identifier(), self.get_name())


class NamelessRecord(ThumbnailMixin, WorkflowLogMixin, BaseRecord):
    __abstract__ = True

    @property
    def references_by(self):
        query_results = Reference.query.filter_by(to_id=self.id, to_class=self.get_class_name()).all()
        results = {r.get_url_by(): r for r in query_results}.values()
        return results

    @property
    def references_to(self):
        results = Reference.query.filter_by(by_id=self.id, by_class=self.get_class_name()).all()
        return results

    def __init__(self):
        BaseRecord.__init__(self)
        WorkflowLogMixin.__init__(self)


class Record(NamelessRecord):
    __abstract__ = True

    name = Column(db.String, nullable=False)

    def __init__(self):
        NamelessRecord.__init__(self)


class RevisionRecord(RevisionLogMixin, Record):
    __abstract__ = True

    def __init__(self):
        RevisionLogMixin.__init__(self)
        Record.__init__(self)
