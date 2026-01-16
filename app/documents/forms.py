from flask_wtf import FlaskForm
from wtforms import StringField, TextAreaField, SelectField, FileField, SubmitField
from wtforms.validators import DataRequired, Length, Optional
from flask import current_app


class DocumentUploadForm(FlaskForm):
    file = FileField("File", validators=[DataRequired()])
    category = SelectField("Category", coerce=int, validators=[DataRequired()])
    academic_period = SelectField(
        "Academic Period", coerce=int, validators=[DataRequired()]
    )
    correspondent = SelectField("Correspondent", coerce=int, validators=[Optional()])
    tags = StringField(
        "Tags (comma separated)", validators=[Optional(), Length(max=200)]
    )
    submit = SubmitField("Upload Document")


class DocumentEditForm(FlaskForm):
    title = StringField("Title", validators=[DataRequired(), Length(max=255)])
    category = SelectField("Category", coerce=int, validators=[DataRequired()])
    academic_period = SelectField(
        "Academic Period", coerce=int, validators=[DataRequired()]
    )
    correspondent = SelectField("Correspondent", coerce=int, validators=[Optional()])
    description = TextAreaField(
        "Description", validators=[Optional(), Length(max=2000)]
    )
    tags = StringField(
        "Tags (comma separated)", validators=[Optional(), Length(max=200)]
    )
    submit = SubmitField("Save Changes")
