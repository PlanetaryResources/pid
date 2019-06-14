# -*- coding: utf-8 -*-
"""VendorPart models."""
from flask import url_for
from pid.database import Column, db, reference_col, relationship
from pid.models import Record
from pid.part.models import Part
from pid.permissions import VendorPartPermissions
from pid.utils import format_match_query
from pid.workflows import VendorPartWorkflow


class VendorPart(Record):
    __tablename__ = 'vendor_parts'
    descriptor = 'Vendor Part'
    part_number = Column(db.String, nullable=False)
    current_best_estimate = Column(db.Float, default=0.0, nullable=False)
    uncertainty = Column(db.Float, default=0.0, nullable=False)
    predicted_best_estimate = Column(db.Float, default=0.0, nullable=False)
    material_id = reference_col('materials', nullable=True)
    material = relationship('Material')
    material_specification_id = reference_col('material_specifications', nullable=True)
    material_specification = relationship('MaterialSpecification')
    approvers = relationship('Approver', secondary='vendor_parts_approvers',
                             order_by='asc(Approver.id)', backref='vendor_part')
    summary = Column(db.String, nullable=True)
    notes = Column(db.Text, nullable=True)
    project_id = reference_col('projects')
    project = relationship('Project')
    vendor_id = reference_col('companies')
    vendor = relationship('Company')
    procedures = relationship('Procedure', secondary='procedures_vendor_parts')
    documents = relationship('Document', secondary='vendor_parts_documents')
    images = relationship('Image', secondary='vendor_parts_images')
    links = relationship('Link', secondary='vendor_parts_links')
    anomalies = relationship('Anomaly', secondary='vendor_parts_anomalies',
                             order_by='desc(Anomaly.created_at)', back_populates='vendor_parts')
    workflow = VendorPartWorkflow()
    state = Column(db.String, default=workflow.initial_state)
    permissions = VendorPartPermissions()
    __table_args__ = (db.UniqueConstraint('part_number', name='part_number_unique'),)

    __mapper_args__ = {
        "order_by": part_number
    }

    def __init__(self, **kwargs):
        super().__init__()
        db.Model.__init__(self, **kwargs)

    @property
    def design_number(self):
        return self.part_number

    @classmethod
    def get_by_part_number(cls, part_number):
        return cls.query.filter_by(part_number=part_number).first()

    @classmethod
    def get_all_vendor_parts(cls):
        results = cls.query.all()
        return results

    @classmethod
    def find_all_vendor_parts_for_user(cls, user):
        results = cls.query.filter_by(owner=user).order_by(cls.part_number).all()
        return results

    @classmethod
    def typeahead_search(cls, query, part_id):
        query = '%{0}%'.format(query)  # Pad query for an ILIKE search
        # Search in vendor parts for part_number or name that matches
        sql_vendor_ids = "SELECT id FROM {0} WHERE (SELECT CONCAT(part_number, ' ', name) ILIKE :query)".format(cls.__tablename__)
        # Get ids of vendor parts already added as part_components, excluding part_components made up of parts
        sql_pc_ids = 'SELECT vendor_part_id FROM part_components WHERE parent_id = :part_id AND vendor_part_id IS NOT NULL'
        # Search in vendor parts, excluding self and already added parts
        sql = 'SELECT * FROM {0} WHERE id NOT in ({1}) AND id IN ({2})'.format(cls.__tablename__, sql_pc_ids, sql_vendor_ids)
        results = db.session.query(cls).from_statement(db.text(sql).params(query=query, part_id=part_id)).all()
        # results = VendorPart.query.whooshee_search(query).all()
        return results

    @classmethod
    def advanced_search(cls, params):
        from pid.anomaly.models import Anomaly
        query = cls.query
        columns = cls.__table__.columns.keys()

        for attr in params:
            if params[attr] != "" and attr in columns:
                query = query.filter(getattr(cls, attr) == params[attr])
            elif params[attr] != "":
                if attr == 'part_number_query':
                    formatted_query = format_match_query(params['part_number_query_type'], params['part_number_query'])
                    query = query.filter(cls.part_number.ilike(formatted_query))
                elif attr == 'text_fields_query':
                    formatted_query = format_match_query('includes', params['text_fields_query'])
                    query = query.filter(cls.name.ilike(formatted_query) | cls.notes.ilike(formatted_query) |
                                         cls.summary.ilike(formatted_query))
                elif attr == 'open_anomalies':
                    query = query.filter(cls.anomalies.any(Anomaly.state.in_(Anomaly.workflow.open_states)))
                elif attr == 'created_on_start':
                    query = query.filter(cls.created_at >= params['created_on_start'])
                elif attr == 'created_on_end':
                    query = query.filter(cls.created_at <= params['created_on_end'])
                elif attr == 'in_open_state':
                    query = query.filter(cls.state.in_(cls.workflow.open_states))
                elif attr =='exclude_obsolete':
                    query = query.filter(cls.state != cls.workflow.obsolete_state)
        if 'open_anomalies' not in params:
            query = query.distinct(cls.part_number)
        return query.order_by(cls.part_number.desc()).all()

    def get_vendor_builds_for_vendor_part(self):
        from pid.vendorproduct.models import VendorBuild
        results = VendorBuild.query.filter_by(vendor_part=self).all()
        return results

    def update_parents_mass(self):
        """ Update the mass of all parents of this part. Call this when updating mass of a part """
        from pid.part.models import PartComponent
        # TODO: rename
        part_components = PartComponent.query.filter_by(vendor_part=self).all()
        for part_component in part_components:
            part_component.parent.update_mass()

    def get_procedures(self):
        return self.get_distinct_procedures()

    def get_distinct_procedures(self):
        from pid.procedure.models import Procedure
        procedures = Procedure.query.filter(Procedure.vendor_parts.contains(self))\
            .order_by(Procedure.procedure_number, Procedure.revision.desc()).distinct(Procedure.procedure_number).all()
        procedures.sort(key=lambda x: x.created_at, reverse=True)  # Sort by newest first
        return procedures

    def get_products_for_part(self):
        from pid.product.models import VendorProduct
        results = VendorProduct.query.filter_by(vendor_part_id=self.id).all()
        return results

    def get_nlas_for_vendor_part(self):
        return Part.get_nlas_for_vendor_part(self)

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
        # Check if open anomalies
        for anomaly in self.anomalies:
            if anomaly.is_open():
                approval_errors.append('{0} must be resolved.'.format(anomaly.get_unique_identifier()))
        return approval_errors

    def get_unique_identifier(self):
        return self.part_number

    def get_url(self, external=False):
        return url_for('vendorpart.view_vendor_part', part_number=self.part_number, _external=external)

    def __str__(self):
        return self.part_number

    def __repr__(self):
        """Represent instance as a unique string."""
        return '<VendorPart({0})>'.format(self.part_number)


vendor_parts_approvers = db.Table('vendor_parts_approvers',
    Column('vendor_part_id', db.BigInteger, db.ForeignKey('vendor_parts.id'), primary_key=True),
    Column('approver_id', db.BigInteger, db.ForeignKey('approvers.id'), primary_key=True)
)

vendor_parts_anomalies = db.Table('vendor_parts_anomalies',
    Column('vendor_part_id', db.BigInteger, db.ForeignKey('vendor_parts.id'), primary_key=True),
    Column('anomaly_id', db.BigInteger, db.ForeignKey('anomalies.id'), primary_key=True)
)

vendor_parts_documents = db.Table('vendor_parts_documents',
    Column('vendor_part_id', db.BigInteger, db.ForeignKey('vendor_parts.id'), primary_key=True),
    Column('document_id', db.BigInteger, db.ForeignKey('documents.id'), primary_key=True)
)

vendor_parts_images = db.Table('vendor_parts_images',
    Column('vendor_part_id', db.BigInteger, db.ForeignKey('vendor_parts.id'), primary_key=True),
    Column('image_id', db.BigInteger, db.ForeignKey('images.id'), primary_key=True)
)

vendor_parts_links = db.Table('vendor_parts_links',
    Column('vendor_part_id', db.BigInteger, db.ForeignKey('vendor_parts.id'), primary_key=True),
    Column('link_id', db.BigInteger, db.ForeignKey('links.id'), primary_key=True)
)
