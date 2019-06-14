# -*- coding: utf-8 -*-
"""Task models."""
from flask import url_for
from flask_login import current_user
import datetime as dt
from pid.database import Column, Model, SurrogatePK, db, reference_col, relationship
from pid.common.models import Reference, ChangeLog
from pid.permissions import TaskPermissions
from pid.models import ChangeLogMixin, ThumbnailMixin


def get_next_task_number():
    seq = db.Sequence('task_number_seq')
    key = "T-{0}".format(str(db.session.connection().execute(seq)).zfill(6))
    return key


class Task(ThumbnailMixin, ChangeLogMixin, SurrogatePK, Model):
    __tablename__ = 'tasks'
    descriptor = 'Task'
    task_number = Column(db.String, default=get_next_task_number, nullable=False)
    title = Column(db.String)
    summary = Column(db.String)
    urgency_states = ["At Your Leisure", "Important", "Urgent", "SoF"]
    urgency = Column(db.String, default='At Your Leisure')
    allowed_states = ['Requested', 'Acknowledged', 'In Work', 'Complete', 'Rejected']
    state = Column(db.String, default='Requested')
    documents = relationship('Document', secondary='tasks_documents')
    links = relationship('Link', secondary='tasks_links')
    images = relationship('Image', secondary='tasks_images')
    assigned_to_id = reference_col('users', nullable=False)
    assigned_to = relationship('User', foreign_keys=[assigned_to_id])
    requested_by_id = reference_col('users', nullable=False)
    requested_by = relationship('User', foreign_keys=[requested_by_id])
    requested_on = Column(db.DateTime, nullable=False, default=dt.datetime.utcnow)
    need_date = Column(db.DateTime, nullable=False, default=dt.datetime.utcnow)
    permissions = TaskPermissions()

    def __init__(self, requested_by, **kwargs):
        ChangeLogMixin.__init__(self)
        db.Model.__init__(self, requested_by=requested_by, **kwargs)

    @property
    def references_to(self):
        results = Reference.query.filter_by(by_id=self.id, by_class=self.get_class_name()).all()
        return results

    @classmethod
    def get_by_task_number(cls, task_number):
        return cls.query.filter_by(task_number=task_number).first()

    @classmethod
    def find_all_tasks_for_user(cls, user, type):
        if type == 'assigned':
            results = cls.query.filter_by(assigned_to=user).order_by(cls.need_date).all()
        else:
            results = cls.query.filter_by(requested_by=user).order_by(cls.need_date).all()
        return results

    def can_user_edit(self, field_name):
        if current_user.is_admin():
            return True  # Admins can do anything always
        role = 'all'
        if current_user == self.assigned_to or current_user == self.requested_by:
            role = 'owner'
        elif current_user.is_superuser():
            role = 'superuser'
        state = 'open'
        return self.permissions.get_permissions().get(state, False).get(role, False).get(field_name)

    def get_name(self):
        return self.title

    def get_unique_identifier(self):
        return '{0}'.format(self.task_number)

    def get_url(self, external=False):
        return url_for('task.view_task', task_number=self.task_number, _external=external)

    def get_descriptive_url(self):
        return '<a href="{0}">{1} - {2}</a>'.format(self.get_url(), self.get_unique_identifier(), self.get_name())

    def __str__(self):
        return str(self.id)

    def __repr__(self):
        return '<Task({0})>'.format(self.id)


tasks_documents = db.Table('tasks_documents',
    Column('task_id', db.BigInteger, db.ForeignKey('tasks.id'), primary_key=True),
    Column('document_id', db.BigInteger, db.ForeignKey('documents.id'), primary_key=True)
)

tasks_images = db.Table('tasks_images',
    Column('task_id', db.BigInteger, db.ForeignKey('tasks.id'), primary_key=True),
    Column('image_id', db.BigInteger, db.ForeignKey('images.id'), primary_key=True)
)

tasks_links = db.Table('tasks_links',
    Column('task_id', db.BigInteger, db.ForeignKey('tasks.id'), primary_key=True),
    Column('link_id', db.BigInteger, db.ForeignKey('links.id'), primary_key=True)
)
