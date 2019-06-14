
from collections import defaultdict
from itertools import chain

class BasePermissions(object):
    __slots__ = ['permissions', 'states', 'roles']

    def __init__(self):
        self.states = ['open', 'released', 'closed']
        self.roles = ['owner', 'all', 'superuser']
        permissions = defaultdict(dict)
        for state in self.states:
            permissions[state] = defaultdict(dict)
            for role in self.roles:
                permissions[state][role] = defaultdict(dict)
            permissions[state]['owner']['references'] = True
            permissions[state]['superuser']['references'] = True  # Superuser and owner can edit references always
            permissions[state]['owner']['state'] = True           # Owner should always be able to alter state
        permissions['open']['superuser']['owner'] = True          # Superuser can change owner when record is open
        permissions['open']['owner']['self_approved'] = True      # Owner can self approve when record is open
        permissions['open']['owner']['approvers'] = True          # Owner can add approvers when record is open
        self.permissions = permissions

    def get_permissions(self):
        return self.permissions


class AnomalyPermissions(BasePermissions):

    def __init__(self):
        super().__init__()
        anomaly_fields = ['name', 'owner', 'project', 'criticality', 'summary', 'analysis',
                          'corrective_action', 'thumbnail', 'documents', 'urls', 'designs', 'software_version']
        permissions = dict(self.permissions)
        for field in anomaly_fields:
            permissions['open']['owner'][field] = True
        self.permissions = permissions


class AsRunPermissions(BasePermissions):

    def __init__(self):
        super().__init__()
        as_run_fields = ['description', 'owner', 'project', 'products', 'notes',
                         'thumbnail', 'documents', 'urls', 'software_version']
        permissions = dict(self.permissions)
        for field in as_run_fields:
            permissions['open']['owner'][field] = True
        self.permissions = permissions


class BuildPermissions(BasePermissions):

    def __init__(self):
        super().__init__()
        build_fields = ['purchase_order', 'vendor', 'manufacturer', 'owner', 'notes', 'discrepancies', 'documents']
        permissions = dict(self.permissions)
        for field in build_fields:
            permissions['open']['owner'][field] = True
        self.permissions = permissions


class ECOPermissions(AnomalyPermissions):
    '''Is exactly the same as AnomalyPermissions (for now at least), so just inherit that'''

    def __init__(self):
        super().__init__()


class DesignPermissions(BasePermissions):
    '''Combined Design and Part permissions, goes on Design class'''

    def __init__(self):
        super().__init__()
        design_fields = ['name', 'summary', 'project', 'owner', 'notes', 'thumbnail',
                         'documents', 'urls', 'parts', 'revision_log']
        part_fields = ['name', 'current_best_estimate', 'uncertainty', 'material',
                       'material_specification', 'quantity', 'components']
        permissions = dict(self.permissions)
        for field in chain(design_fields, part_fields):
            permissions['open']['owner'][field] = True
        permissions['released']['owner']['revision'] = True  # Design
        permissions['released']['superuser']['revision'] = True  # Design
        for role in self.roles:
            permissions['open'][role]['ecos'] = True  # Design
            permissions['released'][role]['builds'] = True  # Part
        self.permissions = permissions


class ProcedurePermissions(BasePermissions):

    def __init__(self):
        super().__init__()
        procedure_fields = ['name', 'owner', 'project', 'parts', 'thumbnail', 'summary',
                            'documents', 'urls', 'revision_log']
        permissions = dict(self.permissions)
        for field in procedure_fields:
            permissions['open']['owner'][field] = True
        for role in self.roles:
            permissions['released'][role]['as_runs'] = True
        permissions['released']['owner']['revision'] = True
        permissions['released']['superuser']['revision'] = True
        self.permissions = permissions


class ProductPermissions(BasePermissions):

    def __init__(self):
        super().__init__()
        product_fields = ['name', 'project', 'owner', 'hardware_type', 'revision', 'notes', 'summary',
                          'discrepancies', 'documents', 'urls', 'measured_mass', 'components', 'thumbnail']
        permissions = dict(self.permissions)
        for field in product_fields:
            permissions['open']['owner'][field] = True
        self.permissions = permissions


class SpecificationPermissions(BasePermissions):

    def __init__(self):
        super().__init__()
        specification_fields = ['name', 'scope', 'owner', 'summary', 'thumbnail', 'documents', 'urls', 'revision_log']
        permissions = dict(self.permissions)
        for field in specification_fields:
            permissions['open']['owner'][field] = True
        permissions['released']['owner']['revision'] = True
        permissions['released']['superuser']['revision'] = True
        self.permissions = permissions


class TaskPermissions(BasePermissions):

    def __init__(self):
        super().__init__()
        task_fields = ['title', 'assigned_to', 'urgency', 'need_date', 'summary',
                       'thumbnail', 'documents', 'urls', 'comments']
        permissions = dict(self.permissions)
        for field in task_fields:
            permissions['open']['owner'][field] = True
        permissions['open']['superuser']['assigned_to'] = True
        self.permissions = permissions


class VendorBuildPermissions(BuildPermissions):
    '''Is exactly the same as BuildPermissions (for now at least), so just inherit that'''

    def __init__(self):
        super().__init__()


class VendorPartPermissions(BasePermissions):

    def __init__(self):
        super().__init__()
        vendor_part_fields = ['name', 'summary', 'notes', 'vendor', 'current_best_estimate', 'uncertainty', 'material',
                              'material_specification', 'project', 'owner', 'thumbnail', 'documents', 'urls']
        permissions = dict(self.permissions)
        for field in vendor_part_fields:
            permissions['open']['owner'][field] = True
        for role in self.roles:
            permissions['released'][role]['builds'] = True
        self.permissions = permissions


class VendorProductPermissions(BasePermissions):
    '''Combined VendorProduct and VendorBuild permissions, goes on VendorProduct class'''

    def __init__(self):
        super().__init__()
        vendor_product_fields = ['name', 'project', 'owner', 'hardware_type', 'measured_mass', 'notes', 'summary',
                                 'discrepancies', 'documents', 'urls', 'components', 'thumbnail', 'serial_number']
        vendor_build_fields = ['purchase_order', 'vendor', 'manufacturer', 'owner',
                               'notes', 'discrepancies', 'documents']
        permissions = dict(self.permissions)
        for field in chain(vendor_product_fields, vendor_build_fields):
            permissions['open']['owner'][field] = True
        self.permissions = permissions
