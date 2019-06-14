# -*- coding: utf-8 -*-
"""VendorPart views."""
from flask import Blueprint, render_template, request, jsonify, make_response
from flask_login import login_required, current_user
from .forms import CreateVendorPartForm
from .models import VendorPart
from pid.common.models import Project, Material, MaterialSpecification, Company, Approver
from pid.user.models import User
from pid.mail import send_email

blueprint = Blueprint('vendorpart', __name__, url_prefix='/vendorpart', static_folder='../static')


@blueprint.route('/create', methods=['POST'])
@login_required
def create_vendor_part():
    """Create new vendor part."""
    form = CreateVendorPartForm(request.form)
    validated = form.validate_on_submit()
    if validated:
        variables = {
            'part_number': form.part_number.data,
            'name': form.name.data,
            'project': form.project.data,
            'vendor': form.vendor.data,
            'owner': form.owner.data
        }
        vendor_part = VendorPart.create(**variables)
        jsonData = {
            'success': True,
            'url': vendor_part.get_url()
        }
        return jsonify(jsonData), 200, {'ContentType': 'application/json'}
    else:
        return make_response(render_template('vendorpart/create_vendor_part.html', form=form), 500)


@blueprint.route('/update_state', methods=['POST'])
@login_required
def update_vendor_part_state():
    # TODO: verify that current_user is owner of record and can edit it
    vendor_part_id = request.values['parent_id']
    state = request.form['state']
    transition = request.form['transition']
    comment = request.values['comment']
    vendor_part = VendorPart.get_by_id(vendor_part_id)
    vendor_part.update(state=state)
    vendor_part.add_workflow_log_entry(capacity='Owner', action=transition, comment=comment)
    if state == vendor_part.workflow.get_approval_state():
        for approver in vendor_part.approvers:
            if not approver.approved_at:
                variables = {
                    'record': vendor_part,
                    'approver': approver,
                    'comment': comment
                }
                send_email(subject='Approval Required for {0}: {1}'.format(vendor_part.descriptor, vendor_part.get_name()),
                           recipients=[approver.approver.email],
                           text_body=render_template('mail/approvals/new_approver.txt', **variables),
                           html_body=render_template('mail/approvals/new_approver.html', **variables))
    elif state == vendor_part.workflow.released_state:
        # Only self-approval will trigger this
        vendor_part.add_workflow_log_entry(capacity='PLAIDmin', action='Released')
    return jsonify({'success': True}), 200, {'ContentType': 'application/json'}


@blueprint.route('/<path:part_number>', methods=['GET'])
@login_required
def view_vendor_part(part_number):
    """View existing vendor part."""
    vendor_part = VendorPart.get_by_part_number(part_number)
    projects = Project.query.all()
    materials = Material.query.all()
    users = User.query.all()
    vendors = Company.get_all_with_pri_on_top()
    variables = {
        'vendor_part': vendor_part,
        'projects': projects,
        'materials': materials,
        'vendors': vendors,
        'users': users
    }
    return render_template('vendorpart/view_vendor_part.html', **variables)


@blueprint.route('/update', methods=['POST'])
@login_required
def update_vendor_part():
    # TODO: Check that field should actually be allowed to change. As in, don't change design number for instance
    id = request.form['pk']
    # UID for field will be ala [fieldname]-[classname]-[id]-editable, field name will be first section always
    field = request.form['name'].split('-')[0]
    field_value = request.form['value']
    original_value = None
    # TODO: Check if design exists
    vendor_part = VendorPart.get_by_id(id)

    if field == 'name':
        original_value = vendor_part.name
        vendor_part.update(name=field_value)
    elif field == 'summary':
        original_value = vendor_part.summary
        vendor_part.update(summary=field_value)
    elif field == 'project':
        if vendor_part.project:
            original_value = vendor_part.project.name
        project = Project.get_by_id(field_value)
        vendor_part.update(project=project)
        field_value = project.name if project else None
    elif field == 'owner':
        if vendor_part.owner:
            original_value = vendor_part.owner.get_name()
            if vendor_part.owner.padawan:
                for approver in vendor_part.approvers:
                    if approver.approver == vendor_part.owner.supervisor and approver.capacity == 'Supervisor':
                        vendor_part.approvers.remove(approver)
                        approver.delete()
        owner = User.get_by_id(field_value)
        if owner.padawan:
            approver = Approver.create(approver_id=owner.supervisor_id, capacity='Supervisor')
            vendor_part.approvers.append(approver)
        vendor_part.update(owner=owner)
        field_value = owner.get_name() if owner else None
    elif field == 'vendor':
        if vendor_part.vendor:
            original_value = vendor_part.vendor.name
        vendor = Company.get_by_id(field_value)
        vendor_part.update(vendor=vendor)
        field_value = vendor.name if vendor else None
    elif field == 'notes':
        original_value = vendor_part.notes
        vendor_part.update(notes=field_value)
    elif field == 'material':
        original_material = None
        original_material_spec = None
        if vendor_part.material:
            original_material = vendor_part.material.name
        if vendor_part.material_specification:
            original_material_spec = vendor_part.material_specification.name
        material = Material.get_by_id(field_value)
        vendor_part.update(material=material, material_specification=None)  # To ensure we don't have a mat_spec linked with old material
        material_name = None
        material_specifications = None
        if material:
            material_name = material.name
            material_specifications = material.specifications
        vendor_part.add_change_log_entry(action='Edit', field='Material', original_value=original_material,
                                           new_value=material_name)
        if original_material_spec:
            vendor_part.add_change_log_entry(action='Edit', field='Material Specification',
                                             original_value=original_material_spec)
        variables = {
            'vendor_part': vendor_part,
            'material_specifications': material_specifications
        }
        return render_template('vendorpart/ajax_select_material_specification.html', **variables)
    elif field == 'material_specification':
        if vendor_part.material_specification:
            original_value = vendor_part.material_specification.name
        material_specification = MaterialSpecification.get_by_id(field_value)
        vendor_part.update(material_specification=material_specification)
        field_value = material_specification.name if material_specification else None
    elif field == 'thumbnail_id':
        thumbnail_id = None if field_value == 'default' else field_value
        vendor_part.update(thumbnail_id=thumbnail_id)
        return render_template('shared/thumbnail_return.html', record=vendor_part)
    elif field == 'current_best_estimate':
        original_value = vendor_part.current_best_estimate
        original_predicted_best_estimate = vendor_part.predicted_best_estimate
        current_best_estimate = float(field_value)
        predicted_best_estimate = current_best_estimate * (1 + (vendor_part.uncertainty / 100))  # PBE = CBE * (1+%Unc)
        vendor_part.update(current_best_estimate=current_best_estimate, predicted_best_estimate=predicted_best_estimate)
        vendor_part.update_parents_mass()  # Updates parts where this is a component
        vendor_part.add_change_log_entry(action='Edit', field='Current Best Estimate', original_value=original_value,
                                         new_value=current_best_estimate)
        vendor_part.add_change_log_entry(action='Edit', field='Predicted Best Estimate',
                                         original_value=original_predicted_best_estimate,
                                         new_value=predicted_best_estimate)
        return render_template('vendorpart/mass_fields.html', vendor_part=vendor_part)
    elif field == 'uncertainty':
        original_value = vendor_part.uncertainty
        original_predicted_best_estimate = vendor_part.predicted_best_estimate
        uncertainty = float(field_value)
        predicted_best_estimate = vendor_part.current_best_estimate * (1 + (uncertainty / 100))  # PBE = CBE * (1+%Unc)
        vendor_part.update(uncertainty=uncertainty, predicted_best_estimate=predicted_best_estimate)
        vendor_part.update_parents_mass()  # Updates parts where this is a component
        vendor_part.add_change_log_entry(action='Edit', field='Uncertainty', original_value=original_value,
                                         new_value=uncertainty)
        vendor_part.add_change_log_entry(action='Edit', field='Predicted Best Estimate',
                                         original_value=original_predicted_best_estimate,
                                         new_value=predicted_best_estimate)
        return render_template('vendorpart/mass_fields.html', vendor_part=vendor_part)

    vendor_part.add_change_log_entry(action='Edit', field=field.title().replace('_', ' '),
                                     original_value=original_value, new_value=field_value)

    return jsonify({'success': True}), 200, {'ContentType': 'application/json'}


@blueprint.route('/typeahead_search_vendor_parts', methods=['GET'])
@login_required
def typeahead_search_vendor_parts():
    query = request.args.get('query')
    part_id = request.args.get('part_id')
    vendor_parts = VendorPart.typeahead_search(query, part_id)
    results = []
    for vendor_part in vendor_parts:
        vendor_part_dict = {}
        vendor_part_dict['class'] = vendor_part.get_class_name()
        vendor_part_dict['icon'] = '<i class="pri-typeahead-icon pri-icons-record-vendor-part" aria-hidden="true"></i>'
        vendor_part_dict['id'] = vendor_part.id
        vendor_part_dict['name'] = vendor_part.name
        vendor_part_dict['number'] = vendor_part.part_number
        vendor_part_dict['object_type'] = 'Vendor Part'
        vendor_part_dict['state'] = vendor_part.state
        vendor_part_dict['table'] = vendor_part.__table__.name
        vendor_part_dict['thumb_url'] = vendor_part.get_thumbnail_url()
        vendor_part_dict['url'] = vendor_part.get_url()
        results.append(vendor_part_dict)
    return jsonify({'success': True, 'vendor_parts': results}), 200, {'ContentType': 'application/json'}


@blueprint.route('/advanced_search', methods=['GET'])
@login_required
def advanced_search_vendor_parts():
    params = request.args.to_dict()
    vendor_parts = VendorPart.advanced_search(params)
    results = []
    for vendor_part in vendor_parts:
        vendor_part_dict = {
            'part_number': vendor_part.part_number,
            'name': vendor_part.name,
            'state': vendor_part.state,
            'summary': vendor_part.summary,
            'notes': vendor_part.notes,
            'project': vendor_part.project.name,
            'owner': vendor_part.owner.get_name(),
            'material': vendor_part.material.name if vendor_part.material else '',
            'vendor': vendor_part.vendor.name,
            'created_by': vendor_part.created_by.get_name(),
            'created_at': vendor_part.created_at,
            'anomalies': len(vendor_part.anomalies),
            'url': vendor_part.get_url()
        }
        results.append(vendor_part_dict)
    return jsonify({'success': True, 'data': results}), 200, {'ContentType': 'application/json'}


@blueprint.route('/get_create_modal', methods=['POST'])
@login_required
def get_vendor_part_modal():
    form = CreateVendorPartForm(request.form)
    return render_template('vendorpart/create_vendor_part.html', form=form)


@blueprint.route('/get_view_nlas_modal', methods=['POST'])
@login_required
def get_view_nlas_modal():
    vendor_part_id = request.form.get('vendor_part_id')
    vendor_part = VendorPart.get_by_id(vendor_part_id)
    parents = vendor_part.get_nlas_for_vendor_part()
    variables = {
        'parents': parents
    }
    return render_template('design/view_nlas_modal.html', **variables)


@blueprint.route('/get_view_builds_modal', methods=['POST'])
@login_required
def get_view_builds_modal():
    vendor_part_id = request.form.get('vendor_part_id')
    vendor_part = VendorPart.get_by_id(vendor_part_id)
    vendor_builds = vendor_part.get_vendor_builds_for_vendor_part()
    variables = {'builds': vendor_builds}
    return render_template('vendorpart/view_vendor_builds_modal.html', **variables)
