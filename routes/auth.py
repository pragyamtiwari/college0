from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_user, logout_user, login_required, current_user
from werkzeug.security import generate_password_hash
from models import db, User

auth_bp = Blueprint('auth', __name__)

@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')
        user = User.query.filter_by(email=email).first()

        if user and user.check_password(password):
            login_user(user)
            if user.is_first_login:
                return redirect(url_for('auth.change_password'))
            
            # Redirect to appropriate dashboard
            if user.role == 'student':
                return redirect(url_for('student.dashboard'))
            elif user.role == 'instructor':
                return redirect(url_for('instructor.dashboard'))
            elif user.role == 'registrar':
                return redirect(url_for('registrar.dashboard'))
        
        flash('Invalid email or password', 'danger')
    return render_template('auth/login.html')

@auth_bp.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('visitor.home'))

@auth_bp.route('/change-password', methods=['GET', 'POST'])
@login_required
def change_password():
    if not current_user.is_first_login:
        return redirect(url_for('visitor.home'))
    
    if request.method == 'POST':
        new_password = request.form.get('password')
        current_user.set_password(new_password)
        current_user.is_first_login = False
        db.session.commit()
        flash('Password updated successfully!', 'success')
        
        # Redirect based on role
        if current_user.role == 'student':
            return redirect(url_for('student.dashboard'))
        elif current_user.role == 'instructor':
            return redirect(url_for('instructor.dashboard'))
        elif current_user.role == 'registrar':
            return redirect(url_for('registrar.dashboard'))

    return render_template('auth/change_password.html')
