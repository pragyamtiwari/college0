from flask import Blueprint, render_template, request, flash, redirect, url_for
from models import db, Class, User, Review, Enrollment, Application
from sqlalchemy import func

visitor_bp = Blueprint('visitor', __name__)

@visitor_bp.route('/')
def home():
    # Highest rated classes (avg stars)
    highest_rated = db.session.query(Class, func.avg(Review.stars).label('avg_rating'))\
        .join(Review, Class.id == Review.class_id)\
        .group_by(Class.id).order_by(func.avg(Review.stars).desc()).limit(5).all()

    # Lowest rated classes
    lowest_rated = db.session.query(Class, func.avg(Review.stars).label('avg_rating'))\
        .join(Review, Class.id == Review.class_id)\
        .group_by(Class.id).order_by(func.avg(Review.stars).asc()).limit(5).all()

    # Students with highest GPA
    # Simplistic GPA calculation for now: 4.0 for A, 3.0 for B, 2.0 for C, 1.0 for D, 0.0 for F
    grade_map = {'A': 4.0, 'B': 3.0, 'C': 2.0, 'D': 1.0, 'F': 0.0}
    # This is complex in pure SQL without a custom function, let's do it in Python for the demo
    # Or just show a placeholder if no grades yet.
    
    return render_template('visitor/home.html', 
                           highest_rated=highest_rated, 
                           lowest_rated=lowest_rated)

@visitor_bp.route('/apply', methods=['GET', 'POST'])
def apply():
    if request.method == 'POST':
        name = request.form.get('name')
        email = request.form.get('email')
        app_type = request.form.get('type') # 'student' or 'instructor'
        gpa = request.form.get('gpa')
        
        new_app = Application(
            applicant_name=name,
            applicant_email=email,
            type=app_type,
            gpa_at_application=float(gpa) if gpa else None
        )
        db.session.add(new_app)
        db.session.commit()
        flash('Application submitted successfully!', 'success')
        return redirect(url_for('visitor.home'))
    return render_template('visitor/apply.html')
