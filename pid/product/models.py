# -*- coding: utf-8 -*-
import datetime as dt
from flask import url_for
from flask_login import current_user
from sqlalchemy import func, types
from pid.database import Column, Model, SurrogatePK, db, reference_col, relationship
from pid.design.models import Design
from pid.models import BaseRecord, NamelessRecord
from pid.part.models import Part
from pid.permissions import BuildPermissions, ProductPermissions
from pid.utils import format_match_query
from pid.workflows import ProductWorkflow
from pid.vendorproduct.models import VendorProduct


class Build(BaseRecord):
    __tablename__ = 'builds'
    build_identifier = Column(db.String, nullable=False, default='001')
    part_id = reference_col('parts')
    part = relationship('Part')
    notes = Column(db.Text)
    purchase_order = Column(db.String)
    products = relationship('Product', back_populates='build', order_by="Product.serial_number")
    documents = relationship('Document', secondary='builds_documents')
    discrepancies = relationship('Discrepancy', secondary='builds_discrepancies')
    vendor_id = reference_col('companies')
    vendor = relationship('Company')
    permissions = BuildPermissions()
    __table_args__ = (db.UniqueConstraint('build_identifier', 'part_id', name='build_identifier_part_unique'),)

    def __init__(self, **kwargs):
        super().__init__()
        db.Model.__init__(self, **kwargs)

    @property
    def build_number(self):
        return '{0}.{1}'.format(self.part.part_identifier, self.build_identifier)

    @property
    def discrepancy_number(self):
        return '{0}-B{1}'.format(self.part.part_number, self.build_identifier)

    @classmethod
    def get_next_build_identifier_for_design_number_and_part_identifier(cls, design_number, part_identifier):
        sql = 'SELECT b.* FROM builds b, parts p, designs d WHERE b.part_id = p.id AND p.design_id = d.id AND d.design_number = :design_number AND p.part_identifier = :part_identifier'
        results = db.session.query(cls).from_statement(db.text(sql).params(design_number=design_number, part_identifier=part_identifier)).all()
        if len(results) == 0:
            build_identifier = 1
        else:
            # resultset = [row[0] for row in results]
            resultset = [b.build_identifier for b in results]
            resultset.sort()
            build_identifier = int(resultset[-1]) + 1
        return '{0:03d}'.format(build_identifier)

    @classmethod
    def get_build_by_build_number(cls, design_number, part_identifier, build_identifier):
        sql = 'SELECT b.* FROM builds b, parts p, designs d WHERE b.part_id = p.id AND p.design_id = d.id AND d.design_number = :design_number AND p.part_identifier = :part_identifier AND b.build_identifier = :build_identifier'
        results = db.session.query(cls).from_statement(db.text(sql).params(design_number=design_number, part_identifier=part_identifier, build_identifier=build_identifier)).first()
        return results

    def find_all_build_identifiers(self):
        results = Build.query.with_entities(Build.build_identifier).order_by(Build.build_identifier.asc()).filter_by(part=self.part).all()
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
        return '<Build({0})>'.format(self.build_number)


builds_discrepancies = db.Table('builds_discrepancies',
    Column('build_id', db.BigInteger, db.ForeignKey('builds.id'), primary_key=True),
    Column('discrepancy_id', db.BigInteger, db.ForeignKey('discrepancies.id'), primary_key=True)
)

builds_documents = db.Table('builds_documents',
    Column('build_id', db.BigInteger, db.ForeignKey('builds.id'), primary_key=True),
    Column('document_id', db.BigInteger, db.ForeignKey('documents.id'), primary_key=True)
)


class Product(NamelessRecord):
    __tablename__ = 'products'
    descriptor = 'Product'
    serial_number = Column(db.String, nullable=False)
    part_id = reference_col('parts')
    part = relationship('Part')
    revision = Column(db.String, nullable=False)
    summary = Column(db.String)
    notes = Column(db.Text)
    approvers = relationship('Approver', secondary='products_approvers', order_by='asc(Approver.id)', backref='product')
    allowed_types = ['SN', 'LOT', 'STOCK']
    product_type = Column(db.String, default='SN')
    measured_mass = Column(db.Float, default=0.0)
    hardware_type_id = reference_col('hardware_types')
    hardware_type = relationship('HardwareType')
    project_id = reference_col('projects')
    project = relationship('Project')
    build_id = reference_col('builds')
    build = relationship('Build', back_populates='products')
    documents = relationship('Document', secondary='products_documents')
    images = relationship('Image', secondary='products_images')
    links = relationship('Link', secondary='products_links')
    components = relationship('ProductComponent', foreign_keys='ProductComponent.parent_id')
    extra_components = relationship('ExtraProductComponent', foreign_keys='ExtraProductComponent.parent_id')
    discrepancies = relationship('Discrepancy', secondary='products_discrepancies')
    as_runs = relationship('AsRun', secondary='as_runs_products', order_by='desc(AsRun.created_at)')
    workflow = ProductWorkflow()
    state = Column(db.String, default=workflow.initial_state)
    permissions = ProductPermissions()
    __table_args__ = (db.UniqueConstraint('serial_number', 'part_id', name='serial_number_part_unique'),)

    __mapper_args__ = {
        "order_by": serial_number
    }

    def __init__(self, **kwargs):
        super().__init__()
        db.Model.__init__(self, **kwargs)

    @property
    def product_number(self):
        return '{0} {1}'.format(self.part.part_number, self.serial_number)

    @property
    def discrepancy_number(self):
        return '{0}-{1}'.format(self.part.part_number, self.serial_number)

    @classmethod
    def get_product_by_product_number(cls, design_number, part_identifier, serial_number):
        sql = 'SELECT prod.* FROM products prod, parts p, designs d WHERE prod.part_id = p.id AND p.design_id = d.id AND d.design_number = :design_number AND p.part_identifier = :part_identifier AND prod.serial_number = :serial_number'
        results = db.session.query(cls).from_statement(db.text(sql).params(design_number=design_number, part_identifier=part_identifier, serial_number=serial_number)).first()
        return results

    @classmethod
    def get_serial_numbers_for_design_number_and_part_identifier(cls, design_number, part_identifier):
        sql = 'SELECT prod.* FROM products prod, parts p, designs d WHERE prod.part_id = p.id AND p.design_id = d.id AND d.design_number = :design_number AND p.part_identifier = :part_identifier'
        results = db.session.query(cls).from_statement(db.text(sql).params(design_number=design_number, part_identifier=part_identifier)).all()
        resultset = [p.serial_number for p in results]
        resultset.sort()
        return resultset

    @classmethod
    def get_next_lot_number_for_design_number_and_part_identifier(cls, design_number, part_identifier):
        sql = 'SELECT prod.* FROM products prod, parts p, designs d WHERE prod.part_id = p.id AND p.design_id = d.id AND d.design_number = :design_number AND p.part_identifier = :part_identifier AND prod.product_type = \'LOT\''
        results = db.session.query(cls).from_statement(db.text(sql).params(design_number=design_number, part_identifier=part_identifier)).all()
        if len(results) == 0:
            lot_number = 1
        else:
            resultset = [p.serial_number for p in results]
            resultset.sort()
            lot_number = int(resultset[-1].replace('L', '')) + 1
        return 'L{0:03d}'.format(lot_number)

    @classmethod
    def find_all_products_for_user(cls, user):
        results = Product.query.filter_by(owner=user).join(cls.part).join(Part.design).order_by(Design.design_number, Part.part_identifier, cls.serial_number).all()
        return results

    def get_installed_ins(self):
        results = ProductComponent.query.filter_by(product=self).all()
        results.extend(ExtraProductComponent.query.filter_by(product=self).all())
        return results

    def get_product_components(self):
        return ProductComponent.query.filter_by(parent_id=self.id).all()

    def get_extra_product_components(self):
        return ExtraProductComponent.query.filter_by(parent_id=self.id).all()

    @classmethod
    def typeahead_search(cls, query):
        query = '%{0}%'.format(query)  # Pad query for an ILIKE search
        sql_name = "SELECT CASE WHEN p.name IS NOT NULL THEN p.name ELSE d.name END AS concat_name"
        sql = "SELECT prod.* FROM products prod, parts p, designs d WHERE prod.part_id = p.id AND p.design_id = d.id AND (SELECT CONCAT(d.design_number, '-', p.part_identifier, '-', prod.serial_number, ' ', ({0})) ILIKE :query)".format(sql_name)
        results = db.session.query(cls).from_statement(db.text(sql).params(query=query)).all()
        return results

    @classmethod
    def advanced_search(cls, params):
        query = cls.query
        columns = cls.__table__.columns.keys()
        for attr in params:
            if params[attr] != "" and attr in columns:
                query = query.filter(getattr(cls, attr) == params[attr])
            elif params[attr] != "":
                if attr == 'product_part_number_query':
                    formatted_query = format_match_query(params['product_part_number_query_type'], params[attr])
                    query = query.filter(cls.part.has(Part.design.has(Design.design_number.ilike(formatted_query))))
                elif attr == 'product_serial_number_query':
                    formatted_query = format_match_query(params['product_serial_number_query_type'], params[attr])
                    query = query.filter(func.cast(cls.serial_number, types.Text).ilike(formatted_query))
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
                elif attr == 'material_id':
                    query = query.filter(cls.part.has(Part.material_id == params[attr]))

        return query.all()

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
        return self.part.get_name()

    def get_unique_identifier(self):
        return '{0}-{1}'.format(self.part.part_number, self.serial_number)

    def get_url(self, external=False):
        return url_for('product.view_product', design_number=self.part.design.design_number,
                       part_identifier=self.part.part_identifier, serial_number=self.serial_number, _external=external)

    def __str__(self):
        return self.product_number

    def __repr__(self):
        return '<Product({0})>'.format(self.product_number)


products_approvers = db.Table('products_approvers',
    Column('product_id', db.BigInteger, db.ForeignKey('products.id'), primary_key=True),
    Column('approver_id', db.BigInteger, db.ForeignKey('approvers.id'), primary_key=True)
)

products_discrepancies = db.Table('products_discrepancies',
    Column('product_id', db.BigInteger, db.ForeignKey('products.id'), primary_key=True),
    Column('discrepancy_id', db.BigInteger, db.ForeignKey('discrepancies.id'), primary_key=True)
)

products_documents = db.Table('products_documents',
    Column('product_id', db.BigInteger, db.ForeignKey('products.id'), primary_key=True),
    Column('document_id', db.BigInteger, db.ForeignKey('documents.id'), primary_key=True)
)

products_images = db.Table('products_images',
    Column('product_id', db.BigInteger, db.ForeignKey('products.id'), primary_key=True),
    Column('image_id', db.BigInteger, db.ForeignKey('images.id'), primary_key=True)
)

products_links = db.Table('products_links',
    Column('product_id', db.BigInteger, db.ForeignKey('products.id'), primary_key=True),
    Column('link_id', db.BigInteger, db.ForeignKey('links.id'), primary_key=True)
)


class ProductComponent(SurrogatePK, Model):
    __tablename__ = 'product_components'
    parent_id = reference_col('products')
    parent = relationship('Product', foreign_keys=[parent_id])
    part_id = reference_col('parts', nullable=True)
    part = relationship('Part', foreign_keys=[part_id])
    vendor_part_id = reference_col('vendor_parts', nullable=True)
    vendor_part = relationship('VendorPart')
    vendor_product_id = reference_col('vendor_products', nullable=True)
    vendor_product = relationship('VendorProduct')
    product_id = reference_col('products', nullable=True)
    product = relationship('Product', foreign_keys=[product_id])
    ordering = Column(db.Integer)

    __mapper_args__ = {
        "order_by": ['ordering', 'id']
    }

    def __init__(self, **kwargs):
        """Create instance."""
        db.Model.__init__(self, **kwargs)

    def get_product(self):
        return self.product if self.product else self.vendor_product

    def get_part(self):
        return self.part if self.part else self.vendor_part

    def update_all_unassigned_product_components_for_part(self, product):
        rowcount = ProductComponent.query.filter_by(part=self.part, parent=self.parent, product=None).update({'product_id': product.id})
        db.session.commit()
        return rowcount

    def update_all_unassigned_product_components_for_vendor_part(self, vendor_product):
        rowcount = ProductComponent.query.filter_by(vendor_part=self.vendor_part, parent=self.parent, vendor_product=None).update({'vendor_product_id': vendor_product.id})
        db.session.commit()
        return rowcount

    def get_products_for_product_component(self):
        # Get all products for this parts design, and then all components for this parts design (not product, as they can be in use across products)
        sql = 'SELECT prod.* FROM products prod, parts p, designs d WHERE prod.part_id = p.id AND p.design_id = d.id AND d.design_number = :design_number AND p.part_identifier = :part_identifier'
        products = db.session.query(Product).from_statement(db.text(sql).params(design_number=self.part.design.design_number, part_identifier=self.part.part_identifier)).all()
        sql = 'SELECT pc.* FROM product_components pc, parts p, designs d WHERE pc.part_id = p.id AND p.design_id = d.id AND d.design_number = :design_number AND p.part_identifier = :part_identifier'
        components = db.session.query(ProductComponent).from_statement(db.text(sql).params(design_number=self.part.design.design_number, part_identifier=self.part.part_identifier)).all()
        sql = 'SELECT epc.* FROM extra_product_components epc, parts p, designs d WHERE epc.part_id = p.id AND p.design_id = d.id AND d.design_number = :design_number AND p.part_identifier = :part_identifier'
        extra_components = db.session.query(ExtraProductComponent).from_statement(db.text(sql).params(design_number=self.part.design.design_number, part_identifier=self.part.part_identifier)).all()
        # Remove products that are already in use, but keep LOT and STCK
        for component in components:
            if component.product and component is not self and component.product.product_type == 'SN' and component.product in products:
                products.remove(component.product)
        for component in extra_components:
            if component.product and component is not self and component.product.product_type == 'SN' and component.product in products:
                products.remove(component.product)
        return products

    def get_vendor_products_for_product_component(self):
        # Get all products for this part, and then all components for this part (not product, as they can be in use across products)
        vendor_products = VendorProduct.query.filter_by(vendor_part=self.vendor_part).all()
        components = ProductComponent.query.filter_by(vendor_part=self.vendor_part).all()
        extra_components = ExtraProductComponent.query.filter_by(vendor_part=self.vendor_part).all()
        # Remove products that are already in use, but keep LOT and STCK
        for component in components:
            if component.vendor_product and component is not self and component.vendor_product.product_type == 'SN' and component.vendor_product in vendor_products:
                vendor_products.remove(component.vendor_product)
        for component in extra_components:
            if component.vendor_product and component is not self and component.vendor_product.product_type == 'SN' and component.vendor_product in vendor_products:
                vendor_products.remove(component.vendor_product)
        return vendor_products

    def can_user_edit(self, field_name):
        return self.parent.can_user_edit('components')

    def __str__(self):
        if (self.part):
            return '{0} {1}'.format(self.parent.product_number, self.part.part_number)
        else:
            return '{0} {1}'.format(self.parent.product_number, self.vendor_part.part_number)

    def __repr__(self):
        """Represent instance as a unique string."""
        return '<ProductComponent({0})>'.format(self.id)


class ExtraProductComponent(SurrogatePK, Model):
    __tablename__ = 'extra_product_components'
    parent_id = reference_col('products')
    parent = relationship('Product', foreign_keys=[parent_id])
    part_id = reference_col('parts', nullable=True)
    part = relationship('Part', foreign_keys=[part_id])
    vendor_part_id = reference_col('vendor_parts', nullable=True)
    vendor_part = relationship('VendorPart')
    vendor_product_id = reference_col('vendor_products', nullable=True)
    vendor_product = relationship('VendorProduct')
    product_id = reference_col('products', nullable=True)
    product = relationship('Product', foreign_keys=[product_id])
    ordering = Column(db.Integer)

    __mapper_args__ = {
        "order_by": ['ordering', 'id']
    }

    def __init__(self, **kwargs):
        """Create instance."""
        db.Model.__init__(self, **kwargs)

    def get_product(self):
        return self.product if self.product else self.vendor_product

    def get_part(self):
        return self.part if self.part else self.vendor_part

    def get_all_unassigned_extra_product_components_like_this(self):
        results = None
        if self.part:
            results = ExtraProductComponent.query.filter_by(part=self.part, parent=self.parent, product=None)
        elif self.vendor_part:
            results = ExtraProductComponent.query.filter_by(vendor_part=self.vendor_part, parent=self.parent, vendor_product=None)
        return results

    def get_all_assigned_extra_product_components_like_this(self):
        results = None
        if self.part:
            results = ExtraProductComponent.query.filter(ExtraProductComponent.part == self.part, ExtraProductComponent.parent == self.parent, ExtraProductComponent.product != None)  # noqa
        elif self.vendor_part:
            results = ExtraProductComponent.query.filter(ExtraProductComponent.vendor_part == self.vendor_part, ExtraProductComponent.parent == self.parent, ExtraProductComponent.vendor_product != None)  # noqa
        return results

    def update_all_unassigned_extra_product_components_for_part(self, product):
        rowcount = ExtraProductComponent.query.filter_by(part=self.part, parent=self.parent, product=None).update({'product_id': product.id})
        db.session.commit()
        return rowcount

    def update_all_unassigned_extra_product_components_for_vendor_part(self, vendor_product):
        rowcount = ExtraProductComponent.query.filter_by(vendor_part=self.vendor_part, parent=self.parent, vendor_product=None).update({'vendor_product_id': vendor_product.id})
        db.session.commit()
        return rowcount

    def get_products_for_extra_product_component(self):
        # Get all products for this parts design, and then all components for this parts design (not product, as they can be in use across products)
        sql = 'SELECT prod.* FROM products prod, parts p, designs d WHERE prod.part_id = p.id AND p.design_id = d.id AND d.design_number = :design_number AND p.part_identifier = :part_identifier'
        products = db.session.query(Product).from_statement(db.text(sql).params(design_number=self.part.design.design_number, part_identifier=self.part.part_identifier)).all()
        sql = 'SELECT pc.* FROM product_components pc, parts p, designs d WHERE pc.part_id = p.id AND p.design_id = d.id AND d.design_number = :design_number AND p.part_identifier = :part_identifier'
        components = db.session.query(ProductComponent).from_statement(db.text(sql).params(design_number=self.part.design.design_number, part_identifier=self.part.part_identifier)).all()
        sql = 'SELECT epc.* FROM extra_product_components epc, parts p, designs d WHERE epc.part_id = p.id AND p.design_id = d.id AND d.design_number = :design_number AND p.part_identifier = :part_identifier'
        extra_components = db.session.query(ExtraProductComponent).from_statement(db.text(sql).params(design_number=self.part.design.design_number, part_identifier=self.part.part_identifier)).all()
        # Remove products that are already in use, but keep LOT and STCK
        for component in components:
            if component.product and component is not self and component.product.product_type == 'SN' and component.product in products:
                products.remove(component.product)
        for component in extra_components:
            if component.product and component is not self and component.product.product_type == 'SN' and component.product in products:
                products.remove(component.product)
        return products

    def get_vendor_products_for_extra_product_component(self):
        # Get all products for this part, and then all components for this part
        vendor_products = VendorProduct.query.filter_by(vendor_part=self.vendor_part).all()
        components = ProductComponent.query.filter_by(vendor_part=self.vendor_part).all()
        extra_components = ExtraProductComponent.query.filter_by(vendor_part=self.vendor_part).all()
        # Remove products that are already in use, but keep LOT and STCK
        for component in components:
            if component.vendor_product and component is not self and component.vendor_product.product_type == 'SN' and component.vendor_product in vendor_products:
                vendor_products.remove(component.vendor_product)
        for component in extra_components:
            if component.vendor_product and component is not self and component.vendor_product.product_type == 'SN' and component.vendor_product in vendor_products:
                vendor_products.remove(component.vendor_product)
        return vendor_products

    def can_user_edit(self, field_name):
        return self.parent.can_user_edit('components')

    def __str__(self):
        if (self.part):
            return '{0} {1}'.format(self.parent.product_number, self.part.part_number)
        else:
            return '{0} {1}'.format(self.parent.product_number, self.vendor_part.part_number)

    def __repr__(self):
        """Represent instance as a unique string."""
        return '<ExtraProductComponent({0})>'.format(self.id)


class Discrepancy(SurrogatePK, Model):
    __tablename__ = 'discrepancies'
    descriptor = 'Discrepancy'
    discrepancy_number = Column(db.String, nullable=False, default='01')
    description = Column(db.Text)
    justification = Column(db.Text)
    disposition_id = reference_col('dispositions', nullable=True)
    disposition = relationship('Disposition')
    allowed_states = ['Open', 'Closed']
    state = Column(db.String, default='Open')
    created_by_id = reference_col('users')
    created_by = relationship('User', foreign_keys=[created_by_id])
    created_at = Column(db.DateTime, nullable=False, default=dt.datetime.utcnow)

    __mapper_args__ = {
        "order_by": discrepancy_number
    }

    def __init__(self, **kwargs):
        db.Model.__init__(self, **kwargs)

    def is_open(self):
        return self.state == 'Open'

    def __str__(self):
        return self.discrepancy_number

    def __repr__(self):
        return '<Discrepancy({0})>'.format(self.discrepancy_number)
