from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_required, current_user
from models import db, Class, Enrollment, Semester, User, Warning
from sqlalchemy import or_

student_bp = Blueprint('student', __name__, url_prefix='/student')

@student_bp.route('/complaint', methods=['POST'])
@login_required
def complaint():
    if current_user.role != 'student':
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
    return redirect(url_for('student.dashboard'))

@student_bp.route('/study-buddy-opt-in', methods=['POST'])
@login_required
def study_buddy_opt_in():
    if current_user.role != 'student':
        return "Unauthorized", 403
    
    enrollment_id = request.form.get('enrollment_id')
    enrollment = Enrollment.query.get_or_404(enrollment_id)
    if enrollment.student_id != current_user.id:
        return "Unauthorized", 403
    
    enrollment.study_buddy_opt_in = not enrollment.study_buddy_opt_in
    db.session.commit()
    status = "opted in" if enrollment.study_buddy_opt_in else "opted out"
    flash(f"Successfully {status} for Study Buddy matching in this class.", "success")
    return redirect(url_for('student.dashboard'))

@student_bp.route('/dashboard')
@login_required
def dashboard():
    if current_user.role != 'student':
        return "Unauthorized", 403
    
    enrollments_data = []
    user_enrollments = Enrollment.query.filter_by(student_id=current_user.id).all()
    
    for enrollment in user_enrollments:
        cls = Class.query.get(enrollment.class_id)
        # Find buddies: same class, opted in, not the current user
        buddies = []
        if enrollment.study_buddy_opt_in:
            buddies = db.session.query(User).join(Enrollment).filter(
                Enrollment.class_id == cls.id,
                Enrollment.study_buddy_opt_in == True,
                Enrollment.student_id != current_user.id
            ).all()
        enrollments_data.append({
            'enrollment': enrollment,
            'class': cls,
            'buddies': buddies
        })
    
    warnings = Warning.query.filter_by(user_id=current_user.id).all()
    
    return render_template('dashboard/student.html', enrollments_data=enrollments_data, warnings=warnings)

from utils import filter_content

@student_bp.route('/review', methods=['POST'])
@login_required
def review():
    if current_user.role != 'student':
        return "Unauthorized", 403
    
    class_id = request.form.get('class_id')
    stars = int(request.form.get('stars'))
    content = request.form.get('content')
    
    # Check if enrolled
    enrollment = Enrollment.query.filter_by(student_id=current_user.id, class_id=class_id).first()
    if not enrollment:
        flash('You must be enrolled in this class to leave a review.', 'danger')
        return redirect(url_for('student.dashboard'))
    
    # Check if instructor has posted grades (P4 check)
    cls = Class.query.get(class_id)
    if enrollment.grade:
        flash('You cannot review a class after a grade has been assigned.', 'warning')
        return redirect(url_for('student.dashboard'))

    # Taboo filtering
    filtered_content, warning_add = filter_content(content, current_user.id)
    current_user.warning_count += warning_add
    
    if filtered_content is None:
        db.session.commit()
        flash('Review blocked due to too many taboo words. You received 2 warnings.', 'danger')
        return redirect(url_for('student.dashboard'))

    new_review = Review(
        student_id=current_user.id,
        class_id=class_id,
        stars=stars,
        content=filtered_content,
        is_visible=True
    )
    db.session.add(new_review)
    db.session.commit()
    
    if warning_add > 0:
        flash(f'Review posted with filters. You received {warning_add} warning(s).', 'warning')
    else:
        flash('Review posted successfully!', 'success')
    
    # Check if avg rating < 2 for instructor warning
    from sqlalchemy import func
    avg_rating = db.session.query(func.avg(Review.stars)).filter(Review.class_id == class_id).scalar()
    if avg_rating and avg_rating < 2:
        instructor = User.query.get(cls.instructor_id)
        if instructor:
            warn = Warning(user_id=instructor.id, reason=f"Average rating for your class '{cls.name}' has dropped below 2.")
            instructor.warning_count += 1
            db.session.add(warn)
            db.session.commit()

    return redirect(url_for('student.dashboard'))
@login_required
def register():
    if current_user.role != 'student':
        return "Unauthorized", 403
    
    # Get current semester (assuming only one active for registration)
    current_sem = Semester.query.filter(Semester.current_period <= 2).order_by(Semester.id.desc()).first()
    if not current_sem or current_sem.current_period != 2:
        flash('Course registration is only open during Period 2.', 'warning')
        return redirect(url_for('student.dashboard'))

    if request.method == 'POST':
        class_id = request.form.get('class_id')
        cls = Class.query.get_or_404(class_id)
        
        # Check if already enrolled
        existing = Enrollment.query.filter_by(student_id=current_user.id, class_id=cls.id).first()
        if existing:
            flash('Already enrolled in this class.', 'info')
            return redirect(url_for('student.register'))

        # Check for max courses (4)
        current_count = Enrollment.query.filter_by(student_id=current_user.id).join(Class).filter(Class.semester_id == current_sem.id).count()
        if current_count >= 4:
            flash('Cannot register for more than 4 courses per semester.', 'danger')
            return redirect(url_for('student.register'))

        # Check if full
        enrolled_count = Enrollment.query.filter_by(class_id=cls.id, is_waitlisted=False).count()
        is_waitlisted = False
        if enrolled_count >= cls.size_limit:
            is_waitlisted = True
            flash('Class is full. You have been added to the waitlist.', 'warning')
        
        new_enrollment = Enrollment(
            student_id=current_user.id,
            class_id=cls.id,
            is_waitlisted=is_waitlisted
        )
        db.session.add(new_enrollment)
        db.session.commit()
        if not is_waitlisted:
            flash(f'Successfully registered for {cls.name}!', 'success')
        return redirect(url_for('student.dashboard'))

    # List available classes for current semester
    available_classes = Class.query.filter_by(semester_id=current_sem.id, status='open').all()
    return render_template('student/register.html', classes=available_classes, current_sem=current_sem)
