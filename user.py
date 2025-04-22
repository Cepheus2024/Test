from flask import Blueprint, render_template, redirect, url_for, flash, request, jsonify, abort
from flask_login import login_required, current_user
from datetime import datetime, timedelta
from app import db, cache
from models import User, Subject, Chapter, Quiz, Question, Score, UserQuizDetail
from utils import calculate_ranking
from tasks import send_csv_export_email
import json

user = Blueprint('user', __name__)

@user.before_request
@login_required
def check_user():
    if current_user.is_admin:
        return redirect(url_for('admin.dashboard'))

@user.route('/dashboard')
@login_required
def dashboard():
    # Get available subjects
    subjects = Subject.query.all()
    
    # Get user's recent quiz attempts
    recent_attempts = db.session.query(
        Score, Quiz, Chapter, Subject
    ).join(
        Quiz, Score.quiz_id == Quiz.id
    ).join(
        Chapter, Quiz.chapter_id == Chapter.id
    ).join(
        Subject, Chapter.subject_id == Subject.id
    ).filter(
        Score.user_id == current_user.id
    ).order_by(
        Score.time_stamp_of_attempt.desc()
    ).limit(5).all()
    
    # Get user's overall statistics
    total_attempts = Score.query.filter_by(user_id=current_user.id).count()
    avg_score = db.session.query(
        db.func.avg(Score.total_scored)
    ).filter(
        Score.user_id == current_user.id
    ).scalar() or 0
    
    # Get upcoming quizzes
    today = datetime.now().date()
    upcoming_quizzes = db.session.query(
        Quiz, Chapter, Subject
    ).join(
        Chapter, Quiz.chapter_id == Chapter.id
    ).join(
        Subject, Chapter.subject_id == Subject.id
    ).filter(
        Quiz.date_of_quiz >= today
    ).order_by(
        Quiz.date_of_quiz
    ).limit(5).all()
    
    return render_template(
        'user/user_dashboard.html',  # Updated template name
        subjects=subjects,
        recent_attempts=recent_attempts,
        total_attempts=total_attempts,
        avg_score=avg_score,
        upcoming_quizzes=upcoming_quizzes
    )

@user.route('/subjects')
@login_required
def subjects():
    all_subjects = Subject.query.all()
    return render_template('user/subject_view.html', subjects=all_subjects)  # Updated template name

@user.route('/chapters/<int:subject_id>')
@login_required
def chapters(subject_id):
    subject = Subject.query.get_or_404(subject_id)
    return render_template('user/chapter_view.html', subject=subject, chapters=subject.chapters)  # Updated template name

@user.route('/quizzes/<int:chapter_id>')
@login_required
def quizzes(chapter_id):
    chapter = Chapter.query.get_or_404(chapter_id)
    today = datetime.now().date()
    
    # Get available quizzes (those with quiz date today or in the future)
    available_quizzes = Quiz.query.filter(
        Quiz.chapter_id == chapter_id,
        Quiz.date_of_quiz >= today
    ).all()
    
    # Get past quizzes
    past_quizzes = Quiz.query.filter(
        Quiz.chapter_id == chapter_id,
        Quiz.date_of_quiz < today
    ).all()
    
    # Get user's attempts for this chapter's quizzes
    user_attempts = {}
    for quiz in available_quizzes + past_quizzes:
        attempt = Score.query.filter_by(
            user_id=current_user.id,
            quiz_id=quiz.id
        ).first()
        
        if attempt:
            user_attempts[quiz.id] = attempt
    
    return render_template(
        'user/quiz_view.html',  # Updated template name
        chapter=chapter,
        available_quizzes=available_quizzes,
        past_quizzes=past_quizzes,
        user_attempts=user_attempts
    )

@user.route('/quiz/<int:quiz_id>/info')
@login_required
def quiz_info(quiz_id):
    quiz = Quiz.query.get_or_404(quiz_id)
    chapter = Chapter.query.get(quiz.chapter_id)
    subject = Subject.query.get(chapter.subject_id)
    
    # Check if user has already attempted this quiz
    previous_attempt = Score.query.filter_by(
        user_id=current_user.id,
        quiz_id=quiz_id
    ).first()
    
    # Get quiz statistics
    total_questions = Question.query.filter_by(quiz_id=quiz_id).count()
    total_marks = db.session.query(db.func.sum(Question.marks)).filter_by(quiz_id=quiz_id).scalar() or 0
    
    return render_template(
        'user/quiz_info.html',  # Updated template name
        quiz=quiz,
        chapter=chapter,
        subject=subject,
        total_questions=total_questions,
        total_marks=total_marks,
        previous_attempt=previous_attempt
    )

@user.route('/quiz/<int:quiz_id>/attempt')
@login_required
def attempt_quiz(quiz_id):
    quiz = Quiz.query.get_or_404(quiz_id)
    
    # Check if quiz is available today
    today = datetime.now().date()
    if quiz.date_of_quiz > today:
        flash('This quiz is not yet available.', 'warning')
        return redirect(url_for('user.quiz_info', quiz_id=quiz_id))
    
    # Check if user has already attempted this quiz
    previous_attempt = Score.query.filter_by(
        user_id=current_user.id,
        quiz_id=quiz_id
    ).first()
    
    if previous_attempt:
        flash('You have already attempted this quiz.', 'info')
        return redirect(url_for('user.result', score_id=previous_attempt.id))
    
    # Get all questions for this quiz
    questions = Question.query.filter_by(quiz_id=quiz_id).all()
    
    if not questions:
        flash('This quiz has no questions yet.', 'warning')
        return redirect(url_for('user.quiz_info', quiz_id=quiz_id))
    
    return render_template(
        'user/attempt_quiz.html',  # Updated template name
        quiz=quiz,
        questions=questions,
        duration_minutes=quiz.time_duration
    )

@user.route('/quiz/submit', methods=['POST'])
@login_required
def submit_quiz():
    quiz_id = request.form.get('quiz_id')
    time_taken = request.form.get('time_taken')  # In seconds
    
    if not quiz_id or not time_taken:
        flash('Invalid submission.', 'danger')
        return redirect(url_for('user.dashboard'))
    
    quiz = Quiz.query.get_or_404(quiz_id)
    questions = Question.query.filter_by(quiz_id=quiz_id).all()
    
    # Check if user has already attempted this quiz
    previous_attempt = Score.query.filter_by(
        user_id=current_user.id,
        quiz_id=quiz_id
    ).first()
    
    if previous_attempt:
        flash('You have already attempted this quiz.', 'info')
        return redirect(url_for('user.result', score_id=previous_attempt.id))
    
    # Calculate score
    total_questions = len(questions)
    correct_answers = 0
    total_scored = 0
    
    # Create a new score record
    score = Score(
        user_id=current_user.id,
        quiz_id=quiz_id,
        total_questions=total_questions,
        correct_answers=0,  # Will update later
        total_scored=0,  # Will update later
        time_taken=int(time_taken)
    )
    
    db.session.add(score)
    db.session.flush()  # Generate ID for score
    
    # Process each question
    for question in questions:
        selected_option = request.form.get(f'question_{question.id}')
        
        # Convert to int if not None
        selected_option_int = int(selected_option) if selected_option else None
        
        # Check if answer is correct
        is_correct = selected_option_int == question.correct_option
        
        if is_correct:
            correct_answers += 1
            total_scored += question.marks
        
        # Save user's answer
        detail = UserQuizDetail(
            score_id=score.id,
            question_id=question.id,
            selected_option=selected_option_int,
            is_correct=is_correct
        )
        
        db.session.add(detail)
    
    # Update score with calculated values
    score.correct_answers = correct_answers
    score.total_scored = total_scored
    
    db.session.commit()
    
    flash('Quiz submitted successfully!', 'success')
    return redirect(url_for('user.result', score_id=score.id))

@user.route('/result/<int:score_id>')
@login_required
def result(score_id):
    score = Score.query.get_or_404(score_id)
    
    # Check if the score belongs to the current user
    if score.user_id != current_user.id:
        abort(403)
    
    quiz = Quiz.query.get(score.quiz_id)
    chapter = Chapter.query.get(quiz.chapter_id)
    subject = Subject.query.get(chapter.subject_id)
    
    # Get question details with user's answers
    question_details = db.session.query(
        Question, UserQuizDetail
    ).join(
        UserQuizDetail, Question.id == UserQuizDetail.question_id
    ).filter(
        UserQuizDetail.score_id == score_id
    ).all()
    
    # Calculate percentage
    percentage = (score.total_scored / (sum(q.marks for q, _ in question_details))) * 100 if question_details else 0
    
    # Calculate ranking
    ranking = calculate_ranking(score.quiz_id, score.total_scored)
    
    return render_template(
        'user/result_view.html',  # Updated template name
        score=score,
        quiz=quiz,
        chapter=chapter,
        subject=subject,
        question_details=question_details,
        percentage=percentage,
        ranking=ranking
    )

@user.route('/history')
@login_required
def history():
    # Get user's all quiz attempts
    attempts = db.session.query(
        Score, Quiz, Chapter, Subject
    ).join(
        Quiz, Score.quiz_id == Quiz.id
    ).join(
        Chapter, Quiz.chapter_id == Chapter.id
    ).join(
        Subject, Chapter.subject_id == Subject.id
    ).filter(
        Score.user_id == current_user.id
    ).order_by(
        Score.time_stamp_of_attempt.desc()
    ).all()
    
    # Group attempts by subject
    attempts_by_subject = {}
    for score, quiz, chapter, subject in attempts:
        if subject.id not in attempts_by_subject:
            attempts_by_subject[subject.id] = {
                'subject': subject,
                'attempts': []
            }
        attempts_by_subject[subject.id]['attempts'].append((score, quiz, chapter))
    
    return render_template(
        'user/user_statistics.html',  # Updated template name
        attempts_by_subject=attempts_by_subject
    )

@user.route('/export/history-csv')
@login_required
def export_history_csv():
    send_csv_export_email.delay(current_user.id, 'history')
    flash('Export job started. You will receive an email with the CSV file shortly.', 'info')
    return redirect(url_for('user.history'))

@user.route('/api/performance-data')
@login_required
@cache.cached(timeout=300)
def performance_data():
    # Get user's performance over time
    performance_data = db.session.query(
        db.func.strftime('%Y-%m-%d', Score.time_stamp_of_attempt).label('date'),
        db.func.avg(Score.total_scored).label('avg_score')
    ).filter(
        Score.user_id == current_user.id
    ).group_by(
        'date'
    ).order_by(
        'date'
    ).all()
    
    # Get subject-wise performance
    subject_performance = db.session.query(
        Subject.name,
        db.func.avg(Score.total_scored).label('avg_score')
    ).join(
        Quiz, Score.quiz_id == Quiz.id
    ).join(
        Chapter, Quiz.chapter_id == Chapter.id
    ).join(
        Subject, Chapter.subject_id == Subject.id
    ).filter(
        Score.user_id == current_user.id
    ).group_by(
        Subject.id
    ).all()
    
    result = {
        'performance_over_time': {
            'labels': [p.date for p in performance_data],
            'data': [float(p.avg_score) for p in performance_data]
        },
        'subject_performance': {
            'labels': [s.name for s in subject_performance],
            'data': [float(s.avg_score) for s in subject_performance]
        }
    }
    
    return jsonify(result)
