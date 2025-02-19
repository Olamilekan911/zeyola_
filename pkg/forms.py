from flask_wtf import FlaskForm
from flask_wtf.file import FileField, FileAllowed
from wtforms import StringField, PasswordField,EmailField,IntegerField, SubmitField,TextAreaField,SelectField,FloatField,DecimalField

from wtforms.validators import DataRequired, Email,length,Optional

class SignUpForm(FlaskForm):
    email = EmailField('Email', validators=[DataRequired()])
    fname = StringField('Firstname', validators=[DataRequired(), length(min=2)])
    lname = StringField('Lastname', validators=[DataRequired(), length(min=2)])
    password = PasswordField('Enter Your Password', validators=[DataRequired(), length(min=6)])
    cpassword = PasswordField('Confirm Your Password', validators=[DataRequired(), length(min=6)])
    submit = SubmitField('Sign Up')



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
    in_stock = IntegerField('Quantity Available', validators=[DataRequired()])
    old_price = FloatField('Old Price', validators=[DataRequired()])
    new_price = FloatField('New Price', validators=[DataRequired()])
    pro_desc = TextAreaField('Product Details', validators=[Optional()])
    pro_spec = TextAreaField('Product Specification', validators=[Optional()])
    pro_picture = FileField('Product Picture', validators=[
        FileAllowed(['jpg', 'png', 'jpeg'], 'Images only!'),
        Optional()  
    ])

    
    def populate_categories(self):
        from pkg.models import Category 
        self.pro_category_id.choices = [
            (cat.category_id, cat.category_name)
            for cat in Category.query.all()
        ]
