from app import app
from models import db, User, Semester, TabooWord, Class, Review, Enrollment

def seed():
    with app.app_context():
        # Clean start
        db.drop_all()
        db.create_all()

        # Create Registrar
        registrar = User(
            name="Admin Registrar",
            email="registrar@college0.edu",
            role="registrar",
            is_first_login=False
        )
        registrar.set_password("admin123")
        db.session.add(registrar)

        # Create Instructors
        inst1 = User(name="Prof. X", email="profx@college0.edu", role="instructor", is_first_login=False)
        inst1.set_password("pass123")
        inst2 = User(name="Dr. Strange", email="strange@college0.edu", role="instructor", is_first_login=False)
        inst2.set_password("pass123")
        db.session.add_all([inst1, inst2])
        db.session.commit()

        # Create Students
        for i in range(1, 6):
            stu = User(name=f"Student {i}", email=f"student{i}@college0.edu", role="student", is_first_login=False)
            stu.set_password("pass123")
            db.session.add(stu)
        db.session.commit()

        # Create Semesters
        sem1 = Semester(name="Fall 2025", current_period=2) # Registration open
        sem2 = Semester(name="Spring 2026", current_period=1)
        db.session.add_all([sem1, sem2])
        db.session.commit()

        # Create Classes for sem1
        c1 = Class(name="Intro to AI", schedule="M/W 10am", instructor_id=inst1.id, semester_id=sem1.id, status="open")
        c2 = Class(name="Data Structures", schedule="T/Th 2pm", instructor_id=inst2.id, semester_id=sem1.id, status="open")
        c3 = Class(name="Ethical Hacking", schedule="Fri 9am", instructor_id=inst1.id, semester_id=sem1.id, status="open")
        db.session.add_all([c1, c2, c3])
        db.session.commit()

        # Create some taboo words
        taboos = ["badword1", "badword2", "spam"]
        for word in taboos:
            db.session.add(TabooWord(word=word))

        db.session.commit()
        print("Database seeded successfully!")

if __name__ == "__main__":
    seed()
