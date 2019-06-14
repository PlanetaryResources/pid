# -*- coding: utf-8 -*-
"""Backend views."""
from collections import defaultdict
from flask import Blueprint, render_template, request, jsonify, redirect, url_for
from flask_login import login_required, current_user
from pid.extensions import whooshee
from pid.anomaly.models import Anomaly
from pid.asrun.models import AsRun
from pid.design.models import Design
from pid.vendorpart.models import VendorPart
from pid.eco.models import ECO
from pid.product.models import Product
from pid.vendorproduct.models import VendorProduct
from pid.procedure.models import Procedure
from pid.user.models import User
from pid.specification.models import Specification
from pid.common.models import Project, Material, MaterialSpecification, HardwareType, Company, Criticality, Approver
from pid.globals import ADVANCED_SEARCH_COLUMNS
from pid.utils import admin_required
from .models import Settings
from .forms import SettingsForm

blueprint = Blueprint('backend', __name__, static_folder='../static')


@blueprint.route('/dashboard/', methods=['GET'])
@login_required
def dashboard():
    user = current_user
    # TODO: Add prefix option to forms so form field ids are unique

    anomalies_for_user = Anomaly.find_all_anomalies_for_user(user)
    as_runs_for_user = AsRun.find_all_as_runs_for_user(user)
    designs_for_user = Design.find_all_designs_for_user(user)
    ecos_for_user = ECO.find_all_ecos_for_user(user)
    products_for_user = Product.find_all_products_for_user(user)
    vendor_products_for_user = VendorProduct.find_all_vendor_products_for_user(user)
    vendor_parts_for_user = VendorPart.find_all_vendor_parts_for_user(user)
    procedures_for_user = Procedure.find_all_distinct_procedures_for_user(user)
    specifications = Specification.find_all_distinct_specifications()
    records_awaiting_approval = []
    for record_list in [anomalies_for_user, as_runs_for_user, designs_for_user, ecos_for_user, procedures_for_user,
                        products_for_user,specifications, vendor_parts_for_user, vendor_products_for_user]:
        for record in record_list:
            if record.state == record.workflow.get_approval_state():
                records_awaiting_approval.append(record)
    variables = {
        'anomalies_for_user': anomalies_for_user,
        'designs_for_user': designs_for_user,
        'ecos_for_user': ecos_for_user,
        'products_for_user': products_for_user,
        'vendor_products_for_user': vendor_products_for_user,
        'vendor_parts_for_user': vendor_parts_for_user,
        'procedures_for_user': procedures_for_user,
        'specifications': specifications,
        'users': User.query.all(),
        'bookmarks': process_bookmarks(user),
        'saved_searches': user.saved_searches,
        'settings': Settings.get_settings(),
        'approvals': Approver.get_open_approvals_for_user(user),
        'records_awaiting_approval': records_awaiting_approval
    }
    return render_template('backend/dashboard.html', **variables)


#@blueprint.route('/reindex_whooshee/')
#@login_required
#@admin_required
#def reindex_whooshee():
#    # TODO: Just here for now for easier reindexing of whooshee
#    whooshee.reindex()
#    return jsonify({'success': True}), 200, {'ContentType': 'application/json'}


@blueprint.route('/styles', methods=['GET'])
@login_required
@admin_required
def view_styles():
    return render_template('backend/style_preview.html')


@blueprint.route('/settings', methods=['GET'])
@login_required
@admin_required
def view_settings():
    form = SettingsForm(request.form)
    settings = Settings.get_settings()
    if settings:
        form.efab_user.data = settings.efab_user
        form.mfab_user.data = settings.mfab_user
        form.plaid_admin.data = settings.plaid_admin
        form.name_order.data = settings.name_order
    return render_template('backend/settings.html', form=form)


@blueprint.route('/settings/update', methods=['POST'])
@login_required
@admin_required
def update_settings():
    form = SettingsForm(request.form)
    validated = form.validate_on_submit()
    if validated:
        variables = {
            'efab_user': form.efab_user.data,
            'mfab_user': form.mfab_user.data,
            'plaid_admin': form.plaid_admin.data,
            'name_order': form.name_order.data
        }
        settings = Settings.get_settings()
        if settings:
            settings.update(**variables)
        else:
            Settings.create(**variables)
    return redirect(url_for('backend.view_settings'))


@blueprint.route('/advanced_search', methods=['GET'])
@login_required
def advanced_search():
    params = request.args.to_dict()
    users = User.query.all()
    projects = Project.query.all()
    materials = Material.query.all()
    material_specs = MaterialSpecification.query.all()
    hardware_types = HardwareType.query.all()
    criticalities = Criticality.query.all()
    vendors = Company.get_all_with_pri_on_top()

    variables = {
        'users': users,
        'projects': projects,
        'vendors': vendors,
        'materials': materials,
        'material_specs': material_specs,
        'hardware_types': hardware_types,
        'criticalities': criticalities,
        'column_names': ADVANCED_SEARCH_COLUMNS,
        'record_type': params['record_type'] if 'record_type' in params else 'design',
        'Design': Design,  # TODO: Consider making these globally accessible if needed
        'VendorPart': VendorPart,
        'Product': Product,
        'VendorProduct': VendorProduct,
        'Procedure': Procedure,
        'Anomaly': Anomaly,
        'ECO': ECO,
        'Specification': Specification
    }
    return render_template('backend/advanced_search.html', **variables)


# ----- HELPER FUNCTIONS ----- #

def process_bookmarks(user):
    bookmarks = defaultdict(list)
    for bookmark in user.bookmarks:
        bookmarks[bookmark.bookmarked_class].append(bookmark)
    return bookmarks
