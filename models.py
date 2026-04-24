from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from datetime import datetime
from werkzeug.security import generate_password_hash, check_password_hash

db = SQLAlchemy()

class User(db.Model, UserMixin):
    __tablename__ = 'users'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(128))
    role = db.Column(db.String(20), nullable=False)  # 'visitor', 'student', 'instructor', 'registrar'
    status = db.Column(db.String(20), default='active')  # 'active', 'suspended', 'terminated'
    warning_count = db.Column(db.Integer, default=0)
    is_first_login = db.Column(db.Boolean, default=True)

    def set_password(self, password):
        self.password_hash = generate_password_hash(password, method='pbkdf2:sha256')

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    def add_warning(self, reason):
        from models import Warning
        warn = Warning(user_id=self.id, reason=reason)
        db.session.add(warn)
        self.warning_count += 1
        
        if self.role == 'student' and self.warning_count >= 3:
            self.status = 'suspended'
        elif self.role == 'instructor' and self.warning_count >= 3:
            self.status = 'suspended'
        
        db.session.commit()

class Application(db.Model):
    __tablename__ = 'applications'
    id = db.Column(db.Integer, primary_key=True)
    applicant_email = db.Column(db.String(120), nullable=False)
    applicant_name = db.Column(db.String(100), nullable=False)
    type = db.Column(db.String(20), nullable=False)  # 'student', 'instructor'
    status = db.Column(db.String(20), default='pending')  # 'pending', 'accepted', 'rejected'
    justification = db.Column(db.Text)
    gpa_at_application = db.Column(db.Float) # Only for student applications

class Semester(db.Model):
    __tablename__ = 'semesters'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), nullable=False)
    current_period = db.Column(db.Integer, default=1)  # 1-4

class Class(db.Model):
    __tablename__ = 'classes'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    schedule = db.Column(db.String(100))
    instructor_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    size_limit = db.Column(db.Integer, default=30)
    semester_id = db.Column(db.Integer, db.ForeignKey('semesters.id'))
    status = db.Column(db.String(20), default='setup') # 'setup', 'open', 'closed', 'cancelled'

class Enrollment(db.Model):
    __tablename__ = 'enrollments'
    id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    class_id = db.Column(db.Integer, db.ForeignKey('classes.id'))
    grade = db.Column(db.String(2), nullable=True) # A, B, C, D, F
    is_waitlisted = db.Column(db.Boolean, default=False)
    study_buddy_opt_in = db.Column(db.Boolean, default=False)

class Review(db.Model):
    __tablename__ = 'reviews'
    id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    class_id = db.Column(db.Integer, db.ForeignKey('classes.id'))
    stars = db.Column(db.Integer, nullable=False)
    content = db.Column(db.Text, nullable=False)
    is_visible = db.Column(db.Boolean, default=True)

class Complaint(db.Model):
    __tablename__ = 'complaints'
    id = db.Column(db.Integer, primary_key=True)
    filer_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    target_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    description = db.Column(db.Text, nullable=False)
    status = db.Column(db.String(20), default='pending') # 'pending', 'resolved'
    resolution = db.Column(db.Text)

class TabooWord(db.Model):
    __tablename__ = 'taboo_words'
    id = db.Column(db.Integer, primary_key=True)
    word = db.Column(db.String(50), unique=True, nullable=False)

class Warning(db.Model):
    __tablename__ = 'warnings'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    reason = db.Column(db.Text, nullable=False)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)
