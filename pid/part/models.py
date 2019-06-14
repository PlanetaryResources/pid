# -*- coding: utf-8 -*-
"""Part models."""
from pid.database import Column, Model, SurrogatePK, db, reference_col, relationship
from sqlalchemy.orm import subqueryload, joinedload
from sqlalchemy import and_
from flask import url_for
from pid.models import BaseRecord


class Part(BaseRecord):
    __tablename__ = 'parts'
    part_identifier = Column(db.Integer, nullable=False)
    name = Column(db.String, nullable=True)
    components = relationship('PartComponent', foreign_keys='PartComponent.parent_id')
    current_best_estimate = Column(db.Float, default=0.0, nullable=False)
    uncertainty = Column(db.Float, default=0.0, nullable=False)
    predicted_best_estimate = Column(db.Float, default=0.0, nullable=False)
    design_id = reference_col('designs')
    design = relationship('Design', back_populates='parts')
    material_id = reference_col('materials', nullable=True)
    material = relationship('Material')
    material_specification_id = reference_col('material_specifications', nullable=True)
    material_specification = relationship('MaterialSpecification')
    inseparable_component = Column(db.Boolean, default=False)
    procedures = relationship('Procedure', secondary='procedures_parts')
    __table_args__ = (db.UniqueConstraint('part_identifier', 'design_id', name='part_identifier_design_unique'),)

    def __init__(self, **kwargs):
        super().__init__()
        db.Model.__init__(self, **kwargs)

    @property
    def part_number(self):
        return '{0}-{1}'.format(self.design.design_number, self.part_identifier)

    @property
    def revision(self):
        return self.design.revision

    @classmethod
    def get_all_parts(cls):
        results = cls.query.all()
        return results

    @classmethod
    def typeahead_search(cls, query, part_id):
        query = '%{0}%'.format(query)  # Pad query for an ILIKE search for design_number and
        # Search in parts for design_numbers, part_identifiers or associated design names that match
        # Union with inseparable components for this specific revision of design
        sql_part_ids = '''
            WITH matching_designs AS (
                SELECT d.design_number AS dn, MAX(d.revision) AS rev
                FROM parts p, designs d
                WHERE p.design_id = d.id
                AND (SELECT CONCAT(d.design_number, '-', cast(p.part_identifier as text), ' ', d.name) ILIKE :query)
                GROUP BY d.design_number
            )
            SELECT p.id
            FROM designs d, parts p, matching_designs md
            WHERE p.design_id = d.id
            AND d.design_number = md.dn
            AND d.revision = md.rev
            AND NOT inseparable_component
            UNION
            SELECT p.id
            FROM parts p
            WHERE inseparable_component
            AND design_id = (SELECT design_id FROM parts WHERE id = :part_id)
        '''
        # Get ids of parts belonging to different revs of same design number
        sql_design_number_part_ids = 'SELECT id FROM designs WHERE design_number = (SELECT design_number FROM designs WHERE id = (SELECT design_id FROM parts WHERE id = :part_id))'
        # Get ids of parts belonging to inseparable components for this specific rev of design, EXCEPT
        sql_inseparable_components_part_ids = 'SELECT id FROM parts WHERE inseparable_component AND design_id = (SELECT design_id FROM parts WHERE id = :part_id)'
        # Get ids of parts already added as part component to this part, UNION
        sql_already_added_part_ids = 'SELECT part_id FROM part_components WHERE parent_id = :part_id AND part_id IS NOT NULL'
        # Get ids of parts where this part is an NLA, UNION
        sql_nla_part_ids = 'SELECT parent_id FROM part_components WHERE part_id = :part_id'
        # Use the above selects to get part ids to exclude
        sql_exclude_part_ids = 'SELECT id FROM parts WHERE design_id IN ({0}) EXCEPT {1} UNION {2} UNION {3}'.format(sql_design_number_part_ids, sql_inseparable_components_part_ids, sql_already_added_part_ids, sql_nla_part_ids)
        # Search in parts for matches excluding self and already added parts
        sql = 'SELECT * FROM parts WHERE id != :part_id AND id NOT in ({0}) AND id IN ({1})'.format(sql_exclude_part_ids, sql_part_ids)
        results = db.session.query(cls).from_statement(db.text(sql).params(query=query, part_id=part_id)).all()
        return results

    @classmethod
    def typeahead_search_all_but_self(cls, query, part_id):
        query = '%{0}%'.format(query)  # Pad query for an ILIKE search for design_number and
        # Search in parts for design_numbers, part_identifiers or associated design names that match, excluding self
        sql_part_ids = "SELECT DISTINCT ON (d.design_number, p.part_identifier) p.id FROM parts p, designs d WHERE p.design_id = d.id AND (SELECT CONCAT(d.design_number, '-', cast(p.part_identifier as text), ' ', d.name) ILIKE :query) ORDER BY d.design_number, p.part_identifier, d.revision DESC"
        sql = 'SELECT * FROM parts p WHERE p.id != :part_id AND p.id IN ({0})'.format(sql_part_ids)
        results = db.session.query(cls).from_statement(db.text(sql).params(query=query, part_id=part_id)).all()
        return results

    @classmethod
    def typeahead_search_all(cls, query):
        query = '%{0}%'.format(query)  # Pad query for an ILIKE search for design_number and
        # Search in parts for design_numbers, part_identifiers or associated design names that match
        sql = "SELECT DISTINCT ON (d.design_number, p.part_identifier) p.* FROM parts p, designs d WHERE p.design_id = d.id AND (SELECT CONCAT(d.design_number, '-', cast(p.part_identifier as text), ' ', d.name) ILIKE :query) ORDER BY d.design_number, p.part_identifier, d.revision DESC"
        results = db.session.query(cls).from_statement(db.text(sql).params(query=query)).all()
        return results

    def get_nlas_for_part(self):
        sql_design_ids = 'SELECT DISTINCT ON (design_number) id FROM designs ORDER BY design_number, revision DESC'  # Unique design_number, highest revision
        sql_pc_ids = 'SELECT parent_id FROM part_components WHERE part_id = :part_id'
        sql = 'SELECT * FROM parts WHERE id IN ({0}) AND design_id IN ({1})'.format(sql_pc_ids, sql_design_ids)
        parents = db.session.query(Part).from_statement(db.text(sql).params(part_id=self.id)).all()
        return parents

    def get_products_for_part(self):
        # TODO: Remove this and change to for_design / for_design_number
        from pid.product.models import Product
        results = Product.query.filter_by(part_id=self.id).all()
        return results

    def get_parts_for_design_revisions(self):
        from pid.design.models import Design
        revisions = Design.query.filter_by(design_number=self.design.design_number).all()
        revisions.sort(key=lambda x: (len(x.revision), x.revision))  # Sort them first alphabetically, then by length
        design_ids = [x.id for x in revisions]
        results = Part.query.filter(and_(Part.design_id.in_(design_ids), Part.part_identifier == self.part_identifier)).all()
        return results

    def get_builds_for_design_number_and_part_identifier(self):
        from pid.product.models import Build
        sql = 'SELECT b.* FROM builds b, parts p, designs d WHERE b.part_id = p.id AND p.design_id = d.id AND d.design_number = :design_number AND p.part_identifier = :part_identifier ORDER BY b.build_identifier'
        results = db.session.query(Build).from_statement(db.text(sql).params(design_number=self.design.design_number, part_identifier=self.part_identifier)).all()
        return results

    @classmethod
    def get_nlas_for_vendor_part(cls, vendor_part):
        sql_design_ids = 'SELECT DISTINCT ON (design_number) id FROM designs ORDER BY design_number, revision DESC'  # Unique design_number, highest revision
        sql_pc_ids = 'SELECT parent_id FROM part_components WHERE vendor_part_id = :vendor_part_id'
        sql = 'SELECT * FROM parts WHERE id IN ({0}) AND design_id IN ({1})'.format(sql_pc_ids, sql_design_ids)
        parents = db.session.query(cls).from_statement(db.text(sql).params(vendor_part_id=vendor_part.id)).all()
        return parents

    def add_component(self, part_component):
        self.components.append(part_component)
        db.session.add(self)
        db.session.commit()

    def update_mass(self):
        # %Unc = (PBE/CBE) - 1 (*100)
        sum_cbe = 0.0
        sum_pbe = 0.0
        if self.components:
            for component in self.components:
                if component.part:
                    sum_cbe += (component.part.current_best_estimate * component.quantity)
                    sum_pbe += (component.part.predicted_best_estimate * component.quantity)
                elif component.vendor_part:
                    sum_cbe += (component.vendor_part.current_best_estimate * component.quantity)
                    sum_pbe += (component.vendor_part.predicted_best_estimate * component.quantity)
            if sum_cbe == 0.0:
                unc = 0.0
            else:
                unc = ((sum_pbe / sum_cbe) - 1) * 100
        else:
            sum_cbe = self.current_best_estimate
            unc = self.uncertainty
            sum_pbe = self.predicted_best_estimate
        self.update(current_best_estimate=sum_cbe, uncertainty=unc, predicted_best_estimate=sum_pbe)
        # TODO: In a large tree, this might take a while, should figure out a queue to do this with
        self.update_parents_mass()  # In case there are parts depending on this as a part_component

    def update_parents_mass(self):
        """ Update the mass of all parents of this part. Call this when updating mass of a part """
        part_components = PartComponent.query.filter_by(part=self).all()
        for part_component in part_components:
            part_component.parent.update_mass()

    def can_user_edit(self, field_name):
        return self.design.can_user_edit(field_name)

    def get_name(self):
        if self.name:
            return self.name
        return self.design.name

    def get_unique_identifier(self):
        return self.part_number

    def get_url(self):
        return url_for('design.view_design', design_number=self.design.design_number, revision=self.design.revision)

    def __str__(self):
        return '{0}-{1} {2}'.format(self.design.design_number, self.design.revision, self.part_identifier)

    def __repr__(self):
        """Represent instance as a unique string."""
        return '<Part({0})>'.format(self.part_number)


class PartComponent(SurrogatePK, Model):
    __tablename__ = 'part_components'
    parent_id = reference_col('parts')
    parent = relationship('Part', foreign_keys=[parent_id])
    quantity = Column(db.Integer, nullable=False, default=1)
    part_id = reference_col('parts', nullable=True)
    part = relationship('Part', foreign_keys=[part_id])
    vendor_part_id = reference_col('vendor_parts', nullable=True)
    vendor_part = relationship('VendorPart')
    ordering = Column(db.Integer)

    __mapper_args__ = {
        "order_by": ordering
    }

    def __init__(self, **kwargs):
        """Create instance."""
        lowest_part_component = PartComponent.query.filter_by(parent_id=kwargs['parent_id']).order_by(PartComponent.ordering.desc()).first()
        if lowest_part_component:
            ordering = lowest_part_component.ordering + 1
        else:
            ordering = 0
        db.Model.__init__(self, ordering=ordering, **kwargs)

    @property
    def component(self):
        return self.part if self.part else self.vendor_part

    @classmethod
    def find_highest_free_ordering_plus_one(cls):
        results = db.session.query(db.func.max(cls.ordering)).first()
        if results[0] is None:
            return 1
        return int(results[0]) + 1

    @classmethod
    def get_components_by_part_id(cls, part_id):
        # Ensures part, part.design, and vendor_part references are all loaded
        return cls.query.filter_by(parent_id=part_id).options(subqueryload('part'),
                                           joinedload('part.design'),
                                           subqueryload('vendor_part')).all()  # noqa

    @classmethod
    def update_part_component_references(cls, design):
        """
        for new_part in new_design.parts:
            find old_versions of this new_part
            for part_component in (select part_components where part_id in old_versions):
                part_component.part = new_part
        """
        for part in design.parts:
            sql_design_ids = 'SELECT id FROM designs WHERE design_number = :design_number'
            sql_parts = 'SELECT * FROM parts WHERE part_identifier = :part_identifier AND design_id IN ({0})'.format(sql_design_ids)
            parts = db.session.query(Part).from_statement(db.text(sql_parts).params(design_number=design.design_number, part_identifier=part.part_identifier)).all()
            for old_part in parts:
                sql = 'SELECT * FROM part_components WHERE part_id = :part_id'
                part_components = db.session.query(cls).from_statement(db.text(sql).params(part_id=old_part.id)).all()
                for part_component in part_components:
                    part_component.part = part
                    part_component.save()

    def can_user_edit(self, field_name):
        return self.parent.can_user_edit(field_name)

    def __str__(self):
        if (self.part):
            return '{0} ({1})'.format(self.part.part_number, self.quantity)
        else:
            return '{0} ({1})'.format(self.vendor_part.part_number, self.quantity)

    def __repr__(self):
        """Represent instance as a unique string."""
        return '<PartComponent({0})>'.format(self.id)
