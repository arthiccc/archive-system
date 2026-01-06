from flask_wtf import FlaskForm
from wtforms import StringField, TextAreaField, SelectField, SubmitField
from wtforms.validators import DataRequired, Length, Optional


class CategoryForm(FlaskForm):
    name = StringField("Category Name", validators=[DataRequired(), Length(max=100)])
    parent = SelectField("Parent Category", coerce=int, validators=[Optional()])
    description = TextAreaField("Description", validators=[Optional(), Length(max=500)])
    submit = SubmitField("Save Category")
