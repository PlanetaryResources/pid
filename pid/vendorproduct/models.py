# -*- coding: utf-8 -*-
import datetime as dt
from flask import url_for
from flask_login import current_user
from pid.database import Column, db, reference_col, relationship
from pid.vendorpart.models import VendorPart
from pid.models import BaseRecord, NamelessRecord
from pid.permissions import VendorBuildPermissions, VendorProductPermissions
from pid.utils import format_match_query
from pid.workflows import ProductWorkflow


class VendorBuild(BaseRecord):
    __tablename__ = 'vendor_builds'
    build_identifier = Column(db.String, nullable=False, default='001')
    vendor_part_id = reference_col('vendor_parts')
    vendor_part = relationship('VendorPart')
    notes = Column(db.Text)
    purchase_order = Column(db.String)
    vendor_products = relationship('VendorProduct', back_populates='vendor_build', order_by="VendorProduct.serial_number")
    documents = relationship('Document', secondary='vendor_builds_documents')
    discrepancies = relationship('Discrepancy', secondary='vendor_builds_discrepancies')
    vendor_id = reference_col('companies')
    vendor = relationship('Company', foreign_keys=[vendor_id])
    manufacturer_id = reference_col('companies')
    manufacturer = relationship('Company', foreign_keys=[manufacturer_id])
    permissions = VendorBuildPermissions()
    __table_args__ = (db.UniqueConstraint('build_identifier', 'vendor_part_id', name='build_identifier_vendor_part_unique'),)

    def __init__(self, **kwargs):
        super().__init__()
        db.Model.__init__(self, **kwargs)

    @property
    def build_number(self):
        return '{0}.{1}'.format(self.vendor_part.part_number, self.build_identifier)

    @property
    def discrepancy_number(self):
        return '{0}-{1}'.format(self.vendor_part.part_number, self.build_identifier)

    @classmethod
    def get_next_build_identifier_for_vendor_part(cls, vendor_part):
        results = cls.query.with_entities(cls.build_identifier).filter_by(vendor_part=vendor_part).all()
        if len(results) == 0:
            build_identifier = 1
        else:
            resultset = [row[0] for row in results]
            resultset.sort()
            build_identifier = int(resultset[-1]) + 1
        return '{0:03d}'.format(build_identifier)

    def find_all_build_identifiers(self):
        results = VendorBuild.query.with_entities(VendorBuild.build_identifier).order_by(VendorBuild.build_identifier.asc()).filter_by(vendor_part=self.vendor_part).all()
        resultset = [row[0] for row in results]
        return resultset

    def can_user_edit(self, field_name):
        # Build state is always open, so need to override can_user_edit
        if current_user.is_admin():
            return True  # Admins can do anything always
        role = 'all'
        if current_user == self.owner:
            role = 'owner'
        elif current_user.is_superuser():
            role = 'superuser'
        state = 'open'
        return self.permissions.get_permissions().get(state, False).get(role, False).get(field_name)

    def __str__(self):
        return self.build_number

    def __repr__(self):
        return '<VendorBuild({0})>'.format(self.build_number)


vendor_builds_discrepancies = db.Table('vendor_builds_discrepancies',
    Column('vendor_build_id', db.BigInteger, db.ForeignKey('vendor_builds.id'), primary_key=True),
    Column('discrepancy_id', db.BigInteger, db.ForeignKey('discrepancies.id'), primary_key=True)
)

vendor_builds_documents = db.Table('vendor_builds_documents',
    Column('vendor_build_id', db.BigInteger, db.ForeignKey('vendor_builds.id'), primary_key=True),
    Column('document_id', db.BigInteger, db.ForeignKey('documents.id'), primary_key=True)
)


class VendorProduct(NamelessRecord):
    __tablename__ = 'vendor_products'
    descriptor = 'Vendor Product'
    serial_number = Column(db.String, nullable=False)
    vendor_part_id = reference_col('vendor_parts')
    vendor_part = relationship('VendorPart')
    summary = Column(db.String)
    notes = Column(db.Text)
    approvers = relationship('Approver', secondary='vendor_products_approvers',
                             order_by='asc(Approver.id)', backref='vendor_product')
    allowed_types = ['SN', 'LOT', 'STOCK']
    product_type = Column(db.String, default='SN')
    measured_mass = Column(db.Float, default=0.0)
    hardware_type_id = reference_col('hardware_types')
    hardware_type = relationship('HardwareType')
    project_id = reference_col('projects')
    project = relationship('Project')
    vendor_build_id = reference_col('vendor_builds')
    vendor_build = relationship('VendorBuild', back_populates='vendor_products')
    documents = relationship('Document', secondary='vendor_products_documents')
    images = relationship('Image', secondary='vendor_products_images')
    links = relationship('Link', secondary='vendor_products_links')
    discrepancies = relationship('Discrepancy', secondary='vendor_products_discrepancies')
    as_runs = relationship('AsRun', secondary='as_runs_vendor_products', order_by='desc(AsRun.created_at)')
    workflow = ProductWorkflow()
    state = Column(db.String, default=workflow.initial_state)
    permissions = VendorProductPermissions()
    __table_args__ = (db.UniqueConstraint('serial_number', 'vendor_part_id', name='serial_number_vendor_part_unique'),)

    __mapper_args__ = {
        "order_by": serial_number
    }

    def __init__(self, **kwargs):
        super().__init__()
        db.Model.__init__(self, **kwargs)

    @property
    def product_number(self):
        return '{0} {1}'.format(self.vendor_part.part_number, self.serial_number)

    @property
    def discrepancy_number(self):
        return '{0}-{1}'.format(self.vendor_part.part_number, self.serial_number)

    @classmethod
    def get_next_lot_number_for_vendor_part(cls, vendor_part):
        results = cls.query.with_entities(cls.serial_number).filter_by(vendor_part=vendor_part, product_type='LOT').distinct().all()
        if len(results) == 0:
            lot_number = 1
        else:
            resultset = [row[0] for row in results]
            resultset.sort(reverse=True)
            lot_number = None
            index = 0
            while not lot_number and index < len(resultset):
                if resultset[index].replace('L', '').isdigit():
                    lot_number = int(resultset[index].replace('L', '')) + 1
                index = index + 1
            if not lot_number:
                lot_number = 1
        return 'L{0:03d}'.format(lot_number)

    @classmethod
    def get_serial_numbers_for_vendor_part(cls, vendor_part):
        results = cls.query.with_entities(cls.serial_number).filter_by(vendor_part=vendor_part).distinct().all()
        resultset = [row[0] for row in results]
        resultset.sort()
        return resultset

    @classmethod
    def get_vendor_product_by_product_number(cls, part_number, serial_number):
        sql = 'SELECT vprod.* FROM vendor_products vprod, vendor_parts vpart WHERE vprod.vendor_part_id = vpart.id AND vpart.part_number = :part_number AND vprod.serial_number = :serial_number'
        results = db.session.query(cls).from_statement(db.text(sql).params(part_number=part_number, serial_number=serial_number)).first()
        return results

    @classmethod
    def find_all_vendor_products_for_user(cls, user):
        results = cls.query.filter_by(owner=user).join(cls.vendor_part).order_by(VendorPart.part_number, cls.serial_number).all()
        return results

    @classmethod
    def typeahead_search(cls, query):
        query = '%{0}%'.format(query)  # Pad query for an ILIKE search
        sql = "SELECT vprod.* FROM vendor_products vprod, vendor_parts vpart WHERE vprod.vendor_part_id = vpart.id AND (SELECT CONCAT(vpart.part_number, '-', vprod.serial_number, ' ', vpart.name) ILIKE :query)"
        results = db.session.query(cls).from_statement(db.text(sql).params(query=query)).all()
        return results

    @classmethod
    def advanced_search(cls, params):
        from pid.product.models import Discrepancy
        query = cls.query
        columns = cls.__table__.columns.keys()
        for attr in params:
            if params[attr] != "" and attr in columns:
                query = query.filter(getattr(cls, attr) == params[attr])
            elif params[attr] != "":
                if attr == 'vprod_part_number_query':
                    formatted_query = format_match_query(params['vprod_part_number_query_type'], params['vprod_part_number_query'])
                    query = query.filter(cls.vendor_part.has(VendorPart.part_number.ilike(formatted_query)))
                elif attr == 'vprod_serial_number_query':
                    formatted_query = format_match_query(params['vprod_serial_number_query_type'], params['vprod_serial_number_query'])
                    query = query.filter(cls.serial_number.ilike(formatted_query))
                elif attr == 'text_fields_query':
                    formatted_query = format_match_query('includes', params['text_fields_query'])
                    query = query.filter(cls.summary.ilike(formatted_query) | cls.notes.ilike(formatted_query))
                elif attr == 'open_discrepancies':
                    query = query.filter(cls.discrepancies.any(Discrepancy.state.in_(['Open'])))
                elif attr == 'created_on_start':
                    query = query.filter(cls.created_at >= params['created_on_start'])
                elif attr == 'created_on_end':
                    query = query.filter(cls.created_at <= params['created_on_end'])
                elif attr == 'in_open_state':
                    query = query.filter(cls.state.in_(cls.workflow.open_states))
                elif attr =='exclude_obsolete':
                    query = query.filter(cls.state != cls.workflow.obsolete_state)
                elif attr == 'vendor_id':
                    query = query.filter(cls.vendor_part.has(VendorPart.vendor_id == params[attr]))
                elif attr == 'material_id':
                    query = query.filter(cls.vendor_part.has(VendorPart.material_id == params[attr]))
        return query.all()

    def get_installed_ins(self):
        from pid.product.models import ProductComponent, ExtraProductComponent
        results = ProductComponent.query.filter_by(vendor_product=self).all()
        results.extend(ExtraProductComponent.query.filter_by(vendor_product=self).all())
        return results

    def get_approval_errors(self):
        approval_errors = []
        if self.state == self.workflow.get_approval_state():
            # Already in approval state, no need to do further checks
            return approval_errors
        # Check if not self_approved and either no approvers added or all approvers have already approved somehow.
        if not self.self_approved:
            if not self.approvers:
                approval_errors.append('You must add at least one approver.')
            elif all([approver.approved_at for approver in self.approvers]):
                approval_errors.append('You must add at least one approver.')
        # Check if open discrepancies
        for discrepancy in self.discrepancies:
            if discrepancy.is_open():
                approval_errors.append('Discrepancy {0} must be resolved.'.format(discrepancy.discrepancy_number))
        return approval_errors

    def get_name(self):
        return self.vendor_part.name

    def get_unique_identifier(self):
        return self.product_number

    def get_url(self, external=False):
        return url_for('vendorproduct.view_vendor_product', part_number=self.vendor_part.part_number,
                       serial_number=self.serial_number, _external=external)

    def __str__(self):
        return self.product_number

    def __repr__(self):
        return '<VendorProduct({0})>'.format(self.product_number)


vendor_products_approvers = db.Table('vendor_products_approvers',
    Column('vendor_product_id', db.BigInteger, db.ForeignKey('vendor_products.id'), primary_key=True),
    Column('approver_id', db.BigInteger, db.ForeignKey('approvers.id'), primary_key=True)
)

vendor_products_discrepancies = db.Table('vendor_products_discrepancies',
    Column('vendor_product_id', db.BigInteger, db.ForeignKey('vendor_products.id'), primary_key=True),
    Column('discrepancy_id', db.BigInteger, db.ForeignKey('discrepancies.id'), primary_key=True)
)

vendor_products_documents = db.Table('vendor_products_documents',
    Column('vendor_product_id', db.BigInteger, db.ForeignKey('vendor_products.id'), primary_key=True),
    Column('document_id', db.BigInteger, db.ForeignKey('documents.id'), primary_key=True)
)

vendor_products_images = db.Table('vendor_products_images',
    Column('vendor_product_id', db.BigInteger, db.ForeignKey('vendor_products.id'), primary_key=True),
    Column('image_id', db.BigInteger, db.ForeignKey('images.id'), primary_key=True)
)

vendor_products_links = db.Table('vendor_products_links',
    Column('vendor_product_id', db.BigInteger, db.ForeignKey('vendor_products.id'), primary_key=True),
    Column('link_id', db.BigInteger, db.ForeignKey('links.id'), primary_key=True)
)
