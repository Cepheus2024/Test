import os
import logging
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from flask_mail import Mail
from flask_jwt_extended import JWTManager
from sqlalchemy.orm import DeclarativeBase
from werkzeug.middleware.proxy_fix import ProxyFix
from flask_cors import CORS
from flask_caching import Cache

# Configure logging
logging.basicConfig(level=logging.DEBUG)

# Create base model class
class Base(DeclarativeBase):
    pass

# Initialize extensions
db = SQLAlchemy(model_class=Base)
login_manager = LoginManager()
mail = Mail()
jwt = JWTManager()
cache = Cache(config={'CACHE_TYPE': 'SimpleCache'})  # Use SimpleCache instead of RedisCache

def create_app(config_file='config.py'):
    # Create the Flask app
    app = Flask(__name__)
    
    # Load configuration
    app.config.from_pyfile(config_file)
    
    # Set up secret key
    app.secret_key = os.environ.get("SESSION_SECRET", app.config.get('SECRET_KEY'))
    
    # Configure proxy fix for proper URL generation with https
    app.wsgi_app = ProxyFix(app.wsgi_app, x_proto=1, x_host=1)
    
    # Initialize extensions with app
    db.init_app(app)
    login_manager.init_app(app)
    mail.init_app(app)
    jwt.init_app(app)
    cache.init_app(app)
    CORS(app)
    
    # Configure login
    login_manager.login_view = 'auth.login'
    login_manager.login_message_category = 'info'
    
    with app.app_context():
        # Import models
        from models import User, Subject, Chapter, Quiz, Question, Score
        
        # Create tables if they don't exist
        db.create_all()
        
        # Create admin user if it doesn't exist
        from werkzeug.security import generate_password_hash
        admin = User.query.filter_by(username=app.config['ADMIN_USERNAME']).first()
        if not admin:
            admin = User(
                username=app.config['ADMIN_USERNAME'],
                fullname='Quiz Master Admin',
                email=app.config['ADMIN_USERNAME'],
                is_admin=True,
                password_hash=generate_password_hash(app.config['ADMIN_PASSWORD'])
            )
            db.session.add(admin)
            db.session.commit()
            app.logger.info('Admin user created')
        
        # Register blueprints
        from auth import auth as auth_blueprint
        app.register_blueprint(auth_blueprint)
        
        from admin import admin as admin_blueprint
        app.register_blueprint(admin_blueprint, url_prefix='/admin')
        
        from user import user as user_blueprint
        app.register_blueprint(user_blueprint, url_prefix='/user')
        
        @app.route('/')
        def index():
            from flask import render_template
            return render_template('index.html')  # Ensure templates link to styles.css
            
        return app

# User loader for Flask-Login
@login_manager.user_loader
def load_user(user_id):
    from models import User
    return User.query.get(int(user_id))
