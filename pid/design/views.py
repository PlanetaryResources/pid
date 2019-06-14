# -*- coding: utf-8 -*-
"""Design views."""
from flask import Blueprint, render_template, request, flash, jsonify, make_response
from flask_login import login_required, current_user
from .forms import CreateDesignForm, ReviseDesignForm
from .models import Design
from pid.part.models import Part, PartComponent
from pid.common.models import Project, Material, Reference, Approver, WorkflowLog, ChangeLog
from pid.task.models import Task
from pid.user.models import User
from pid.anomaly.models import Anomaly
from pid.eco.models import ECO
from pid.specification.models import Specification
from pid.procedure.models import Procedure
from pid.asrun.models import AsRun
from pid.product.models import Product
from pid.vendorproduct.models import VendorProduct
from pid.vendorpart.models import VendorPart
from pid.mail import send_email

blueprint = Blueprint('design', __name__, url_prefix='/design', static_folder='../static')


@blueprint.route('/create', methods=['POST'])
@login_required
def create_design():
    """Create new design. This method is always called via AJAX."""
    form = CreateDesignForm(request.form)
    validated, design_numbers = form.validate_on_submit()
    if validated:
        designs = []
        for design_number in design_numbers:
            variables = {
                'design_number': design_number,
                'name': form.name.data,
                'project': form.project.data,
                'revision': form.revision.data,
                'owner': form.owner.data
            }
            # TODO: Create both design and part in one transaction, so if Part create fails, design create fails
            # Create the design
            design = Design.create(**variables)
            # Create part -1 (dash one) on design item
            variables = {
                'design': design,
                'owner': design.owner,
                'part_identifier': 1
            }
            Part.create(**variables)
            designs.append(design.as_dict())  # For modal if user creates more than one Design
        jsonData = {
            'designs': designs
        }
        return jsonify(jsonData), 200, {'ContentType': 'application/json'}
    else:
        response = make_response(render_template('design/create_design_modal.html', form=form), 500)
        return response


@blueprint.route('/<string:design_number>-<string:revision>', methods=['GET'])
@login_required
def view_design(design_number, revision):
    design = Design.get_by_design_number_and_revision(design_number, revision)
    if design is None:
        flash('Could not find design {0}-{1}.'.format(design_number, revision), 'warning')
    revisions = design.find_all_revisions()
    projects = Project.query.all()
    materials = Material.query.all()
    users = User.query.all()
    variables = {
        'design': design,
        'revisions': revisions,
        'projects': projects,
        'materials': materials,
        'users': users
    }
    return render_template('design/view_design.html', **variables)


@blueprint.route('/update', methods=['POST'])
@login_required
def update_design():
    design_id = request.form['pk']
    # UID for field will be ala [fieldname]-[classname]-[id]-editable, field name will be first section always
    field = request.form['name'].split('-')[0]
    field_value = request.form['value']
    # TODO: Check if design exists
    design = Design.get_by_id(design_id)
    original_value = None
    if field == 'name':
        original_value = design.name
        design.update(name=field_value)
    elif field == 'summary':
        original_value = design.summary
        design.update(summary=field_value)
    elif field == 'project':
        if design.project:
            original_value = design.project.name
        project = Project.get_by_id(field_value)
        design.update(project=project)
        field_value = project.name if project else None
    elif field == 'owner':
        if design.owner:
            original_value = design.owner.get_name()
            if design.owner.padawan:
                for approver in design.approvers:
                    if approver.approver == design.owner.supervisor and approver.capacity == 'Supervisor':
                        design.approvers.remove(approver)
                        approver.delete()
        owner = User.get_by_id(field_value)
        if owner.padawan:
            approver = Approver.create(approver_id=owner.supervisor_id, capacity='Supervisor')
            design.approvers.append(approver)
        design.update(owner=owner)
        field_value = owner.get_name() if owner else None
    elif field == 'notes':
        original_value = design.notes
        design.update(notes=field_value)
    elif field == 'thumbnail_id':
        thumbnail_id = None if field_value == 'default' else field_value
        design.update(thumbnail_id=thumbnail_id)
        return render_template('shared/thumbnail_return.html', record=design)

    design.add_change_log_entry(action='Edit', field=field.title().replace('_', ' '), original_value=original_value,
                                new_value=field_value)

    return jsonify({'success': True}), 200, {'ContentType': 'application/json'}


@blueprint.route('/update_state', methods=['POST'])
@login_required
def update_design_state():
    # TODO: This could probably be moved to Base class and made more generic
    # TODO: verify that current_user is owner of record and can edit it
    design_id = request.values['parent_id']
    state = request.form['state']
    transition = request.form['transition']
    comment = request.values['comment']
    design = Design.get_by_id(design_id)
    design.update(state=state)
    design.add_workflow_log_entry(capacity='Owner', action=transition, comment=comment)
    if state == design.workflow.get_approval_state():
        for approver in design.approvers:
            if not approver.approved_at:
                variables = {
                    'record': design,
                    'approver': approver,
                    'comment': comment
                }
                send_email(subject='Approval Required for {0}: {1}'.format(design.descriptor, design.get_name()),
                           recipients=[approver.approver.email],
                           text_body=render_template('mail/approvals/new_approver.txt', **variables),
                           html_body=render_template('mail/approvals/new_approver.html', **variables))
    elif state == design.workflow.released_state:
        # Only self-approval will trigger this
        comment = 'Revision ' + design.revision
        design.add_workflow_log_entry(capacity='PLAIDmin', action='Released', comment=comment)
    return jsonify({'success': True}), 200, {'ContentType': 'application/json'}


@blueprint.route('/typeahead_search_designs', methods=['GET'])
@login_required
def typeahead_search_designs():
    # TODO: Change all tyupeaheads to POST if possible
    query = request.args.get('query')
    search_only_open = request.args.get('search_only_open', False, type=bool)
    designs = Design.typeahead_search(query)
    results = []
    for design in designs:
        design_dict = {}
        design_dict['class'] = design.get_class_name()
        design_dict['icon'] = '<i class="pri-typeahead-icon pri-icons-record-design" aria-hidden="true"></i>'
        design_dict['id'] = design.id
        design_dict['name'] = design.name
        design_dict['number'] = design.design_number
        design_dict['object_type'] = 'Design'
        design_dict['state'] = design.state
        design_dict['thumb_url'] = design.get_thumbnail_url()
        design_dict['url'] = design.get_url()
        revisions = []
        for instance in design.find_all_revisions():
            if (search_only_open and instance.is_open()) or (not search_only_open):
                revisions.append({'id': instance.id, 'revision': instance.revision})
        design_dict['revisions'] = revisions
        if len(revisions) > 0:
            results.append(design_dict)
    return jsonify({'success': True, 'data': results}), 200, {'ContentType': 'application/json'}


@blueprint.route('/advanced_search', methods=['GET'])
@login_required
def advanced_search_designs():
    params = request.args.to_dict()
    designs = Design.advanced_search(params)
    results = []

    for design in designs:
        design_dict = {
            'design_number': design.design_number,
            'revision': design.revision,
            'name': design.name,
            'state': design.state,
            'summary': design.summary,
            'notes': design.notes,
            'project': design.project.name,
            'anomalies': len(design.anomalies),
            'ecos': len(design.ecos),
            'owner': design.owner.get_name(),
            'created_by': design.created_by.get_name(),
            'created_at': design.created_at,
            'url': design.get_url()
        }

        results.append(design_dict)
    return jsonify({'success': True, 'data': results}), 200, {'ContentType': 'application/json'}


@blueprint.route('/revise', methods=['POST'])
@login_required
def revise_design():
    form = ReviseDesignForm(request.form)
    validated = form.validate_on_submit()
    if not validated:
        design_id = form.design_id.data
        design = Design.get_by_id(design_id)
        variables = {
            'design': design,
            'form': form
        }
        return make_response(render_template('design/revise_design_modal.html', **variables), 500)
    old_design_id = form.design_id.data
    new_revision = form.revision.data
    reason = form.revision_reason.data
    new_owner = form.owner.data
    include_parts = request.form['include_parts']
    old_design = Design.get_by_id(old_design_id)
    # Get the old bits while we can
    parts = old_design.parts
    links = old_design.links
    documents = old_design.documents
    images = old_design.images
    references_to = old_design.references_to
    # TODO: Duplicate anomalies, ecos, specifications, produres, family, changelog, revisionlog
    replace_values = {
        'revision': new_revision,
        'owner': new_owner,
        'created_by': current_user,
        'state': old_design.workflow.initial_state,
        'export_control': old_design.export_control,  # Because make_transient uses default values
        'self_approved': Design.self_approved.default.arg
    }
    design = old_design.clone(replace_values)  # After this point, old_design is the same as design, a cloned instance
    # Clone all parts
    if include_parts == 'all':
        for old_part in parts:
            # TODO: Parent? Changelog?
            components = old_part.components
            replace_values = {'design': design}
            part = old_part.clone(replace_values)
            for old_component in components:
                replace_values = {
                    'parent': part,
                    'part': old_component.part,
                    'vendor_part': old_component.vendor_part,
                    'quantity': old_component.quantity  # Because make_transient uses default values
                }
                old_component.clone(replace_values)
    # Clone selected parts
    else:
        include_selected_parts = request.form.getlist('include_selected_parts')
        for part_id in include_selected_parts:
            # TODO: Parent? Changelog?
            old_part = Part.get_by_id(part_id)
            components = old_part.components
            replace_values = {'design': design}
            part = old_part.clone(replace_values)
            for old_component in components:
                replace_values = {
                    'parent': part,
                    'part': old_component.part,
                    'vendor_part': old_component.vendor_part,
                    'quantity': old_component.quantity  # Because make_transient uses default values
                }
                old_component.clone(replace_values)
    # Clone links
    for old_link in links:
        link = old_link.clone()
        design.links.append(link)
    # Clone documents
    for old_document in documents:
        document = old_document.clone_document(design)
        design.documents.append(document)
    # Clone images
    for old_image in images:
        image = old_image.clone_image(design)
        design.images.append(image)
    # Clone what this references
    for reference in references_to:
        Reference.create(by_id=design.id, by_class=design.get_class_name(), to_id=reference.to_id, to_class=reference.to_class)
    # Create new change log and new workflow log
    design.change_log = ChangeLog.create()
    design.workflow_log = WorkflowLog.create()
    # Add supervisor approval if user is a padawan
    if current_user.padawan:
        approver = Approver.create(approver_id=current_user.supervisor_id, capacity='Supervisor')
        design.approvers.append(approver)
    design.save()

    # Update any references in part components from old revision to new revision
    PartComponent.update_part_component_references(design)

    # Update revision log
    design.revision_log.add_entry(design.revision, reason, current_user)

    jsonData = {
        'success': True,
        'url': design.get_url()
    }
    return jsonify(jsonData), 200, {'ContentType': 'application/json'}


@blueprint.route('/get_revise_design_modal', methods=['POST'])
@login_required
def get_revise_design_modal():
    design_id = request.form.get('design_id')
    design = Design.get_by_id(design_id)
    form = ReviseDesignForm(request.form)
    # Pre-populate some form data
    form.design_id.data = design.id
    form.owner.data = design.owner
    form.revision.data = design.find_next_revision()
    variables = {
        'design': design,
        'form': form
    }
    return render_template('design/revise_design_modal.html', **variables)


@blueprint.route('/get_create_design_modal', methods=['POST'])
@login_required
def get_create_design_modal():
    form = CreateDesignForm(request.form)
    return render_template('design/create_design_modal.html', form=form)


@blueprint.route('/get_multiple_designs_created_modal', methods=['POST'])
@login_required
def get_multiple_designs_created_modal():
    designs_json = request.get_json()
    design_ids = [design['id'] for design in designs_json]
    designs = Design.query.filter(Design.id.in_(design_ids)).all()
    variables = {
        'designs': designs
    }
    return render_template('design/multiple_designs_created_modal.html', **variables)
