from flask_wtf import FlaskForm
from flask_wtf.file import FileField, FileAllowed
from wtforms import StringField, PasswordField,EmailField, SubmitField,TextAreaField,SelectField,FloatField,DecimalField

from wtforms.validators import DataRequired, Email,length


class LoginForm(FlaskForm):
    email = StringField('Email:', validators=[Email(message='Enter a valid email')])
    password = PasswordField('Password:', validators=[DataRequired(message='Password cannot be emppty')])
    submit = SubmitField('Login')

class AdminForm(FlaskForm):
    email = EmailField('Email', validators=[DataRequired()])
    password = PasswordField('Enter your password', validators=[DataRequired(), length(min=6)])
    submit = SubmitField('Sign In')

class AddProductForm(FlaskForm):
    pro_name = StringField('Product Name', validators=[DataRequired()])
    pro_category_id = SelectField('Category', coerce=int, validators=[DataRequired()])
    in_stock = FloatField('Quantity Available', validators=[DataRequired()])
    old_price = DecimalField('New price', validators=[DataRequired()])
    new_price = DecimalField('Old Price', validators=[DataRequired()])
    pro_picture = FileField('Product Picture',
                            validators=[FileAllowed(['jpg', 'png', 'jpeg'],
                                                    'Images only!')])

    # Populate the categories dropdown dynamically from your Category model
    def populate_categories(self):
        from pkg.models import Category
        self.pro_category_id.choices = [
            (cat.category_id, cat.category_name)
            for cat in Category.query.all()]
