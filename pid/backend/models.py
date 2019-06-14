# -*- coding: utf-8 -*-
"""Backend models."""
from pid.database import Column, Model, SurrogatePK, db, reference_col, relationship


class Settings(SurrogatePK, Model):
    '''
        Single row settings. Considered key/value pair entries, but figured this would be easier as settings should be limited.
    '''
    __tablename__ = 'plaid_settings'
    efab_user_id = reference_col('users')
    efab_user = relationship('User', foreign_keys=[efab_user_id])
    mfab_user_id = reference_col('users')
    mfab_user = relationship('User', foreign_keys=[mfab_user_id])
    plaid_admin_id = reference_col('users')
    plaid_admin = relationship('User', foreign_keys=[plaid_admin_id])
    name_order_options = [('last_name_first_name', 'Last, First'), ('full_name', 'First Last'), ('username', 'Username'), ('email', 'Email')]
    name_order = Column(db.String, default='last_name_first_name')

    def __init__(self, **kwargs):
        db.Model.__init__(self, **kwargs)

    def __str__(self):
        return str(self.as_dict())

    @classmethod
    def get_settings(cls):
        return cls.query.first()

    def as_dict(self):
       return {c.name: getattr(self, c.name) for c in self.__table__.columns}

    def __repr__(self):
        return '<Settings>'
