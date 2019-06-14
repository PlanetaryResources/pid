# -*- coding: utf-8 -*-
"""Common views."""
from flask import Blueprint, redirect, url_for, jsonify, make_response, render_template, request
from flask_login import login_required, current_user
from sqlalchemy import exc
from .models import Criticality, Disposition, HardwareType, Company, Reference, Bookmark, AdvancedSearch, Approver, RevisionLogEntry
from .forms import CreateCompanyForm
import json
import datetime as dt
from pid.database import db, get_record_by_id_and_class
from pid.user.models import User
from pid.mail import send_email

blueprint = Blueprint('common', __name__, url_prefix='/common', static_folder='../static')


@blueprint.route('/reorder_criticalities/<string:role>/<int:id>/<string:direction>', methods=['GET', 'POST'])
@login_required
def reorder_criticalities(role, id, direction):
    criticality = Criticality.get_by_id(id)
    old_order = criticality.ordering
    if direction == 'up':
        new_order = criticality.ordering - 1
    if direction == 'down':
        new_order = criticality.ordering + 1
    current_criticality_at_new_order = Criticality.find_by_ordering(new_order)
    if current_criticality_at_new_order is None:
        criticality.update(ordering=new_order)
    else:
        # Save criticality with new temp ordering
        criticality.update(ordering=Criticality.find_highest_free_ordering_plus_one())
        current_criticality_at_new_order.update(ordering=old_order)
        criticality.update(ordering=new_order)
    return redirect(url_for('{0}_criticalities.index_view'.format(role)))


@blueprint.route('/reorder_dispositions/<string:role>/<int:id>/<string:direction>', methods=['GET', 'POST'])
@login_required
def reorder_dispositions(role, id, direction):
    disposition = Disposition.get_by_id(id)
    old_order = disposition.ordering
    if direction == 'up':
        new_order = disposition.ordering - 1
    if direction == 'down':
        new_order = disposition.ordering + 1
    current_disposition_at_new_order = Disposition.find_by_ordering(new_order)
    if current_disposition_at_new_order is None:
        disposition.update(ordering=new_order)
    else:
        # Save criticality with new temp ordering
        disposition.update(ordering=Disposition.find_highest_free_ordering_plus_one())
        current_disposition_at_new_order.update(ordering=old_order)
        disposition.update(ordering=new_order)
    return redirect(url_for('{0}_dispositions.index_view'.format(role)))


@blueprint.route('/reorder_hardware_types/<string:role>/<int:id>/<string:direction>', methods=['GET', 'POST'])
@login_required
def reorder_hardware_types(role, id, direction):
    hardware_type = HardwareType.get_by_id(id)
    old_order = hardware_type.ordering
    if direction == 'up':
        new_order = hardware_type.ordering - 1
    if direction == 'down':
        new_order = hardware_type.ordering + 1
    current_hardware_type_at_new_order = HardwareType.find_by_ordering(new_order)
    if current_hardware_type_at_new_order is None:
        hardware_type.update(ordering=new_order)
    else:
        # Save criticality with new temp ordering
        hardware_type.update(ordering=HardwareType.find_highest_free_ordering_plus_one())
        current_hardware_type_at_new_order.update(ordering=old_order)
        hardware_type.update(ordering=new_order)
    return redirect(url_for('{0}_hardwaretypes.index_view'.format(role)))


@blueprint.route('/add_reference', methods=['POST'])
@login_required
def add_reference():
    by_id = request.form.get('by_id')
    by_class = request.form.get('by_class')
    to_id = request.form.get('to_id')
    to_class = request.form.get('to_class')
    variables = {
        'by_id': by_id,
        'by_class': by_class,
        'to_id': to_id,
        'to_class': to_class,
    }
    reference = Reference.create(**variables)
    by = get_record_by_id_and_class(by_id, by_class)
    to = get_record_by_id_and_class(to_id, to_class)
    log_entry = 'From {0} to {1}'.format(by.get_descriptive_url(), to.get_descriptive_url())
    by.add_change_log_entry(action='Add', field='Reference', new_value=log_entry, changed_by=current_user)
    to.add_change_log_entry(action='Add', field='Reference', new_value=log_entry, changed_by=current_user)
    variables = {
        'ref': reference,
        'success': True
    }
    return render_template('common/reference_to_row.html', **variables)


@blueprint.route('/delete_reference', methods=['POST'])
@login_required
def delete_reference():
    id = request.form['pk']
    reference = Reference.get_by_id(id)
    by = get_record_by_id_and_class(reference.by_id, reference.by_class)
    to = get_record_by_id_and_class(reference.to_id, reference.to_class)
    log_entry = 'From {0} to {1}'.format(by.get_descriptive_url(), to.get_descriptive_url())
    by.add_change_log_entry(action='Remove', field='Reference', original_value=log_entry, changed_by=current_user)
    to.add_change_log_entry(action='Remove', field='Reference', original_value=log_entry, changed_by=current_user)
    reference.delete()
    return jsonify({'success': True}), 200, {'ContentType': 'application/json'}


@blueprint.route('/get_add_reference_modal', methods=['POST'])
@login_required
def get_add_reference_modal():
    record_id = request.form.get('record_id')
    record_class = request.form.get('record_class')
    variables = {
        'referencing_object_class': record_class,
        'referencing_object_id': record_id
    }
    return render_template('common/add_reference_modal.html', **variables)


@blueprint.route('/add_bookmark', methods=['POST'])
@login_required
def add_bookmark():
    variables = {
        'user_id': request.values['user_id'],
        'bookmarked_id': request.values['bookmark_id'],
        'bookmarked_class': request.values['bookmark_class']
    }
    Bookmark.create(**variables)
    # TODO: Check for success
    return jsonify({'success': True}), 200, {'ContentType': 'application/json'}


@blueprint.route('/remove_bookmark', methods=['POST'])
@login_required
def remove_bookmark():
    user_id = request.values['user_id']
    bookmark_id = request.values['bookmark_id']
    bookmark_class = request.values['bookmark_class']
    Bookmark.query.filter_by(user_id=user_id, bookmarked_id=bookmark_id, bookmarked_class=bookmark_class).first().delete()
    # TODO: Check for success
    return jsonify({'success': True}), 200, {'ContentType': 'application/json'}


@blueprint.route('/company/create', methods=['POST'])
@login_required
def create_company():
    """Create new Company."""
    form = CreateCompanyForm(request.form)
    if request.method == 'POST':
        validated = form.validate_on_submit()

        if validated:
            variables = {
                'name' : form.name.data,
                'website': form.website.data,
                'address': form.address.data,
                'notes': form.notes.data
            }
            try:
                company = Company.create(**variables)
            except exc.IntegrityError:
                db.session.rollback()
                form.name.errors.append('{0} already exists as a company.'.format(form.name.data))
                return make_response(render_template('shared/create_company.html', form=form), 500)

            jsonData = {
                'success': True,
                'companyId': company.id,
                'companyName': company.name
            }
            return jsonify(jsonData), 200, {'ContentType': 'application/json'}
        else:
            return make_response(render_template('shared/create_company.html', form=form), 500)


@blueprint.route('/add_company_modal', methods=['POST'])
@login_required
def get_add_company_modal():
    form = CreateCompanyForm(request.form)
    return render_template('shared/create_company.html', form=form)


@blueprint.route('/get_dispositions_json', methods=['GET'])
@login_required
def get_dispositions_json():
    dispositions = Disposition.query.all()
    json_string = json.dumps([disposition.as_dict() for disposition in dispositions])
    return jsonify(json_string), 200, {'ContentType': 'application/json'}


@blueprint.route('/get_users_json', methods=['GET'])
@login_required
def get_users_json():
    users = User.query.all()
    users.remove(current_user)  # TODO: Need to indicate better that this is here
    json_string = json.dumps([user.as_dict() for user in users])
    return jsonify(json_string), 200, {'ContentType': 'application/json'}


@blueprint.route('/get_changelog_modal', methods=['POST'])
@login_required
def get_changelog_modal():
    record_id = request.form.get('record_id')
    record_class = request.form.get('record_class')
    variables = {
        'parent_object': get_record_by_id_and_class(record_id, record_class)
    }
    return render_template('shared/view_changelog_modal.html', **variables)


@blueprint.route('/get_revisionlog_modal', methods=['POST'])
@login_required
def get_revisionlog_modal():
    record_id = request.form.get('record_id')
    record_class = request.form.get('record_class')
    variables = {
        'parent_object': get_record_by_id_and_class(record_id, record_class)
    }
    return render_template('shared/view_revisionlog_modal.html', **variables)


@blueprint.route('/update_revision_log', methods=['POST'])
@login_required
def update_revision_log():
    entry_id = request.form['pk']
    # UID for field will be ala [fieldname]-[classname]-[id]-editable, field name will be first section always
    field = request.form['name'].split('-')[0]
    field_value = request.form['value']
    entry = RevisionLogEntry.get_by_id(entry_id)
    if field == 'reason':
        entry.update(reason=field_value)
    return jsonify({'success': True}), 200, {'ContentType': 'application/json'}


@blueprint.route('/add_advanced_search', methods=['POST'])
@login_required
def add_advanced_search():
    variables = {
        'user_id': current_user.id,
        'search_parameters': request.values['searchParams'],
        'name': request.values['name']
    }
    AdvancedSearch.create(**variables)
    return jsonify({'success': True}), 200, {'ContentType': 'application/json'}


@blueprint.route('/get_advanced_search_modal', methods=['POST'])
@login_required
def get_advanced_search_modal():
    search_params = request.values['searchParams']
    variables = {'search_params': search_params}
    return render_template('shared/save_search_modal.html', **variables)


@blueprint.route('/get_workflow_comment_modal', methods=['POST'])
@login_required
def get_workflow_comment_modal():
    variables = {
        'parent_class': request.values['parent_class'],
        'parent_id': request.values['parent_id'],
        'state': request.values['state'],
        'transition': request.values['transition']
    }
    return render_template('shared/workflow_comment_modal.html', **variables)


@blueprint.route('/get_workflow_obsolete_modal', methods=['POST'])
@login_required
def get_workflow_obsolete_modal():
    variables = {
        'parent_class': request.values['parent_class'],
        'parent_id': request.values['parent_id'],
        'state': request.values['state'],
        'transition': request.values['transition']
    }
    return render_template('shared/workflow_obsolete_modal.html', **variables)


@blueprint.route('/get_workflow_container', methods=['POST'])
@login_required
def get_workflow_container():
    record_id = request.values['record_id']
    record_class = request.values['record_class']
    record = get_record_by_id_and_class(record_id, record_class)
    return render_template('shared/workflow_container.html', record=record)


@blueprint.route('/add_approver', methods=['POST'])
@login_required
def add_approver():
    # TODO: verify ID's actually have DB entires
    record_id = request.values['pk']
    record_class = request.values['class'].lower()
    record = get_record_by_id_and_class(record_id, record_class)
    variables = {
        'approver_id': request.values['approver_id'],
        'capacity': request.values['capacity']
    }
    approver = Approver.create(**variables)
    record.approvers.append(approver)
    record.save()
    variables = {
        'approver': approver,
        'users': User.query.all(),
        'parent_object': record
    }
    return render_template('shared/approver_row.html', **variables)


@blueprint.route('/update_approver', methods=['POST'])
@login_required
def update_approver():
    # TODO: verify ID's actually have DB entires
    record_id = request.values['parent_id']
    record_class = request.values['parent_class'].lower()
    approver_id = request.values['approver_id']
    approver = Approver.get_by_id(int(approver_id))
    if approver.approver_id != request.values['approver']:
        approver.update(approver_id=request.values['approver'], commit=False)
    if approver.capacity != request.values['capacity']:
        approver.update(capacity=request.values['capacity'], commit=False)
    approver.save()
    record = get_record_by_id_and_class(record_id, record_class)
    variables = {
        'approver': approver,
        'users': User.query.all(),
        'parent_object': record
    }
    return render_template('shared/approver_row.html', **variables)


@blueprint.route('/delete_approver', methods=['POST'])
@login_required
def delete_approver():
    # TODO: verify ID's actually have DB entires
    record_id = request.values['parent_id']
    record_class = request.values['parent_class'].lower()
    approver_id = request.values['approver_id']
    approver = Approver.get_by_id(approver_id)
    record = get_record_by_id_and_class(record_id, record_class)
    record.approvers.remove(approver)
    record.save()
    approver.delete()
    return jsonify({'success': True}), 200, {'ContentType': 'application/json'}


@blueprint.route('/self_approve', methods=['POST'])
@login_required
def self_approve():
    record_id = request.values['parent_id']
    record_class = request.values['parent_class'].lower()
    approve = request.values['approve']
    record = get_record_by_id_and_class(record_id, record_class)
    record.self_approved = approve
    record.save()
    return jsonify({'success': True}), 200, {'ContentType': 'application/json'}


@blueprint.route('/get_approvals', methods=['POST'])
@login_required
def get_approvals():
    record_id = request.values['parent_id']
    record_class = request.values['parent_class'].lower()
    record = get_record_by_id_and_class(record_id, record_class)
    approvals = []
    for approval in record.approvers:
        if current_user == approval.approver and not approval.approved_at:
            approvals.append(approval)
    variables = {
        'parent_object': record,
        'approvals': approvals,
        'users': User.query.all()
    }
    return render_template('shared/approvals_modal.html', **variables)


@blueprint.route('/approve', methods=['POST'])
@login_required
def approve():
    approver_ids = request.values.getlist('approver_id')
    record_id = request.values['parent_id']
    record_class = request.values['parent_class'].lower()
    record = get_record_by_id_and_class(record_id, record_class)
    for approver_id in approver_ids:
        approver = Approver.get_by_id(approver_id)
        resolution = request.values['approval_' + approver_id]
        comment = request.values['approval_comment_' + approver_id]
        if resolution == 'approve':
            approver.approved_at = dt.datetime.utcnow()
            approver.save()
            record.add_workflow_log_entry(current_user, capacity=approver.capacity, action='Approved', comment=comment)
            move_to_released = True
            for approval in record.approvers:
                if not approval.approved_at:
                    move_to_released = False
                    break
            if move_to_released:
                try:
                    comment = 'Revision ' + record.revision
                except AttributeError:
                    comment = None
                #TODO: PLAIDmin user
                record.add_workflow_log_entry(current_user, capacity='PLAIDmin',
                                              action=record.workflow.released_state, comment=comment)
                record.state = record.workflow.released_state
                send_email(subject='{0} {1}: {2}'.format(record.descriptor, record.state, record.get_name()),
                           recipients=[record.owner.email],
                           text_body=render_template('mail/approvals/record_released.txt', record=record),
                           html_body=render_template('mail/approvals/record_released.html', record=record))
            record.save()
        elif resolution =='edit':
            record.add_workflow_log_entry(current_user, capacity=approver.capacity, action='Required Edit',
                                          comment=comment)
            record.state = 'In Work'
            record.save()
            variables = {
                'record': record,
                'approver': approver,
                'comment': comment
            }
            send_email(subject='Edit Required on {0}: {1}'.format(record.descriptor, record.get_name()),
                       recipients=[approver.approver.email],
                       text_body=render_template('mail/approvals/record_required_edit.txt', **variables),
                       html_body=render_template('mail/approvals/record_required_edit.html', **variables))
        elif resolution == 'reassign':
            approver.approver_id = request.values['approval_reassign_' + approver_id]
            approver.save()
            record.add_workflow_log_entry(current_user, capacity=approver.capacity, action='Reassigned',
                                          comment=comment)
            record.save()
            variables = {
                'record': record,
                'approver': approver,
                'comment': comment
            }
            # Send email to owner of record to let him know approver has changed
            send_email(subject='Approval Reassigned for {0}: {1}'.format(record.descriptor, record.get_name()),
                       recipients=[record.owner.email],
                       text_body=render_template('mail/approvals/changed_approver.txt', **variables),
                       html_body=render_template('mail/approvals/changed_approver.html', **variables))
            # Send email to new approver to let him know he needs to approve this record
            send_email(subject='Approval Required: {0}'.format(record.get_name()),
                       recipients=[approver.approver.email],
                       text_body=render_template('mail/approvals/new_approver.txt', **variables),
                       html_body=render_template('mail/approvals/new_approver.html', **variables))
    return jsonify({'success': True}), 200, {'ContentType': 'application/json'}


@blueprint.route('/get_thumbnail_modal', methods=['POST'])
@login_required
def get_thumbnail_modal():
    record_id = request.form.get('record_id')
    record_class = request.form.get('record_class')
    record = get_record_by_id_and_class(record_id, record_class)
    variables = {
        'record': record
    }
    return render_template('shared/thumbnail_modal.html', **variables)
