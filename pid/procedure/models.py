
from flask import url_for
from pid.database import Column, db, relationship, reference_col
import pid.utils as Utils
from pid.common.models import Reference
from pid.workflows import ProcedureWorkflow
from pid.permissions import ProcedurePermissions
from pid.models import RevisionRecord


def get_next_procedure_number():
    seq = db.Sequence('procedure_number_seq')
    key = "DOC-{0}".format(str(db.session.connection().execute(seq)).zfill(6))
    return key


class Procedure(RevisionRecord):
    __tablename__ = 'procedures'
    descriptor = 'Procedure'
    procedure_number = Column(db.String, default=get_next_procedure_number, nullable=False)
    summary = Column(db.String)
    approvers = relationship('Approver', secondary='procedures_approvers',
                             order_by='asc(Approver.id)', backref='procedure')
    parts = relationship('Part', secondary='procedures_parts')
    vendor_parts = relationship('VendorPart', secondary='procedures_vendor_parts')
    documents = relationship('Document', secondary='procedures_documents')
    links = relationship('Link', secondary='procedures_links')
    images = relationship('Image', secondary='procedures_images')
    as_runs = relationship('AsRun', back_populates='procedure')
    project_id = reference_col('projects')
    project = relationship('Project')
    workflow = ProcedureWorkflow()
    state = Column(db.String, default=workflow.initial_state)
    permissions = ProcedurePermissions()
    __table_args__ = (db.UniqueConstraint('procedure_number', 'revision', name='procedure_number_revision_unique'),)

    __mapper_args__ = {
        "order_by": procedure_number
    }

    def __init__(self, **kwargs):
        super().__init__()
        db.Model.__init__(self, **kwargs)

    @property
    def identifier(self):
        return '{0}-{1}'.format(self.procedure_number, self.revision)

    @property
    def references_by(self):
        # Override base method due to revisions
        sql_revision_ids = 'SELECT id FROM procedures WHERE procedure_number = :procedure_number ORDER BY revision'
        sql = 'SELECT * FROM "references" WHERE to_id IN ({0}) AND to_class = :class_name'.format(sql_revision_ids)
        query_results = db.session.query(Reference).from_statement(db.text(sql).params(procedure_number=self.procedure_number, class_name=self.get_class_name())).all()
        results = {r.get_url_by(): r for r in query_results}.values()
        return results

    @classmethod
    def get_by_procedure_number(cls, procedure_number):
        return cls.query.filter_by(procedure_number=procedure_number).first()

    @classmethod
    def get_by_procedure_number_and_revision(cls, procedure_number, revision):
        return cls.query.filter_by(procedure_number=procedure_number, revision=revision).first()

    @classmethod
    def find_all_procedures_for_user(cls, user):
        results = cls.query.filter_by(owner=user).order_by(cls.procedure_number).all()
        return results

    @classmethod
    def find_all_distinct_procedures_for_user(cls, user):
        results = cls.query.filter_by(owner=user).distinct(cls.procedure_number).order_by(cls.procedure_number, cls.revision.desc()).all()
        return results

    @classmethod
    def typeahead_search(cls, query):
        query = '%{0}%'.format(query)  # Pad query for an ILIKE search
        sql = "SELECT DISTINCT ON (procedure_number) * FROM {0} WHERE (SELECT CONCAT(procedure_number, ' ', name) ILIKE :query) ORDER BY procedure_number, revision DESC".format(cls.__tablename__)
        results = db.session.query(cls).from_statement(db.text(sql).params(query=query)).all()
        return results

    @classmethod
    def advanced_search(cls, params):
        from pid.part.models import Part
        from pid.design.models import Design
        from pid.vendorpart.models import VendorPart
        query = cls.query
        columns = cls.__table__.columns.keys()
        for attr in params:
            if params[attr] != "" and attr in columns:
                query = query.filter(getattr(cls, attr) == params[attr])
            elif params[attr] != "":
                if attr == 'proc_number_query':
                    formatted_query = Utils.format_match_query(params['proc_number_query_type'], params['proc_number_query'])
                    query = query.filter(cls.procedure_number.ilike(formatted_query))
                elif attr == 'part_number_query':
                    formatted_query = Utils.format_match_query(params['part_number_query_type'], params['part_number_query'])
                    query = query.filter(cls.parts.any(Part.design.has(Design.design_number.ilike(formatted_query))) |
                                         cls.vendor_parts.any(VendorPart.part_number.ilike(formatted_query)))
                elif attr == 'text_fields_query':
                    formatted_query = Utils.format_match_query('includes', params['text_fields_query'])
                    query = query.filter(cls.name.ilike(formatted_query) | cls.summary.ilike(formatted_query))
                elif attr == 'created_on_start':
                    query = query.filter(cls.created_at >= params['created_on_start'])
                elif attr == 'created_on_end':
                    query = query.filter(cls.created_at <= params['created_on_end'])
                elif attr == 'in_open_state':
                    query = query.filter(cls.state.in_(cls.workflow.open_states))
                elif attr =='exclude_obsolete':
                    query = query.filter(cls.state != cls.workflow.obsolete_state)
        return query.distinct(cls.procedure_number).order_by(cls.procedure_number.desc(), cls.revision.desc()).all()

    def find_all_revisions(self):
        results = Procedure.query.filter_by(procedure_number=self.procedure_number).all()
        return Utils.find_all_revisions(results)

    def find_latest_revision(self):
        results = Procedure.query.with_entities(Procedure.revision).filter_by(procedure_number=self.procedure_number).all()
        return Utils.find_latest_revision(results)

    def find_next_revision(self):
        results = Procedure.query.with_entities(Procedure.revision).filter_by(procedure_number=self.procedure_number).order_by(Procedure.revision).all()
        return Utils.find_next_revision(results)

    def find_all_as_runs_numbers(self):
        from pid.asrun.models import AsRun
        as_runs = AsRun.query.filter_by(procedure_number=self.procedure_number).all()
        as_run_numbers = []
        for as_run in as_runs:
            as_run_numbers.append({'id': as_run.id, 'number': str(as_run.as_run_number).zfill(3)})
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
        return approval_errors

    def get_latest_revision_unique_identifier(self):
        return '{0}-{1}'.format(self.procedure_number, self.find_latest_revision())

    def get_latest_revision_url(self):
        # BEWARE: This function will always point to latest revision of design
        return url_for('procedure.view_procedure', procedure_number=self.procedure_number, revision=self.find_latest_revision())

    def get_unique_identifier(self):
        return '{0}-{1}'.format(self.procedure_number, self.revision)

    def get_url(self, external=False):
        return url_for('procedure.view_procedure', procedure_number=self.procedure_number,
                       revision=self.revision, _external=external)

    def find_all_as_runs(self):
        from pid.asrun.models import AsRun
        return AsRun.query.filter_by(procedure_number=self.procedure_number).all()

    def __repr__(self):
        """Represent instance as a unique string."""
        return '<Procedure({id!r},{procedure_number!r})>'.format(id=self.id, procedure_number=self.procedure_number)


procedures_approvers = db.Table('procedures_approvers',
    Column('procedure_id', db.BigInteger, db.ForeignKey('procedures.id'), primary_key=True),
    Column('approver_id', db.BigInteger, db.ForeignKey('approvers.id'), primary_key=True)
)

procedures_documents = db.Table('procedures_documents',
    Column('procedure_id', db.BigInteger, db.ForeignKey('procedures.id'), primary_key=True),
    Column('document_id', db.BigInteger, db.ForeignKey('documents.id'), primary_key=True)
)

procedures_images = db.Table('procedures_images',
    Column('procedure_id', db.BigInteger, db.ForeignKey('procedures.id'), primary_key=True),
    Column('image_id', db.BigInteger, db.ForeignKey('images.id'), primary_key=True)
)

procedures_links = db.Table('procedures_links',
    Column('procedure_id', db.BigInteger, db.ForeignKey('procedures.id'), primary_key=True),
    Column('link_id', db.BigInteger, db.ForeignKey('links.id'), primary_key=True)
)

procedures_parts = db.Table('procedures_parts',
    Column('procedure_id', db.BigInteger, db.ForeignKey('procedures.id'), primary_key=True),
    Column('part_id', db.BigInteger, db.ForeignKey('parts.id'), primary_key=True)
)

procedures_vendor_parts = db.Table('procedures_vendor_parts',
    Column('procedure_id', db.BigInteger, db.ForeignKey('procedures.id'), primary_key=True),
    Column('vendor_part_id', db.BigInteger, db.ForeignKey('vendor_parts.id'), primary_key=True)
)
