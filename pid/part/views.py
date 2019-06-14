# -*- coding: utf-8 -*-
"""Design views."""
from flask import Blueprint, request, jsonify, render_template, make_response
from flask_login import login_required
from .models import Part, PartComponent
from .forms import CreatePartForm
from pid.common.models import Material, MaterialSpecification
from pid.design.models import Design
from flask_login import current_user

blueprint = Blueprint('part', __name__, url_prefix='/part', static_folder='../static')


@blueprint.route('/update', methods=['POST'])
@login_required
def update_part():
    # TODO: Check that field should actually be allowed to change.
    id = request.form['pk']
    # UID for field will be ala [fieldname]-[classname]-[id]-editable, field name will be first section always
    field = request.form['name'].split('-')[0]
    field_value = request.form['value']
    original_value = None
    # TODO: Check if part exists
    part = Part.get_by_id(id)

    if field == 'name':
        original_value = part.get_name()
        part.update(name=field_value)
    elif field == 'material':
        original_material = None
        original_material_spec = None
        if part.material:
            original_material = part.material.name
        if part.material_specification:
            original_material_spec = part.material_specification.name
        material = Material.get_by_id(field_value)
        part.update(material=material, material_specification=None)  # To ensure we don't have a mat_spec linked with old material
        material_name = None
        if material:
            material_name = material.name
        part.add_change_log_entry(action='Edit', field='Material', original_value=original_material,
                                  new_value=material_name)
        if original_material_spec:
            part.add_change_log_entry(action='Edit', field='Material Specification',
                                      original_value=original_material_spec)
        variables = {'part': part}
        return render_template('part/ajax_select_material_specification.html', **variables)
    elif field == 'material_specification':
        if part.material_specification:
            original_value = part.material_specification.name
        material_specification = MaterialSpecification.get_by_id(field_value)
        part.update(material_specification=material_specification)
        field_value = material_specification.name if material_specification else None
    # Will only be run on parts with no components
    elif field == 'current_best_estimate':
        original_cbe = part.current_best_estimate
        original_pbe = part.predicted_best_estimate
        current_best_estimate = float(field_value)
        predicted_best_estimate = current_best_estimate * (1 + (part.uncertainty / 100))  # PBE = CBE * (1+%Unc)
        part.update(current_best_estimate=current_best_estimate, predicted_best_estimate=predicted_best_estimate)
        part.update_parents_mass()  # Updates parts where this is a component
        part.add_change_log_entry(action='Edit', field='Current Best Estimate', original_value=original_cbe,
                                  new_value=current_best_estimate)
        part.add_change_log_entry(action='Edit', field='Predicted Best Estimate', original_value=original_pbe,
                                  new_value=predicted_best_estimate)
        return render_template('part/mass_fields.html', part=part)
    # Will only be run on parts with no components
    elif field == 'uncertainty':
        original_uncertainty = part.uncertainty
        original_pbe = part.predicted_best_estimate
        uncertainty = float(field_value)
        predicted_best_estimate = part.current_best_estimate * (1 + (uncertainty / 100))
        part.update(uncertainty=uncertainty, predicted_best_estimate=predicted_best_estimate)
        part.update_parents_mass()  # Updates parts where this is a component
        part.add_change_log_entry(action='Edit', field='Uncertainty', original_value=original_uncertainty,
                                  new_value=uncertainty)
        part.add_change_log_entry(action='Edit', field='Predicted Best Estimate', original_value=original_pbe,
                                  new_value=predicted_best_estimate)
        return render_template('part/mass_fields.html', part=part)

    part.add_change_log_entry(action='Edit', field=field.title().replace('_', ' '), original_value=original_value,
                              new_value=field_value)

    return jsonify({'success': True}), 200, {'ContentType': 'application/json'}


@blueprint.route('/update_part_component', methods=['POST'])
@login_required
def update_part_component():
    # TODO: Check that field should actually be allowed to change.
    id = request.form['pk']
    # UID for field will be ala [fieldname]-[classname]-[id]-editable, field name will be first section always
    field = request.form['name'].split('-')[0]
    field_value = request.form['value']
    # TODO: Check if part exists
    part_component = PartComponent.get_by_id(id)
    if field == 'quantity':
        parent = part_component.parent
        component = part_component.component
        try:
            if int(field_value) == 0:  # Delete the entry if quantity is set to 0
                # TODO: Prevent delete if part/design is released.
                parent.add_change_log_entry(action='Remove', field='Component',
                                            original_value=component.get_descriptive_url())
                part_component.delete()
                parent.update_mass()
            else:
                old_value = '{0} - Quantity: {1}'.format(component.get_descriptive_url(), part_component.quantity)
                new_value = '{0} - Quantity: {1}'.format(component.get_descriptive_url(), field_value)
                part_component.update(quantity=field_value)
                parent.update_mass()
                parent.add_change_log_entry(action='Edit', field='Component', original_value=old_value,
                                            new_value=new_value)
        except ValueError:
            return 'Please enter a number.', 500, {'ContentType': 'application/json'}
    elif field == 'reorder':
        components = part_component.parent.components
        current_index = components.index(part_component)
        if field_value == 'up':
            if current_index == 0:
                new_index = 0
            else:
                new_index = current_index - 1
        elif field_value == 'down':
            if current_index == (len(components) - 1):
                new_index = len(components) - 1
            else:
                new_index = current_index + 1
        components[current_index], components[new_index] = components[new_index], components[current_index]
        for i, component in enumerate(components):
            component.update(ordering=i)
        return render_template('part/view_part_components.html', part=part_component.parent)
    return jsonify({'success': True}), 200, {'ContentType': 'application/json'}


@blueprint.route('/delete_part_component', methods=['POST'])
@login_required
def delete_part_component():
    # TODO: Prevent delete if part/design is released.
    id = request.form['pk']
    part_component = PartComponent.get_by_id(id)
    parent = part_component.parent
    component = part_component.component
    parent.add_change_log_entry(action='Remove', field='Component', original_value=component.get_descriptive_url())
    part_component.delete()
    parent.update_mass()
    # Reorder remaining part_compoments if any
    ordering = 1
    for part_component in parent.components:
        part_component.update(ordering=ordering)
        ordering += 1
    return jsonify({'success': True}), 200, {'ContentType': 'application/json'}


@blueprint.route('/create_part', methods=['POST'])
@login_required
def create_part():
    type = request.form.get('part_type')
    form = CreatePartForm(request.form)
    validated = form.validate_on_submit()

    design_id = request.form['design_id']
    design = Design.get_by_id(design_id)

    if validated:
        variables = {
            'design': design,
            'part_identifier': form.part_identifier.data,
            'owner': design.owner,
            'name': form.name.data if not design.name == form.name.data else None
        }
        if type == 'inseparable':
            variables['inseparable_component'] = True
        part = Part.create(**variables)
        materials = Material.query.all()
        variables = {
            'part': part,
            'materials': materials
        }
        return render_template('part/view_part.html', **variables)
    else:
        if type == 'inseparable':
            next_part_number = design.find_next_inseparable_part_number()
        else:
            next_part_number = design.find_next_part_number()
        variables = {
            'design': design,
            'next_part_number': next_part_number,
            'form': form,
            'type': type
        }
        return make_response(render_template('part/create_part.html', **variables), 500)


@blueprint.route('/typeahead_search_parts', methods=['GET'])
@login_required
def typeahead_search_parts():
    query = request.args.get('query')
    part_id = request.args.get('part_id')
    search_type = request.args.get('search_type')
    if search_type == 'part_component':
        parts = Part.typeahead_search(query, part_id)
    elif search_type == 'product_component':
        parts = Part.typeahead_search_all_but_self(query, part_id)
    else:
        parts = Part.typeahead_search_all(query)
    results = []
    for part in parts:
        part_dict = {}
        part_dict['icon'] = '<i class="pri-typeahead-icon pri-icons-record-design" aria-hidden="true"></i>'
        part_dict['id'] = part.id
        part_dict['number'] = part.part_number
        part_dict['name'] = part.get_name()
        part_dict['state'] = part.design.state
        part_dict['thumb_url'] = part.design.get_thumbnail_url()
        part_dict['table'] = 'designs' if part.design else 'vendor_parts'
        part_dict['class'] = part.get_class_name()
        results.append(part_dict)
    return jsonify({'success': True, 'parts': results}), 200, {'ContentType': 'application/json'}


@blueprint.route('/add_component', methods=['POST'])
@login_required
def add_component():
    # TODO: Check if part exists
    part_id = request.form.get('part_id')
    record_id = request.form.get('record_id')
    record_class = request.form.get('record_class')
    part = Part.get_by_id(part_id)
    part_component = None
    if record_class == 'part':
        part_component = PartComponent.create(parent_id=part_id, part_id=record_id)
    elif record_class == 'vendorpart':
        part_component = PartComponent.create(parent_id=part_id, vendor_part_id=record_id)
    # Remove material information after adding a component, if there
    part.material = None
    part.material_specification = None
    component = part_component.component
    part.add_change_log_entry(action='Add', field='Component', new_value=component.get_descriptive_url())
    # No need to update here, updating mass will save part
    part.update_mass()
    variables = {'part_component': part_component}
    return render_template('part/view_part_component.html', **variables)


@blueprint.route('/update_mass', methods=['POST'])
@login_required
def update_mass():
    id = request.form['part_id']
    part = Part.get_by_id(id)
    # part.update_mass()  # This should've already been done by functions where values are updated
    variables = {'part': part}
    return render_template('part/mass_fields.html', **variables)


@blueprint.route('/get_view_nlas_modal', methods=['POST'])
@login_required
def get_view_nlas_modal():
    part_id = request.form.get('part_id')
    part = Part.get_by_id(part_id)
    parents = part.get_nlas_for_part()
    variables = {
        'part': part,
        'parents': parents
    }
    return render_template('part/view_nlas_modal.html', **variables)


@blueprint.route('/get_view_builds_modal', methods=['POST'])
@login_required
def get_view_builds_modal():
    part_id = request.form.get('part_id')
    part = Part.get_by_id(part_id)
    builds = part.get_builds_for_design_number_and_part_identifier()
    variables = {'builds': builds}
    return render_template('part/view_builds_modal.html', **variables)


@blueprint.route('/get_add_component_modal', methods=['POST'])
@login_required
def get_add_component_modal():
    part_id = request.form.get('part_id')
    part = Part.get_by_id(part_id)
    variables = {'part': part}
    return render_template('part/add_part_component_modal.html', **variables)


@blueprint.route('/reload_material_fields', methods=['POST'])
@login_required
def reload_material_fields():
    id = request.form['part_id']
    part = Part.get_by_id(id)
    materials = Material.query.all()
    variables = {
        'part': part,
        'materials': materials
    }
    return render_template('part/material_fields.html', **variables)


@blueprint.route('/<int:id>/design_list', methods=['GET'])
@login_required
def get_design_list(id):
    part = Part.get_by_id(id)
    variables = {
        'part': part,
        'components': PartComponent.get_components_by_part_id(part.id),
        'PartComponent': PartComponent
    }
    return render_template('part/design_list.html', **variables)


@blueprint.route('/get_create_modal', methods=['POST'])
@login_required
def get_create_part_modal():
    design_id = request.form.get('design_id')
    part_type = request.form.get('part_type')
    form = CreatePartForm(request.form)
    design = Design.get_by_id(design_id)
    next_part_number = design.find_next_inseparable_part_number() if part_type == 'inseparable' else design.find_next_part_number()

    variables = {
        'design': design,
        'next_part_number': next_part_number,
        'form': form,
        'type': part_type
    }
    return render_template('part/create_part.html', **variables)
