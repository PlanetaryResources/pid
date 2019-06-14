from flask import url_for
from pid.database import Column, db, relationship
import pid.utils as Utils
from pid.common.models import Reference
from pid.models import RevisionRecord
from pid.permissions import SpecificationPermissions
from pid.workflows import ProcedureWorkflow


def get_next_specification_number():
    seq = db.Sequence('specification_number_seq')
    key = "PRI-{0}".format(str(db.session.connection().execute(seq)).zfill(5))
    return key


class Specification(RevisionRecord):
    __tablename__ = 'specifications'
    descriptor = 'Specification'
    specification_number = Column(db.String, default=get_next_specification_number, nullable=False)
    scope = Column(db.String)
    summary = Column(db.String)
    approvers = relationship('Approver', secondary='specifications_approvers',
                             order_by='asc(Approver.id)', backref='specification')
    documents = relationship('Document', secondary='specifications_documents')
    links = relationship('Link', secondary='specifications_links')
    images = relationship('Image', secondary='specifications_images')
    workflow = ProcedureWorkflow()
    state = Column(db.String, default=workflow.initial_state)
    permissions = SpecificationPermissions()
    __table_args__ = (db.UniqueConstraint('specification_number', 'revision',
                      name='specification_number_revision_unique'),)

    __mapper_args__ = {
        "order_by": specification_number
    }

    def __init__(self, **kwargs):
        super().__init__()
        db.Model.__init__(self, **kwargs)

    @property
    def references_by(self):
        # Override base method due to revisions
        sql_revision_ids = 'SELECT id FROM specifications WHERE specification_number = :specification_number ORDER BY revision'
        sql = 'SELECT * FROM "references" WHERE to_id IN ({0}) AND to_class = :class_name'.format(sql_revision_ids)
        query_results = db.session.query(Reference).from_statement(db.text(sql).params(specification_number=self.specification_number, class_name=self.get_class_name())).all()
        results = {r.get_url_by(): r for r in query_results}.values()
        return results

    @classmethod
    def get_by_specification_number(cls, specification_number):
        return cls.query.filter_by(specification_number=specification_number).first()

    @classmethod
    def get_by_specification_number_and_revision(cls, specification_number, revision):
        return cls.query.filter_by(specification_number=specification_number, revision=revision).first()

    @classmethod
    def find_all_specifications_for_user(cls, user):
        results = cls.query.filter_by(owner=user).order_by(cls.number).all()
        return results

    @classmethod
    def find_all_distinct_specifications(cls):
        results = cls.query.distinct(cls.specification_number).order_by(cls.specification_number, cls.revision.desc()).all()
        return results

    @classmethod
    def typeahead_search(cls, query):
        query = '%{0}%'.format(query)  # Pad query for an ILIKE search
        sql = "SELECT DISTINCT ON (specification_number) * FROM {0} WHERE (SELECT CONCAT(specification_number, ' ', name) ILIKE :query) ORDER BY specification_number, revision DESC".format(cls.__tablename__)
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
                if attr == 'spec_number_match':
                    formatted_query = Utils.format_match_query(params['spec_number_match_type'], params['spec_number_match'])
                    query = query.filter(cls.specification_number.ilike(formatted_query))
                elif attr == 'text_fields_query':
                    formatted_query = Utils.format_match_query('includes', params['text_fields_query'])
                    query = query.filter(cls.name.ilike(formatted_query) | cls.scope.ilike(formatted_query) |
                                         cls.summary.ilike(formatted_query))
                elif attr == 'created_on_start':
                    query = query.filter(cls.created_at >= params['created_on_start'])
                elif attr == 'created_on_end':
                    query = query.filter(cls.created_at <= params['created_on_end'])
                elif attr == 'in_open_state':
                    query = query.filter(cls.state.in_(cls.workflow.open_states))
                elif attr =='exclude_obsolete':
                    query = query.filter(cls.state != cls.workflow.obsolete_state)
        return query.distinct(cls.specification_number).order_by(cls.specification_number.desc(), cls.revision.desc()).all()

    def find_all_revisions(self):
        results = Specification.query.filter_by(specification_number=self.specification_number).all()
        return Utils.find_all_revisions(results)

    def find_latest_revision(self):
        results = Specification.query.with_entities(Specification.revision).filter_by(specification_number=self.specification_number).all()
        return Utils.find_latest_revision(results)

    def find_next_revision(self):
        results = Specification.query.with_entities(Specification.revision).filter_by(specification_number=self.specification_number).order_by(Specification.revision).all()
        return Utils.find_next_revision(results)

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
        return self.specification_number

    def get_latest_revision_url(self):
        # BEWARE: This function will always point to latest revision of design
        return url_for('specification.view_specification', specification_number=self.specification_number, revision=self.find_latest_revision())

    def get_unique_identifier(self):
        return self.specification_number

    def get_url(self, external=False):
        return url_for('specification.view_specification', specification_number=self.specification_number,
                       revision=self.revision, _external=external)

    def __repr__(self):
        """Represent instance as a unique string."""
        return '<Specification({id!r},{specification_number!r})>'.format(id=self.id, specification_number=self.specification_number)


specifications_approvers = db.Table('specifications_approvers',
    Column('specification_id', db.BigInteger, db.ForeignKey('specifications.id'), primary_key=True),
    Column('approver_id', db.BigInteger, db.ForeignKey('approvers.id'), primary_key=True)
)

specifications_documents = db.Table('specifications_documents',
    Column('specification_id', db.BigInteger, db.ForeignKey('specifications.id'), primary_key=True),
    Column('document_id', db.BigInteger, db.ForeignKey('documents.id'), primary_key=True)
)

specifications_images = db.Table('specifications_images',
    Column('specification_id', db.BigInteger, db.ForeignKey('specifications.id'), primary_key=True),
    Column('image_id', db.BigInteger, db.ForeignKey('images.id'), primary_key=True)
)

specifications_links = db.Table('specifications_links',
    Column('specification_id', db.BigInteger, db.ForeignKey('specifications.id'), primary_key=True),
    Column('link_id', db.BigInteger, db.ForeignKey('links.id'), primary_key=True)
)
