# -*- coding: utf-8 -*-
"""Database module, including the SQLAlchemy database object and DB-related utilities."""
from sqlalchemy.orm import relationship
from sqlalchemy.orm.session import make_transient

from .compat import basestring
from .extensions import db

# Alias common SQLAlchemy names
Column = db.Column
relationship = relationship


class CRUDMixin(object):
    """Mixin that adds convenience methods for CRUD (create, read, update, delete) operations."""

    @classmethod
    def create(cls, **kwargs):
        """Create a new record and save it the database."""
        instance = cls(**kwargs)
        return instance.save()

    def update(self, commit=True, **kwargs):
        """Update specific fields of a record."""
        for attr, value in kwargs.items():
            setattr(self, attr, value)
        return commit and self.save() or self

    def save(self, commit=True):
        """Save the record."""
        db.session.add(self)
        if commit:
            db.session.commit()
        return self

    def delete(self, commit=True):
        """Remove the record from the database."""
        db.session.delete(self)
        return commit and db.session.commit()

    def clone(self, replace_values_dict={}):
        # TODO: Is there a better way of ensuring object is loaded?
        id = self.id  # noqa, to ensure object is loaded prior to cloning
        make_transient(self)  # NB! make_transient does not copy any foreign_keys
        self.id = None  # Assumes that PK is given by id parameter
        for key, value in replace_values_dict.items():
            setattr(self, key, value)
        self.save()
        return self


class Model(CRUDMixin, db.Model):
    """Base model class that includes CRUD convenience methods."""

    __abstract__ = True

    @classmethod
    def get_class_name(cls):
        return cls.__name__.lower()


# From Mike Bayer's "Building the app" talk
# https://speakerdeck.com/zzzeek/building-the-app
class SurrogatePK(object):
    """A mixin that adds a surrogate integer 'primary key' column named ``id`` to any declarative-mapped class."""

    __table_args__ = {'extend_existing': True}

    id = db.Column(db.BigInteger, primary_key=True)

    @classmethod
    def get_by_id(cls, record_id):
        """Get record by ID."""
        if any(
                (isinstance(record_id, basestring) and record_id.isdigit(),
                 isinstance(record_id, (int, float))),
        ):
            return cls.query.get(int(record_id))
        return None


def reference_col(tablename, nullable=False, pk_name='id', **kwargs):
    """Column that adds primary key foreign key reference.

    Usage: ::

        category_id = reference_col('category')
        category = relationship('Category', backref='categories')
    """
    return db.Column(
        db.ForeignKey('{0}.{1}'.format(tablename, pk_name)),
        nullable=nullable, **kwargs)


def get_record_by_id_and_class(record_id, record_class):
    # TODO: Try to find a better way that doesn't involve so much dynamic loading
    record = None
    record_class = record_class.lower()  # Just in case
    if record_class == 'anomaly':
        from pid.anomaly.models import Anomaly
        record = Anomaly.get_by_id(record_id)
    elif record_class == 'asrun':
        from pid.asrun.models import AsRun
        record = AsRun.get_by_id(record_id)
    elif record_class == 'build':
        from pid.product.models import Build
        record = Build.get_by_id(record_id)
    elif record_class == 'design':
        from pid.design.models import Design
        record = Design.get_by_id(record_id)
    elif record_class == 'eco':
        from pid.eco.models import ECO
        record = ECO.get_by_id(record_id)
    elif record_class == 'part':
        from pid.part.models import Part
        record = Part.get_by_id(record_id)
    elif record_class == 'procedure':
        from pid.procedure.models import Procedure
        record = Procedure.get_by_id(record_id)
    elif record_class == 'product':
        from pid.product.models import Product
        record = Product.get_by_id(record_id)
    elif record_class == 'specification':
        from pid.specification.models import Specification
        record = Specification.get_by_id(record_id)
    elif record_class == 'task':
        from pid.task.models import Task
        record = Task.get_by_id(record_id)
    elif record_class == 'vendorbuild':
        from pid.vendorproduct.models import VendorBuild
        record = VendorBuild.get_by_id(record_id)
    elif record_class == 'vendorpart':
        from pid.vendorpart.models import VendorPart
        record = VendorPart.get_by_id(record_id)
    elif record_class == 'vendorproduct':
        from pid.vendorproduct.models import VendorProduct
        record = VendorProduct.get_by_id(record_id)
    return record
