# -*- coding: utf-8 -*-
"""Design models."""
from flask import url_for
from pid.database import Column, db, reference_col, relationship
from pid.models import RevisionRecord
from collections import defaultdict
from string import ascii_uppercase as AUC
from itertools import product
from pid.common.models import Reference
from pid.globals import FORBIDDEN_REVISIONS
from pid.permissions import DesignPermissions
from pid.utils import format_match_query
from pid.workflows import DesignWorkflow


class Design(RevisionRecord):
    __tablename__ = 'designs'
    descriptor = 'Design'
    design_number = Column(db.String, nullable=False)
    summary = Column(db.String)
    notes = Column(db.Text)
    documents = relationship('Document', secondary='designs_documents')
    anomalies = relationship('Anomaly', secondary='designs_anomalies',
                             order_by='desc(Anomaly.created_at)', back_populates='designs')
    ecos = relationship('ECO', secondary='designs_ecos', order_by='desc(ECO.created_at)', back_populates='designs')
    approvers = relationship('Approver', secondary='designs_approvers', order_by='asc(Approver.id)', backref='design')
    project_id = reference_col('projects')
    project = relationship('Project')
    parts = relationship('Part', back_populates='design', order_by="Part.part_identifier")
    links = relationship('Link', secondary='designs_links')
    images = relationship('Image', secondary='designs_images')
    export_control = Column(db.Boolean(), default=False)
    workflow = DesignWorkflow()
    state = Column(db.String, default=workflow.initial_state)
    permissions = DesignPermissions()
    __table_args__ = (db.UniqueConstraint('design_number', 'revision', name='design_number_revision_unique'),)

    __mapper_args__ = {
        "order_by": design_number
    }

    def __init__(self, **kwargs):
        super().__init__()
        db.Model.__init__(self, **kwargs)

    @property
    def references_by(self):
        # Override base method due to revisions
        sql_revision_ids = 'SELECT id FROM designs WHERE design_number = :design_number ORDER BY revision'
        sql = 'SELECT * FROM "references" WHERE to_id IN ({0}) AND to_class = :class_name'.format(sql_revision_ids)
        query_results = db.session.query(Reference).from_statement(db.text(sql).params(design_number=self.design_number, class_name=self.get_class_name())).all()
        results = {r.get_url_by(): r for r in query_results}.values()
        return results

    @classmethod
    def find_all_design_numbers(cls):
        results = cls.query.with_entities(cls.design_number).order_by(cls.design_number.asc()).distinct().all()
        resultset = [int(row[0]) for row in results]
        return resultset

    @classmethod
    def find_all_designs_for_user(cls, user):
        results = cls.query.filter_by(owner=user).distinct(cls.design_number).order_by(cls.design_number, cls.revision.desc()).all()
        return results

    @classmethod
    def get_by_design_number_and_revision(cls, design_number, revision):
        return cls.query.filter_by(design_number=design_number, revision=revision).first()

    @classmethod
    def typeahead_search(cls, query):
        query = '%{0}%'.format(query)  # Pad query for an ILIKE search
        sql = "SELECT DISTINCT ON (design_number) * FROM {0} WHERE (SELECT CONCAT(design_number, ' ', name) ILIKE :query) ORDER BY design_number, revision DESC".format(cls.__tablename__)
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
                if attr == 'design_number_query':
                    formatted_query = format_match_query(params['design_number_query_type'], params['design_number_query'])
                    query = query.filter(cls.design_number.ilike(formatted_query))
                elif attr == 'text_fields_query':
                    formatted_query = format_match_query('includes', params['text_fields_query'])
                    query = query.filter(cls.name.ilike(formatted_query) | cls.notes.ilike(formatted_query) |
                                         cls.summary.ilike(formatted_query))
                elif attr == 'open_anomalies':
                    from pid.anomaly.models import Anomaly
                    query = query.filter(cls.anomalies.any(Anomaly.state.in_(Anomaly.workflow.open_states)))
                elif attr == 'open_ecos':
                    from pid.eco.models import ECO
                    query = query.filter(cls.ecos.any(ECO.state.in_(ECO.workflow.open_states)))
                elif attr == 'created_on_start':
                    query = query.filter(cls.created_at >= params['created_on_start'])
                elif attr == 'created_on_end':
                    query = query.filter(cls.created_at <= params['created_on_end'])
                elif attr == 'in_open_state':
                    query = query.filter(cls.state.in_(cls.workflow.open_states))
                elif attr =='exclude_obsolete':
                    query = query.filter(cls.state != cls.workflow.obsolete_state)
                elif attr == 'material_id':
                    from pid.part.models import Part
                    query = query.filter(cls.parts.any(Part.material_id == params['material_id']))
        if 'open_anomalies' not in params and 'open_ecos' not in params:
            query = query.distinct(cls.design_number)
        return query.order_by(cls.design_number.desc(), cls.revision.desc()).all()

    def find_all_revisions(self):
        results = Design.query.filter_by(design_number=self.design_number).all()
        # Sort them first alphabetically, then by length
        results.sort(key=lambda x: (len(x.revision), x.revision))
        return results

    def find_latest_revision(self):
        results = Design.query.with_entities(Design.revision).filter_by(design_number=self.design_number).all()
        # Sort them first alphabetically, then by length, in reverse. First element will have the highest revision.
        resultset = [row[0] for row in results]
        resultset.sort(key=lambda x: (len(x), x), reverse=True)
        return resultset[0]

    def find_next_revision(self):
        # Doing separate lists that we then concat, due to sorting issues
        all_possible_single_revisions = []
        all_possible_double_revisions = []
        # See: https://stackoverflow.com/questions/23686398/iterate-a-to-zzz-in-python
        for chars in AUC:
            all_possible_single_revisions.append(''.join(chars))
        for chars in product(AUC, repeat=2):
            all_possible_double_revisions.append(''.join(chars))
        results = Design.query.with_entities(Design.revision).filter_by(design_number=self.design_number).order_by(Design.revision).all()
        used_revisions = [str(row[0]) for row in results]
        free_single_revisions = list(set(all_possible_single_revisions) - set(used_revisions) - set(FORBIDDEN_REVISIONS))
        free_double_revisions = list(set(all_possible_double_revisions) - set(used_revisions))
        return (sorted(free_single_revisions) + sorted(free_double_revisions))[0]

    def find_next_part_number(self):
        # https://stackoverflow.com/a/16974075
        part_numbers = [int(part.part_identifier) for part in self.parts]
        difference = sorted(set(range(part_numbers[0], part_numbers[-1] + 1)).difference(part_numbers))
        next_part_number = difference[0] if difference else part_numbers[-1] + 1
        return next_part_number

    def find_next_inseparable_part_number(self):
        part_numbers = [int(part.part_identifier) for part in self.parts]
        start = part_numbers[0] if part_numbers[0] > 100 else 101
        end = part_numbers[-1] if part_numbers[-1] > 100 else 102
        difference = sorted(set(range(start, end)).difference(part_numbers))
        next_part_number = difference[0] if difference else part_numbers[-1] + 1
        return next_part_number

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
        # Check if open ecos
        for eco in self.ecos:
            if eco.is_open():
                approval_errors.append('{0} must be resolved.'.format(eco.get_unique_identifier()))
        return approval_errors

    def get_procedures(self):
        return self.get_all_procedures()

    def get_all_procedures(self):
        from pid.procedure.models import Procedure
        procedures = []
        for part in self.parts:
            part_procedures = defaultdict(str)
            for procedure in part.procedures:
                if part_procedures[procedure.procedure_number] < procedure.revision:
                    part_procedures[procedure.procedure_number] = procedure.revision
            for key, value in part_procedures.items():
                procedures.append(Procedure.get_by_procedure_number_and_revision(key, value))
        procedures.sort(key=lambda x: x.created_at, reverse=True)  # Sort by newest first
        return procedures

    def as_dict(self):
        return {
            'id': self.id,
            'design_number': self.design_number,
            'revision': self.revision,
            'url': self.get_url()
        }

    def get_latest_revision_unique_identifier(self):
        return '{0}-{1}'.format(self.design_number, self.find_latest_revision())

    def get_latest_revision_url(self):
        # BEWARE: This function will always point to latest revision of design
        return url_for('design.view_design', design_number=self.design_number, revision=self.find_latest_revision())

    def get_unique_identifier(self):
        return '{0}-{1}'.format(self.design_number, self.revision)

    def get_url(self, external=False):
        return url_for('design.view_design', design_number=self.design_number,
                       revision=self.revision, _external=external)

    def __str__(self):
        return '{0}-{1}'.format(self.design_number, self.revision)

    def __repr__(self):
        """Represent instance as a unique string."""
        return '<Design({0} {1})>'.format(self.design_number, self.revision)


designs_anomalies = db.Table('designs_anomalies',
    Column('design_id', db.BigInteger, db.ForeignKey('designs.id'), primary_key=True),
    Column('anomaly_id', db.BigInteger, db.ForeignKey('anomalies.id'), primary_key=True)
)

designs_approvers = db.Table('designs_approvers',
    Column('design_id', db.BigInteger, db.ForeignKey('designs.id'), primary_key=True),
    Column('approver_id', db.BigInteger, db.ForeignKey('approvers.id'), primary_key=True)
)

designs_documents = db.Table('designs_documents',
    Column('design_id', db.BigInteger, db.ForeignKey('designs.id'), primary_key=True),
    Column('document_id', db.BigInteger, db.ForeignKey('documents.id'), primary_key=True)
)

designs_ecos = db.Table('designs_ecos',
    Column('design_id', db.BigInteger, db.ForeignKey('designs.id'), primary_key=True),
    Column('eco_id', db.BigInteger, db.ForeignKey('ecos.id'), primary_key=True)
)

designs_images = db.Table('designs_images',
    Column('design_id', db.BigInteger, db.ForeignKey('designs.id'), primary_key=True),
    Column('image_id', db.BigInteger, db.ForeignKey('images.id'), primary_key=True)
)

designs_links = db.Table('designs_links',
    Column('design_id', db.BigInteger, db.ForeignKey('designs.id'), primary_key=True),
    Column('link_id', db.BigInteger, db.ForeignKey('links.id'), primary_key=True)
)
