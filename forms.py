from flask_wtf import FlaskForm
from wtforms import StringField , PasswordField , SubmitField
from wtforms.fields.simple import TextAreaField
from wtforms.validators import DataRequired, Email, EqualTo, Length


class RegistrationForm(FlaskForm):
    username = StringField('Username',validators=[DataRequired(),Length(min=3,max=100)])
    email = StringField('Email',validators=[DataRequired(),Email()])
    password = PasswordField('Password',validators=[DataRequired(),Length(min=6)])
    confirm_password = PasswordField('Confirm Password',validators=[DataRequired(),EqualTo('password' , message='密码必须一致')])
    submit = SubmitField('Sign Up')
    

class LoginForm(FlaskForm):
    email = StringField('Email',validators=[DataRequired(),Email()])
    password = PasswordField('Password',validators=[DataRequired(),Length(min=6)])
    submit = SubmitField('Login')


class GroupForm(FlaskForm):
    name = StringField('Group Name',validators=[DataRequired(),Length(min=3,max=100)])
    description = TextAreaField('Description',validators=[DataRequired(),Length(min=10,max=512)])
    submit = SubmitField('Create Group')


class PostForm(FlaskForm):
    title = StringField('Title',validators=[DataRequired(),Length(min=3,max=100)])
    content = TextAreaField('Content',validators=[DataRequired(),Length(min=10)])
    submit = SubmitField('Post')


class CommentForm(FlaskForm):
    content = TextAreaField('Comment',validators=[DataRequired(),Length(min=1,max=512)])
    submit = SubmitField('Submit Comment')
