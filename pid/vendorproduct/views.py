# -*- coding: utf-8 -*-
"""Product views."""
from collections import defaultdict

from flask import Blueprint, render_template, request, jsonify, make_response
from flask_login import login_required, current_user

from pid.common.models import Project, HardwareType, Company, Disposition, Approver
from pid.vendorpart.models import VendorPart
from pid.mail import send_email
from pid.user.models import User
from .forms import CreateVendorBuildForm
from .models import VendorBuild, VendorProduct

blueprint = Blueprint('vendorproduct', __name__, url_prefix='/vendorproduct', static_folder='../static')


# ===== VENDOR BUILD VIEWS ===== #

@blueprint.route('/build/create', methods=['GET', 'POST'])
@login_required
def create_vendor_build():
    """Create new VendorBuild. Also creates one or more VendorProducts."""
    form = CreateVendorBuildForm(request.form)
    if request.method == 'GET':
        vendor_part = VendorPart.get_by_id(request.args.get('vendor_part_id'))
        existing_build_id = request.args.get('existing_build_id')
        if existing_build_id:
            existing_build = VendorBuild.get_by_id(existing_build_id)
            build_identifier = existing_build.build_identifier
        else:
            build_identifier = VendorBuild.get_next_build_identifier_for_vendor_part(vendor_part)
        lot_identifier = VendorProduct.get_next_lot_number_for_vendor_part(vendor_part)
        existing_serial_numbers = ','.join(VendorProduct.get_serial_numbers_for_vendor_part(vendor_part))
        # Pre-populate with values from vendor_part
        form.project.data = vendor_part.project
        form.vendor.data = vendor_part.vendor
        form.manufacturer.data = Company.get_company_by_name('N/A')
        variables = {
            'form': form,
            'vendor_part': vendor_part,
            'build_identifier': build_identifier,
            'lot_identifier': lot_identifier,
            'existing_serial_numbers': existing_serial_numbers,
            'existing_build_id': existing_build_id
        }
        return render_template('vendorproduct/create_vendor_build_modal.html', **variables)
    validated, data = form.validate_on_submit()
    if validated:
        vendor_part = VendorPart.get_by_id(form.vendor_part_id.data)
        vendor = vendor_part.vendor
        manufacturer = form.manufacturer.data
        owner = form.owner.data
        build_identifier = form.build_identifier.data
        # Create build
        if form.existing_build_id.data:
            build = VendorBuild.get_by_id(form.existing_build_id.data)
        else:
            build = VendorBuild.create(vendor_part=vendor_part, vendor=vendor, manufacturer=manufacturer,
                                       owner=owner, build_identifier=build_identifier)
        # For each s/n in s/n, create product
        summary = vendor_part.summary
        hardware_type = form.hardware_type.data
        project = form.project.data
        # Create serial numbers
        serial_numbers = data.get('serial_numbers', [])
        for sn in serial_numbers:
            product = VendorProduct.create(serial_number=sn, vendor_part=vendor_part, vendor_build=build,
                                           summary=summary, hardware_type=hardware_type,
                                           project=project, owner=owner)
        # Or create LOT product
        lot_record = data.get('lot_record', None)
        if lot_record:
            product = VendorProduct.create(serial_number=lot_record, vendor_part=vendor_part, vendor_build=build,
                                           summary=summary, hardware_type=hardware_type, product_type='LOT',
                                           project=project, owner=owner)
        # Or create STOCK product
        is_stock = data.get('is_stock', False)
        if is_stock:
            product = VendorProduct.create(serial_number='STCK', vendor_part=vendor_part, vendor_build=build,
                                           summary=summary, hardware_type=hardware_type, product_type='STOCK',
                                           project=project, owner=owner)

        jsonData = {
            'success': True,
            'product_number': product.product_number.replace(' ', '-'),  # Slugify product_number
            'url': product.get_url()
        }
        return jsonify(jsonData), 200, {'ContentType': 'application/json'}
    else:
        vendor_part = VendorPart.get_by_id(request.form['vendor_part_id'])
        build_identifier = VendorBuild.get_next_build_identifier_for_vendor_part(vendor_part)
        lot_identifier = VendorProduct.get_next_lot_number_for_vendor_part(vendor_part)
        existing_serial_numbers = ','.join(VendorProduct.get_serial_numbers_for_vendor_part(vendor_part))
        variables = {
            'form': form,
            'vendor_part': vendor_part,
            'build_identifier': build_identifier,
            'lot_identifier': lot_identifier,
            'existing_serial_numbers': existing_serial_numbers
        }
        response = make_response(render_template('vendorproduct/create_vendor_build_modal.html', **variables), 500)
        return response


@blueprint.route('/build/update', methods=['POST'])
@login_required
def update_vendor_build():
    id = request.form['pk']
    # UID for field will be ala [fieldname]-[classname]-[id]-editable, field name will be first section always
    field = request.form['name'].split('-')[0]
    field_value = request.form['value']
    # TODO: Check if build exists
    vendor_build = VendorBuild.get_by_id(id)
    original_value = None

    if field == 'notes':
        original_value = vendor_build.notes
        vendor_build.update(notes=field_value)
    elif field == 'owner':
        if vendor_build.owner:
            original_value = vendor_build.owner.get_name()
        owner = User.get_by_id(field_value)
        vendor_build.update(owner=owner)
        field_value = owner.get_name() if owner else None
    elif field == 'purchase_order':
        original_value = vendor_build.purchase_order
        vendor_build.update(purchase_order=field_value)
    elif field == 'vendor':
        if vendor_build.vendor:
            original_value = vendor_build.vendor.name
        vendor = Company.get_by_id(field_value)
        vendor_build.update(vendor=vendor)
        field_value = vendor.name if vendor else None
    elif field == 'manufacturer':
        if vendor_build.manufacturer:
            original_value = vendor_build.manufacturer.name
        manufacturer = Company.get_by_id(field_value)
        vendor_build.update(manufacturer=manufacturer)
        field_value = manufacturer.name if manufacturer else None

    vendor_build.add_change_log_entry(action='Edit', field=field.title().replace('_', ' '),
                                      original_value=original_value, new_value=field_value)

    return jsonify({'success': True}), 200, {'ContentType': 'application/json'}


# ===== VENDOR PRODUCT VIEWS ===== #

@blueprint.route('/typeahead_search', methods=['GET'])
@login_required
def typeahead_search_vendor():
    query = request.args.get('query')
    vendor_products = VendorProduct.typeahead_search(query)
    results = []
    for product in vendor_products:
        results_dict = {}
        results_dict['class'] = product.get_class_name()
        results_dict['icon'] = '<i class="pri-typeahead-icon pri-icons-record-vendor-product" aria-hidden="true"></i>'
        results_dict['id'] = product.id
        results_dict['name'] = product.get_name()
        results_dict['number'] = product.get_unique_identifier()
        results_dict['object_type'] = 'Vendor Product'
        results_dict['state'] = product.state
        results_dict['thumb_url'] = product.get_thumbnail_url()
        results_dict['url'] = product.get_url()
        results.append(results_dict)
    return jsonify({'success': True, 'data': results}), 200, {'ContentType': 'application/json'}


@blueprint.route('/update', methods=['POST'])
@login_required
def update_vendor_product():
    id = request.form['pk']
    # UID for field will be ala [fieldname]-[classname]-[id]-editable, field name will be first section always
    field = request.form['name'].split('-')[0]
    field_value = request.form['value']
    # TODO: Check if product exists
    vendor_product = VendorProduct.get_by_id(id)
    original_value = None
    jsonData = {}
    if field == 'hardware_type':
        if vendor_product.hardware_type:
            original_value = vendor_product.hardware_type.name
        hardware_type = HardwareType.get_by_id(field_value)
        vendor_product.update(hardware_type=hardware_type)
        field_value = hardware_type.name if hardware_type else None
    elif field == 'measured_mass':
        original_value = vendor_product.measured_mass
        vendor_product.update(measured_mass=float(field_value))
        vendor_product.add_change_log_entry(action='Edit', field='Measured Mass', original_value=original_value,
                                            new_value=field_value)
        variables = {'vendor_product': vendor_product}
        return render_template('vendorproduct/mass_field.html', **variables)
    elif field == 'owner':
        if vendor_product.owner:
            original_value = vendor_product.owner.get_name()
            if vendor_product.owner.padawan:
                for approver in vendor_product.approvers:
                    if approver.approver == vendor_product.owner.supervisor and approver.capacity == 'Supervisor':
                        vendor_product.approvers.remove(approver)
                        approver.delete()
        owner = User.get_by_id(field_value)
        if owner.padawan:
            approver = Approver.create(approver_id=owner.supervisor_id, capacity='Supervisor')
            vendor_product.approvers.append(approver)
        vendor_product.update(owner=owner)
        field_value = owner.get_name() if owner else None
    elif field == 'project':
        if vendor_product.project:
            original_value = vendor_product.project.name
        project = Project.get_by_id(field_value)
        vendor_product.update(project=project)
        field_value = project.name if project else None
    elif field == 'notes':
        original_value = vendor_product.notes
        vendor_product.update(notes=field_value)
    elif field == 'summary':
        original_value = vendor_product.summary
        vendor_product.update(summary=field_value)
    elif field == 'thumbnail_id':
        thumbnail_id = None if field_value == 'default' else field_value
        vendor_product.update(thumbnail_id=thumbnail_id)
        return render_template('shared/thumbnail_return.html', record=vendor_product)
    elif field == 'serial_number':
        original_value = vendor_product.serial_number
        try:
            vendor_product.update(serial_number=field_value)
        except:
            return jsonify(jsonData), 500, {'ContentType': 'application/json'}
        jsonData = {'url': vendor_product.get_url()}  # Return URL to reload page with new S/N

    vendor_product.add_change_log_entry(action='Edit', field=field.title().replace('_', ' '),
                                        original_value=original_value, new_value=field_value)

    return jsonify(jsonData), 200, {'ContentType': 'application/json'}


@blueprint.route('/update_state', methods=['POST'])
@login_required
def update_vendor_product_state():
    # TODO: verify that current_user is owner of record and can edit it
    design_id = request.values['parent_id']
    state = request.form['state']
    transition = request.form['transition']
    comment = request.values['comment']
    vendor_product = VendorProduct.get_by_id(design_id)
    vendor_product.update(state=state)
    vendor_product.add_workflow_log_entry(capacity='Owner', action=transition, comment=comment)
    if state == vendor_product.workflow.get_approval_state():
        for approver in vendor_product.approvers:
            if not approver.approved_at:
                variables = {
                    'record': vendor_product,
                    'approver': approver,
                    'comment': comment
                }
                send_email(subject='Approval Required for {0}: {1}'.format(vendor_product.descriptor, vendor_product.get_name()),
                           recipients=[approver.approver.email],
                           text_body=render_template('mail/approvals/new_approver.txt', **variables),
                           html_body=render_template('mail/approvals/new_approver.html', **variables))
    elif state == vendor_product.workflow.released_state:
        # Only self-approval will trigger this
        vendor_product.add_workflow_log_entry(capacity='PLAIDmin', action='Released')
    return jsonify({'success': True}), 200, {'ContentType': 'application/json'}


@blueprint.route('/<path:part_number>-<path:serial_number>', methods=['GET'])
@login_required
def view_vendor_product(part_number, serial_number):
    vendor_product = VendorProduct.get_vendor_product_by_product_number(part_number, serial_number)
    index = 1
    back_index = -1
    product_number = part_number + '-' + serial_number
    product_number_parts = product_number.split('-')
    max_index = len(product_number.split('-'))
    while not vendor_product:
        # Probably due to a dash in serial_number causing the above match to fail. Do some magic and try again
        part_number = '-'.join(product_number_parts[0:max_index - index])
        serial_number = '-'.join(product_number_parts[back_index:])
        vendor_product = VendorProduct.get_vendor_product_by_product_number(part_number, serial_number)
        index += 1
        back_index -= 1
        if index == max_index:
            break  # TODO: Make this error gracefully rather than nastily
    serial_numbers = VendorProduct.get_serial_numbers_for_vendor_part(vendor_product.vendor_part)
    projects = Project.query.all()
    companies = Company.get_all_with_pri_on_top()
    hardware_types = HardwareType.query.all()
    users = User.query.all()
    dispositions = Disposition.query.all()
    installed_ins = defaultdict(list)
    for pc in vendor_product.get_installed_ins():
        installed_ins[pc.parent.product_number].append(pc)
    variables = {
        'vendor_product': vendor_product,
        'serial_numbers': serial_numbers,
        'projects': projects,
        'hardware_types': hardware_types,
        'users': users,
        'companies': companies,
        'dispositions': dispositions,
        'installed_ins': installed_ins
    }
    return render_template('vendorproduct/view_vendor_product.html', **variables)


@blueprint.route('/advanced_search', methods=['GET'])
@login_required
def advanced_search_vendor_products():
    params = request.args.to_dict()
    vendor_products = VendorProduct.advanced_search(params)
    results = []
    for vendor_product in vendor_products:
        vendor_product_dict = {
            'serial_number': vendor_product.serial_number,
            'id': vendor_product.vendor_part.part_number + ' - ' + vendor_product.serial_number,
            'title': vendor_product.get_name(),
            'state': vendor_product.state,
            'hardware_type': vendor_product.hardware_type.name,
            'owner': vendor_product.owner.get_name(),
            'vendor': vendor_product.vendor_part.vendor.name if vendor_product.vendor_part else '',
            'material': vendor_product.vendor_part.material.name if vendor_product.vendor_part.material else '',
            'notes': vendor_product.notes,
            'project': vendor_product.project.name,
            'created_by': vendor_product.created_by.get_name(),
            'created_at': vendor_product.created_at,
            'url': vendor_product.get_url()
        }
        results.append(vendor_product_dict)
    return jsonify({'success': True, 'data': results}), 200, {'ContentType': 'application/json'}


@blueprint.route('/get_view_vendor_build_modal', methods=['POST'])
@login_required
def get_view_vendor_build_modal():
    build_id = request.values['build_id']
    build = VendorBuild.get_by_id(build_id)
    variables = {
        'build': build
    }
    return render_template('vendorproduct/view_vendor_build_modal.html', **variables)
