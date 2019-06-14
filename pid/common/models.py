# -*- coding: utf-8 -*-
"""Common models."""
import datetime as dt
from flask_login import current_user
from sqlalchemy import asc, desc, and_
from pid.database import Column, Model, SurrogatePK, db, reference_col, relationship, get_record_by_id_and_class


class Company(SurrogatePK, Model):
    __tablename__ = 'companies'
    name = Column(db.String, unique=True, nullable=False)
    website = Column(db.String)
    address = Column(db.Text)
    notes = Column(db.Text)
    pri_account_number = Column(db.String)
    terms = Column(db.Text)
    alias = Column(db.String)

    __mapper_args__ = {
        "order_by": name
    }

    def __init__(self, **kwargs):
        db.Model.__init__(self, **kwargs)

    @classmethod
    def get_company_by_name(cls, name):
        result = cls.query.filter_by(name=name).first()
        return result

    @classmethod
    def get_all_with_pri_on_top(cls):
        sql = "SELECT * FROM {0} ORDER BY CASE WHEN NAME = 'PRDC' THEN 1 WHEN NAME = 'PR-Lux' THEN 2 ELSE 3 END, name".format(cls.__tablename__)
        results = db.session.query(cls).from_statement(db.text(sql)).all()
        return results

    def __str__(self):
        return self.name

    def __repr__(self):
        return '<Company({name!r})>'.format(name=self.name)


class Criticality(SurrogatePK, Model):
    __tablename__ = 'criticalities'
    name = Column(db.String, unique=True, nullable=False)
    description = Column(db.Text)
    ordering = Column(db.Integer, unique=True)  # Unique to prevent clashes in ordering

    __mapper_args__ = {
        "order_by": ordering
    }

    def __init__(self, name='Name', description=None, **kwargs):
        db.Model.__init__(self, name=name, description=description, **kwargs)

    @classmethod
    def find_by_ordering(cls, ordering):
        # Should ideally only return one
        result = cls.query.filter_by(ordering=ordering).first()
        return result

    @classmethod
    def find_highest_free_ordering_plus_one(cls):
        results = db.session.query(db.func.max(cls.ordering)).first()
        return int(results[0]) + 1

    def __str__(self):
        return self.name

    def __repr__(self):
        return '<Criticality({name!r})>'.format(name=self.name)


class Disposition(SurrogatePK, Model):
    __tablename__ = 'dispositions'
    name = Column(db.String, unique=True, nullable=False)
    description = Column(db.Text)
    ordering = Column(db.Integer, unique=True)  # Unique to prevent clashes in ordering

    __mapper_args__ = {
        "order_by": ordering
    }

    def __init__(self, name='Name', description=None, **kwargs):
        db.Model.__init__(self, name=name, description=description, **kwargs)

    @classmethod
    def find_by_ordering(cls, ordering):
        # Should ideally only return one
        result = cls.query.filter_by(ordering=ordering).first()
        return result

    @classmethod
    def find_highest_free_ordering_plus_one(cls):
        results = db.session.query(db.func.max(cls.ordering)).first()
        return int(results[0]) + 1

    def as_dict(self):
       return {c.name: getattr(self, c.name) for c in self.__table__.columns}

    def __str__(self):
        return self.name

    def __repr__(self):
        return '<Disposition({name!r})>'.format(name=self.name)


class HardwareType(SurrogatePK, Model):
    __tablename__ = 'hardware_types'
    name = Column(db.String, unique=True, nullable=False)
    description = Column(db.Text)
    ordering = Column(db.Integer, unique=True)  # Unique to prevent clashes in ordering

    __mapper_args__ = {
        "order_by": ordering
    }

    def __init__(self, name='Name', description=None, **kwargs):
        db.Model.__init__(self, name=name, description=description, **kwargs)

    @classmethod
    def find_by_ordering(cls, ordering):
        # Should ideally only return one
        result = cls.query.filter_by(ordering=ordering).first()
        return result

    @classmethod
    def find_highest_free_ordering_plus_one(cls):
        results = db.session.query(db.func.max(cls.ordering)).first()
        return int(results[0]) + 1

    def __str__(self):
        return self.name

    def __repr__(self):
        return '<HardwareType({name!r})>'.format(name=self.name)


class Material(SurrogatePK, Model):
    __tablename__ = 'materials'
    name = Column(db.String, unique=True, nullable=False)
    description = Column(db.Text)
    ordering = Column(db.Integer, unique=True)  # Unique to prevent clashes in ordering

    __mapper_args__ = {
        "order_by": ordering
    }

    def __init__(self, name='Name', description=None, **kwargs):
        db.Model.__init__(self, name=name, description=description, **kwargs)

    def __str__(self):
        return self.name

    def __repr__(self):
        return '<Material({name!r})>'.format(name=self.name)


class MaterialSpecification(SurrogatePK, Model):
    __tablename__ = 'material_specifications'
    name = Column(db.String, nullable=False)
    # description = Column(db.Text)
    material_id = reference_col('materials', nullable=False)
    material = relationship('Material', backref='specifications')

    __mapper_args__ = {
        "order_by": name
    }

    def __init__(self, name='Name', description=None, **kwargs):
        db.Model.__init__(self, name=name, **kwargs)

    def __str__(self):
        return self.name

    def __repr__(self):
        return '<MaterialSpecification({name!r})>'.format(name=self.name)


class Project(SurrogatePK, Model):
    __tablename__ = 'projects'
    name = Column(db.String, unique=True, nullable=False)
    description = Column(db.Text)

    __mapper_args__ = {
        "order_by": name
    }

    def __init__(self, name='Name', description=None, **kwargs):
        db.Model.__init__(self, name=name, description=description, **kwargs)

    def __str__(self):
        return self.name

    def __repr__(self):
        return '<Project({name!r})>'.format(name=self.name)


class RevisionLog(SurrogatePK, Model):
    __tablename__ = 'revision_logs'
    entries = relationship('RevisionLogEntry')

    def __init__(self, **kwargs):
        db.Model.__init__(self, **kwargs)

    def add_entry(self, revision, reason, revisioned_by):
        entry = RevisionLogEntry.create(parent=self, revision=revision, reason=reason, revisioned_by=revisioned_by)
        self.entries.append(entry)
        self.save()

    def __str__(self):
        return '{0} entries'.format(len(self.entries))

    def __repr__(self):
        return '<RevisionLog({0})>'.format(self.id)


class RevisionLogEntry(SurrogatePK, Model):
    __tablename__ = 'revision_log_entries'
    parent_id = reference_col('revision_logs')
    parent = relationship('RevisionLog')
    revision = Column(db.String)
    reason = Column(db.Text)
    revisioned_by_id = reference_col('users')
    revisioned_by = relationship('User')
    revisioned_at = Column(db.DateTime, nullable=False, default=dt.datetime.utcnow)

    __mapper_args__ = {
        "order_by": desc(revisioned_at)
    }

    def __init__(self, **kwargs):
        db.Model.__init__(self, **kwargs)

    def can_user_edit(self, field_name):
        # TODO: Redo this logic, this is currently handled in Jinja2 template
        return True

    def __str__(self):
        return str(self.id)

    def __repr__(self):
        return '<RevisionLogEntry({0})>'.format(self.id)


class ChangeLog(SurrogatePK, Model):
    __tablename__ = 'change_logs'
    entries = relationship('ChangeLogEntry')

    def __init__(self, **kwargs):
        db.Model.__init__(self, **kwargs)
        self.add_entry(action='Create', changed_by=current_user)

    def add_entry(self, **kwargs):
        entry = ChangeLogEntry.create(parent=self, **kwargs)
        self.entries.append(entry)
        self.save()

    def __str__(self):
        return '{0} entries'.format(len(self.entries))

    def __repr__(self):
        return '<ChangeLog({0})>'.format(self.id)


class ChangeLogEntry(SurrogatePK, Model):
    __tablename__ = 'change_log_entries'
    parent_id = reference_col('change_logs')
    parent = relationship('ChangeLog')
    action = Column(db.String)
    field = Column(db.String)
    original_value = Column(db.Text)
    new_value = Column(db.Text)
    changed_by_id = reference_col('users')
    changed_by = relationship('User')
    changed_at = Column(db.DateTime, nullable=False, default=dt.datetime.utcnow)

    __mapper_args__ = {
        "order_by": desc(changed_at)
    }

    def __init__(self, **kwargs):
        db.Model.__init__(self, **kwargs)

    def __str__(self):
        return str(self.id)

    def __repr__(self):
        return '<ChangeLogEntry({0})>'.format(self.id)


class WorkflowLog(SurrogatePK, Model):
    __tablename__ = 'workflow_logs'
    entries = relationship('WorkflowLogEntry')

    def __init__(self, **kwargs):
        db.Model.__init__(self, **kwargs)
        self.add_entry(action='Create', capacity='Owner', changed_by=current_user)

    def add_entry(self, **kwargs):
        entry = WorkflowLogEntry.create(parent=self, **kwargs)
        self.entries.append(entry)
        self.save()

    def __str__(self):
        return '{0} entries'.format(len(self.entries))

    def __repr__(self):
        return '<WorkflowLog({0})>'.format(self.id)


class WorkflowLogEntry(SurrogatePK, Model):
    __tablename__ = 'workflow_log_entries'
    parent_id = reference_col('workflow_logs')
    parent = relationship('WorkflowLog')
    changed_by_id = reference_col('users')
    changed_by = relationship('User')
    changed_at = Column(db.DateTime, nullable=False, default=dt.datetime.utcnow)
    capacity = Column(db.String)
    action = Column(db.String)
    comment = Column(db.Text)

    __mapper_args__ = {
        "order_by": asc(changed_at)
    }

    def __init__(self, **kwargs):
        db.Model.__init__(self, **kwargs)

    def __str__(self):
        return str(self.id)

    def __repr__(self):
        return '<WorkflowLogEntry({0})>'.format(self.id)


class Reference(SurrogatePK, Model):
    """A reference that can be tied to a design item, part, ECO, anomaly...etc"""
    __tablename__ = 'references'
    by_id = Column(db.BigInteger, nullable=False)
    by_class = Column(db.String, nullable=False)  # Will be slugified
    to_id = Column(db.BigInteger, nullable=False)
    to_class = Column(db.String, nullable=False)  # Will be slugified

    def __init__(self, **kwargs):
        db.Model.__init__(self, **kwargs)

    def can_user_edit(self, field_name):
        reference_object = self.get_reference_object_by()
        return reference_object.can_user_edit(field_name)

    def get_name_by(self):
        reference_object = self.get_reference_object_by()
        return reference_object.get_name()

    def get_name_to(self):
        reference_object = self.get_reference_object_to()
        return reference_object.get_name()

    def get_state_by(self):
        reference_object = self.get_reference_object_by()
        return reference_object.state

    def get_state_to(self):
        reference_object = self.get_reference_object_to()
        return reference_object.state

    def get_unique_identifier_by(self):
        from pid.design.models import Design
        from pid.procedure.models import Procedure
        from pid.specification.models import Specification
        reference_object = self.get_reference_object_by()
        if reference_object.get_class_name() in [Design.get_class_name(), Procedure.get_class_name(),
                                                 Specification.get_class_name()]:
            return reference_object.get_latest_revision_unique_identifier()
        return reference_object.get_unique_identifier()

    def get_unique_identifier_to(self):
        from pid.design.models import Design
        from pid.procedure.models import Procedure
        from pid.specification.models import Specification
        reference_object = self.get_reference_object_to()
        if reference_object.get_class_name() in [Design.get_class_name(), Procedure.get_class_name(),
                                                 Specification.get_class_name()]:
            return reference_object.get_latest_revision_unique_identifier()
        return reference_object.get_unique_identifier()

    def get_url_by(self):
        from pid.design.models import Design
        from pid.procedure.models import Procedure
        from pid.specification.models import Specification
        reference_object = self.get_reference_object_by()
        if reference_object.get_class_name() in [Design.get_class_name(), Procedure.get_class_name(),
                                                 Specification.get_class_name()]:
            return reference_object.get_latest_revision_url()
        return reference_object.get_url()

    def get_url_to(self):
        from pid.design.models import Design
        from pid.procedure.models import Procedure
        from pid.specification.models import Specification
        reference_object = self.get_reference_object_to()
        if reference_object.get_class_name() in [Design.get_class_name(), Procedure.get_class_name(),
                                                 Specification.get_class_name()]:
            return reference_object.get_latest_revision_url()
        return reference_object.get_url()

    def get_reference_object_by(self):
        return self.get_reference_object("by")

    def get_reference_object_to(self):
        return self.get_reference_object("to")

    def get_reference_object(self, direction):
        # Imports need to be here to prevent circular imports
        if direction == 'to':
            reference_object_class_name = self.to_class
            reference_object_id = self.to_id
        else:
            reference_object_class_name = self.by_class
            reference_object_id = self.by_id
        reference_object = get_record_by_id_and_class(reference_object_id, reference_object_class_name)
        return reference_object

    def __repr__(self):
        """Represent instance as a unique string."""
        return '<Reference({0})>'.format(self.get_url_by())


class Bookmark(SurrogatePK, Model):
    """A reference that can be tied to a design item, part, ECO, anomaly...etc"""
    __tablename__ = 'bookmarks'
    user_id = reference_col('users')
    user = relationship('User', foreign_keys=[user_id])
    bookmarked_id = Column(db.BigInteger, nullable=False)
    bookmarked_class = Column(db.String, nullable=False)

    def __init__(self, **kwargs):
        db.Model.__init__(self, **kwargs)

    def get_name(self):
        bookmarked_object = self.get_bookmarked_object()
        return bookmarked_object.get_name()

    def get_state(self):
        bookmarked_object = self.get_bookmarked_object()
        return bookmarked_object.state

    def get_unique_identifier(self):
        bookmarked_object = self.get_bookmarked_object()
        return bookmarked_object.get_unique_identifier()

    def get_url(self):
        bookmarked_object = self.get_bookmarked_object()
        return bookmarked_object.get_url()

    def get_bookmarked_object(self):
        bookmarked_class = self.bookmarked_class
        bookmarked_id = self.bookmarked_id
        bookmarked_object = get_record_by_id_and_class(bookmarked_id, bookmarked_class)
        return bookmarked_object

    def __repr__(self):
        """Represent instance as a unique string."""
        return '<Bookmark({0})>'.format(self.id)


class AdvancedSearch(SurrogatePK, Model):
    __tablename__ = 'advanced_searches'
    user_id = reference_col('users')
    user = relationship('User', foreign_keys=[user_id])
    search_parameters = Column(db.String, nullable=True)
    name = Column(db.String, nullable=True)

    def __init__(self, **kwargs):
        db.Model.__init__(self, **kwargs)


class Approver(SurrogatePK, Model):
    __tablename__ = 'approvers'
    approver_id = reference_col('users')
    approver = relationship('User', foreign_keys=[approver_id])
    capacity = Column(db.String, nullable=False)
    approved_at = Column(db.DateTime)

    def __init__(self, **kwargs):
        db.Model.__init__(self, **kwargs)

    @classmethod
    def get_open_approvals_for_user(cls, user=current_user):
        query_results = db.session.query(cls).filter(and_(cls.approver == user, cls.approved_at == None)).all()
        results = []
        for approver in query_results:
            record = approver.get_record()
            if record.state == record.workflow.get_approval_state():
                results.append(approver)
        return results

    def get_record(self):
        # TODO: Current relationship is many-to-many, should try to make this a many-to-one
        if self.design:
            return self.design[0]
        elif self.vendor_part:
            return self.vendor_part[0]
        elif self.product:
            return self.product[0]
        elif self.vendor_product:
            return self.vendor_product[0]
        elif self.eco:
            return self.eco[0]
        elif self.anomaly:
            return self.anomaly[0]
        elif self.procedure:
            return self.procedure[0]
        elif self.specification:
            return self.specification[0]
        elif self.as_run:
            return self.as_run[0]

