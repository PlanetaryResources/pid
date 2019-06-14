# -*- coding: utf-8 -*-
"""User models."""
import datetime as dt
from flask_login import UserMixin
from pid.database import Column, Model, SurrogatePK, db, relationship, reference_col
from sqlalchemy.orm import backref


class User(UserMixin, SurrogatePK, Model):
    """A user of the app."""
    __tablename__ = 'users'
    id = db.Column(db.BigInteger, primary_key=True)  # Need to have this for the remote_side association below
    first_name = Column(db.String)
    last_name = Column(db.String)
    username = Column(db.String, unique=True, nullable=False)
    email = Column(db.String, unique=True, nullable=False)
    roles = Column(db.String, nullable=False)
    bookmarks = relationship('Bookmark', back_populates='user', order_by='Bookmark.bookmarked_class')
    saved_searches = relationship('AdvancedSearch', back_populates='user')
    padawan = Column(db.Boolean, default=False)
    supervisor_id = reference_col('users', nullable=True)
    padawans = relationship('User', backref=backref('supervisor', remote_side=[id]))
    last_active = Column(db.DateTime, nullable=True, default=dt.datetime.utcnow)

    __mapper_args__ = {
        "order_by": [last_name, first_name]
    }

    def __init__(self, username='Username', email=None, first_name=None, last_name=None, roles=None, **kwargs):
        """Create instance."""
        db.Model.__init__(self, username=username, email=email, first_name=first_name, last_name=last_name,
                          roles=roles, **kwargs)

    def get_id(self):
        ''' DO NOT REMOVE! Needed for mapping users to username '''
        return self.username

    def is_admin(self):
        return 'plaid-admins' in self.roles

    def is_superuser(self):
        return 'plaid-superusers' in self.roles

    def is_admin_or_superuser(self):
        return 'plaid-superusers' in self.roles or 'plaid-admins' in self.roles

    @property
    def full_name(self):
        return '{0} {1}'.format(self.first_name, self.last_name)

    @property
    def last_name_first_name(self):
        return '{0}, {1}'.format(self.last_name, self.first_name)

    @classmethod
    def get_by_username(cls, username):
        return cls.query.filter_by(username=username).first()

    @classmethod
    def get_online_users(cls):
        # Get all users active within the last 5 minutes
        cutoff = dt.datetime.utcnow() - dt.timedelta(minutes=5)
        results = cls.query.filter(cls.last_active >= cutoff).all()
        return results

    def get_name(self):
        from pid.backend.models import Settings
        settings = Settings.get_settings()
        if not settings:
            return self.last_name_first_name
        if settings.name_order == 'email':
            return self.email
        elif settings.name_order == 'username':
            return self.username
        elif settings.name_order == 'full_name':
            return self.full_name
        else:
            return self.last_name_first_name

    def has_bookmarked(self, object):
        for bookmark in self.bookmarks:
            if bookmark.bookmarked_id == object.id and bookmark.bookmarked_class == object.get_class_name():
                return True
        return False

    def mark_online(self):
        self.update(last_active=dt.datetime.utcnow())

    def as_dict(self):
        return {'id': self.id, 'name': self.get_name()}

    def __str__(self):
        """Readable representation of instance"""
        return self.last_name_first_name

    def __repr__(self):
        """Represent instance as a unique string."""
        return '<User({username!r},{roles!r})>'.format(username=self.username, roles=self.roles)
