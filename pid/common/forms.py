from flask_wtf import FlaskForm
from wtforms import StringField, TextAreaField, HiddenField
from wtforms.validators import DataRequired, Optional


class CreateCompanyForm(FlaskForm):
    name = StringField('Name', validators=[DataRequired('A name is required.')])
    website = StringField('Website')
    address = StringField('Address')
    notes = StringField('Notes')

    def __init__(self, *args, **kwargs):
        """Create instance."""
        super(CreateCompanyForm, self).__init__(*args, **kwargs)

    def validate(self):
        return super(CreateCompanyForm, self).validate()


class WorkflowCommentForm(FlaskForm):
    parent_id = HiddenField()
    parent_class = HiddenField()
    state = HiddenField()
    comment = TextAreaField('Comment', validators=[Optional()])

    def __init__(self, *args, **kwargs):
        """Create instance."""
        super(WorkflowCommentForm, self).__init__(*args, **kwargs)


    def validate(self):
        return super(WorkflowCommentForm, self).validate()
