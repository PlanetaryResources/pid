# -*- coding: utf-8 -*-
"""Design views."""
from flask import Blueprint, request, jsonify, render_template, make_response
from flask_login import login_required, current_user
from sqlalchemy.orm import subqueryload, joinedload
from .forms import CreateAsRunForm
from .models import AsRun
from pid.common.models import Project, Approver
from pid.user.models import User
from pid.procedure.models import Procedure
from pid.product.models import Product
from pid.vendorproduct.models import VendorProduct
from pid.mail import send_email

blueprint = Blueprint('asrun', __name__, url_prefix='/asrun', static_folder='../static')


@blueprint.route('/create', methods=['POST'])
@login_required
def create_as_run():
    """Create new As-Run."""
    form = CreateAsRunForm(request.form)
    validated = form.validate_on_submit()

    if validated:
        procedure_id = request.form['procedure_id']
        procedure = Procedure.get_by_id(procedure_id)
        as_run_number = AsRun.find_next_as_run_number(procedure)
        variables = {
            'owner': form.owner.data,
            'procedure': procedure,
            'project': procedure.project,
            'as_run_number': as_run_number
        }
        as_run = AsRun.create(**variables)

        product_ids = [] if request.form['products'] == '' else request.form['products'].split(',')
        for product_id in product_ids:
            product = Product.get_by_id(product_id)
            as_run.products.append(product)

        vendor_product_ids = [] if request.form['vendor_products'] == '' else request.form['vendor_products'].split(',')
        for vendor_product_id in vendor_product_ids:
            vendor_product = VendorProduct.get_by_id(vendor_product_id)
            as_run.vendor_products.append(vendor_product)

        as_run.save()

        jsonData = {
            'success': True,
            'url': as_run.get_url()
        }
        return jsonify(jsonData), 200, {'ContentType': 'application/json'}
    else:
        procedure_id = request.form['procedure_id']
        procedure = Procedure.get_by_id(procedure_id)
        as_run_instance = str(AsRun.find_next_as_run_number(procedure)).zfill(3)
        return make_response(render_template('asrun/create_as_run.html', form=form, proc=procedure, as_run_instance=as_run_instance), 500)


@blueprint.route('/update', methods=['POST'])
@login_required
def update_as_run():
    id = request.form['pk']
    # UID for field will be ala [fieldname]-[classname]-[id]-editable, field name will be first section always
    field = request.form['name'].split('-')[0]
    field_value = request.form['value']
    as_run = AsRun.get_by_id(id)
    original_value = None

    if field == 'name':
        original_value = as_run.name
        as_run.update(name=field_value)
    elif field == 'notes':
        original_value = as_run.notes
        as_run.update(notes=field_value)
    elif field == 'software_version':
        original_value = as_run.software_version
        as_run.update(software_version=field_value)
    elif field == 'summary':
        original_value = as_run.summary
        as_run.update(summary=field_value)
    elif field == 'thumbnail_id':
        thumbnail_id = None if field_value == 'default' else field_value
        as_run.update(thumbnail_id=thumbnail_id)
        return render_template('shared/thumbnail_return.html', record=as_run)
    elif field == 'project':
        if as_run.project:
            original_value = as_run.project.name
        project = Project.get_by_id(field_value)
        as_run.update(project=project)
        field_value = project.name if project else None
    elif field == 'owner':
        if as_run.owner:
            original_value = as_run.owner.get_name()
            if as_run.owner.padawan:
                for approver in as_run.approvers:
                    if approver.approver == as_run.owner.supervisor and approver.capacity == 'Supervisor':
                        as_run.approvers.remove(approver)
                        approver.delete()
        owner = User.get_by_id(field_value)
        if owner.padawan:
            approver = Approver.create(approver_id=owner.supervisor_id, capacity='Supervisor')
            as_run.approvers.append(approver)
        as_run.update(owner=owner)
        field_value = owner.get_name() if owner else None

    as_run.add_change_log_entry(action='Edit', field=field.title().replace('_', ' '),
                                original_value=original_value, new_value=field_value)

    return jsonify({'success': True}), 200, {'ContentType': 'application/json'}


@blueprint.route('/update_state', methods=['POST'])
@login_required
def update_as_run_state():
    # TODO: verify that current_user is owner of record and can edit it
    design_id = request.values['parent_id']
    state = request.form['state']
    transition = request.form['transition']
    comment = request.values['comment']
    as_run = AsRun.get_by_id(design_id)
    as_run.update(state=state)
    as_run.add_workflow_log_entry(capacity='Owner', action=transition, comment=comment)
    if state == as_run.workflow.get_approval_state():
        for approver in as_run.approvers:
            if not approver.approved_at:
                variables = {
                    'record': as_run,
                    'approver': approver,
                    'comment': comment
                }
                send_email(subject='Approval Required for {0}: {1}'.format(as_run.descriptor, as_run.get_name()),
                           recipients=[approver.approver.email],
                           text_body=render_template('mail/approvals/new_approver.txt', **variables),
                           html_body=render_template('mail/approvals/new_approver.html', **variables))
    elif state == as_run.workflow.released_state:
        # Only self-approval will trigger this
        as_run.add_workflow_log_entry(capacity='PLAIDmin', action='Approved')
    return jsonify({'success': True}), 200, {'ContentType': 'application/json'}


@blueprint.route('/<string:procedure_number>/<string:as_run_number>', methods=['GET'])
@login_required
def view_as_run(procedure_number, as_run_number):
    """View existing as-run."""
    raw_as_run_number = int(as_run_number.lstrip('0'))
    as_run = AsRun.query.filter_by(procedure_number=procedure_number, as_run_number=raw_as_run_number).options(
                                   joinedload('procedure'), subqueryload('procedure.parts'), subqueryload('procedure.vendor_parts')).one()  # noqa
    users = User.query.all()
    projects = Project.query.all()
    instances = as_run.find_all_procedure_as_runs_numbers(as_run.procedure_number)
    variables = {
        'as_run': as_run,
        'instances': instances,
        'users': users,
        'projects': projects,
        'as_run_number': as_run_number
    }
    return render_template('asrun/view_as_run.html', **variables)


@blueprint.route('/get_create_modal', methods=['POST'])
@login_required
def get_as_run_modal():
    form = CreateAsRunForm(request.form)
    procedure_id = request.form.get('procedure_id')
    procedure = Procedure.get_by_id(procedure_id)
    as_run_instance = str(AsRun.find_next_as_run_number(procedure))
    return render_template('asrun/create_as_run.html', form=form, proc=procedure, as_run_instance=as_run_instance)


@blueprint.route('/add_product', methods=['POST'])
@login_required
def add_product():
    as_run_id = request.form.get('as_run_id')
    product_type = request.form.get('product_type')
    product_id = request.form.get('product_id')
    as_run = AsRun.get_by_id(as_run_id)
    if product_type == "design":
        product = Product.get_by_id(product_id)
        if product in as_run.products:
            jsonData = {
                'success': False,
                'message': "Product already added."
            }
            return jsonify(jsonData), 500, {'ContentType': 'application/json'}
        as_run.products.append(product)
    elif product_type == "vendor":
        product = VendorProduct.get_by_id(product_id)
        if product in as_run.vendor_products:
            jsonData = {
                'success': False,
                'message': "Product already added."
            }
            return jsonify(jsonData), 500, {'ContentType': 'application/json'}
        as_run.vendor_products.append(product)
    as_run.add_change_log_entry(action='Add', field='Product', new_value=product.get_descriptive_url())
    as_run.save()
    return render_template('asrun/as_run_product.html', as_run=as_run, product=product)


@blueprint.route('/remove_product', methods=['POST'])
@login_required
def remove_product():
    as_run_id = request.form.get('as_run_id')
    product_type = request.form.get('product_type')
    product_id = request.form.get('product_id')
    as_run = AsRun.get_by_id(as_run_id)
    if product_type == "design":
        product = Product.get_by_id(product_id)
        as_run.products.remove(product)
    elif product_type == "vendor":
        product = VendorProduct.get_by_id(product_id)
        as_run.vendor_products.remove(product)
    as_run.add_change_log_entry(action='Add', field='Product', original_value=product.get_descriptive_url())
    as_run.save()
    jsonData = {
        'success': True,
        'productId': product_id
    }
    return jsonify(jsonData), 200, {'ContentType': 'application/json'}


@blueprint.route('/typeahead_search', methods=['GET'])
@login_required
def typeahead_search():
    query = request.args.get('query')
    as_runs = AsRun.typeahead_search(query)
    results = []
    for as_run in as_runs:
        results_dict = {}
        results_dict['class'] = as_run.get_class_name()
        results_dict['icon'] = '<i class="pri-typeahead-icon pri-icons-record-as-run" aria-hidden="true"></i>'
        results_dict['id'] = as_run.id
        results_dict['name'] = as_run.get_name()
        results_dict['number'] = as_run.get_unique_identifier()
        results_dict['object_type'] = 'As Run'
        results_dict['state'] = as_run.state
        results_dict['thumb_url'] = as_run.get_thumbnail_url()
        results_dict['url'] = as_run.get_url()
        results.append(results_dict)
    return jsonify({'success': True, 'data': results}), 200, {'ContentType': 'application/json'}
