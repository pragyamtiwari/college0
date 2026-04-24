from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_required, current_user
from models import db, Application, User, Semester, Class, Warning
import random
import string

registrar_bp = Blueprint('registrar', __name__, url_prefix='/registrar')

def generate_random_password(length=8):
    characters = string.ascii_letters + string.digits
    return ''.join(random.choice(characters) for i in range(length))

@registrar_bp.route('/dashboard')
@login_required
def dashboard():
    if current_user.role != 'registrar':
        return "Unauthorized", 403
    
    student_count = User.query.filter_by(role='student').count()
    instructor_count = User.query.filter_by(role='instructor').count()
    pending_apps = Application.query.filter_by(status='pending').count()
    
    return render_template('dashboard/registrar.html', 
                           student_count=student_count, 
                           instructor_count=instructor_count, 
                           pending_apps=pending_apps)

@registrar_bp.route('/applications')
@login_required
def applications():
    if current_user.role != 'registrar':
        return "Unauthorized", 403
    apps = Application.query.all()
    return render_template('registrar/applications.html', apps=apps)

@registrar_bp.route('/applications/<int:app_id>/process', methods=['POST'])
@login_required
def process_application(app_id):
    if current_user.role != 'registrar':
        return "Unauthorized", 403
    
    app = Application.query.get_or_404(app_id)
    action = request.form.get('action') # 'approve' or 'reject'
    justification = request.form.get('justification')
    
    # Auto-approval rule for students: GPA > 3.0
    if app.type == 'student' and app.gpa_at_application and app.gpa_at_application > 3.0:
        if action == 'reject' and not justification:
            flash('Justification required to override auto-approval rule (GPA > 3.0)', 'danger')
            return redirect(url_for('registrar.applications'))

    if action == 'approve':
        app.status = 'accepted'
        temp_pass = generate_random_password()
        new_user = User(
            name=app.applicant_name,
            email=app.applicant_email,
            role=app.type,
            is_first_login=True
        )
        new_user.set_password(temp_pass)
        db.session.add(new_user)
        flash(f'Application approved! Temporary password for {app.applicant_email}: {temp_pass}', 'success')
    else:
        app.status = 'rejected'
        app.justification = justification
        flash(f'Application for {app.applicant_email} rejected.', 'info')
    
    db.session.commit()
    return redirect(url_for('registrar.applications'))

@registrar_bp.route('/semesters', methods=['GET', 'POST'])
@login_required
def semesters():
    if current_user.role != 'registrar':
        return "Unauthorized", 403
    
    if request.method == 'POST':
        name = request.form.get('name')
        new_sem = Semester(name=name, current_period=1)
        db.session.add(new_sem)
        db.session.commit()
        flash('New semester created!', 'success')
        return redirect(url_for('registrar.semesters'))

    semesters = Semester.query.all()
    return render_template('registrar/semesters.html', semesters=semesters)

@registrar_bp.route('/semesters/<int:sem_id>/next_period', methods=['POST'])
@login_required
def next_period(sem_id):
    if current_user.role != 'registrar':
        return "Unauthorized", 403
    
    sem = Semester.query.get_or_404(sem_id)
    if sem.current_period < 4:
        sem.current_period += 1
        
        # Period 3 rules (Class Running)
        if sem.current_period == 3:
            process_period_3_transition(sem)
        
        # Period 4 rules (Grading)
        if sem.current_period == 4:
            # Registration is closed
            classes = Class.query.filter_by(semester_id=sem.id).all()
            for c in classes:
                if c.status == 'open':
                    c.status = 'closed'
        
        db.session.commit()
        flash(f'Moved to Period {sem.current_period} for {sem.name}', 'success')
    else:
        # End of Semester - process graduation, probation, etc.
        process_semester_end(sem)
        flash(f'Semester {sem.name} finalized.', 'success')
        
    return redirect(url_for('registrar.semesters'))

def process_period_3_transition(sem):
    # Courses with < 3 enrolled are cancelled
    classes = Class.query.filter_by(semester_id=sem.id).all()
    for c in classes:
        enrollment_count = Enrollment.query.filter_by(class_id=c.id, is_waitlisted=False).count()
        if enrollment_count < 3:
            c.status = 'cancelled'
            # Instructor of cancelled course gets warning
            instructor = User.query.get(c.instructor_id)
            if instructor:
                warn = Warning(user_id=instructor.id, reason=f"Course '{c.name}' cancelled due to low enrollment (<3 students).")
                instructor.warning_count += 1
                db.session.add(warn)
    
    # Students with < 2 registered courses receive warning
    students = User.query.filter_by(role='student', status='active').all()
    for s in students:
        active_enrollments = db.session.query(Enrollment).join(Class).filter(
            Enrollment.student_id == s.id,
            Class.semester_id == sem.id,
            Class.status != 'cancelled',
            Enrollment.is_waitlisted == False
        ).count()
        if active_enrollments < 2:
            warn = Warning(user_id=s.id, reason=f"Fewer than 2 courses registered for semester {sem.name}.")
            s.warning_count += 1
            db.session.add(warn)

def process_semester_end(sem):
    # This would involve GPA calculations and academic standing
    # For now, just a placeholder.
    pass

@registrar_bp.route('/complaints', methods=['GET', 'POST'])
@login_required
def complaints():
    if current_user.role != 'registrar':
        return "Unauthorized", 403
    
    from models import Complaint
    if request.method == 'POST':
        comp_id = request.form.get('comp_id')
        action = request.form.get('action') # 'punish' or 'warn_filer'
        resolution = request.form.get('resolution')
        
        comp = Complaint.query.get_or_404(comp_id)
        comp.status = 'resolved'
        comp.resolution = resolution
        
        if action == 'punish':
            target = User.query.get(comp.target_id)
            if target:
                target.add_warning(f"Warning issued based on complaint #{comp.id}: {resolution}")
                flash(f"Warning issued to user #{target.id}", "success")
        elif action == 'warn_filer':
            filer = User.query.get(comp.filer_id)
            if filer:
                filer.add_warning(f"Warning for false/unjustified complaint #{comp.id}: {resolution}")
                flash(f"Warning issued to filer user #{filer.id}", "warning")
        
        db.session.commit()
        return redirect(url_for('registrar.complaints'))

    complaints = Complaint.query.all()
    return render_template('registrar/complaints.html', complaints=complaints)

@registrar_bp.route('/classes', methods=['GET', 'POST'])
@login_required
def classes():
    if current_user.role != 'registrar':
        return "Unauthorized", 403
    
    if request.method == 'POST':
        name = request.form.get('name')
        schedule = request.form.get('schedule')
        instructor_id = request.form.get('instructor_id')
        size_limit = request.form.get('size_limit')
        semester_id = request.form.get('semester_id')
        
        new_class = Class(
            name=name,
            schedule=schedule,
            instructor_id=instructor_id,
            size_limit=int(size_limit),
            semester_id=semester_id,
            status='open' # Open for registration in Period 1/2
        )
        db.session.add(new_class)
        db.session.commit()
        flash('Class created successfully!', 'success')
        return redirect(url_for('registrar.classes'))

    classes = Class.query.all()
    instructors = User.query.filter_by(role='instructor').all()
    semesters = Semester.query.all()
    return render_template('registrar/classes.html', classes=classes, instructors=instructors, semesters=semesters)
