import datetime as dt
import operator

from flask_login import current_user
from flask_wtf import FlaskForm
from wtforms import StringField, DateTimeField, SelectField, TextAreaField
from wtforms.ext.sqlalchemy.fields import QuerySelectField
from wtforms.validators import DataRequired, Optional

from pid.backend.models import Settings
from pid.user.models import User


def get_users():
    return User.query.all()


class CreateTaskForm(FlaskForm):
    title = StringField('Title', validators=[DataRequired()])
    assign_to = QuerySelectField('Assign To', query_factory=get_users,
                                 get_label='last_name_first_name', default=current_user)
    urgency = SelectField(choices=[("At Your Leisure", "At Your Leisure"), ("Important", "Important"),
                                   ("Urgent", "Urgent"), ("SoF", "SoF")], default="At Your Leisure")
    create_need_date = DateTimeField('Need Date', validators=[DataRequired()],
                                     default=dt.datetime.utcnow, format="%Y-%m-%d")
    summary = TextAreaField('Summary', validators=[Optional()])

    def __init__(self, *args, **kwargs):
        """Create instance."""
        super(CreateTaskForm, self).__init__(*args, **kwargs)
        settings = Settings.get_settings()
        if settings:
            self.assign_to.get_label = operator.attrgetter(settings.name_order)

    def validate(self):
        return super(CreateTaskForm, self).validate()
