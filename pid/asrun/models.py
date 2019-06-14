from flask import url_for
from pid.database import Column, db, relationship, reference_col
import pid.utils as Utils
from sqlalchemy.ext.associationproxy import association_proxy
from pid.models import NamelessRecord
from pid.permissions import AsRunPermissions
from pid.workflows import AsRunWorkflow


class AsRun(NamelessRecord):
    __tablename__ = 'as_runs'
    descriptor = 'As-Run'
    name = Column(db.String, nullable=True)
    as_run_number = Column(db.Integer, nullable=False)
    approvers = relationship('Approver', secondary='as_runs_approvers', order_by='asc(Approver.id)', backref='as_run')
    procedure_id = reference_col('procedures')
    procedure = relationship('Procedure')  # Inherit revision, name from procedure
    notes = Column(db.String)
    software_version = Column(db.String)
    products = relationship('Product', secondary='as_runs_products')
    vendor_products = relationship('VendorProduct', secondary='as_runs_vendor_products')
    anomalies = relationship('Anomaly', secondary='as_runs_anomalies',
                             order_by='desc(Anomaly.created_at)', back_populates='as_runs')
    documents = relationship('Document', secondary='as_runs_documents')
    links = relationship('Link', secondary='as_runs_links')
    images = relationship('Image', secondary='as_runs_images')
    project_id = reference_col('projects')
    project = relationship('Project')
    procedure_number = association_proxy('procedure', 'procedure_number')
    workflow = AsRunWorkflow()
    state = Column(db.String, default=workflow.initial_state)
    permissions = AsRunPermissions()

    __mapper_args__ = {
        "order_by": [procedure_id, as_run_number]
    }

    def __init__(self, **kwargs):
        """Create instance with change log."""
        super().__init__()
        db.Model.__init__(self, **kwargs)

    @property
    def identifier(self):
        return '{0}.{1}'.format(self.procedure.procedure_number, str(self.as_run_number).zfill(3))

    @classmethod
    def get_by_procedure_id_as_run_number(cls, procedure_id, as_run_number):
        return cls.query.filter_by(as_run_number=as_run_number, procedure_id=procedure_id).first()

    @classmethod
    def find_all_as_runs_for_user(cls, user):
        from pid.procedure.models import Procedure
        results = cls.query.filter_by(owner=user).join(cls.procedure).order_by(Procedure.procedure_number, cls.as_run_number).all()
        return results

    @classmethod
    def typeahead_search(cls, query):
        query = '%{0}%'.format(query)  # Pad query for an ILIKE search
        # Need to zero pad as_run_number in following query
        sql = "SELECT ar.* FROM as_runs ar, procedures p WHERE ar.procedure_id = p.id AND (SELECT CONCAT(p.procedure_number, '-', lpad(cast(ar.as_run_number as text), 3, '0'), ' ', ar.name) ILIKE :query)"
        results = db.session.query(cls).from_statement(db.text(sql).params(query=query)).all()
        return results

    def find_all_revisions(self):
        results = AsRun.query.filter_by(as_run_number=self.as_run_number).all()
        return Utils.find_all_revisions(results)

    def find_latest_revision(self):
        results = AsRun.query.with_entities(AsRun.revision).filter_by(as_run_number=self.as_run_number).all()
        return Utils.find_latest_revision(results)

    def find_next_revision(self):
        results = AsRun.query.with_entities(AsRun.revision).filter_by(as_run_number=self.procedure_number).order_by(AsRun.revision).all()
        return Utils.find_next_revision(results)

    @classmethod
    def find_next_as_run_number(cls, procedure):
        as_runs = cls.query.filter_by(procedure_number=procedure.procedure_number).all()
        highest_as_run_number = 0

        for as_run in as_runs:
            if int(as_run.as_run_number) > highest_as_run_number:
                highest_as_run_number = int(as_run.as_run_number)
        return highest_as_run_number + 1

    @classmethod
    def find_all_procedure_as_runs_numbers(cls, procedure_number):
        as_runs = cls.query.filter_by(procedure_number=procedure_number).all()
        as_run_numbers = []
        for as_run in as_runs:
            as_run_numbers.append(as_run.as_run_number)
        return as_run_numbers

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

    def get_name(self):
        return self.name if self.name else self.procedure.name

    def get_unique_identifier(self):
        return '{0}-{1}'.format(self.procedure.procedure_number, str(self.as_run_number).zfill(3))

    def get_url(self, external=False):
        return url_for('asrun.view_as_run', procedure_number=self.procedure.procedure_number,
                       as_run_number=self.as_run_number, _external=external)

    def __repr__(self):
        """Represent instance as a unique string."""
        return '<AsRun({id!r},{as_run_number!r})>'.format(id=self.id, as_run_number=self.as_run_number)


as_runs_anomalies = db.Table('as_runs_anomalies',
    Column('as_run_id', db.BigInteger, db.ForeignKey('as_runs.id'), primary_key=True),
    Column('anomaly_id', db.BigInteger, db.ForeignKey('anomalies.id'), primary_key=True)
)

as_runs_approvers = db.Table('as_runs_approvers',
    Column('as_run_id', db.BigInteger, db.ForeignKey('as_runs.id'), primary_key=True),
    Column('approver_id', db.BigInteger, db.ForeignKey('approvers.id'), primary_key=True)
)

as_runs_documents = db.Table('as_runs_documents',
    Column('as_run_id', db.BigInteger, db.ForeignKey('as_runs.id'), primary_key=True),
    Column('document_id', db.BigInteger, db.ForeignKey('documents.id'), primary_key=True)
)

as_runs_images = db.Table('as_runs_images',
    Column('as_run_id', db.BigInteger, db.ForeignKey('as_runs.id'), primary_key=True),
    Column('image_id', db.BigInteger, db.ForeignKey('images.id'), primary_key=True)
)

as_runs_links = db.Table('as_runs_links',
    Column('as_run_id', db.BigInteger, db.ForeignKey('as_runs.id'), primary_key=True),
    Column('link_id', db.BigInteger, db.ForeignKey('links.id'), primary_key=True)
)

as_runs_products = db.Table('as_runs_products',
    Column('as_run_id', db.BigInteger, db.ForeignKey('as_runs.id'), primary_key=True),
    Column('product_id', db.BigInteger, db.ForeignKey('products.id'), primary_key=True)
)

as_runs_vendor_products = db.Table('as_runs_vendor_products',
    Column('as_run_id', db.BigInteger, db.ForeignKey('as_runs.id'), primary_key=True),
    Column('vendor_product_id', db.BigInteger, db.ForeignKey('vendor_products.id'), primary_key=True)
)
