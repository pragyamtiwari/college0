import os
from flask import Flask, render_template, redirect, url_for, request, jsonify
from flask_login import LoginManager, current_user
from models import db, User
from dotenv import load_dotenv
from ai.chatbot import get_chatbot_response

load_dotenv()

app = Flask(__name__)
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'dev-key-for-college0')
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///college0.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db.init_app(app)

login_manager = LoginManager()
login_manager.login_view = 'auth.login'
login_manager.init_app(app)

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

@app.route('/chat', methods=['POST'])
def chat():
    data = request.json
    user_input = data.get('message')
    user_role = current_user.role if current_user.is_authenticated else 'visitor'
    
    answer, is_llm = get_chatbot_response(user_input, user_role)
    return jsonify({
        'answer': answer,
        'is_llm': is_llm
    })

# Create database tables
with app.app_context():
    db.create_all()

# Register Blueprints
from routes.auth import auth_bp
from routes.visitor import visitor_bp
from routes.student import student_bp
from routes.instructor import instructor_bp
from routes.registrar import registrar_bp

app.register_blueprint(auth_bp)
app.register_blueprint(visitor_bp)
app.register_blueprint(student_bp)
app.register_blueprint(instructor_bp)
app.register_blueprint(registrar_bp)

if __name__ == '__main__':
    app.run(debug=True)
