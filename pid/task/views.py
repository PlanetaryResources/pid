# -*- coding: utf-8 -*-
"""Task views."""
from datetime import datetime

from dateutil.parser import parse
from dateutil.relativedelta import relativedelta
from flask import Blueprint, jsonify, make_response, render_template, request
from flask_login import login_required, current_user

from pid.backend.models import Settings
from pid.mail import send_email
from pid.user.models import User
from pid.task.forms import CreateTaskForm
from pid.task.models import Task

blueprint = Blueprint('task', __name__, url_prefix='/task', static_folder='../static')


@blueprint.route('/create', methods=['POST'])
@login_required
def create_task():
    """Create new Task."""
    form = CreateTaskForm(request.form)
    validated = form.validate_on_submit()

    if validated:
        title = form.title.data
        urgency = form.urgency.data
        assigned_to = form.assign_to.data
        need_date = form.create_need_date.data
        summary = form.summary.data
        task = Task.create(title=title, urgency=urgency, assigned_to=assigned_to,
                           requested_by=current_user, need_date=need_date, summary=summary)
        send_email(subject='Task Assigned: {0}'.format(task.title), recipients=[task.assigned_to.email],
                   text_body=render_template('mail/new_task.txt', task=task),
                   html_body=render_template('mail/new_task.html', task=task))
        json = {
            'success': True,
            'url': task.get_url()
        }
        return jsonify(json), 200, {'ContentType': 'application/json'}
    else:
        return make_response(render_template('task/create_task.html', form=form), 500)


@blueprint.route('/<string:task_number>', methods=['GET'])
@login_required
def view_task(task_number):
    """View existing task."""
    task = Task.get_by_task_number(task_number)
    users = User.query.all()
    criticalities = {
        'at your leisure': 'odd',
        'important': 'worrisome',
        'urgent': 'serious',
        'sof': 'sof'
    }
    variables = {
        'task': task,
        'users': users,
        'criticalities': criticalities
    }
    return render_template('task/view_task.html', **variables)


@blueprint.route('/update', methods=['POST'])
@login_required
def update_task():
    task_id = request.form['pk']
    # UID for field will be ala [fieldname]-[classname]-[id]-editable, field name will be first section always
    field = request.form['name'].split('-')[0]
    field_value = request.form['value']
    task = Task.get_by_id(task_id)
    original_value = None

    if field == 'title':
        original_value = task.title
        task.update(title=field_value)
    elif field == 'summary':
        original_value = task.summary
        task.update(summary=field_value)
    elif field == 'state':
        original_value = task.state
        task.update(state=field_value)
    elif field == 'urgency':
        original_value = task.urgency
        task.update(urgency=field_value)
        field = 'criticality'  # To match what is visually displayed
    elif field == 'assigned_to':
        if task.assigned_to:
            original_value = task.assigned_to.get_name()
        assigned_to = User.get_by_id(field_value)
        task.update(assigned_to=assigned_to)
        send_email(subject='Task Assigned: {0}'.format(task.title), recipients=[task.assigned_to.email],
                   text_body=render_template('mail/new_task.txt', task=task),
                   html_body=render_template('mail/new_task.html', task=task))
        field_value = assigned_to.get_name() if assigned_to else None
    elif field == 'need_date':
        try:
            original_value = task.need_date.date()
            # Need to append UTC hours due to moment.js and timezones
            task.update(need_date=parse(field_value).date() + relativedelta(hours=+datetime.utcnow().hour))
        except ValueError:
            return "Incorrect date format: " + field_value, 500, {'ContentType': 'application/json'}
    elif field == 'thumbnail_id':
        thumbnail_id = None if field_value == 'default' else field_value
        task.update(thumbnail_id=thumbnail_id)
        return render_template('shared/thumbnail_return.html', record=task)

    task.add_change_log_entry(action='Edit', field=field.title().replace('_', ' '),
                              original_value=original_value, new_value=field_value)

    return jsonify({'success': True}), 200, {'ContentType': 'application/json'}


@blueprint.route('/add_task_modal', methods=['POST'])
@login_required
def get_add_task_modal():
    form = CreateTaskForm(request.form)
    urgency_states = ["At Your Leisure", "Important", "Urgent", "SoF"]
    return render_template('task/create_task.html', form=form, urgency_states=urgency_states)


@blueprint.route('/get_tasks_for_user/<string:username>/<string:task_type>', methods=['POST'])
@login_required
def get_tasks_for_user(username, task_type='assigned'):
    # TODO: Change this away from this kind of URL, but task table is tricky right now
    user = None
    if username == 'efab':
        settings = Settings.get_settings()
        user = settings.efab_user
    elif username == 'mfab':
        settings = Settings.get_settings()
        user = settings.mfab_user
    elif username == 'plaid_admin':
        settings = Settings.get_settings()
        user = settings.plaid_admin
    else:
        user = User.get_by_username(username)
    tasks = Task.find_all_tasks_for_user(user, task_type)
    task_columns = Task.__table__.columns._data.keys()
    results = []
    for task in tasks:
        task_dict = {}
        for column in task_columns:
            if column not in ['assigned_to_id', 'requested_by_id']:
                task_dict[column] = getattr(task, column)
        task_dict['assigned_to'] = {
            'id': task.assigned_to.id,
            'get_name': task.assigned_to.get_name(),
            'username': task.assigned_to.username
        }
        task_dict['requested_by'] = {
            'id': task.requested_by.id,
            'get_name': task.requested_by.get_name(),
            'username': task.requested_by.username
        }

        results.append(task_dict)
    return jsonify({'success': True, 'data': results}), 200, {'ContentType': 'application/json'}
