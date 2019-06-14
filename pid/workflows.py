
from collections import defaultdict
from flask import url_for


class DesignWorkflow(object):
    __slots__ = ['states', 'open_states', 'initial_state', 'pre_approval_state', 'released_state', 'obsolete_state',
                 'transitions', 'comment_transitions', 'obsolete_transitions', 'self_approve_transitions']

    def __init__(self):
        self.states = ['Planned', 'In Work', 'Approval', 'Released', 'Obsolete']
        self.open_states = ['Planned', 'In Work']
        self.initial_state = 'Planned'
        self.pre_approval_state = ['In Work']
        self.released_state = 'Released'
        self.obsolete_state = 'Obsolete'
        transitions = defaultdict(dict)
        transitions['Planned']['In Work'] = 'In Work'
        transitions['In Work']['Planned'] = 'Planned'
        transitions['In Work']['Approval'] = 'Send for Approval'
        transitions['In Work']['Obsolete'] = 'Make Obsolete'
        transitions['Approval']['In Work'] = 'Required Edit'
        transitions['Released']['Obsolete'] = 'Make Obsolete'
        self.transitions = transitions
        self_approve_transitions = defaultdict(dict)
        self_approve_transitions['In Work']['Released'] = 'Self-Approve'
        self_approve_transitions['Approval']['Released'] = 'Self-Approve'
        self.self_approve_transitions = self_approve_transitions
        self.comment_transitions = ['Send for Approval', 'Required Edit', 'Self-Approve']
        self.obsolete_transitions = ['Make Obsolete']

    def get_transitions_for_state(self, state, self_approved):
        transitions = dict(self.transitions[state])
        if self_approved:
            if state in self.self_approve_transitions.keys():
                # Remove any transitions which indicate approval
                del transitions[self.get_approval_state()]
                # Add self=approve transitions
                transitions.update(self.self_approve_transitions[state])
        return transitions

    def get_approval_state(self):
        return 'Approval'

    def get_workflow_image(self):
        return url_for('static', filename='images/workflows/design_workflow.png')

    def get_icon_for_state(self, state):
        icons = {}
        icons['Planned'] = 'pri-icons-planned'
        icons['In Work'] = 'pri-icons-in-work'
        icons['Approval'] = 'pri-icons-approval'
        icons['Released'] = 'pri-icons-thumbs-up'
        icons['Obsolete'] = 'pri-icons-obsolete'
        return icons[state]


class VendorPartWorkflow(object):
    __slots__ = ['states', 'open_states', 'initial_state', 'pre_approval_state', 'released_state', 'obsolete_state',
                 'transitions', 'comment_transitions', 'obsolete_transitions', 'self_approve_transitions']

    def __init__(self):
        self.states = ['Planned', 'In Work', 'Approval', 'Released', 'Obsolete']
        self.open_states = ['Planned', 'In Work']
        self.initial_state = 'Planned'
        self.pre_approval_state = ['In Work']
        self.released_state = 'Released'
        self.obsolete_state = 'Obsolete'
        transitions = defaultdict(dict)
        transitions['Planned']['In Work'] = 'In Work'
        transitions['In Work']['Planned'] = 'Planned'
        transitions['In Work']['Approval'] = 'Send for Approval'
        transitions['In Work']['Obsolete'] = 'Make Obsolete'
        transitions['Approval']['In Work'] = 'Required Edit'
        transitions['Released']['In Work'] = 'Update'
        transitions['Released']['Obsolete'] = 'Make Obsolete'
        self.transitions = transitions
        self_approve_transitions = defaultdict(dict)
        self_approve_transitions['In Work']['Released'] = 'Self-Approve'
        self_approve_transitions['Approval']['Released'] = 'Self-Approve'
        self.self_approve_transitions = self_approve_transitions
        self.comment_transitions = ['Send for Approval', 'Required Edit', 'Self-Approve', 'Update']
        self.obsolete_transitions = ['Make Obsolete']

    def get_transitions_for_state(self, state, self_approved):
        transitions = dict(self.transitions[state])
        if self_approved:
            if state in self.self_approve_transitions.keys():
                # Remove any transitions which indicate approval
                del transitions[self.get_approval_state()]
                # Add self=approve transitions
                transitions.update(self.self_approve_transitions[state])
        return transitions

    def get_approval_state(self):
        return 'Approval'

    def get_workflow_image(self):
        return url_for('static', filename='images/workflows/vendor_part_workflow.png')

    def get_icon_for_state(self, state):
        icons = {}
        icons['Planned'] = 'pri-icons-planned'
        icons['In Work'] = 'pri-icons-in-work'
        icons['Approval'] = 'pri-icons-approval'
        icons['Released'] = 'pri-icons-thumbs-up'
        icons['Obsolete'] = 'pri-icons-obsolete'
        return icons[state]


class ProductWorkflow(object):
    __slots__ = ['states', 'open_states', 'initial_state', 'pre_approval_state', 'released_state', 'obsolete_state',
                 'transitions', 'comment_transitions', 'obsolete_transitions', 'self_approve_transitions']

    def __init__(self):
        self.states = ['Planned', 'In Work', 'Inspection', 'Approval', 'Released', 'Scrapped']
        self.open_states = ['Planned', 'In Work', 'Inspection']
        self.initial_state = 'Planned'
        self.pre_approval_state = ['Inspection']
        self.released_state = 'Released'
        self.obsolete_state = 'Scrapped'
        transitions = defaultdict(dict)
        transitions['Planned']['In Work'] = 'In Work'
        transitions['In Work']['Planned'] = 'Planned'
        transitions['In Work']['Inspection'] = 'Send for Inspection'
        transitions['In Work']['Scrapped'] = 'Scrap'
        transitions['Inspection']['In Work'] = 'In Work'
        transitions['Inspection']['Approval'] = 'Send for Approval'
        transitions['Inspection']['Scrapped'] = 'Scrap'
        transitions['Approval']['In Work'] = 'Required Edit'
        transitions['Released']['In Work'] = 'Rework'
        transitions['Released']['Scrapped'] = 'Scrap'
        self.transitions = transitions
        self_approve_transitions = defaultdict(dict)
        self_approve_transitions['In Work']['Released'] = 'Self-Approve'
        self_approve_transitions['Inspection']['Released'] = 'Self-Approve'
        self_approve_transitions['Approval']['Released'] = 'Self-Approve'
        self.self_approve_transitions = self_approve_transitions
        self.comment_transitions = ['Send for Inspection', 'Send for Approval',
                                    'Required Edit','Self-Approve', 'Rework']
        self.obsolete_transitions = ['Scrap']

    def get_transitions_for_state(self, state, self_approved):
        transitions = dict(self.transitions[state])
        if self_approved:
            if state in self.self_approve_transitions.keys():
                # Remove any transitions which indicate approval
                transitions.pop('Inspection', None)
                transitions.pop(self.get_approval_state(), None)
                # Add self=approve transitions
                transitions.update(self.self_approve_transitions[state])
        return transitions

    def get_approval_state(self):
        return 'Approval'

    def get_workflow_image(self):
        return url_for('static', filename='images/workflows/product_workflow.png')

    def get_icon_for_state(self, state):
        icons = {}
        icons['Planned'] = 'pri-icons-planned'
        icons['In Work'] = 'pri-icons-in-work'
        icons['Inspection'] = 'pri-icons-inspection'
        icons['Approval'] = 'pri-icons-approval'
        icons['Released'] = 'pri-icons-thumbs-up'
        icons['Scrapped'] = 'pri-icons-obsolete'
        return icons[state]


class AnomalyWorkflow(object):
    __slots__ = ['states', 'open_states', 'initial_state', 'pre_approval_state', 'released_state', 'obsolete_state',
                 'transitions', 'comment_transitions', 'self_approve_transitions']

    def __init__(self):
        self.states = ['Open', 'Analysis', 'Corrective', 'Approval', 'Closed']
        self.open_states = ['Open', 'Analysis', 'Corrective']
        self.initial_state = 'Open'
        self.pre_approval_state = ['Corrective']
        self.released_state = 'Closed'
        self.obsolete_state = 'Closed'
        transitions = defaultdict(dict)
        transitions['Open']['Analysis'] = 'Analysis'
        transitions['Analysis']['Open'] = 'Open'
        transitions['Analysis']['Corrective'] = 'Corrective'
        transitions['Corrective']['Analysis'] = 'Analysis'
        transitions['Corrective']['Approval'] = 'Send for Approval'
        transitions['Approval']['Analysis'] = 'Edit'
        self.transitions = transitions
        self_approve_transitions = defaultdict(dict)
        self_approve_transitions['Corrective']['Closed'] = 'Self-Approve'
        self.self_approve_transitions = self_approve_transitions
        self.comment_transitions = ['Corrective', 'Edit', 'Self-Approve', 'Send for Approval']
        #  self.obsolete_transitions = ['Make Obsolete']

    def get_transitions_for_state(self, state, self_approved):
        transitions = dict(self.transitions[state])
        if self_approved:
            if state in self.self_approve_transitions.keys():
                # Remove any transitions which indicate approval
                del transitions[self.get_approval_state()]
                # Add self=approve transitions
                transitions.update(self.self_approve_transitions[state])
        return transitions

    def get_approval_state(self):
        return 'Approval'

    def get_workflow_image(self):
        return url_for('static', filename='images/workflows/anomaly_workflow.png')

    def get_icon_for_state(self, state):
        icons = {}
        icons['Open'] = 'pri-icons-open'
        icons['Analysis'] = 'pri-icons-in-work'
        icons['Corrective'] = 'pri-icons-corrective'
        icons['Approval'] = 'pri-icons-approval'
        icons['Closed'] = 'pri-icons-thumbs-up'
        return icons[state]


class ECOWorkflow(object):
    __slots__ = ['states', 'open_states', 'initial_state', 'pre_approval_state', 'released_state', 'obsolete_state',
                 'transitions', 'comment_transitions', 'obsolete_transitions', 'self_approve_transitions']

    def __init__(self):
        self.states = ['In Work', 'Approval', 'Approved', 'Obsolete']
        self.open_states = ['In Work']
        self.initial_state = 'In Work'
        self.pre_approval_state = ['In Work']
        self.released_state = 'Approved'
        self.obsolete_state = 'Obsolete'
        transitions = defaultdict(dict)
        transitions['In Work']['Approval'] = 'Send for Approval'
        transitions['In Work']['Obsolete'] = 'Make Obsolete'
        transitions['Approval']['In Work'] = 'Required Edit'
        transitions['Approved']['Obsolete'] = 'Make Obsolete'
        self.transitions = transitions
        self_approve_transitions = defaultdict(dict)
        self_approve_transitions['In Work']['Approved'] = 'Self-Approve'
        self_approve_transitions['Approval']['Approved'] = 'Self-Approve'
        self.self_approve_transitions = self_approve_transitions
        self.comment_transitions = ['Send for Approval', 'Required Edit', 'Self-Approve']
        self.obsolete_transitions = ['Make Obsolete']

    def get_transitions_for_state(self, state, self_approved):
        transitions = dict(self.transitions[state])
        if self_approved:
            if state in self.self_approve_transitions.keys():
                # Remove any transitions which indicate approval
                del transitions[self.get_approval_state()]
                # Add self=approve transitions
                transitions.update(self.self_approve_transitions[state])
        return transitions

    def get_approval_state(self):
        return 'Approval'

    def get_workflow_image(self):
        return url_for('static', filename='images/workflows/eco_workflow.png')

    def get_icon_for_state(self, state):
        icons = {}
        icons['In Work'] = 'pri-icons-in-work'
        icons['Approval'] = 'pri-icons-approval'
        icons['Approved'] = 'pri-icons-thumbs-up'
        icons['Obsolete'] = 'pri-icons-obsolete'
        return icons[state]


class ProcedureWorkflow(object):
    __slots__ = ['states', 'open_states', 'initial_state', 'pre_approval_state', 'released_state', 'obsolete_state',
                 'transitions', 'comment_transitions', 'obsolete_transitions', 'self_approve_transitions']

    def __init__(self):
        self.states = ['In Work', 'Approval', 'Released', 'Obsolete']
        self.open_states = ['In Work']
        self.initial_state = 'In Work'
        self.pre_approval_state = ['In Work']
        self.released_state = 'Released'
        self.obsolete_state = 'Obsolete'
        transitions = defaultdict(dict)
        transitions['In Work']['Approval'] = 'Send for Approval'
        transitions['In Work']['Obsolete'] = 'Make Obsolete'
        transitions['Approval']['In Work'] = 'Required Edit'
        transitions['Approved']['Obsolete'] = 'Make Obsolete'
        self.transitions = transitions
        self_approve_transitions = defaultdict(dict)
        self_approve_transitions['In Work']['Released'] = 'Self-Approve'
        self_approve_transitions['Approval']['Released'] = 'Self-Approve'
        self.self_approve_transitions = self_approve_transitions
        self.comment_transitions = ['Send for Approval', 'Required Edit', 'Self-Approve']
        self.obsolete_transitions = ['Make Obsolete']

    def get_transitions_for_state(self, state, self_approved):
        transitions = dict(self.transitions[state])
        if self_approved:
            if state in self.self_approve_transitions.keys():
                # Remove any transitions which indicate approval
                del transitions[self.get_approval_state()]
                # Add self=approve transitions
                transitions.update(self.self_approve_transitions[state])
        return transitions

    def get_approval_state(self):
        return 'Approval'

    def get_workflow_image(self):
        return url_for('static', filename='images/workflows/procedure_workflow.png')

    def get_icon_for_state(self, state):
        icons = {}
        icons['In Work'] = 'pri-icons-in-work'
        icons['Approval'] = 'pri-icons-approval'
        icons['Released'] = 'pri-icons-thumbs-up'
        icons['Obsolete'] = 'pri-icons-obsolete'
        return icons[state]


class AsRunWorkflow(object):
    __slots__ = ['states', 'open_states', 'initial_state', 'pre_approval_state', 'released_state', 'obsolete_state',
                 'transitions', 'comment_transitions', 'obsolete_transitions', 'self_approve_transitions']

    def __init__(self):
        self.states = ['In Work', 'Approval', 'Complete', 'Obsolete']
        self.open_states = ['In Work']
        self.initial_state = 'In Work'
        self.pre_approval_state = ['In Work']
        self.released_state = 'Complete'
        self.obsolete_state = 'Obsolete'
        transitions = defaultdict(dict)
        transitions['In Work']['Approval'] = 'Send for Approval'
        transitions['In Work']['Obsolete'] = 'Make Obsolete'
        transitions['Approval']['In Work'] = 'Required Edit'
        transitions['Approved']['Obsolete'] = 'Make Obsolete'
        self.transitions = transitions
        self_approve_transitions = defaultdict(dict)
        self_approve_transitions['In Work']['Complete'] = 'Self-Approve'
        self_approve_transitions['Approval']['Complete'] = 'Self-Approve'
        self.self_approve_transitions = self_approve_transitions
        self.comment_transitions = ['Send for Approval', 'Required Edit', 'Self-Approve']
        self.obsolete_transitions = ['Make Obsolete']

    def get_transitions_for_state(self, state, self_approved):
        transitions = dict(self.transitions[state])
        if self_approved:
            if state in self.self_approve_transitions.keys():
                # Remove any transitions which indicate approval
                del transitions[self.get_approval_state()]
                # Add self=approve transitions
                transitions.update(self.self_approve_transitions[state])
        return transitions

    def get_approval_state(self):
        return 'Approval'

    def get_workflow_image(self):
        return url_for('static', filename='images/workflows/as_run_workflow.png')

    def get_icon_for_state(self, state):
        icons = {}
        icons['In Work'] = 'pri-icons-in-work'
        icons['Approval'] = 'pri-icons-approval'
        icons['Complete'] = 'pri-icons-thumbs-up'
        icons['Obsolete'] = 'pri-icons-obsolete'
        return icons[state]
