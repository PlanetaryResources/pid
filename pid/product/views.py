# -*- coding: utf-8 -*-
"""Product views."""
from collections import defaultdict

from flask import Blueprint, render_template, request, jsonify, make_response, redirect
from flask_login import login_required, current_user

from pid.common.models import Project, HardwareType, Company, Disposition, Approver
from pid.database import get_record_by_id_and_class
from pid.vendorpart.models import VendorPart
from pid.mail import send_email
from pid.part.models import Part
from pid.user.models import User
from .forms import CreateBuildForm, AddExtraProductComponentForm
from .models import Build, Product, ProductComponent, Discrepancy, ExtraProductComponent
from pid.vendorproduct.models import VendorProduct, VendorBuild

blueprint = Blueprint('product', __name__, url_prefix='/product', static_folder='../static')


# ======= BUILD VIEWS ======= #

@blueprint.route('/build/create', methods=['GET', 'POST'])
@login_required
def create_build():
    """Create new Build. Also creates one or more Products."""
    form = CreateBuildForm(request.form)
    if request.method == 'GET':
        part = Part.get_by_id(request.args.get('part_id'))
        existing_build_id = request.args.get('existing_build_id')
        if existing_build_id:
            existing_build = Build.get_by_id(existing_build_id)
            build_identifier = existing_build.build_identifier
        else:
            build_identifier = Build.get_next_build_identifier_for_design_number_and_part_identifier(part.design.design_number, part.part_identifier)
        lot_identifier = Product.get_next_lot_number_for_design_number_and_part_identifier(part.design.design_number, part.part_identifier)
        existing_serial_numbers = ','.join(Product.get_serial_numbers_for_design_number_and_part_identifier(part.design.design_number, part.part_identifier))
        # Pre-populate with values from design
        form.project.data = part.design.project
        variables = {
            'form': form,
            'part': part,
            'build_identifier': build_identifier,
            'lot_identifier': lot_identifier,
            'existing_serial_numbers': existing_serial_numbers,
            'existing_build_id': existing_build_id
        }
        return render_template('product/create_build_modal.html', **variables)
    validated, data = form.validate_on_submit()
    if validated:
        part = Part.get_by_id(form.part_id.data)
        vendor = form.vendor.data
        owner = form.owner.data
        build_identifier = form.build_identifier.data
        # Create build
        if form.existing_build_id.data:
            build = Build.get_by_id(form.existing_build_id.data)
        else:
            build = Build.create(part=part, vendor=vendor, owner=owner, build_identifier=build_identifier)
        # For each s/n in s/n, create product
        revision = part.design.revision
        summary = part.design.summary
        hardware_type = form.hardware_type.data
        project = form.project.data
        # Create serial numbers
        serial_numbers = data.get('serial_numbers', [])
        for sn in serial_numbers:
            product = Product.create(serial_number=sn, part=part, build=build, revision=revision, summary=summary,
                                     hardware_type=hardware_type, project=project, owner=owner)
            # Create Product Components
            for part_component in part.components:
                for i in range(part_component.quantity):
                    if part_component.part:
                        ProductComponent.create(parent=product, part=part_component.part, ordering=part_component.ordering)
                    elif part_component.vendor_part:
                        ProductComponent.create(parent=product, vendor_part=part_component.vendor_part, ordering=part_component.ordering)
        # Or create LOT product
        lot_record = data.get('lot_record', None)
        if lot_record:
            product = Product.create(serial_number=lot_record, part=part, build=build, revision=revision,
                                     summary=summary, hardware_type=hardware_type, product_type='LOT',
                                     project=project, owner=owner)
            # Create Product Components
            for part_component in part.components:
                for i in range(part_component.quantity):
                    if part_component.part:
                        ProductComponent.create(parent=product, part=part_component.part, ordering=part_component.ordering)
                    elif part_component.vendor_part:
                        ProductComponent.create(parent=product, vendor_part=part_component.vendor_part, ordering=part_component.ordering)
        # Or create STOCK product
        is_stock = data.get('is_stock', False)
        if is_stock:
            product = Product.create(serial_number='STCK', part=part, build=build, revision=revision,
                                     summary=summary, hardware_type=hardware_type, product_type='STOCK',
                                     project=project, owner=owner)

        jsonData = {
            'success': True,
            'product_number': product.product_number.replace(' ', '-')  # Slugify product_number
        }
        return jsonify(jsonData), 200, {'ContentType': 'application/json'}
    else:
        part = Part.get_by_id(request.form['part_id'])
        build_identifier = Build.get_next_build_identifier_for_design_number_and_part_identifier(part.design.design_number, part.part_identifier)
        lot_identifier = Product.get_next_lot_number_for_design_number_and_part_identifier(part.design.design_number, part.part_identifier)
        existing_serial_numbers = ','.join(Product.get_serial_numbers_for_design_number_and_part_identifier(part.design.design_number, part.part_identifier))
        variables = {
            'form': form,
            'part': part,
            'build_identifier': build_identifier,
            'lot_identifier': lot_identifier,
            'existing_serial_numbers': existing_serial_numbers
        }
        response = make_response(render_template('product/create_build_modal.html', **variables), 500)
        return response


@blueprint.route('/build/update', methods=['POST'])
@login_required
def update_build():
    id = request.form['pk']
    # UID for field will be ala [fieldname]-[classname]-[id]-editable, field name will be first section always
    field = request.form['name'].split('-')[0]
    field_value = request.form['value']
    # TODO: Check if build exists
    build = Build.get_by_id(id)
    original_value = None
    if field == 'notes':
        original_value = build.notes
        build.update(notes=field_value)
    elif field == 'owner':
        if build.owner:
            original_value = build.owner.get_name()
        owner = User.get_by_id(field_value)
        build.update(owner=owner)
        field_value = owner.get_name() if owner else None
    elif field == 'purchase_order':
        original_value = build.purchase_order
        build.update(purchase_order=field_value)
    elif field == 'vendor':
        if build.vendor:
            original_value = build.vendor.name
        vendor = Company.get_by_id(field_value)
        build.update(vendor=vendor)
        field_value = vendor.name if vendor else None

    build.add_change_log_entry(action='Edit', field=field.title().replace('_', ' '),
                               original_value=original_value, new_value=field_value)

    return jsonify({'success': True}), 200, {'ContentType': 'application/json'}


# ======= PRODUCT VIEWS ======= #

@blueprint.route('/add_extra_product_component/', methods=['POST'])
@login_required
def add_extra_product_component():
    form = AddExtraProductComponentForm(request.form)
    validated = form.validate_on_submit()
    if validated:
        quantity = form.quantity.data
        part_group = form.part_group.data
        part_id = form.part_id.data
        product_id = form.product_id.data
        product = Product.get_by_id(product_id)
        ordering = len(product.extra_components) + 1
        if part_group == 'Part':  # part_group from typeahead group, not class name
            part = Part.get_by_id(part_id)
            for i in range(quantity):
                epc = ExtraProductComponent.create(parent=product, part=part, ordering=ordering)
        elif part_group == 'Vendor Part':  # part_group from typeahead group, not class name
            vendor_part = VendorPart.get_by_id(part_id)
            for i in range(quantity):
                epc = ExtraProductComponent.create(parent=product, vendor_part=vendor_part, ordering=ordering)
        components_array = arrange_product_components(product)
        extra_components_array = arrange_extra_product_components(product)
        variables = {
            'success': True,
            'product': product,
            'components_array': components_array,
            'extra_components_array': extra_components_array
        }
        new_value = '{0} -  Quantity: {1}'.format(epc.get_part().get_descriptive_url(), quantity)
        product.add_change_log_entry(action='Add', field='Extra Component', new_value=new_value)
        return render_template('product/as-built/component_list.html', **variables)
    else:
        product_id = form.product_id.data
        product = Product.get_by_id(product_id)
        part = None
        if form.part_id.data:
            part_group = form.part_group.data
            part_id = form.part_id.data
            if part_group == 'Part':  # part_group from typeahead, not class name
                part = Part.get_by_id(part_id)
            elif part_group == 'Vendor Part':  # part_group from typeahead, not class name
                part = VendorPart.get_by_id(part_id)
        variables = {
            'form': form,
            'product': product,
            'part': part
        }
        response = make_response(render_template('product/add_product_component_modal.html', **variables), 500)
        return response


@blueprint.route('/delete_product_component', methods=['POST'])
@login_required
def delete_product_component():
    id = request.form['pk']
    amount = request.form['amount']
    component = ExtraProductComponent.get_by_id(id)  # Only ExtraProductComponents can be deleted
    old_value = '{0}'.format(component.get_part().get_descriptive_url())
    parent = component.parent
    if amount == 'all_unassigned':
        components = component.get_all_unassigned_extra_product_components_like_this()
        for c in components:
            # TODO: Find a why to do this all in one call
            c.delete()
    elif amount == 'all_assigned':
        components = component.get_all_assigned_extra_product_components_like_this()
        for c in components:
            # TODO: Find a why to do this all in one call
            c.delete()
    elif amount == 'single':
        component.delete()
    parent.add_change_log_entry(action='Remove', field='Extra Component', original_value=old_value)
    return jsonify({'success': True}), 200, {'ContentType': 'application/json'}


@blueprint.route('/get_add_product_component_modal', methods=['POST'])
@login_required
def get_add_product_component_modal():
    product_id = request.form.get('product_id')
    product = Product.get_by_id(product_id)
    form = AddExtraProductComponentForm(request.form)
    form.product_id.data = product.id
    variables = {
        'product': product,
        'form': form
    }
    return render_template('product/add_product_component_modal.html', **variables)


@blueprint.route('/get_update_product_revision_modal', methods=['POST'])
@login_required
def get_update_product_revision_modal():
    product_id = request.form.get('product_id')
    product = Product.get_by_id(product_id)
    designs = product.part.design.find_all_revisions()
    revisions = [d.revision for d in designs]
    revisions.remove(product.revision)
    variables = {
        'product': product,
        'revisions': revisions
    }
    return render_template('product/update_product_revision_modal.html', **variables)


@blueprint.route('/revise', methods=['POST'])
@login_required
def revise_product():
    product_id = request.form['product_id']
    new_revision = request.form['revision']
    product = Product.get_by_id(product_id)
    parts = product.part.get_parts_for_design_revisions()  # With same identifier
    parts.remove(product.part)  # Remove old part from this list
    for part in parts:  # Then remove parts not belonging to new revision
        if part.design.revision != new_revision:
            parts.remove(part)
    # Should be left with only one part ideally
    new_part = parts[0]

    # Convert old and new components to dicts for easiness
    old_part_components = defaultdict(list)
    old_vendor_components = defaultdict(list)
    old_part_components_tracker = set()
    old_vendor_components_tracker = set()
    for component in product.components:
        if component.part:
            old_part_components[component.part.part_number].append(component)
            old_part_components_tracker.add(component.part.part_number)
        else:
            old_vendor_components[component.vendor_part.part_number].append(component)
            old_vendor_components_tracker.add(component.vendor_part.part_number)

    new_part_components = defaultdict(list)
    new_vendor_components = defaultdict(list)
    for component in new_part.components:
        for i in range(component.quantity):
            if component.part:
                new_part_components[component.part.part_number].append(component)
            else:
                new_vendor_components[component.vendor_part.part_number].append(component)

    # Go through new components and add or subtract if needed
    for pn, ncs in new_part_components.items():
        ocs = old_part_components.get(pn, None)
        if ocs:
            # Component existed in old revision as well
            if len(ncs) > len(ocs):
                # More components in new rev than in old rev, make new ones
                for i in range(len(ncs) - len(ocs)):
                    ProductComponent.create(parent=product, part=ncs[0].part, ordering=ncs[0].ordering)
                # Then update the old ones to new part
                for c in ocs:
                    c.update(part=ncs[0].part)
            if len(ncs) < len(ocs):
                # Fewer components in new rev than in old rev, delete all the old ones and make new ones
                for c in ocs:
                    c.delete()
                for i in range(len(ncs)):
                    ProductComponent.create(parent=product, part=ncs[0].part, ordering=ncs[0].ordering)
        else:
            # New component that has did not exist in old
            for i in range(len(ncs)):
                ProductComponent.create(parent=product, part=ncs[0].part, ordering=ncs[0].ordering)
        old_part_components_tracker.discard(pn)
    # Do the same for vendor parts
    for pn, ncs in new_vendor_components.items():
        ocs = old_vendor_components.get(pn, None)
        if ocs:
            # Component existed in old revision as well
            if len(ncs) > len(ocs):
                # More components in new rev than in old rev, make new ones
                for i in range(len(ncs) - len(ocs)):
                    ProductComponent.create(parent=product, vendor_part=ncs[0].vendor_part, ordering=ncs[0].ordering)
                # Then update the old ones to new part
                for c in ocs:
                    c.update(vendor_part=ncs[0].vendor_part)
            if len(ncs) < len(ocs):
                # Fewer components in new rev than in old rev, delete all the old ones and make new ones
                for c in ocs:
                    c.delete()
                for i in range(len(ncs)):
                    ProductComponent.create(parent=product, vendor_part=ncs[0].vendor_part, ordering=ncs[0].ordering)
        else:
            # New component that has did not exist in old
            for i in range(len(ncs)):
                ProductComponent.create(parent=product, vendor_part=ncs[0].vendor_part, ordering=ncs[0].ordering)
        old_vendor_components_tracker.discard(pn)

    # The remaning components have been removed in the new revision, delete them
    for pn in old_part_components_tracker:
        ocs = old_part_components.get(pn, None)
        for c in ocs:
            c.delete()
    # Do the same for vendor parts
    for pn in old_vendor_components_tracker:
        ocs = old_vendor_components.get(pn, None)
        for c in ocs:
            c.delete()

    product.add_change_log_entry(action='Revise', field='Revision',
                                 original_value=product.revision, new_value=new_revision)
    product.update(revision=new_revision, part=new_part, state=product.workflow.initial_state)


    return jsonify({'success': True, 'url': product.get_url()}), 200, {'ContentType': 'application/json'}


@blueprint.route('/typeahead_search', methods=['GET'])
@login_required
def typeahead_search():
    query = request.args.get('query')
    products = Product.typeahead_search(query)
    results = []
    for product in products:
        results_dict = {}
        results_dict['class'] = product.get_class_name()
        results_dict['icon'] = '<i class="pri-typeahead-icon pri-icons-record-product" aria-hidden="true"></i>'
        results_dict['id'] = product.id
        results_dict['name'] = product.get_name()
        results_dict['number'] = product.get_unique_identifier()
        results_dict['object_type'] = 'Product'
        results_dict['state'] = product.state
        results_dict['thumb_url'] = product.get_thumbnail_url()
        results_dict['url'] = product.get_url()
        results.append(results_dict)
    return jsonify({'success': True, 'data': results}), 200, {'ContentType': 'application/json'}


@blueprint.route('/update', methods=['POST'])
@login_required
def update_product():
    id = request.form['pk']
    # UID for field will be ala [fieldname]-[classname]-[id]-editable, field name will be first section always
    field = request.form['name'].split('-')[0]
    field_value = request.form['value']
    # TODO: Check if product exists
    product = Product.get_by_id(id)
    original_value = None

    if field == 'hardware_type':
        if product.hardware_type:
            original_value = product.hardware_type.name
        hardware_type = HardwareType.get_by_id(field_value)
        product.update(hardware_type=hardware_type)
        field_value = hardware_type.name if hardware_type else None
    elif field == 'measured_mass':
        original_value = product.measured_mass
        product.update(measured_mass=float(field_value))
    elif field == 'owner':
        if product.owner:
            original_value = product.owner.get_name()
            if product.owner.padawan:
                for approver in product.approvers:
                    if approver.approver == product.owner.supervisor and approver.capacity == 'Supervisor':
                        product.approvers.remove(approver)
                        approver.delete()
        owner = User.get_by_id(field_value)
        if owner.padawan:
            approver = Approver.create(approver_id=owner.supervisor_id, capacity='Supervisor')
            product.approvers.append(approver)
        product.update(owner=owner)
        field_value = owner.get_name() if owner else None
    elif field == 'project':
        if product.project:
            original_value = product.project.name
        project = Project.get_by_id(field_value)
        product.update(project=project)
        field_value = project.name if project else None
    elif field == 'notes':
        original_value = product.notes
        product.update(notes=field_value)
    elif field == 'summary':
        original_value = product.summary
        product.update(summary=field_value)
    elif field == 'thumbnail_id':
        thumbnail_id = None if field_value == 'default' else field_value
        product.update(thumbnail_id=thumbnail_id)
        return render_template('shared/thumbnail_return.html', record=product)

    product.add_change_log_entry(action='Edit', field=field.title().replace('_', ' '), original_value=original_value,
                                 new_value=field_value)

    return jsonify({'success': True}), 200, {'ContentType': 'application/json'}


@blueprint.route('/update_state', methods=['POST'])
@login_required
def update_product_state():
    # TODO: verify that current_user is owner of record and can edit it
    design_id = request.values['parent_id']
    state = request.form['state']
    transition = request.form['transition']
    comment = request.values['comment']
    product = Product.get_by_id(design_id)
    product.update(state=state)
    product.add_workflow_log_entry(capacity='Owner', action=transition, comment=comment)
    if state == product.workflow.get_approval_state():
        for approver in product.approvers:
            if not approver.approved_at:
                variables = {
                    'record': product,
                    'approver': approver,
                    'comment': comment
                }
                send_email(subject='Approval Required for {0}: {1}'.format(product.descriptor, product.get_name()),
                           recipients=[approver.approver.email],
                           text_body=render_template('mail/approvals/new_approver.txt', **variables),
                           html_body=render_template('mail/approvals/new_approver.html', **variables))
    elif state == product.workflow.released_state:
        # Only self-approval will trigger this
        comment = 'Revision ' + product.revision
        product.add_workflow_log_entry(capacity='PLAIDmin', action='Released', comment=comment)
    return jsonify({'success': True}), 200, {'ContentType': 'application/json'}


@blueprint.route('/component/update', methods=['POST'])
@login_required
def update_product_component():
    id = request.form['pk']
    # UID for field will be ala [fieldname]-[classname]-[id]-editable, field name will be first section always
    field = request.form['name'].split('-')[0]
    field_value = request.form['value']
    # TODO: Check if product component exists
    product_component = ProductComponent.get_by_id(id)
    parent = product_component.parent
    if field == 'product':
        product = Product.get_by_id(field_value)

        # Change log on this product and on product making up the component
        if product_component.product:
            p = product_component.product
            old_value = '{0} (1)'.format(p.get_descriptive_url())
            p.add_change_log_entry(action='Remove', field='Product Component',
                                   original_value='Removed as Product Component on {0}'.format(parent.get_descriptive_url()))
        else:
            old_value = '{0} - Empty (1)'.format(product_component.part.get_descriptive_url())
        if product:
            new_value = '{0} (1)'.format(product.get_descriptive_url())
            product.add_change_log_entry(action='Add', field='Product Component',
                                         original_value='Added as Product Component on {0}'.format(parent.get_descriptive_url()))
        else:
            p = product_component.part
            new_value = '{0} - Empty (1)'.format(p.get_descriptive_url())
        parent.add_change_log_entry(action='Edit', field='Product Component', original_value=old_value, new_value=new_value)

        product_component.update(product=product)
        # Group installed components so can show them grouped on page
        components_array = arrange_product_components(parent)
        extra_components_array = arrange_extra_product_components(parent)

        variables = {
            'success': True,
            'product': parent,
            'components_array': components_array,
            'extra_components_array': extra_components_array
        }
        return render_template('product/as-built/component_list.html', **variables)
    elif field == 'product_all':
        product = Product.get_by_id(field_value)
        if product.product_type != 'SN':
            qty = product_component.update_all_unassigned_product_components_for_part(product)
        else:
            product_component.update(product=product)
            qty = 1

        # Add change log, this method will only be used when adding new components
        product.add_change_log_entry(action='Add', field='Product Component',
                                     original_value='Added as Product Component on {0}'.format(parent.get_descriptive_url()))
        old_value = '{0} - Empty ({1})'.format(product.part.get_descriptive_url(), qty)
        new_value = '{0} ({1})'.format(product.get_descriptive_url(), qty)
        parent.add_change_log_entry(action='Edit', field='Product Component',
                                    original_value=old_value, new_value=new_value)

        # Group installed components so can show them grouped on page
        components_array = arrange_product_components(parent)
        extra_components_array = arrange_extra_product_components(parent)

        variables = {
            'success': True,
            'product': parent,
            'components_array': components_array,
            'extra_components_array': extra_components_array
        }
        return render_template('product/as-built/component_list.html', **variables)
    if field == 'vendor_product':
        vendor_product = VendorProduct.get_by_id(field_value)

        # Change log on this product and on vendor_product making up the component
        if product_component.vendor_product:
            vp = product_component.vendor_product
            old_value = '{0} (1)'.format(vp.get_descriptive_url())
            vp.add_change_log_entry(action='Remove', field='Product Component',
                                   original_value='Removed as Product Component on {0}'.format(parent.get_descriptive_url()))
        else:
            old_value = '{0} - Empty (1)'.format(product_component.vendor_part.get_descriptive_url())
        if vendor_product:
            new_value = '{0} (1)'.format(vendor_product.get_descriptive_url())
            vendor_product.add_change_log_entry(action='Add', field='Product Component',
                                                original_value='Added as Product Component on {0}'.format(parent.get_descriptive_url()))
        else:
            new_value = '{0} - Empty (1)'.format(product_component.vendor_part.get_descriptive_url())
        parent.add_change_log_entry(action='Edit', field='Product Component', original_value=old_value, new_value=new_value)

        product_component.update(vendor_product=vendor_product)
        # Group installed components so can show them grouped on page
        components_array = arrange_product_components(parent)
        extra_components_array = arrange_extra_product_components(parent)

        variables = {
            'success': True,
            'product': parent,
            'components_array': components_array,
            'extra_components_array': extra_components_array
        }
        return render_template('product/as-built/component_list.html', **variables)
    elif field == 'vendor_product_all':
        vendor_product = VendorProduct.get_by_id(field_value)
        if vendor_product.product_type != 'SN':
            # Adding all to STOCK or LOT
            qty = product_component.update_all_unassigned_product_components_for_vendor_part(vendor_product)
        else:
            # Adding a single S/N
            product_component.update(vendor_product=vendor_product)
            qty = 1

        # Add change log, this method will only be used when adding new components
        vendor_product.add_change_log_entry(action='Add', field='Product Component',
                                            original_value='Added as Product Component on {0}'.format(parent.get_descriptive_url()))
        old_value = '{0} - Empty ({1})'.format(vendor_product.vendor_part.get_descriptive_url(), qty)
        new_value = '{0} ({1})'.format(vendor_product.get_descriptive_url(), qty)
        parent.add_change_log_entry(action='Edit', field='Product Component', original_value=old_value, new_value=new_value)

        # Group installed components so can show them grouped on page
        components_array = arrange_product_components(parent)
        extra_components_array = arrange_extra_product_components(parent)

        variables = {
            'success': True,
            'product': parent,
            'components_array': components_array,
            'extra_components_array': extra_components_array
        }
        return render_template('product/as-built/component_list.html', **variables)
    return jsonify({'success': True}), 200, {'ContentType': 'application/json'}


@blueprint.route('/extra_component/update', methods=['POST'])
@login_required
def update_extra_product_component():
    id = request.form['pk']
    # UID for field will be ala [fieldname]-[classname]-[id]-editable, field name will be first section always
    field = request.form['name'].split('-')[0]
    field_value = request.form['value']
    # TODO: Check if product component exists
    product_component = ExtraProductComponent.get_by_id(id)
    parent = product_component.parent
    if field == 'product':
        product = Product.get_by_id(field_value)

        # Change log on this product and on product making up the component
        if product_component.product:
            p = product_component.product
            old_value = '{0} (1)'.format(p.get_descriptive_url())
            p.add_change_log_entry(action='Remove', field='Extra Product Component',
                                   original_value='Removed as Extra Product Component on {0}'.format(parent.get_descriptive_url()))
        else:
            old_value = '{0} - Empty (1)'.format(product_component.part.get_descriptive_url())
        if product:
            new_value = '{0} (1)'.format(product.get_descriptive_url())
            product.add_change_log_entry(action='Add', field='Extra Product Component',
                                         original_value='Added as Extra Product Component on {0}'.format(parent.get_descriptive_url()))
        else:
            p = product_component.part
            new_value = '{0} - Empty (1)'.format(p.get_descriptive_url())
        parent.add_change_log_entry(action='Edit', field='Extra Product Component', original_value=old_value, new_value=new_value)

        product_component.update(product=product)
        # Group installed components so can show them grouped on page
        components_array = arrange_product_components(parent)
        extra_components_array = arrange_extra_product_components(parent)

        variables = {
            'success': True,
            'product': parent,
            'components_array': components_array,
            'extra_components_array': extra_components_array
        }
        return render_template('product/as-built/component_list.html', **variables)
    elif field == 'product_all':
        product = Product.get_by_id(field_value)
        if product.product_type != 'SN':
            qty = product_component.update_all_unassigned_extra_product_components_for_part(product)
        else:
            product_component.update(product=product)
            qty = 1

        # Add change log, this method will only be used when adding new components
        product.add_change_log_entry(action='Add', field='Extra Product Component',
                                     original_value='Added as Extra Product Component on {0}'.format(parent.get_descriptive_url()))
        old_value = '{0} - Empty ({1})'.format(product.part.get_descriptive_url(), qty)
        new_value = '{0} ({1})'.format(product.get_descriptive_url(), qty)
        parent.add_change_log_entry(action='Edit', field='Extra Product Component', original_value=old_value, new_value=new_value)

        # Group installed components so can show them grouped on page
        components_array = arrange_product_components(parent)
        extra_components_array = arrange_extra_product_components(parent)

        variables = {
            'success': True,
            'product': parent,
            'components_array': components_array,
            'extra_components_array': extra_components_array
        }
        return render_template('product/as-built/component_list.html', **variables)
    if field == 'vendor_product':
        vendor_product = VendorProduct.get_by_id(field_value)

        # Change log on this product and on vendor_product making up the component
        if product_component.vendor_product:
            vp = product_component.vendor_product
            old_value = '{0} (1)'.format(vp.get_descriptive_url())
            vp.add_change_log_entry(action='Remove', field='Extra Product Component',
                                   original_value='Removed as Extra Product Component on {0}'.format(parent.get_descriptive_url()))
        else:
            old_value = '{0} - Empty (1)'.format(product_component.vendor_part.get_descriptive_url())
        if vendor_product:
            new_value = '{0} (1)'.format(vendor_product.get_descriptive_url())
            vendor_product.add_change_log_entry(action='Add', field='Extra Product Component',
                                                original_value='Added as Extra Product Component on {0}'.format(parent.get_descriptive_url()))
        else:
            new_value = '{0} - Empty (1)'.format(product_component.vendor_part.get_descriptive_url())
        parent.add_change_log_entry(action='Edit', field='Extra Product Component', original_value=old_value, new_value=new_value)

        product_component.update(vendor_product=vendor_product)
        # Group installed components so can show them grouped on page
        components_array = arrange_product_components(parent)
        extra_components_array = arrange_extra_product_components(parent)

        variables = {
            'success': True,
            'product': parent,
            'components_array': components_array,
            'extra_components_array': extra_components_array
        }
        return render_template('product/as-built/component_list.html', **variables)
    elif field == 'vendor_product_all':
        vendor_product = VendorProduct.get_by_id(field_value)
        if vendor_product.product_type != 'SN':
            qty = product_component.update_all_unassigned_extra_product_components_for_vendor_part(vendor_product)
        else:
            product_component.update(vendor_product=vendor_product)
            qty = 1

        # Add change log, this method will only be used when adding new components
        vendor_product.add_change_log_entry(action='Add', field='Extra Product Component',
                                            original_value='Added as Extra Product Component on {0}'.format(parent.get_descriptive_url()))
        old_value = '{0} - Empty ({1})'.format(vendor_product.vendor_part.get_descriptive_url(), qty)
        new_value = '{0} ({1})'.format(vendor_product.get_descriptive_url(), qty)
        parent.add_change_log_entry(action='Edit', field='Extra Product Component', original_value=old_value, new_value=new_value)

        # Group installed components so can show them grouped on page
        components_array = arrange_product_components(parent)
        extra_components_array = arrange_extra_product_components(parent)

        variables = {
            'success': True,
            'product': parent,
            'components_array': components_array,
            'extra_components_array': extra_components_array
        }
        return render_template('product/as-built/component_list.html', **variables)
    return jsonify({'success': True}), 200, {'ContentType': 'application/json'}


@blueprint.route('/<string:design_number>-<string:part_identifier>-<string:serial_number>', methods=['GET'])
@login_required
def view_product(design_number, part_identifier, serial_number):
    product = Product.get_product_by_product_number(design_number, part_identifier, serial_number)
    serial_numbers = Product.get_serial_numbers_for_design_number_and_part_identifier(product.part.design.design_number, product.part.part_identifier)
    projects = Project.query.all()
    companies = Company.get_all_with_pri_on_top()
    hardware_types = HardwareType.query.all()
    users = User.query.all()
    dispositions = Disposition.query.all()
    components_array = arrange_product_components(product)  # Group installed components so can show them grouped on page
    extra_components_array = arrange_extra_product_components(product)
    installed_ins = defaultdict(list)
    for pc in product.get_installed_ins():
        installed_ins[pc.parent.product_number].append(pc)
    variables = {
        'product': product,
        'projects': projects,
        'hardware_types': hardware_types,
        'users': users,
        'serial_numbers': serial_numbers,
        'components_array': components_array,
        'extra_components_array': extra_components_array,
        'dispositions': dispositions,
        'companies': companies,
        'installed_ins': installed_ins
    }
    return render_template('product/view_product.html', **variables)


# ===== HELPER FUNCTIONS ===== #

def arrange_product_components(product):
    components_array = []
    index = 0
    product_indexes = {}
    vendor_product_indexes = {}
    part_indexes = {}
    vendor_part_indexes = {}
    for component in product.components:
        if component.product and component.product.product_type != 'SN':
            old_index = product_indexes.get(component.product.id, None)
            if old_index is not None:  # Already have an entry for product_id, append to there
                multiple_components = components_array[old_index]
                multiple_components.append(component)
                components_array[old_index] = multiple_components
            else:  # Create new entry for product_id
                product_indexes[component.product.id] = index
                components_array.append([component])
                index += 1
        elif component.vendor_product and component.vendor_product.product_type != 'SN':
            old_index = vendor_product_indexes.get(component.vendor_product.id, None)
            if old_index is not None:  # Already have an entry for product_id, append to there
                multiple_components = components_array[old_index]
                multiple_components.append(component)
                components_array[old_index] = multiple_components
            else:  # Create new entry for product_id
                vendor_product_indexes[component.vendor_product.id] = index
                components_array.append([component])
                index += 1
        elif component.product:
            # Serial numbers get their own row (lucky bastards)
            components_array.append([component])
            components_array[index] = [component]
            index += 1
        elif component.vendor_product:
            # Serial numbers get their own row (lucky bastards)
            components_array.append([component])
            components_array[index] = [component]
            index += 1
        else:
            if component.part:
                old_index = part_indexes.get(component.part.id, None)
            else:
                old_index = vendor_part_indexes.get(component.vendor_part.id, None)
            if old_index is not None:  # Already have an entry for part_id, append to there
                multiple_components = components_array[old_index]
                multiple_components.append(component)
                components_array[old_index] = multiple_components
            else:  # Create new entry for part_id or vendor_id
                if component.part:
                    part_indexes[component.part.id] = index
                else:
                    vendor_part_indexes[component.vendor_part.id] = index
                components_array.append([component])
                index += 1
    return components_array


def arrange_extra_product_components(product):
    components_array = []
    index = 0
    product_indexes = {}
    vendor_product_indexes = {}
    part_indexes = {}
    vendor_part_indexes = {}
    for component in product.extra_components:
        if component.product and component.product.product_type != 'SN':
            old_index = product_indexes.get(component.product.id, None)
            if old_index is not None:  # Already have an entry for product_id, append to there
                multiple_components = components_array[old_index]
                multiple_components.append(component)
                components_array[old_index] = multiple_components
            else:  # Create new entry for product_id
                product_indexes[component.product.id] = index
                components_array.append([component])
                index += 1
        elif component.vendor_product and component.vendor_product.product_type != 'SN':
            old_index = vendor_product_indexes.get(component.vendor_product.id, None)
            if old_index is not None:  # Already have an entry for product_id, append to there
                multiple_components = components_array[old_index]
                multiple_components.append(component)
                components_array[old_index] = multiple_components
            else:  # Create new entry for product_id
                vendor_product_indexes[component.vendor_product.id] = index
                components_array.append([component])
                index += 1
        elif component.product:
            # Serial numbers get their own row (lucky bastards)
            components_array.append([component])
            components_array[index] = [component]
            index += 1
        elif component.vendor_product:
            # Serial numbers get their own row (lucky bastards)
            components_array.append([component])
            components_array[index] = [component]
            index += 1
        else:
            if component.part:
                old_index = part_indexes.get(component.part.id, None)
            else:
                old_index = vendor_part_indexes.get(component.vendor_part.id, None)
            if old_index is not None:  # Already have an entry for part_id, append to there
                multiple_components = components_array[old_index]
                multiple_components.append(component)
                components_array[old_index] = multiple_components
            else:  # Create new entry for part_id or vendor_id
                if component.part:
                    part_indexes[component.part.id] = index
                else:
                    vendor_part_indexes[component.vendor_part.id] = index
                components_array.append([component])
                index += 1
    return components_array


@blueprint.route('/create_discrepancy', methods=['POST'])
@login_required
def create_discrepancy():
    parent_id = request.values['pk']
    parent_class = request.values['class']
    description = request.values['description']
    disposition_id = request.values['disposition_id']
    justification = request.values['justification']
    state = request.values['state']
    parent = get_record_by_id_and_class(parent_id, parent_class)
    disposition = Disposition.get_by_id(disposition_id)
    discrepancy = Discrepancy.create(created_by=current_user, discrepancy_number='{0:02d}'.format(len(parent.discrepancies) + 1),
                                     description=description, disposition=disposition, justification=justification, state=state)
    parent.discrepancies.append(discrepancy)  # parent should not be None at this point
    log_entry = 'Discrepancy {0}'.format(discrepancy.discrepancy_number)
    parent.add_change_log_entry(action='Add', field='Discrepancy', new_value=log_entry)
    parent.save()
    dispositions = Disposition.query.all()
    variables = {
        'discrepancy': discrepancy,
        'dispositions': dispositions,
        'parent_object': parent
    }
    return render_template('product/discrepancy_row.html', **variables)


@blueprint.route('/update_discrepancy', methods=['POST'])
@login_required
def update_discrepancy():
    # This method differs from other update methods as it's an full table row edit and save
    id = request.values['pk']
    parent_id = request.values['parent_id']
    parent_class = request.values['parent_class']
    parent = get_record_by_id_and_class(parent_id, parent_class)
    discrepancy = Discrepancy.get_by_id(int(id))
    field = 'Discrepancy {0}'.format(discrepancy.discrepancy_number)
    if discrepancy.description != request.values['description']:
        old_value = discrepancy.description
        discrepancy.update(description=request.values['description'], commit=False)
        parent.add_change_log_entry(action='Edit', field=field, original_value=old_value,
                                    new_value=request.values['description'])
    if int(discrepancy.disposition_id) != int(request.values['disposition']):
        old_value = discrepancy.disposition.name
        if not request.values['disposition'] == 'None':
            disposition = Disposition.get_by_id(request.values['disposition'])
            new_value = disposition.name
            discrepancy.update(disposition_id=request.values['disposition'], commit=False)
            parent.add_change_log_entry(action='Edit', field=field, original_value=old_value, new_value=new_value)
        else:
            discrepancy.update(disposition_id=None, commit=False)
            parent.add_change_log_entry(action='Edit', field=field, original_value=old_value)
    if discrepancy.justification != request.values['justification']:
        old_value = discrepancy.justification
        discrepancy.update(justification=request.values['justification'], commit=False)
        parent.add_change_log_entry(action='Edit', field=field, original_value=old_value,
                                    new_value=request.values['justification'])
    if discrepancy.state != request.values['state']:
        old_value = discrepancy.state
        discrepancy.update(state=request.values['state'], commit=False)
        parent.add_change_log_entry(action='Edit', field=field, original_value=old_value,
                                    new_value=request.values['state'])
    discrepancy.save()
    variables = {
        'discrepancy': discrepancy,
        'dispositions': Disposition.query.all(),
        'parent_object': parent
    }
    return render_template('product/discrepancy_row.html', **variables)


@blueprint.route('/<string:design_number>-<string:part_identifier>-<string:serial_number>/as-built-list', methods=['GET'])
@login_required
def get_as_built_list(design_number, part_identifier, serial_number):
    product = Product.get_product_by_product_number(design_number, part_identifier, serial_number)
    variables = {
        'product': product,
        'components': arrange_product_components(product),
        'extra_components': arrange_extra_product_components(product),
        'arrange_product_components': arrange_product_components,
        'arrange_extra_product_components': arrange_extra_product_components
    }
    return render_template('product/as-built/as_built_list.html', **variables)


@blueprint.route('/advanced_search', methods=['GET'])
@login_required
def advanced_search_products():
    params = request.args.to_dict()
    products = Product.advanced_search(params)
    results = []
    for product in products:
        product_dict = {
            'part_number': product.part.part_number,
            'serial_number': product.serial_number,
            'id': product.part.part_number + ' - ' + product.serial_number,
            'title': product.get_name(),
            'state': product.state,
            'hardware_type': product.hardware_type.name,
            'owner': product.owner.get_name(),
            'material': product.part.material.name if product.part.material else '',
            'notes': product.notes,
            'project': product.project.name,
            'created_by': product.created_by.get_name(),
            'created_at': product.created_at,
            'url': product.get_url()
        }
        results.append(product_dict)
    return jsonify({'success': True, 'data': results}), 200, {'ContentType': 'application/json'}


@blueprint.route('/get_view_build_modal', methods=['POST'])
@login_required
def get_view_build_modal():
    build_id = request.values['build_id']
    build = Build.get_by_id(build_id)
    variables = {
        'build': build
    }
    return render_template('product/view_build_modal.html', **variables)
