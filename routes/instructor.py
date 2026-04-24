from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_required, current_user
from models import db, Class, Enrollment, User, Semester, Warning

instructor_bp = Blueprint('instructor', __name__, url_prefix='/instructor')

@instructor_bp.route('/complaint', methods=['POST'])
@login_required
def complaint():
    if current_user.role != 'instructor':
        return "Unauthorized", 403
    
    target_id = request.form.get('target_id')
    description = request.form.get('description')
    
    from models import Complaint
    new_comp = Complaint(
        filer_id=current_user.id,
        target_id=target_id,
        description=description
    )
    db.session.add(new_comp)
    db.session.commit()
    flash('Complaint filed successfully.', 'info')
    return redirect(url_for('instructor.dashboard'))

@instructor_bp.route('/dashboard')
@login_required
def dashboard():
    if current_user.role != 'instructor':
        return "Unauthorized", 403
    
    classes = Class.query.filter_by(instructor_id=current_user.id).all()
    warnings = Warning.query.filter_by(user_id=current_user.id).all()
    
    return render_template('dashboard/instructor.html', classes=classes, warnings=warnings)

@instructor_bp.route('/class/<int:class_id>')
@login_required
def class_detail(class_id):
    if current_user.role != 'instructor':
        return "Unauthorized", 403
    
    cls = Class.query.get_or_404(class_id)
    if cls.instructor_id != current_user.id:
        return "Unauthorized", 403
    
    enrollments = db.session.query(Enrollment, User).join(User).filter(Enrollment.class_id == class_id).all()
    sem = Semester.query.get(cls.semester_id)
    
    return render_template('instructor/class_detail.html', cls=cls, enrollments=enrollments, sem=sem)

@instructor_bp.route('/grade', methods=['POST'])
@login_required
def grade():
    if current_user.role != 'instructor':
        return "Unauthorized", 403
    
    enrollment_id = request.form.get('enrollment_id')
    grade = request.form.get('grade')
    
    enrollment = Enrollment.query.get_or_404(enrollment_id)
    cls = Class.query.get(enrollment.class_id)
    
    if cls.instructor_id != current_user.id:
        return "Unauthorized", 403
    
    sem = Semester.query.get(cls.semester_id)
    if sem.current_period != 4:
        flash('Grading is only allowed during Period 4.', 'danger')
        return redirect(url_for('instructor.class_detail', class_id=cls.id))
    
    enrollment.grade = grade
    db.session.commit()
    flash(f'Grade {grade} assigned successfully.', 'success')
    return redirect(url_for('instructor.class_detail', class_id=cls.id))
