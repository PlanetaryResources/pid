# -*- coding: utf-8 -*-
"""Design views."""
from flask import Blueprint, request, jsonify, render_template, make_response
from flask_login import login_required, current_user
from .forms import CreateProcedureForm, ReviseProcedureForm
from .models import Procedure
from pid.common.models import Project, Reference, Approver, ChangeLog, WorkflowLog
from pid.mail import send_email
from pid.user.models import User
from pid.part.models import Part
from pid.vendorpart.models import VendorPart
from pid.product.models import Product

blueprint = Blueprint('procedure', __name__, url_prefix='/procedure', static_folder='../static')


@blueprint.route('/create', methods=['POST'])
@login_required
def create_proc():
    """Create new Procedure."""
    form = CreateProcedureForm(request.form)
    validated = form.validate_on_submit()
    if validated:
        kwargs = {
            'name': form.name.data,
            'owner': form.owner.data,
            'project': form.project.data
        }
        procedure = Procedure.create(**kwargs)
        part_ids = [] if request.form['parts'] == '' else request.form['parts'].split(',')
        vendor_part_ids = [] if request.form['vendor_parts'] == '' else request.form['vendor_parts'].split(',')

        for part_id in part_ids:
            part = Part.get_by_id(part_id)
            procedure.parts.append(part)

        for vendor_part_id in vendor_part_ids:
            part = VendorPart.get_by_id(vendor_part_id)
            procedure.vendor_parts.append(part)

        procedure.save()
        jsonData = {
            'success': True,
            'url': procedure.get_url()
        }
        return jsonify(jsonData), 200, {'ContentType': 'application/json'}
    else:
        part_ids = [] if request.form['parts'] == '' else request.form['parts'].split(',')
        vendor_part_ids = [] if request.form['vendor_parts'] == '' else request.form['vendor_parts'].split(',')
        parts = []
        vendor_parts = []
        for part_id in part_ids:
            part = Part.get_by_id(part_id)
            parts.append(part)

        for vendor_part_id in vendor_part_ids:
            part = VendorPart.get_by_id(vendor_part_id)
            vendor_parts.append(part)
        variables = {
            'vendor_parts': vendor_parts,
            'parts': parts,
            'current_part_ids': request.form['parts'],
            'current_vendor_part_ids': request.form['vendor_parts'],
            'form': form
        }
        return make_response(render_template('procedure/create_procedure.html', **variables), 500)


@blueprint.route('/update', methods=['POST'])
@login_required
def update_procedure():
    id = request.form['pk']
    # UID for field will be ala [fieldname]-[classname]-[id]-editable, field name will be first section always
    field = request.form['name'].split('-')[0]
    field_value = request.form['value']
    procedure = Procedure.get_by_id(id)
    original_value = None

    if field == 'name':
        original_value = procedure.name
        procedure.update(name=field_value)
    elif field == 'summary':
        original_value = procedure.summary
        procedure.update(summary=field_value)
    elif field == 'thumbnail_id':
        thumbnail_id = None if field_value == 'default' else field_value
        procedure.update(thumbnail_id=thumbnail_id)
        return render_template('shared/thumbnail_return.html', record=proc)
    elif field == 'project':
        if procedure.project:
            original_value = procedure.project.name
        project = Project.get_by_id(field_value)
        procedure.update(project=project)
        field_value = project.name if project else None
    elif field == 'owner':
        if procedure.owner:
            original_value = procedure.owner.get_name()
            if procedure.owner.padawan:
                for approver in procedure.approvers:
                    if approver.approver == procedure.owner.supervisor and approver.capacity == 'Supervisor':
                        procedure.approvers.remove(approver)
                        approver.delete()
        owner = User.get_by_id(field_value)
        if owner.padawan:
            approver = Approver.create(approver_id=owner.supervisor_id, capacity='Supervisor')
            procedure.approvers.append(approver)
        procedure.update(owner=owner)
        field_value = owner.get_name() if owner else None

    procedure.add_change_log_entry(action='Edit', field=field.title().replace('_', ' '),
                                   original_value=original_value, new_value=field_value)

    return jsonify({'success': True}), 200, {'ContentType': 'application/json'}


@blueprint.route('/update_state', methods=['POST'])
@login_required
def update_procedure_state():
    # TODO: verify that current_user is owner of record and can edit it
    design_id = request.values['parent_id']
    state = request.form['state']
    transition = request.form['transition']
    comment = request.values['comment']
    procedure = Procedure.get_by_id(design_id)
    procedure.update(state=state)
    procedure.add_workflow_log_entry(capacity='Owner', action=transition, comment=comment)
    if state == procedure.workflow.get_approval_state():
        for approver in procedure.approvers:
            if not approver.approved_at:
                variables = {
                    'record': procedure,
                    'approver': approver,
                    'comment': comment
                }
                send_email(subject='Approval Required for {0}: {1}'.format(procedure.descriptor, procedure.get_name()),
                           recipients=[approver.approver.email],
                           text_body=render_template('mail/approvals/new_approver.txt', **variables),
                           html_body=render_template('mail/approvals/new_approver.html', **variables))
    elif state == procedure.workflow.released_state:
        # Only self-approval will trigger this
        comment = 'Revision ' + procedure.revision
        procedure.add_workflow_log_entry(capacity='PLAIDmin', action='Released', comment=comment)
    return jsonify({'success': True}), 200, {'ContentType': 'application/json'}


@blueprint.route('/<string:procedure_number>-<string:revision>', methods=['GET'])
@login_required
def view_procedure(procedure_number, revision):
    """View existing procedure."""
    procedure = Procedure.get_by_procedure_number_and_revision(procedure_number, revision)
    users = User.query.all()
    projects = Project.query.all()
    revisions = procedure.find_all_revisions()
    variables = {
        'proc': procedure,
        'revisions': revisions,
        'users': users,
        'projects': projects
    }
    return render_template('procedure/view_procedure.html', **variables)


@blueprint.route('/typeahead_search', methods=['GET'])
@login_required
def typeahead_search():
    query = request.args.get('query')
    procedures = Procedure.typeahead_search(query)
    results = []
    for proc in procedures:
        proc_dict = {}
        proc_dict['as_runs'] = proc.find_all_as_runs_numbers()
        proc_dict['class'] = proc.get_class_name()
        proc_dict['name'] = proc.name
        proc_dict['icon'] = '<i class="pri-typeahead-icon pri-icons-record-procedure" aria-hidden="true"></i>'
        proc_dict['id'] = proc.id
        proc_dict['number'] = proc.procedure_number
        proc_dict['object_type'] = 'Procedure'
        proc_dict['state'] = proc.state
        proc_dict['thumb_url'] = proc.get_thumbnail_url()
        proc_dict['url'] = proc.get_url()
        results.append(proc_dict)
    return jsonify({'success': True, 'data': results}), 200, {'ContentType': 'application/json'}


@blueprint.route('/get_create_modal', methods=['POST'])
@login_required
def get_procedure_modal():
    form = CreateProcedureForm(request.form)
    vendor_parts = []
    parts = []
    table = request.form.get('table', None)
    part_id = request.form.get('part_id', None)
    if table:
        if table == 'vendor_parts':
            vendor_parts.append(VendorPart.get_by_id(part_id))
        elif table == 'designs':
            parts.append(Part.get_by_id(part_id))

    variables = {
        'vendor_parts': vendor_parts,
        'parts': parts,
        'current_part_ids': ','.join([str(x.id) for x in parts]),
        'current_vendor_part_ids': ','.join([str(x.id) for x in vendor_parts]),
        'form': form
    }
    return render_template('procedure/create_procedure.html', **variables)


@blueprint.route('/get_revise_procedure_modal', methods=['POST'])
@login_required
def get_revise_procedure_modal():
    form = ReviseProcedureForm(request.form)
    procedure_id = request.form.get('procedure_id')
    procedure = Procedure.get_by_id(procedure_id)
    variables = {
        'proc': procedure,
        'form': form
    }
    return render_template('procedure/revise_procedure.html', **variables)


@blueprint.route('/revise', methods=['POST'])
@login_required
def revise_procedure():
    form = ReviseProcedureForm(request.form)
    validated = form.validate_on_submit()
    old_procedure_id = request.form['procedure_id']
    old_proc = Procedure.get_by_id(old_procedure_id)

    if validated:
        new_revision = old_proc.find_next_revision()
        reason = request.form['revision_reason']
        links = old_proc.links
        documents = old_proc.documents
        images = old_proc.images
        parts = old_proc.parts
        vendor_parts = old_proc.vendor_parts
        references_to = old_proc.references_to
        old_revision = old_proc.revision
        replace_values = {
            'revision': new_revision,
            'revision_reason': reason,
            'created_by': current_user,
            'state': old_proc.workflow.initial_state,
            'self_approved': Procedure.self_approved.default.arg
        }
        proc = old_proc.clone(replace_values)  # After this point, old_proc is the same as proc, a cloned instance

        # Clone links
        for old_link in links:
            link = old_link.clone()
            proc.links.append(link)
        # Clone documents
        for old_document in documents:
            document = old_document.clone_document(proc)
            proc.documents.append(document)
        # Clone images
        for old_image in images:
            image = old_image.clone_image(proc)
            proc.images.append(image)
        # Clone parts
        for old_part in parts:
            proc.parts.append(old_part)
        # CLone vendor parts
        for old_part in vendor_parts:
            proc.vendor_parts.append(old_part)
        # Clone what this references
        for reference in references_to:
            Reference.create(by_id=proc.id, by_class=proc.get_class_name(), to_id=reference.to_id, to_class=reference.to_class)
        # Create new change log and new workflow log
        proc.change_log = ChangeLog.create()
        proc.workflow_log = WorkflowLog.create()
        # Add supervisor approval if user is a padawan
        if current_user.padawan:
            approver = Approver.create(approver_id=current_user.supervisor_id, capacity='Supervisor')
            proc.approvers.append(approver)
        proc.save()

        # Update revision log
        proc.revision_log.add_entry(proc.revision, reason, current_user)

        jsonData = {
            'success': True,
            'url': proc.get_url()
        }
        return jsonify(jsonData), 200, {'ContentType': 'application/json'}
    else:
        return make_response(render_template('procedure/revise_procedure.html', form=form, proc=old_proc), 500)


@blueprint.route('/get_add_part_typeahead_modal', methods=['POST'])
@login_required
def get_add_part_typeahead_modal():
    procedure_id = request.form.get('procedure_id')
    proc = Procedure.get_by_id(procedure_id)
    parts = [str(part.id) for part in proc.parts]
    vendor_parts = [str(vendor_part.id) for vendor_part in proc.vendor_parts]
    variables = {
        'procedure_id': proc.id,
        'parts': parts,
        'vendor_parts': vendor_parts
    }
    return render_template('procedure/add_part_typeahead_modal.html', **variables)


@blueprint.route('/add_part', methods=['POST'])
@login_required
def add_part():
    procedure_id = request.form.get('procedure_id')
    record_id = request.form.get('record_id')
    record_class = request.form.get('record_class')
    proc = Procedure.get_by_id(procedure_id)
    part = None
    if record_class == "part":
        part = Part.get_by_id(record_id)
        proc.parts.append(part)
    elif record_class == "vendorpart":
        part = VendorPart.get_by_id(record_id)
        proc.vendor_parts.append(part)
    proc.add_change_log_entry(action='Add', field='Part', new_value=part.get_descriptive_url())
    proc.save()
    return render_template('procedure/procedure_part.html', part=part, proc=proc)


@blueprint.route('/remove_part', methods=['POST'])
@login_required
def remove_part():
    procedure_id = request.form.get('procedure_id')
    part_type = request.form.get('part_type')
    part_id = request.form.get('part_id')
    proc = Procedure.get_by_id(procedure_id)
    part = None
    if part_type == "designs":
        part = Part.get_by_id(part_id)
        proc.parts.remove(part)
    elif part_type == "vendor_parts":
        part = VendorPart.get_by_id(part_id)
        proc.vendor_parts.remove(part)
    proc.add_change_log_entry(action='Remove', field='Part', original_value=part.get_descriptive_url())
    proc.save()
    jsonData = {
        'success': True,
        'partId': part_id
    }
    return jsonify(jsonData), 200, {'ContentType': 'application/json'}


@blueprint.route('/<int:procedure_id>/update_part_revision/<int:part_id>', methods=['POST'])
@login_required
def update_part_revision(procedure_id, part_id):
    # TODO: Change this away from hardcoded URL, but using ajax select field now which just calls this as api_url
    proc = Procedure.get_by_id(procedure_id)
    procedure = Procedure.get_by_id(procedure_id)
    new_part_id = request.form['value']
    part = Part.get_by_id(part_id)
    new_part = Part.get_by_id(new_part_id)

    # Remove association to part from old revision
    procedure.parts.remove(part)

    # Add new association to part from new revision
    procedure.parts.append(new_part)

    procedure.save()
    return render_template('procedure/procedure_part.html', part=new_part, proc=proc)


@blueprint.route('/advanced_search', methods=['GET'])
@login_required
def advanced_search_procedures():
    params = request.args.to_dict()
    procedures = Procedure.advanced_search(params)
    results = []
    for procedure in procedures:
        procedure_dict = {
            'procedure_number': procedure.procedure_number,
            'revision': procedure.revision,
            'name': procedure.name,
            'state': procedure.state,
            'summary': procedure.summary,
            'owner': procedure.owner.get_name(),
            'project': procedure.project.name,
            'created_by': procedure.created_by.get_name(),
            'created_at': procedure.created_at,
            'url': procedure.get_url()
        }
        results.append(procedure_dict)
    return jsonify({'success': True, 'data': results}), 200, {'ContentType': 'application/json'}
