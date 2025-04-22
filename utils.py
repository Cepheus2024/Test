from functools import wraps
from flask import abort, render_template
from flask_login import current_user
from app import db
from models import Score, User
import io
import csv
from datetime import datetime, timedelta

def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_admin:
            abort(403)
        return f(*args, **kwargs)
    return decorated_function

def calculate_ranking(quiz_id, current_score):
    """Calculate user's ranking in a quiz based on score"""
    # Get all scores for this quiz
    scores = Score.query.filter_by(quiz_id=quiz_id).order_by(Score.total_scored.desc()).all()
    
    # Create ranking list
    ranking = []
    for i, score in enumerate(scores, 1):
        user = User.query.get(score.user_id)
        ranking.append({
            'rank': i,
            'user_id': user.id,
            'username': user.username,
            'score': score.total_scored,
            'current_user': score.total_scored == current_score
        })
    
    return ranking

def generate_users_csv():
    """Generate CSV file with user data"""
    output = io.StringIO()
    writer = csv.writer(output)
    
    # Write header
    writer.writerow(['ID', 'Username', 'Email', 'Full Name', 'Qualification', 'DOB', 'Quizzes Taken', 'Average Score'])
    
    # Query all users with their statistics
    users = db.session.query(
        User,
        db.func.count(Score.id).label('quiz_count'),
        db.func.avg(Score.total_scored).label('avg_score')
    ).outerjoin(
        Score, User.id == Score.user_id
    ).filter(
        User.is_admin == False
    ).group_by(
        User.id
    ).all()
    
    # Write data
    for user, quiz_count, avg_score in users:
        writer.writerow([
            user.id,
            user.username,
            user.email,
            user.fullname,
            user.qualification,
            user.dob.strftime('%Y-%m-%d') if user.dob else 'N/A',
            quiz_count,
            f"{avg_score:.2f}" if avg_score else '0.00'
        ])
    
    return output.getvalue()

def generate_quizzes_csv():
    """Generate CSV file with quiz data"""
    output = io.StringIO()
    writer = csv.writer(output)
    
    # Write header
    writer.writerow(['Quiz ID', 'Title', 'Subject', 'Chapter', 'Date', 'Duration (min)', 
                    'Attempts', 'Average Score'])
    
    # Query all quizzes with their statistics
    quiz_data = db.session.query(
        'quiz.id', 'quiz.title', 'subject.name', 'chapter.name', 'quiz.date_of_quiz', 
        'quiz.time_duration', 'attempt_count', 'avg_score'
    ).from_statement(
        db.text('''
        SELECT 
            q.id as quiz_id, 
            q.title, 
            s.name as subject_name, 
            c.name as chapter_name,
            q.date_of_quiz,
            q.time_duration,
            COUNT(sc.id) as attempt_count,
            AVG(sc.total_scored) as avg_score
        FROM quizzes q
        JOIN chapters c ON q.chapter_id = c.id
        JOIN subjects s ON c.subject_id = s.id
        LEFT JOIN scores sc ON q.id = sc.quiz_id
        GROUP BY q.id
        ORDER BY q.date_of_quiz DESC
        ''')
    ).all()
    
    # Write data
    for quiz_id, title, subject, chapter, date, duration, attempts, avg_score in quiz_data:
        writer.writerow([
            quiz_id,
            title,
            subject,
            chapter,
            date.strftime('%Y-%m-%d') if date else 'N/A',
            duration,
            attempts,
            f"{avg_score:.2f}" if avg_score else '0.00'
        ])
    
    return output.getvalue()

def generate_user_history_csv(user_id):
    """Generate CSV file with a user's quiz history"""
    output = io.StringIO()
    writer = csv.writer(output)
    
    # Write header
    writer.writerow(['Quiz ID', 'Quiz Title', 'Subject', 'Chapter', 'Date Attempted', 
                    'Total Questions', 'Correct Answers', 'Score', 'Time Taken (seconds)'])
    
    # Query user's quiz attempts
    history_data = db.session.query(
        Score.quiz_id,
        Quiz.title,
        Subject.name,
        Chapter.name,
        Score.time_stamp_of_attempt,
        Score.total_questions,
        Score.correct_answers,
        Score.total_scored,
        Score.time_taken
    ).join(
        Quiz, Score.quiz_id == Quiz.id
    ).join(
        Chapter, Quiz.chapter_id == Chapter.id
    ).join(
        Subject, Chapter.subject_id == Subject.id
    ).filter(
        Score.user_id == user_id
    ).order_by(
        Score.time_stamp_of_attempt.desc()
    ).all()
    
    # Import models in function to avoid circular import
    from models import Quiz, Chapter, Subject
    
    # Write data
    for quiz_id, title, subject, chapter, date, total_q, correct, score, time in history_data:
        writer.writerow([
            quiz_id,
            title,
            subject,
            chapter,
            date.strftime('%Y-%m-%d %H:%M:%S'),
            total_q,
            correct,
            score,
            time
        ])
    
    return output.getvalue()

def generate_monthly_report(user_id, month=None):
    """Generate monthly report data for a user"""
    # If month not specified, use previous month
    if month is None:
        today = datetime.now()
        if today.month == 1:
            month = 12
            year = today.year - 1
        else:
            month = today.month - 1
            year = today.year
    else:
        # Parse month string "YYYY-MM"
        year, month = map(int, month.split('-'))
    
    # Start and end dates for the month
    start_date = datetime(year, month, 1)
    if month == 12:
        end_date = datetime(year + 1, 1, 1) - timedelta(days=1)
    else:
        end_date = datetime(year, month + 1, 1) - timedelta(days=1)
    
    # Import models in function to avoid circular import
    from models import Score, Quiz, Chapter, Subject, User
    
    # Get user info
    user = User.query.get(user_id)
    
    # Get all quiz attempts for the month
    attempts = db.session.query(
        Score, Quiz, Chapter, Subject
    ).join(
        Quiz, Score.quiz_id == Quiz.id
    ).join(
        Chapter, Quiz.chapter_id == Chapter.id
    ).join(
        Subject, Chapter.subject_id == Subject.id
    ).filter(
        Score.user_id == user_id,
        Score.time_stamp_of_attempt >= start_date,
        Score.time_stamp_of_attempt <= end_date
    ).all()
    
    # Calculate statistics
    total_attempts = len(attempts)
    total_score = sum(score.total_scored for score, _, _, _ in attempts)
    avg_score = total_score / total_attempts if total_attempts > 0 else 0
    
    # Group by subject
    subject_performance = {}
    for score, quiz, chapter, subject in attempts:
        if subject.id not in subject_performance:
            subject_performance[subject.id] = {
                'name': subject.name,
                'attempts': 0,
                'total_score': 0
            }
        
        subject_performance[subject.id]['attempts'] += 1
        subject_performance[subject.id]['total_score'] += score.total_scored
    
    # Calculate averages for each subject
    for subject_id in subject_performance:
        attempts = subject_performance[subject_id]['attempts']
        total = subject_performance[subject_id]['total_score']
        subject_performance[subject_id]['avg_score'] = total / attempts
    
    # Get user's overall ranking
    ranking_query = db.session.query(
        User.id,
        User.username,
        db.func.avg(Score.total_scored).label('avg_score')
    ).join(
        Score, User.id == Score.user_id
    ).filter(
        Score.time_stamp_of_attempt >= start_date,
        Score.time_stamp_of_attempt <= end_date
    ).group_by(
        User.id
    ).order_by(
        db.desc('avg_score')
    ).all()
    
    # Find user's rank
    user_rank = None
    for i, (u_id, _, _) in enumerate(ranking_query, 1):
        if u_id == user_id:
            user_rank = i
            break
    
    report_data = {
        'user': user,
        'month': f"{year}-{month:02d}",
        'month_name': start_date.strftime('%B %Y'),
        'total_attempts': total_attempts,
        'avg_score': avg_score,
        'attempts': attempts,
        'subject_performance': subject_performance,
        'user_rank': user_rank,
        'total_users': len(ranking_query)
    }
    
    return report_data

def render_monthly_report_html(report_data):
    """Render monthly report as HTML"""
    return render_template('emails/monthly_report.html', **report_data)

def generate_monthly_report_pdf(report_data):
    """Generate monthly report as PDF"""
    from weasyprint import HTML
    import tempfile
    
    # Generate HTML content
    html_content = render_template('emails/monthly_report.html', **report_data)
    
    # Create a temporary file to store the HTML
    with tempfile.NamedTemporaryFile(suffix='.html', delete=False) as temp:
        temp.write(html_content.encode('utf-8'))
        temp_filename = temp.name
    
    # Generate PDF from HTML
    pdf = HTML(filename=temp_filename).write_pdf()
    
    # Clean up the temporary file
    import os
    os.unlink(temp_filename)
    
    return pdf
