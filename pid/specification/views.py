# -*- coding: utf-8 -*-
"""Design views."""
from flask import Blueprint, request, jsonify, render_template, make_response
from flask_login import login_required, current_user
from .forms import CreateSpecificationForm, ReviseSpecificationForm
from .models import Specification
from pid.common.models import Project, Reference, Approver, ChangeLog, WorkflowLog
from pid.user.models import User
from pid.mail import send_email

blueprint = Blueprint('specification', __name__, url_prefix='/specification', static_folder='../static')


@blueprint.route('/create', methods=['POST'])
@login_required
def create_spec():
    """Create new Specification."""
    form = CreateSpecificationForm(request.form)
    validated = form.validate_on_submit()

    if validated:
        variables = {
            'name': form.name.data,
            'owner': form.owner.data
        }
        specification = Specification.create(**variables)

        jsonData = {
            'success': True,
            'specId': specification.id,
            'url': specification.get_url()
        }
        return jsonify(jsonData), 200, {'ContentType': 'application/json'}
    else:
        return make_response(render_template('specification/create_specification.html', form=form), 500)


@blueprint.route('/update', methods=['POST'])
@login_required
def update_specification():
    id = request.form['pk']
    # UID for field will be ala [fieldname]-[classname]-[id]-editable, field name will be first section always
    field = request.form['name'].split('-')[0]
    field_value = request.form['value']
    specification = Specification.get_by_id(id)
    original_value = None

    if field == 'name':
        original_value = specification.name
        specification.update(name=field_value)
    elif field == 'scope':
        original_value = specification.scope
        specification.update(scope=field_value)
    elif field == 'summary':
        original_value = specification.summary
        specification.update(summary=field_value)
    elif field == 'owner':
        if specification.owner:
            original_value = specification.owner.get_name()
            if specification.owner.padawan:
                for approver in specification.approvers:
                    if approver.approver == specification.owner.supervisor and approver.capacity == 'Supervisor':
                        specification.approvers.remove(approver)
                        approver.delete()
        owner = User.get_by_id(field_value)
        if owner.padawan:
            approver = Approver.create(approver_id=owner.supervisor_id, capacity='Supervisor')
            specification.approvers.append(approver)
        specification.update(owner=owner)
        field_value = owner.get_name() if owner else None
    elif field == 'thumbnail_id':
        thumbnail_id = None if field_value == 'default' else field_value
        specification.update(thumbnail_id=thumbnail_id)
        return render_template('shared/thumbnail_return.html', record=specification)

    specification.add_change_log_entry(action='Edit', field=field.title().replace('_', ' '),
                                       original_value=original_value, new_value=field_value)

    return jsonify({'success': True}), 200, {'ContentType': 'application/json'}


@blueprint.route('/update_state', methods=['POST'])
@login_required
def update_specification_state():
    # TODO: verify that current_user is owner of record and can edit it
    design_id = request.values['parent_id']
    state = request.form['state']
    transition = request.form['transition']
    comment = request.values['comment']
    specification = Specification.get_by_id(design_id)
    specification.update(state=state)
    specification.add_workflow_log_entry(capacity='Owner', action=transition, comment=comment)
    if state == specification.workflow.get_approval_state():
        for approver in specification.approvers:
            if not approver.approved_at:
                variables = {
                    'record': specification,
                    'approver': approver,
                    'comment': comment
                }
                send_email(subject='Approval Required for {0}: {1}'.format(specification.descriptor,
                                                                           specification.get_name()),
                           recipients=[approver.approver.email],
                           text_body=render_template('mail/approvals/new_approver.txt', **variables),
                           html_body=render_template('mail/approvals/new_approver.html', **variables))
    elif state == specification.workflow.released_state:
        # Only self-approval will trigger this
        comment = 'Revision ' + specification.revision
        specification.add_workflow_log_entry(capacity='PLAIDmin', action='Released', comment=comment)
    return jsonify({'success': True}), 200, {'ContentType': 'application/json'}


@blueprint.route('/<string:specification_number>-<string:revision>', methods=['GET'])
@login_required
def view_specification(specification_number, revision):
    """View existing specification."""
    specification = Specification.get_by_specification_number_and_revision(specification_number, revision)
    users = User.query.all()
    projects = Project.query.all()
    revisions = specification.find_all_revisions()
    variables = {
        'spec': specification,
        'revisions': revisions,
        'users': users,
        'projects': projects
    }
    return render_template('specification/view_specification.html', **variables)


@blueprint.route('/typeahead_search', methods=['GET'])
@login_required
def typeahead_search():
    query = request.args.get('query')
    specifications = Specification.typeahead_search(query)
    results = []
    for spec in specifications:
        spec_dict = {}
        spec_dict['class'] = spec.get_class_name()
        spec_dict['icon'] = '<i class="pri-typeahead-icon pri-icons-record-specification" aria-hidden="true"></i>'
        spec_dict['id'] = spec.id
        spec_dict['name'] = spec.name
        spec_dict['number'] = spec.specification_number
        spec_dict['object_type'] = 'Specification'
        spec_dict['state'] = spec.state
        spec_dict['thumb_url'] = spec.get_thumbnail_url()
        spec_dict['url'] = spec.get_url()
        results.append(spec_dict)
    return jsonify({'success': True, 'data': results}), 200, {'ContentType': 'application/json'}


@blueprint.route('/get_create_modal', methods=['POST'])
@login_required
def get_specification_modal():
    form = CreateSpecificationForm(request.form)
    return render_template('specification/create_specification.html', form=form)


@blueprint.route('/get_revise_specification_modal', methods=['GET', 'POST'])
@login_required
def get_revise_specification_modal():
    form = ReviseSpecificationForm(request.form)
    specification_id = request.form.get('specification_id')
    specification = Specification.get_by_id(specification_id)
    variables = {
        'spec': specification,
        'form': form
    }
    return render_template('specification/revise_specification.html', **variables)


@blueprint.route('/revise', methods=['POST'])
@login_required
def revise_specification():
    form = ReviseSpecificationForm(request.form)
    if request.method == 'POST':
        validated = form.validate_on_submit()
        old_specification_id = request.form['specification_id']
        old_spec = Specification.get_by_id(old_specification_id)

        if validated:
            new_revision = old_spec.find_next_revision()
            reason = form.revision_reason.data
            new_owner_id = form.owner.data.id
            # Get the old bits while we can
            links = old_spec.links
            documents = old_spec.documents
            images = old_spec.images
            references_to = old_spec.references_to
            old_revision = old_spec.revision
            # TODO: changelog, revisionlog
            replace_values = {
                'revision': new_revision,
                'revision_reason': reason,
                'owner_id': new_owner_id,
                'created_by': current_user,
                'state': old_spec.workflow.initial_state,
                'self_approved': Specification.self_approved.default.arg
            }
            spec = old_spec.clone(replace_values)  # After this point, old_design is the same as design, a cloned instance

            # Clone links
            for old_link in links:
                link = old_link.clone()
                spec.links.append(link)
            # Clone documents
            for old_document in documents:
                document = old_document.clone_document(spec)
                spec.documents.append(document)
            # Clone images
            for old_image in images:
                image = old_image.clone_image(spec)
                spec.images.append(image)
            # Clone what this references
            for reference in references_to:
                Reference.create(by_id=spec.id, by_class=spec.get_class_name(), to_id=reference.to_id, to_class=reference.to_class)
            # Create new change log and new workflow log
            spec.change_log = ChangeLog.create()
            spec.workflow_log = WorkflowLog.create()
            # Add supervisor approval if user is a padawan
            if current_user.padawan:
                approver = Approver.create(approver_id=current_user.supervisor_id, capacity='Supervisor')
                spec.approvers.append(approver)
            spec.save()

            # Update revision log
            spec.revision_log.add_entry(spec.revision, reason, current_user)
            jsonData = {
                'success': True,
                'specId': spec.id,
                'url': spec.get_url()
            }
            return jsonify(jsonData), 200, {'ContentType': 'application/json'}
        else:
            return make_response(render_template('specification/revise_specification.html', form=form, spec=old_spec), 500)


@blueprint.route('/advanced_search', methods=['GET'])
@login_required
def advanced_search_specifications():
    params = request.args.to_dict()
    specifications = Specification.advanced_search(params)
    results = []
    for specification in specifications:
        specification_dict = {
            'specification_number': specification.specification_number,
            'revision': specification.revision,
            'name': specification.name,
            'state': specification.state,
            'summary': specification.summary,
            'scope': specification.scope,
            'owner': specification.owner.get_name(),
            'created_by': specification.created_by.get_name(),
            'created_at': specification.created_at,
            'url': specification.get_url()
        }

        results.append(specification_dict)
    return jsonify({'success': True, 'data': results}), 200, {'ContentType': 'application/json'}
