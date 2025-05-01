from wtforms import Form, StringField, PasswordField, BooleanField, SelectField, validators

class RegisterForm(Form):
    username = StringField('Username', [
        validators.Length(min=4, max=25, message='Username must be between 4-25 characters'),
        validators.DataRequired(message='Username is required')
    ])
    email = StringField('Email', [
        validators.Length(min=6, max=50, message='Email must be between 6-50 characters'),
        validators.DataRequired(message='Email is required')
        # validators.Email(message='Please enter a valid email address')  # 这行被完全注释掉了
    ])
    password = PasswordField('Password', [
        validators.DataRequired(message='Password is required'),
        validators.Length(min=6, message='Password must be at least 6 characters'),
        validators.EqualTo('confirm', message='Passwords must match')
    ])
    confirm = PasswordField('Confirm Password')
    riot_id = StringField('Riot ID')
    tagline = StringField('Tagline')
    region = SelectField('Region', choices=[
        ('', 'Select your region'),
        ('asia', 'Asia'),
        ('europe', 'Europe'),
        ('america', 'Americas'),
        ('oceania', 'Oceania')
    ])

class LoginForm(Form):
    username = StringField('Username', [
        validators.DataRequired(message='Please enter your username')
    ])
    password = PasswordField('Password', [
        validators.DataRequired(message='Please enter your password')
    ])
    remember = BooleanField('Remember Me')