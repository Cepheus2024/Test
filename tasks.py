from celery import Celery
from flask import render_template
from flask_mail import Message
from datetime import datetime, timedelta
import logging
import os

# Configure Celery
def make_celery(app):
    celery = Celery(
        app.import_name,
        backend=app.config['CELERY_RESULT_BACKEND'],
        broker=app.config['CELERY_BROKER_URL']
    )
    celery.conf.update(app.config)

    class ContextTask(celery.Task):
        def __call__(self, *args, **kwargs):
            with app.app_context():
                return self.run(*args, **kwargs)

    celery.Task = ContextTask
    return celery

# Create a function to access resources to avoid circular imports
def get_app_resources():
    from app import create_app, db, mail
    app = create_app()
    return app, db, mail

# Create Celery instance
celery = Celery(__name__)

# Load celery configuration from config_file
@celery.on_after_configure.connect
def setup_celery_tasks(sender, **kwargs):
    from app import create_app
    app = create_app()
    celery.conf.update(app.config)

# Load required models inside tasks to avoid circular imports
@celery.task
def send_daily_reminders():
    """Send daily reminders to users who haven't visited recently or have new quizzes"""
    app, db, mail = get_app_resources()
    from models import User, Quiz
    
    with app.app_context():
        logging.info("Starting daily reminder task")
        
        # Get today's date
        today = datetime.now().date()
        
        # Get users who haven't logged in for 3 days
        inactive_users = User.query.filter(
            User.is_admin == False,
            (User.last_login < (datetime.now() - timedelta(days=3))) | (User.last_login.is_(None))
        ).all()
        
        # Find quizzes created in the last 24 hours
        new_quizzes = Quiz.query.filter(
            Quiz.created_at > (datetime.now() - timedelta(days=1))
        ).all()
        
        if not inactive_users and not new_quizzes:
            logging.info("No reminders to send")
            return "No reminders to send"
        
        # Send emails to inactive users
        for user in inactive_users:
            msg = Message(
                "Quiz Master: We miss you!",
                recipients=[user.email]
            )
            
            msg.html = render_template(
                'emails/daily_reminder.html',
                user=user,
                new_quizzes=new_quizzes,
                reason="inactivity"
            )
            
            mail.send(msg)
            logging.info(f"Sent inactivity reminder to {user.email}")
        
        # If there are new quizzes, notify all users
        if new_quizzes:
            active_users = User.query.filter(
                User.is_admin == False,
                (User.last_login >= (datetime.now() - timedelta(days=3))) | (User.last_login.is_(None))
            ).all()
            
            for user in active_users:
                msg = Message(
                    "Quiz Master: New quizzes available!",
                    recipients=[user.email]
                )
                
                msg.html = render_template(
                    'emails/daily_reminder.html',
                    user=user,
                    new_quizzes=new_quizzes,
                    reason="new_quizzes"
                )
                
                mail.send(msg)
                logging.info(f"Sent new quiz reminder to {user.email}")
        
        return f"Sent reminders to {len(inactive_users)} inactive users and {len(active_users) if 'active_users' in locals() else 0} active users about {len(new_quizzes)} new quizzes"

@celery.task
def send_monthly_reports():
    """Send monthly activity reports to all users at the beginning of each month"""
    app, db, mail = get_app_resources()
    from models import User
    from utils import generate_monthly_report, render_monthly_report_html, generate_monthly_report_pdf
    
    with app.app_context():
        logging.info("Starting monthly report generation")
        
        # Get all non-admin users
        users = User.query.filter_by(is_admin=False).all()
        
        # Calculate the previous month
        today = datetime.now()
        if today.month == 1:
            prev_month = 12
            year = today.year - 1
        else:
            prev_month = today.month - 1
            year = today.year
        
        month_str = f"{year}-{prev_month:02d}"
        month_name = datetime(year, prev_month, 1).strftime('%B %Y')
        
        sent_count = 0
        for user in users:
            # Generate report data
            report_data = generate_monthly_report(user.id, month_str)
            
            # Skip users with no activity in the month
            if report_data['total_attempts'] == 0:
                continue
            
            # Create email
            msg = Message(
                f"Quiz Master: Your Monthly Report for {month_name}",
                recipients=[user.email]
            )
            
            # Render HTML for email body
            msg.html = render_monthly_report_html(report_data)
            
            # Generate PDF version and attach to email
            try:
                pdf_report = generate_monthly_report_pdf(report_data)
                msg.attach(
                    f"monthly_report_{month_str}.pdf",
                    "application/pdf",
                    pdf_report
                )
                logging.info(f"PDF report generated for user {user.id}")
            except Exception as e:
                logging.error(f"Failed to generate PDF report: {str(e)}")
            
            # Send email
            mail.send(msg)
            sent_count += 1
            logging.info(f"Sent monthly report to {user.email}")
        
        return f"Sent monthly reports to {sent_count} users"

@celery.task
def send_csv_export_email(user_id, export_type):
    """Generate and send CSV export to user via email"""
    app, db, mail = get_app_resources()
    from models import User
    from utils import generate_users_csv, generate_quizzes_csv, generate_user_history_csv
    
    with app.app_context():
        logging.info(f"Starting CSV export: {export_type} for user {user_id}")
        
        # Get user
        user = User.query.get(user_id)
        if not user:
            logging.error(f"User {user_id} not found")
            return f"User {user_id} not found"
        
        # Generate CSV based on type
        if export_type == 'users' and user.is_admin:
            csv_data = generate_users_csv()
            filename = "users_export.csv"
            subject = "Quiz Master: Users Export"
        elif export_type == 'quizzes' and user.is_admin:
            csv_data = generate_quizzes_csv()
            filename = "quizzes_export.csv"
            subject = "Quiz Master: Quizzes Export"
        elif export_type == 'history':
            csv_data = generate_user_history_csv(user_id)
            filename = "quiz_history_export.csv"
            subject = "Quiz Master: Your Quiz History Export"
        else:
            logging.error(f"Invalid export type: {export_type}")
            return f"Invalid export type: {export_type}"
        
        # Create email
        msg = Message(
            subject,
            recipients=[user.email]
        )
        
        msg.body = f"Please find your requested {export_type} export attached."
        
        # Attach CSV
        msg.attach(filename, "text/csv", csv_data)
        
        # Send email
        mail.send(msg)
        logging.info(f"Sent {export_type} export to {user.email}")
        
        return f"Sent {export_type} export to {user.email}"
