# -*- coding: utf-8 -*-
"""Design views."""
from flask import Blueprint, request, jsonify, render_template, make_response
from flask_login import login_required, current_user
from .forms import CreateAnomalyForm
from .models import Anomaly
from pid.common.models import Criticality, Project, Approver
from pid.mail import send_email
from pid.user.models import User
from pid.design.models import Design
from pid.vendorpart.models import VendorPart
from pid.asrun.models import AsRun

blueprint = Blueprint('anomaly', __name__, url_prefix='/anomaly', static_folder='../static')


@blueprint.route('/create', methods=['POST'])
@login_required
def create_anomaly():
    """Create new anomaly."""
    form = CreateAnomalyForm(request.form)
    validated = form.validate_on_submit()
    if validated:
        variables = {
            'name': form.name.data,
            'criticality': form.criticality.data,
            'owner': form.owner.data,
            'anomaly_type': form.affected.data
        }
        anomaly = Anomaly.create(**variables)
        if form.affected.data == 'design':
            for design_id in form.designs.data.split(','):
                design = Design.get_by_id(design_id)
                if design != None:
                    anomaly.designs.append(design)
                    design.anomalies.append(anomaly)
                    design.save()
            for vendor_part_id in form.vendor_parts.data.split(','):
                vendor_part = VendorPart.get_by_id(vendor_part_id)
                if vendor_part != None:
                    anomaly.vendor_parts.append(vendor_part)
                    vendor_part.anomalies.append(anomaly)
                    vendor_part.save()
            anomaly.save()
        elif form.affected.data == 'asrun':
            for as_run_id in form.as_runs.data.split(','):
                as_run = AsRun.get_by_id(as_run_id)
                if as_run != None:
                    anomaly.as_runs.append(as_run)
                    as_run.anomalies.append(anomaly)
                    as_run.save()
            anomaly.save()
        jsonData = {
            'success': True,
            'url': anomaly.get_url()
        }
        return jsonify(jsonData), 200, {'ContentType': 'application/json'}
    else:
        designs = []
        vendor_parts = []
        as_runs = []
        print(form.designs.data)
        for design_id in form.designs.data.split(','):
            design = Design.get_by_id(design_id)
            if design != None:
                designs.append(design)
        for vendor_part_id in form.vendor_parts.data.split(','):
            vendor_part = VendorPart.get_by_id(vendor_part_id)
            if vendor_part != None:
                vendor_parts.append(vendor_part)
        for as_run_id in form.as_runs.data.split(','):
            as_run = AsRun.get_by_id(as_run_id)
            if as_run != None:
                as_runs.append(as_run)
        variables = {
            'form': form,
            'designs': designs,
            'vendor_parts': vendor_parts,
            'as_runs': as_runs
        }
        return make_response(render_template('anomaly/create_anomaly.html', **variables), 500)


@blueprint.route('/update', methods=['POST'])
@login_required
def update_anomaly():
    id = request.form['pk']
    # UID for field will be ala [fieldname]-[classname]-[id]-editable, field name will be first section always
    field = request.form['name'].split('-')[0]
    field_value = request.form['value']
    original_value = None
    anomaly = Anomaly.get_by_id(id)

    if field == 'name':
        original_value = anomaly.name
        anomaly.update(name=field_value)
    elif field == 'summary':
        original_value = anomaly.summary
        anomaly.update(summary=field_value)
    elif field == 'analysis':
        original_value = anomaly.analysis
        anomaly.update(analysis=field_value)
    elif field == 'software_version':
        original_value = anomaly.software_version
        anomaly.update(software_version=field_value)
    elif field == 'criticality':
        if anomaly.criticality:
            original_value = anomaly.criticality.name
        criticality = Criticality.get_by_id(field_value)
        anomaly.update(criticality=criticality)
        field_value = criticality.name if criticality else None
    elif field == 'corrective_action':
        original_value = anomaly.corrective_action
        anomaly.update(corrective_action=field_value)
    elif field == 'project':
        if anomaly.project:
            original_value = anomaly.project.name
        project = Project.get_by_id(field_value)
        anomaly.update(project=project)
        field_value = project.name if project else None
    elif field == 'owner':
        if anomaly.owner:
            original_value = anomaly.owner.get_name()
            if anomaly.owner.padawan:
                for approver in anomaly.approvers:
                    if approver.approver == anomaly.owner.supervisor and approver.capacity == 'Supervisor':
                        anomaly.approvers.remove(approver)
                        approver.delete()
        owner = User.get_by_id(field_value)
        if owner.padawan:
            approver = Approver.create(approver_id=owner.supervisor_id, capacity='Supervisor')
            anomaly.approvers.append(approver)
        anomaly.update(owner=owner)
        field_value = owner.get_name() if owner else None
    elif field == 'thumbnail_id':
        thumbnail_id = None if field_value == 'default' else field_value
        anomaly.update(thumbnail_id=thumbnail_id)
        return render_template('shared/thumbnail_return.html', record=anomaly)

    anomaly.add_change_log_entry(action='Edit', field=field.title().replace('_', ' '),
                                 original_value=original_value, new_value=field_value)

    return jsonify({'success': True}), 200, {'ContentType': 'application/json'}


@blueprint.route('/update_state', methods=['POST'])
@login_required
def update_anomaly_state():
    # TODO: verify that current_user is owner of record and can edit it
    design_id = request.values['parent_id']
    state = request.form['state']
    transition = request.form['transition']
    comment = request.values['comment']
    anomaly = Anomaly.get_by_id(design_id)
    anomaly.update(state=state)
    anomaly.add_workflow_log_entry(capacity='Owner', action=transition, comment=comment)
    if state == anomaly.workflow.get_approval_state():
        for approver in anomaly.approvers:
            if not approver.approved_at:
                variables = {
                    'record': anomaly,
                    'approver': approver,
                    'comment': comment
                }
                send_email(subject='Approval Required for {0}: {1}'.format(anomaly.descriptor, anomaly.get_name()),
                           recipients=[approver.approver.email],
                           text_body=render_template('mail/approvals/new_approver.txt', **variables),
                           html_body=render_template('mail/approvals/new_approver.html', **variables))
    elif state == anomaly.workflow.released_state:
        # Only self-approval will trigger this
        anomaly.add_workflow_log_entry(capacity='PLAIDmin', action='Closed')
    return jsonify({'success': True}), 200, {'ContentType': 'application/json'}


@blueprint.route('/<string:key>', methods=['GET'])
@login_required
def view_anomaly(key):
    """View existing anomaly."""
    anomaly = Anomaly.get_by_key(key)
    users = User.query.all()
    projects = Project.query.all()
    variables = {
        'projects': projects,
        'users': users,
        'anomaly': anomaly,
        'criticality_options': Criticality.query.all()
    }
    return render_template('anomaly/view_anomaly.html', **variables)


@blueprint.route('/typeahead_search', methods=['GET'])
@login_required
def typeahead_search():
    query = request.args.get('query')
    anomalies = Anomaly.typeahead_search(query)
    results = []
    for anomaly in anomalies:
        anomaly_dict = {}
        anomaly_dict['class'] = anomaly.get_class_name()
        anomaly_dict['icon'] = '<i class="pri-typeahead-icon pri-icons-record-anomaly" aria-hidden="true"></i>'
        anomaly_dict['id'] = anomaly.id
        anomaly_dict['name'] = anomaly.get_name()
        anomaly_dict['number'] = anomaly.get_unique_identifier()
        anomaly_dict['object_type'] = 'Anomaly'
        anomaly_dict['state'] = anomaly.state
        anomaly_dict['thumb_url'] = anomaly.get_thumbnail_url()
        anomaly_dict['url'] = anomaly.get_url()
        results.append(anomaly_dict)
    return jsonify({'success': True, 'data': results}), 200, {'ContentType': 'application/json'}


@blueprint.route('/get_create_modal', methods=['POST'])
@login_required
def get_anomaly_modal():
    form = CreateAnomalyForm(request.form)
    variables = {
        'form': form,
        'designs': [],
        'vendor_parts': [],
        'as_runs': []
    }
    record_id = request.form.get('record_id', None)
    record_class = request.form.get('record_class', None)
    if record_id:
        if record_class == Design.get_class_name():
            variables['designs'] = [Design.get_by_id(record_id)]
            form.affected.data = 'design'
        elif record_class == VendorPart.get_class_name():
            variables['vendor_parts'] = [VendorPart.get_by_id(record_id)]
            form.affected.data = 'design'
        elif record_class == AsRun.get_class_name():
            variables['as_runs'] = [AsRun.get_by_id(record_id)]
            form.affected.data = 'asrun'
    return render_template('anomaly/create_anomaly.html', **variables)


@blueprint.route('/advanced_search', methods=['GET'])
@login_required
def advanced_search_anomalies():
    params = request.args.to_dict()
    anomalies = Anomaly.advanced_search(params)
    results = []
    for anomaly in anomalies:
        anomaly_dict = {
            'anomaly_number': anomaly.key,
            'name': anomaly.name,
            'state': anomaly.state,
            'criticality': anomaly.criticality.name,
            'project': anomaly.project.name if anomaly.project else '',
            'summary': anomaly.summary,
            'owner': anomaly.owner.get_name(),
            'created_by': anomaly.created_by.get_name(),
            'created_at': anomaly.created_at,
            'url': anomaly.get_url(),
            'corrective_action': anomaly.corrective_action,
            'analysis': anomaly.analysis
        }

        results.append(anomaly_dict)
    return jsonify({'success': True, 'data': results}), 200, {'ContentType': 'application/json'}


@blueprint.route('/get_add_design_typeahead_modal', methods=['POST'])
@login_required
def get_add_design_typeahead_modal():
    anomaly_id = request.values['anomaly_id']
    anomaly = Anomaly.get_by_id(anomaly_id)
    designs = []
    for design in anomaly.designs:
        designs.extend([rev_design.id for rev_design in design.find_all_revisions()])
    vendor_parts = [vendor_part.id for vendor_part in anomaly.vendor_parts]
    variables = {
        'anomaly': anomaly,
        'designs': designs,
        'vendor_parts': vendor_parts
    }
    return render_template('anomaly/add_design_typeahead_modal.html', **variables)


@blueprint.route('/update_design', methods=['POST'])
@login_required
def update_design():
    anomaly_id = request.values['anomaly_id']
    old_design_id = request.values['old_design_id']
    new_design_id = request.values['new_design_id']
    anomaly = Anomaly.get_by_id(anomaly_id)
    old_design = Design.get_by_id(old_design_id)
    new_design = Design.get_by_id(new_design_id)
    anomaly.designs.remove(old_design)
    anomaly.designs.append(new_design)
    anomaly.add_change_log_entry(action='Edit', field='Design', original_value=old_design.get_descriptive_url(),
                                 new_value=new_design.get_descriptive_url())
    anomaly.save()
    variables = {
        'anomaly': anomaly,
        'design': new_design
    }
    return render_template('anomaly/anomaly_design_row.html', **variables)


@blueprint.route('/add_design', methods=['POST'])
@login_required
def add_design():
    anomaly_id = request.values['anomaly_id']
    design_id = request.values['design_id']
    vendor_part_id = request.values['vendor_part_id']
    anomaly = Anomaly.get_by_id(anomaly_id)
    record = None
    if design_id:
        record = Design.get_by_id(design_id)
        anomaly.designs.append(record)
    elif vendor_part_id:
        record = VendorPart.get_by_id(vendor_part_id)
        anomaly.vendor_parts.append(record)
    anomaly.add_change_log_entry(action='Add', field='Design/Part', new_value=record.get_descriptive_url())
    anomaly.save()
    variables = {
        'anomaly': anomaly,
        'design': record
    }
    return render_template('anomaly/anomaly_design_row.html', **variables)


@blueprint.route('/remove_design', methods=['POST'])
@login_required
def remove_design():
    anomaly_id = request.values['anomaly_id']
    anomaly = Anomaly.get_by_id(anomaly_id)
    design_id = request.values['design_id']
    design_class = request.values['design_class']
    record = None
    if design_class == 'design':
        record = Design.get_by_id(design_id)
        anomaly.designs.remove(record)
    elif design_class == 'vendorpart':
        record = VendorPart.get_by_id(design_id)
        anomaly.vendor_parts.remove(record)
    anomaly.add_change_log_entry(action='Remove', field='Design/Part', original_value=record.get_descriptive_url())
    anomaly.save()
    return jsonify({'success': True}), 200, {'ContentType': 'application/json'}
