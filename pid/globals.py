# -*- coding: utf-8 -*-

# This global will put all the contents of text.properties in a dictionary during app start,
# to make it easier to query from Jinja2 templates and only one place to update text for the application
TEXT = {}
with open('pid/text.properties', 'r') as f:
    for line in f:
        stripped_line = line.strip()
        if stripped_line and not stripped_line.startswith('#'):
            key_value = stripped_line.split('=')
            key = key_value[0].strip()
            value = '='.join(key_value[1:]).strip('" \t')
            TEXT[key] = value

FORBIDDEN_REVISIONS = ['I', 'O', 'Q', 'S', 'X', 'Z']

ADVANCED_SEARCH_COLUMNS = {
    'design': [
        'ID #',
        'Revision',
        'Name',
        'State',
        'Summary',
        'Notes',
        'Project',
        'Owner',
        'Created By',
        'Created On',
        'Anomalies',
        'ECOs'
    ],
    'vendor_part': [
        'ID #',
        'Name',
        'State',
        'Summary',
        'Notes',
        'Project',
        'Owner',
        'Material',
        'Vendor',
        'Created By',
        'Created On',
        'Anomalies'
    ],
    'product': [
        'ID #',
        'Title',
        'State',
        'H/W Type',
        'Owner',
        'Material',
        'Notes',
        'Project',
        'Created By',
        'Created On'
    ],
    'vendor_product': [
        'ID #',
        'Title',
        'State',
        'H/W Type',
        'Owner',
        'Material',
        'Notes',
        'Project',
        'Created By',
        'Created On',
        'Vendor'
    ],
    'anomaly': [
        'ID #',
        'Title',
        'State',
        'Criticality',
        'Project',
        'Summary',
        'Owner',
        'Created By',
        'Created On',
        'Corrective Action',
        'Analysis'
    ],
    'eco': [
        'ID #',
        'Title',
        'State',
        'Project',
        'Summary',
        'Owner',
        'Created By',
        'Created On'
    ],
    'procedure': [
        'ID #',
        'Revision',
        'Title',
        'State',
        'Summary',
        'Project',
        'Owner',
        'Created By',
        'Created On'
    ],
    'spec': [
        'ID #',
        'Revision',
        'Title',
        'State',
        'Summary',
        'Scope',
        'Owner',
        'Created By',
        'Created On'
    ]
}
