# -*- coding: utf-8 -*-
"""Design views."""
from flask import Blueprint, request, jsonify, render_template, make_response
from flask_login import login_required, current_user
from .forms import CreateECOForm
from .models import ECO
from pid.common.models import Project, Approver
from pid.mail import send_email
from pid.user.models import User
from pid.design.models import Design

blueprint = Blueprint('eco', __name__, url_prefix='/eco', static_folder='../static')


@blueprint.route('/create', methods=['POST'])
@login_required
def create_eco():
    """Create new ECO."""
    form = CreateECOForm(request.form)
    validated = form.validate_on_submit()

    design_ids = form.designs.data.split(',')
    designs = []
    for design_id in design_ids:
        design = Design.get_by_id(design_id)
        if design != None:
            designs.append(design)

    if validated:
        variables = {
            'name': form.name.data,
            'owner': form.owner.data,
            'project': designs[0].project
        }
        eco = ECO.create(**variables)
        for design in designs:
            eco.designs.append(design)
        eco.save()
        jsonData = {
            'success': True,
            'ecoId': eco.id,
            'url': eco.get_url()
        }
        return jsonify(jsonData), 200, {'ContentType': 'application/json'}
    else:
        return make_response(render_template('eco/create_eco.html', form=form, designs=designs), 500)


@blueprint.route('/update', methods=['POST'])
@login_required
def update_eco():
    id = request.form['pk']
    # UID for field will be ala [fieldname]-[classname]-[id]-editable, field name will be first section always
    field = request.form['name'].split('-')[0]
    field_value = request.form['value']
    eco = ECO.get_by_id(id)
    original_value = None

    if field == 'name':
        original_value = eco.name
        eco.update(name=field_value)
    if field == 'summary':
        original_value = eco.summary
        eco.update(summary=field_value)
    if field == 'analysis':
        original_value = eco.analysis
        eco.update(analysis=field_value)
    if field == 'corrective_action':
        original_value = eco.corrective_action
        eco.update(corrective_action=field_value)
    elif field == 'project':
        if eco.project:
            original_value = eco.project.name
        project = Project.get_by_id(field_value)
        eco.update(project=project)
        field_value = project.name if project else None
    elif field == 'owner':
        if eco.owner:
            original_value = eco.owner.get_name()
            if eco.owner.padawan:
                for approver in eco.approvers:
                    if approver.approver == eco.owner.supervisor and approver.capacity == 'Supervisor':
                        eco.approvers.remove(approver)
                        approver.delete()
        owner = User.get_by_id(field_value)
        if owner.padawan:
            approver = Approver.create(approver_id=owner.supervisor_id, capacity='Supervisor')
            eco.approvers.append(approver)
        eco.update(owner=owner)
        field_value = owner.get_name() if owner else None
    if field == 'thumbnail_id':
        thumbnail_id = None if field_value == 'default' else field_value
        eco.update(thumbnail_id=thumbnail_id)
        return render_template('shared/thumbnail_return.html', record=eco)

    eco.add_change_log_entry(action='Edit', field=field.title().replace('_', ' '),
                             original_value=original_value, new_value=field_value)

    return jsonify({'success': True}), 200, {'ContentType': 'application/json'}


@blueprint.route('/update_state', methods=['POST'])
@login_required
def update_eco_state():
    # TODO: verify that current_user is owner of record and can edit it
    design_id = request.values['parent_id']
    state = request.form['state']
    transition = request.form['transition']
    comment = request.values['comment']
    eco = ECO.get_by_id(design_id)
    eco.update(state=state)
    eco.add_workflow_log_entry(capacity='Owner', action=transition, comment=comment)
    if state == eco.workflow.get_approval_state():
        for approver in eco.approvers:
            if not approver.approved_at:
                variables = {
                    'record': eco,
                    'approver': approver,
                    'comment': comment
                }
                send_email(subject='Approval Required for {0}: {1}'.format(eco.descriptor, eco.get_name()),
                           recipients=[approver.approver.email],
                           text_body=render_template('mail/approvals/new_approver.txt', **variables),
                           html_body=render_template('mail/approvals/new_approver.html', **variables))
    elif state == eco.workflow.released_state:
        # Only self-approval will trigger this
        eco.add_workflow_log_entry(capacity='PLAIDmin', action='Approved')
    return jsonify({'success': True}), 200, {'ContentType': 'application/json'}


@blueprint.route('/<string:key>', methods=['GET'])
@login_required
def view_eco(key):
    """View existing eco."""
    eco = ECO.get_by_key(key)
    users = User.query.all()
    projects = Project.query.all()
    variables = {
        'eco': eco,
        'users': users,
        'projects': projects
    }
    return render_template('eco/view_eco.html', **variables)


@blueprint.route('/typeahead_search', methods=['GET'])
@login_required
def typeahead_search():
    query = request.args.get('query')
    ecos = ECO.typeahead_search(query)
    results = []
    for eco in ecos:
        eco_dict = {}
        eco_dict['class'] = eco.get_class_name()
        eco_dict['icon'] = '<i class="pri-typeahead-icon pri-icons-record-eco" aria-hidden="true"></i>'
        eco_dict['id'] = eco.id
        eco_dict['name'] = eco.name
        eco_dict['number'] = eco.key
        eco_dict['object_type'] = 'ECO'
        eco_dict['state'] = eco.state
        eco_dict['thumb_url'] = eco.get_thumbnail_url()
        eco_dict['url'] = eco.get_url()
        results.append(eco_dict)
    return jsonify({'success': True, 'data': results}), 200, {'ContentType': 'application/json'}


@blueprint.route('/get_create_modal', methods=['POST'])
@login_required
def get_eco_modal():
    form = CreateECOForm(request.form)
    variables = {
        'form': form
    }
    design_id = request.form.get('design_id', None)
    if design_id:
        variables['designs'] = [Design.get_by_id(design_id)]
    return render_template('eco/create_eco.html', **variables)


@blueprint.route('/advanced_search', methods=['GET'])
@login_required
def advanced_search_ecos():
    params = request.args.to_dict()
    ecos = ECO.advanced_search(params)
    results = []
    for eco in ecos:
        eco_dict = {
            'eco_number': eco.key,
            'name': eco.name,
            'state': eco.state,
            'project': eco.project.name,
            'summary': eco.summary,
            'owner': eco.owner.get_name(),
            'created_by': eco.created_by.get_name(),
            'created_at': eco.created_at,
            'url': eco.get_url()
        }
        results.append(eco_dict)
    return jsonify({'success': True, 'data': results}), 200, {'ContentType': 'application/json'}


@blueprint.route('/get_add_design_typeahead_modal', methods=['POST'])
@login_required
def get_add_design_typeahead_modal():
    eco_id = request.values['eco_id']
    eco = ECO.get_by_id(eco_id)
    designs = []
    for design in eco.designs:
        designs.extend([rev_design.id for rev_design in design.find_all_revisions()])
    variables = {
        'eco': eco,
        'designs': designs
    }
    return render_template('eco/add_design_typeahead_modal.html', **variables)


@blueprint.route('/update_design', methods=['POST'])
@login_required
def update_design():
    eco_id = request.values['eco_id']
    old_design_id = request.values['old_design_id']
    new_design_id = request.values['new_design_id']
    eco = ECO.get_by_id(eco_id)
    old_design = Design.get_by_id(old_design_id)
    new_design = Design.get_by_id(new_design_id)
    eco.designs.remove(old_design)
    eco.designs.append(new_design)
    eco.add_change_log_entry(action='Edit', field='Design', original_value=old_design.get_descriptive_url(),
                             new_value=new_design.get_descriptive_url())
    eco.save()
    variables = {
        'eco': eco,
        'design': new_design
    }
    return render_template('eco/eco_design_row.html', **variables)


@blueprint.route('/add_design', methods=['POST'])
@login_required
def add_design():
    eco_id = request.values['eco_id']
    design_id = request.values['design_id']
    eco = ECO.get_by_id(eco_id)
    design = Design.get_by_id(design_id)
    eco.designs.append(design)
    eco.add_change_log_entry(action='Add', field='Design', new_value=design.get_descriptive_url())
    eco.save()
    variables = {
        'eco': eco,
        'design': design
    }
    return render_template('eco/eco_design_row.html', **variables)


@blueprint.route('/remove_design', methods=['POST'])
@login_required
def remove_design():
    eco_id = request.values['eco_id']
    eco = ECO.get_by_id(eco_id)
    design_id = request.values['design_id']
    design = Design.get_by_id(design_id)
    eco.designs.remove(design)
    eco.add_change_log_entry(action='Remove', field='Design', original_value=design.get_descriptive_url())
    eco.save()
    return jsonify({'success': True}), 200, {'ContentType': 'application/json'}
