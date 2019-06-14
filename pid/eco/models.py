
from flask import url_for
from pid.database import Column, db, relationship, reference_col
from pid.models import Record
from pid.permissions import ECOPermissions
from pid.utils import format_match_query
from pid.workflows import ECOWorkflow


def get_next_eco_key():
    seq = db.Sequence('eco_key_seq')
    key = "ECO-{0}".format(str(db.session.connection().execute(seq)).zfill(6))
    return key


class ECO(Record):
    __tablename__ = 'ecos'
    descriptor = 'ECO'
    key = Column(db.String, default=get_next_eco_key, nullable=False)
    designs = relationship('Design', secondary='designs_ecos', back_populates='ecos')
    summary = Column(db.String)
    approvers = relationship('Approver', secondary='ecos_approvers', order_by='asc(Approver.id)', backref='eco')
    analysis = Column(db.String)
    corrective_action = Column(db.String)
    documents = relationship('Document', secondary='ecos_documents')
    links = relationship('Link', secondary='ecos_links')
    images = relationship('Image', secondary='ecos_images')
    project_id = reference_col('projects')
    project = relationship('Project')
    workflow = ECOWorkflow()
    state = Column(db.String, default=workflow.initial_state)
    permissions = ECOPermissions()

    __mapper_args__ = {
        "order_by": key
    }

    def __init__(self, **kwargs):
        super().__init__()
        db.Model.__init__(self, **kwargs)

    @classmethod
    def get_by_key(cls, key):
        return cls.query.filter_by(key=key).first()

    @classmethod
    def find_all_ecos_for_user(cls, user):
        results = cls.query.filter_by(owner=user).order_by(cls.key).all()
        return results

    @classmethod
    def typeahead_search(cls, query):
        query = '%{0}%'.format(query)  # Pad query for an ILIKE search
        sql = "SELECT * FROM {0} WHERE (SELECT CONCAT(key, ' ', name) ILIKE :query)".format(cls.__tablename__)
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
                if attr == 'eco_number_query':
                    formatted_query = format_match_query(params['eco_number_query_type'], params['eco_number_query'])
                    query = query.filter(cls.key.ilike(formatted_query))
                elif attr == 'text_fields_query':
                    formatted_query = format_match_query('includes', params['text_fields_query'])
                    query = query.filter(cls.name.ilike(formatted_query) | cls.summary.ilike(formatted_query))
                elif attr == 'created_on_start':
                    query = query.filter(cls.created_at >= params['created_on_start'])
                elif attr == 'created_on_end':
                    query = query.filter(cls.created_at <= params['created_on_end'])
                elif attr == 'in_open_state':
                    query = query.filter(cls.state.in_(cls.workflow.open_states))
                elif attr =='exclude_obsolete':
                    query = query.filter(cls.state != cls.workflow.obsolete_state)
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
        return approval_errors

    def get_unique_identifier(self):
        return self.key

    def get_url(self, external=False):
        return url_for('eco.view_eco', key=self.key, _external=external)

    def __repr__(self):
        """Represent instance as a unique string."""
        return '<ECO({id!r},{key!r})>'.format(id=self.id, key=self.key)


ecos_approvers = db.Table('ecos_approvers',
    Column('eco_id', db.BigInteger, db.ForeignKey('ecos.id'), primary_key=True),
    Column('approver_id', db.BigInteger, db.ForeignKey('approvers.id'), primary_key=True)
)

ecos_documents = db.Table('ecos_documents',
    Column('eco_id', db.BigInteger, db.ForeignKey('ecos.id'), primary_key=True),
    Column('document_id', db.BigInteger, db.ForeignKey('documents.id'), primary_key=True)
)

ecos_images = db.Table('ecos_images',
    Column('eco_id', db.BigInteger, db.ForeignKey('ecos.id'), primary_key=True),
    Column('image_id', db.BigInteger, db.ForeignKey('images.id'), primary_key=True)
)

ecos_links = db.Table('ecos_links',
    Column('eco_id', db.BigInteger, db.ForeignKey('ecos.id'), primary_key=True),
    Column('link_id', db.BigInteger, db.ForeignKey('links.id'), primary_key=True)
)
