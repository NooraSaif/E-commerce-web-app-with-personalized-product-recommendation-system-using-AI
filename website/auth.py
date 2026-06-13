from flask import Blueprint, render_template, flash, redirect, request
from .forms import LoginForm, RegistrForm, ChangePasswordForm
from .models import User
from . import database
from flask_login import login_user, login_required, logout_user

auth = Blueprint('auth', __name__)

@auth.route('/signup', methods=['GET', 'POST'])
def sing_up(): 
    form = RegistrForm()
    if form.validate_on_submit():
        email = form.email.data
        username = form.user_name.data
        phone_number = form.phone_number.data
        password1 = form.password1.data
        password2 = form.password2.data

        if password1 == password2:
            new_user = User()
            new_user.email = email
            new_user.user_name = username
            new_user.phone_number = phone_number
            new_user.password = password2

            try:
                database.session.add(new_user)
                database.session.commit()
                flash('Account Created Successfully, Login now')
                return redirect('/login')
            except Exception as e:
                print(e)
                flash('Email already exists')

            form.email.data = ''
            form.user_name.data = ''
            form.phone_number.data = ''
            form.password1.data = ''
            form.password2.data = ''
        else:
            flash('Password do not match!')
    elif request.method == 'POST':
        for error_list in form.errors.values():
            for error in error_list:
                flash(error)

    return render_template('signup.html', form=form)

@auth.route('/login', methods=['GET', 'POST'])
def login():
    form = LoginForm()
    if form.validate_on_submit():
        email = form.email.data
        password = form.password.data

        user: User = User.query.filter_by(email=email).first()

        if user:
            if user.check_password(password=password):
                login_user(user)
                return redirect('/')
            else:
                flash('Incorrect Email or Password')

        else:
            flash('You do not have account yet, please Sign Up')

    elif request.method == 'POST':
        for error_list in form.errors.values():
            for error in error_list:
                flash(error)

    return render_template('login.html', form=form)

@auth.route('/logout', methods=['GET', 'POST'])
@login_required
def log_out():
    logout_user()
    return redirect('/')

@auth.route('/profile/<int:user_id>')
@login_required
def profile(user_id):
    user = User.query.get(user_id)
    print('User ID:', user_id)
    return render_template('profile.html', user=user)


@auth.route('/change-password/<int:user_id>', methods=['GET', 'POST'])
@login_required
def change_password(user_id):
    form = ChangePasswordForm()
    user: User = User.query.get(user_id)
    if form.validate_on_submit():
        old_password = form.old_password.data
        new_password = form.new_password.data
        confirm = form.confirm.data

        if user.check_password(old_password):
            if new_password == confirm:
                user.password = confirm
                database.session.commit()
                flash('Updated Successfully')
                return redirect(f'/profile/{user.id}')
            else:
                flash('New Passwords do not match!!')

        else:
            flash('The old password is Incorrect')
    return render_template('change_password.html', form=form)


