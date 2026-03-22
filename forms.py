from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, TextAreaField, SubmitField
from wtforms.validators import DataRequired, Email, Length, EqualTo

class RegistrationForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired(), Length(min=3, max=80)])
    email = StringField('Email', validators=[DataRequired(), Email()])
    password = PasswordField('Password', validators=[DataRequired(), Length(min=6)])
    confirm_password = PasswordField('Confirm Password', validators=[DataRequired(), EqualTo('password')])
    submit = SubmitField('Sign Up')

class LoginForm(FlaskForm):
    email = StringField('Email', validators=[DataRequired(), Email()])
    password = PasswordField('Password', validators=[DataRequired()])
    submit = SubmitField('Login')

class ResumeForm(FlaskForm):
    title = StringField('Resume Title', validators=[DataRequired()])
    full_name = StringField('Full Name', validators=[DataRequired()])
    email = StringField('Email', validators=[DataRequired(), Email()])
    phone = StringField('Phone Number')
    address = StringField('Address')
    summary = TextAreaField('Professional Summary', validators=[DataRequired()])
    education = TextAreaField('Education', validators=[DataRequired()], 
                              description='Format: Degree, Institution, Year, GPA\nExample: B.Sc. Computer Science, Stanford University, 2020, 3.8')
    experience = TextAreaField('Work Experience', validators=[DataRequired()],
                               description='Format: Job Title, Company, Year, Description\nExample: Software Engineer, Google, 2020-2023, Developed web applications')
    skills = TextAreaField('Skills', validators=[DataRequired()],
                          description='List your skills separated by commas\nExample: Python, JavaScript, Flask, React')
    submit = SubmitField('Save Resume')