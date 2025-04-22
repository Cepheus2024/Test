from flask import Blueprint, render_template, redirect, url_for, flash, request, jsonify, current_app, abort, Response
from sqlalchemy import or_
from flask_login import login_required, current_user
from werkzeug.security import generate_password_hash
from datetime import datetime
from app import db, cache
from models import User, Subject, Chapter, Quiz, Question, Score
from utils import admin_required, generate_monthly_report
import csv
import io

admin = Blueprint('admin', __name__)

@admin.before_request
@login_required
def check_admin():
    if not current_user.is_admin:
        abort(403)  # Forbidden

@admin.route('/dashboard')
@login_required
@admin_required
def dashboard():
    # Get count statistics for the dashboard
    stats = {
        'subjects': Subject.query.count(),
        'chapters': Chapter.query.count(),
        'quizzes': Quiz.query.count(),
        'questions': Question.query.count(),
        'users': User.query.filter(User.is_admin == False).count(),
        'quiz_attempts': Score.query.count()
    }
    
    # Get recent quiz attempts
    recent_attempts = db.session.query(
        Score, User, Quiz
    ).join(
        User, Score.user_id == User.id
    ).join(
        Quiz, Score.quiz_id == Quiz.id
    ).order_by(
        Score.time_stamp_of_attempt.desc()
    ).limit(10).all()
    
    # Get top performing users
    top_users = db.session.query(
        User,
        db.func.avg(Score.total_scored).label('avg_score'),
        db.func.count(Score.id).label('quiz_count')
    ).join(
        Score, User.id == Score.user_id
    ).group_by(
        User.id
    ).order_by(
        db.desc('avg_score')
    ).limit(5).all()
    
    # Check if there are any quiz attempts for graph data
    graph_data = db.session.query(
        db.func.strftime('%Y-%m', Score.time_stamp_of_attempt).label('month'),
        db.func.count(Score.id).label('attempt_count')
    ).group_by(
        'month'
    ).order_by(
        'month'
    ).all()
    
    # Only pass graph_data if it contains data
    graph_data = graph_data if graph_data else None

    return render_template(
        'admin/admin_dashboard.html',  # Updated template name
        stats=stats,
        recent_attempts=recent_attempts,
        top_users=top_users,
        graph_data=graph_data
    )

# Subject Management
@admin.route('/subjects')
@login_required
@admin_required
def subjects():
    all_subjects = Subject.query.all()
    return render_template('admin/subject_manage.html', subjects=all_subjects)  # Updated template name

@admin.route('/subjects/add', methods=['POST'])
@login_required
@admin_required
def add_subject():
    name = request.form.get('name')
    description = request.form.get('description')
    
    if not name:
        flash('Subject name is required.', 'danger')
        return redirect(url_for('admin.subjects'))
    
    subject = Subject(name=name, description=description)
    db.session.add(subject)
    db.session.commit()
    
    flash('Subject added successfully!', 'success')
    return redirect(url_for('admin.subjects'))

@admin.route('/subjects/edit/<int:id>', methods=['POST'])
@login_required
@admin_required
def edit_subject(id):
    subject = Subject.query.get_or_404(id)
    
    subject.name = request.form.get('name')
    subject.description = request.form.get('description')
    
    db.session.commit()
    flash('Subject updated successfully!', 'success')
    return redirect(url_for('admin.subjects'))

@admin.route('/subjects/delete/<int:id>')
@login_required
@admin_required
def delete_subject(id):
    subject = Subject.query.get_or_404(id)
    db.session.delete(subject)
    db.session.commit()
    
    flash('Subject deleted successfully!', 'success')
    return redirect(url_for('admin.subjects'))

# Chapter Management
@admin.route('/chapters/<int:subject_id>')
@login_required
@admin_required
def chapters(subject_id):
    subject = Subject.query.get_or_404(subject_id)
    return render_template('admin/chapter_manage.html', subject=subject, chapters=subject.chapters)  # Updated template name

@admin.route('/chapters/add/<int:subject_id>', methods=['POST'])
@login_required
@admin_required
def add_chapter(subject_id):
    subject = Subject.query.get_or_404(subject_id)
    
    name = request.form.get('name')
    description = request.form.get('description')
    
    if not name:
        flash('Chapter name is required.', 'danger')
        return redirect(url_for('admin.chapters', subject_id=subject_id))
    
    chapter = Chapter(subject=subject, name=name, description=description)
    db.session.add(chapter)
    db.session.commit()
    
    flash('Chapter added successfully!', 'success')
    return redirect(url_for('admin.chapters', subject_id=subject_id))

@admin.route('/chapters/edit/<int:id>', methods=['POST'])
@login_required
@admin_required
def edit_chapter(id):
    chapter = Chapter.query.get_or_404(id)
    
    chapter.name = request.form.get('name')
    chapter.description = request.form.get('description')
    
    db.session.commit()
    flash('Chapter updated successfully!', 'success')
    return redirect(url_for('admin.chapters', subject_id=chapter.subject_id))

@admin.route('/chapters/delete/<int:id>')
@login_required
@admin_required
def delete_chapter(id):
    chapter = Chapter.query.get_or_404(id)
    subject_id = chapter.subject_id
    
    db.session.delete(chapter)
    db.session.commit()
    
    flash('Chapter deleted successfully!', 'success')
    return redirect(url_for('admin.chapters', subject_id=subject_id))

# Quiz Management
@admin.route('/quizzes/<int:chapter_id>')
@login_required
@admin_required
def quizzes(chapter_id):
    chapter = Chapter.query.get_or_404(chapter_id)
    return render_template('admin/quiz_manage.html', chapter=chapter, quizzes=chapter.quizzes)  # Updated template name

@admin.route('/quizzes/add/<int:chapter_id>', methods=['POST'])
@login_required
@admin_required
def add_quiz(chapter_id):
    chapter = Chapter.query.get_or_404(chapter_id)
    
    title = request.form.get('title')
    description = request.form.get('description')
    date_of_quiz = request.form.get('date_of_quiz')
    time_duration = request.form.get('time_duration')
    remarks = request.form.get('remarks')
    
    if not title or not date_of_quiz or not time_duration:
        flash('Title, date, and duration are required.', 'danger')
        return redirect(url_for('admin.quizzes', chapter_id=chapter_id))
    
    try:
        quiz_date = datetime.strptime(date_of_quiz, '%Y-%m-%d').date()
        duration_minutes = int(time_duration) if time_duration.isdigit() else None
        
        if duration_minutes is None:
            raise ValueError("Invalid duration format.")
    except ValueError as e:
        flash(f'Invalid input: {str(e)}', 'danger')
        return redirect(url_for('admin.quizzes', chapter_id=chapter_id))
    
    quiz = Quiz(
        chapter=chapter,
        title=title,
        description=description,
        date_of_quiz=quiz_date,
        time_duration=duration_minutes,
        remarks=remarks
    )
    
    db.session.add(quiz)
    db.session.commit()
    
    flash('Quiz added successfully!', 'success')
    return redirect(url_for('admin.edit_quiz', id=quiz.id))

@admin.route('/quizzes/edit/<int:id>', methods=['GET', 'POST'])
@login_required
@admin_required
def edit_quiz(id):
    quiz = Quiz.query.get_or_404(id)
    
    if request.method == 'POST':
        quiz.title = request.form.get('title')
        quiz.description = request.form.get('description')
        
        date_of_quiz = request.form.get('date_of_quiz')
        time_duration = request.form.get('time_duration')
        quiz.remarks = request.form.get('remarks')
        
        try:
            quiz.date_of_quiz = datetime.strptime(date_of_quiz, '%Y-%m-%d').date()
            quiz.time_duration = int(time_duration) if time_duration.isdigit() else None
            
            if quiz.time_duration is None:
                raise ValueError("Invalid duration format.")
        except ValueError as e:
            flash(f'Invalid input: {str(e)}', 'danger')
            return redirect(url_for('admin.edit_quiz', id=id))
        
        db.session.commit()
        flash('Quiz updated successfully!', 'success')
        return redirect(url_for('admin.edit_quiz', id=id))
    
    return render_template('admin/quiz_edit.html', quiz=quiz)  # Updated template name

@admin.route('/quizzes/delete/<int:id>')
@login_required
@admin_required
def delete_quiz(id):
    quiz = Quiz.query.get_or_404(id)
    chapter_id = quiz.chapter_id
    
    db.session.delete(quiz)
    db.session.commit()
    
    flash('Quiz deleted successfully!', 'success')
    return redirect(url_for('admin.quizzes', chapter_id=chapter_id))

# Question Management
@admin.route('/questions/add/<int:quiz_id>', methods=['POST'])
@login_required
@admin_required
def add_question(quiz_id):
    quiz = Quiz.query.get_or_404(quiz_id)
    
    question_statement = request.form.get('question_statement')
    option1 = request.form.get('option1')
    option2 = request.form.get('option2')
    option3 = request.form.get('option3')
    option4 = request.form.get('option4')
    correct_option = request.form.get('correct_option')
    marks = request.form.get('marks', 1)
    
    if not all([question_statement, option1, option2, option3, option4, correct_option]):
        flash('All fields are required.', 'danger')
        return redirect(url_for('admin.edit_quiz', id=quiz_id))
    
    try:
        correct_option_int = int(correct_option)
        marks_int = int(marks)
        
        if correct_option_int < 1 or correct_option_int > 4:
            raise ValueError("Correct option must be between 1 and 4")
        
        if marks_int < 1:
            raise ValueError("Marks must be at least 1")
    except ValueError as e:
        flash(f'Invalid input: {str(e)}', 'danger')
        return redirect(url_for('admin.edit_quiz', id=quiz_id))
    
    question = Question(
        quiz=quiz,
        question_statement=question_statement,
        option1=option1,
        option2=option2,
        option3=option3,
        option4=option4,
        correct_option=correct_option_int,
        marks=marks_int
    )
    
    db.session.add(question)
    db.session.commit()
    
    flash('Question added successfully!', 'success')
    return redirect(url_for('admin.edit_quiz', id=quiz_id))

@admin.route('/questions/edit/<int:id>', methods=['POST'])
@login_required
@admin_required
def edit_question(id):
    question = Question.query.get_or_404(id)
    
    question.question_statement = request.form.get('question_statement')
    question.option1 = request.form.get('option1')
    question.option2 = request.form.get('option2')
    question.option3 = request.form.get('option3')
    question.option4 = request.form.get('option4')
    
    correct_option = request.form.get('correct_option')
    marks = request.form.get('marks')
    
    try:
        question.correct_option = int(correct_option)
        question.marks = int(marks)
    except ValueError:
        flash('Invalid correct option or marks format.', 'danger')
        return redirect(url_for('admin.edit_quiz', id=question.quiz_id))
    
    db.session.commit()
    flash('Question updated successfully!', 'success')
    return redirect(url_for('admin.edit_quiz', id=question.quiz_id))

@admin.route('/questions/delete/<int:id>')
@login_required
@admin_required
def delete_question(id):
    question = Question.query.get_or_404(id)
    quiz_id = question.quiz_id
    
    db.session.delete(question)
    db.session.commit()
    
    flash('Question deleted successfully!', 'success')
    return redirect(url_for('admin.edit_quiz', id=quiz_id))

# User Management
@admin.route('/users')
@login_required
@admin_required
def users():
    all_users = User.query.filter(User.is_admin == False).all()
    return render_template('admin/user_manage.html', users=all_users)  # Updated template name

@admin.route('/users/delete/<int:id>')
@login_required
@admin_required
def delete_user(id):
    user = User.query.get_or_404(id)
    
    if user.is_admin:
        flash('Cannot delete admin user.', 'danger')
        return redirect(url_for('admin.users'))
    
    db.session.delete(user)
    db.session.commit()
    
    flash('User deleted successfully!', 'success')
    return redirect(url_for('admin.users'))

# Generate Reports
@admin.route('/export/users-csv')
@login_required
@admin_required
def export_users_csv():
    users = User.query.filter(User.is_admin == False).all()
    
    # Generate CSV content
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(['ID', 'Username', 'Full Name', 'Email', 'Date Joined', 'Last Login'])
    
    for user in users:
        writer.writerow([
            user.id,
            user.username,
            user.fullname,
            user.email,
            user.created_at.strftime('%Y-%m-%d'),
            user.last_login.strftime('%Y-%m-%d %H:%M') if user.last_login else 'Never'
        ])
    
    output.seek(0)
    
    # Return CSV as a response
    return Response(
        output,
        mimetype='text/csv',
        headers={"Content-Disposition": "attachment;filename=users.csv"}
    )

@admin.route('/export/quizzes-csv')
@login_required
@admin_required
def export_quizzes_csv():
    quizzes = Quiz.query.all()
    
    # Generate CSV content
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(['ID', 'Title', 'Chapter', 'Subject', 'Date', 'Duration (minutes)', 'Remarks'])
    
    for quiz in quizzes:
        writer.writerow([
            quiz.id,
            quiz.title,
            quiz.chapter.name,
            quiz.chapter.subject.name,
            quiz.date_of_quiz.strftime('%Y-%m-%d'),
            quiz.time_duration,
            quiz.remarks or 'N/A'
        ])
    
    output.seek(0)
    
    # Return CSV as a response
    return Response(
        output,
        mimetype='text/csv',
        headers={"Content-Disposition": "attachment;filename=quizzes.csv"}
    )

@admin.route('/search', methods=['GET', 'POST'])
@login_required
@admin_required
def search():
    # Get query from either POST or GET
    if request.method == 'POST':
        query = request.form.get('q', '')
    else:
        query = request.args.get('q', '')
    
    # Validate query length
    if not query or len(query.strip()) < 2:
        return jsonify({
            'success': False,
            'message': 'Search query must be at least 2 characters long',
            'results': {}
        })
    
    # Search results by category
    results = {
        'subjects': [],
        'chapters': [],
        'quizzes': [],
        'users': []
    }
    
    # Search subjects
    subjects = Subject.query.filter(
        or_(
            Subject.name.ilike(f'%{query}%'),
            Subject.description.ilike(f'%{query}%')
        )
    ).limit(10).all()
    
    for subject in subjects:
        results['subjects'].append({
            'id': subject.id,
            'name': subject.name,
            'description': subject.description,
            'chapter_count': subject.chapters.count(),
            'url': url_for('admin.chapters', subject_id=subject.id)
        })
    
    # Search chapters
    chapters = Chapter.query.filter(
        or_(
            Chapter.name.ilike(f'%{query}%'),
            Chapter.description.ilike(f'%{query}%')
        )
    ).limit(10).all()
    
    for chapter in chapters:
        results['chapters'].append({
            'id': chapter.id,
            'name': chapter.name,
            'description': chapter.description,
            'subject_name': chapter.subject.name,
            'subject_id': chapter.subject_id,
            'quiz_count': chapter.quizzes.count(),
            'url': url_for('admin.quizzes', chapter_id=chapter.id)
        })
    
    # Search quizzes
    quizzes = Quiz.query.filter(
        or_(
            Quiz.title.ilike(f'%{query}%'),
            Quiz.description.ilike(f'%{query}%'),
            Quiz.remarks.ilike(f'%{query}%')
        )
    ).limit(10).all()
    
    for quiz in quizzes:
        results['quizzes'].append({
            'id': quiz.id,
            'title': quiz.title,
            'description': quiz.description,
            'date': quiz.date_of_quiz.strftime('%Y-%m-%d'),
            'chapter_name': quiz.chapter.name,
            'chapter_id': quiz.chapter_id,
            'subject_name': quiz.chapter.subject.name,
            'subject_id': quiz.chapter.subject_id,
            'url': url_for('admin.edit_quiz', id=quiz.id)
        })
    
    # Search users
    users = User.query.filter(
        or_(
            User.username.ilike(f'%{query}%'),
            User.email.ilike(f'%{query}%'),
            User.fullname.ilike(f'%{query}%')
        )
    ).limit(10).all()
    
    for user in users:
        results['users'].append({
            'id': user.id,
            'username': user.username,
            'fullname': user.fullname,
            'email': user.email,
            'joined_date': user.created_at.strftime('%Y-%m-%d'),
            'url': url_for('admin.users')
        })
    
    # Count total results
    total_results = len(results['subjects']) + len(results['chapters']) + len(results['quizzes']) + len(results['users'])
    
    # Check if this is an AJAX request
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return jsonify({
            'success': True,
            'message': f'Found {total_results} results for "{query}"',
            'query': query,
            'results': results
        })
    else:
        # For regular form submission, render a template (not used now, but could be in the future)
        return render_template(
            'admin/search_results.html',
            query=query,
            total_results=total_results,
            subjects=results['subjects'],
            chapters=results['chapters'],
            quizzes=results['quizzes'],
            users=results['users']
        )

@admin.route('/reports')
@login_required
@admin_required
def reports():
    # Get statistics for reports
    total_users = User.query.filter(User.is_admin == False).count()
    total_quizzes = Quiz.query.count()
    total_attempts = Score.query.count()
    
    # Get subject statistics
    subject_stats = db.session.query(
        Subject.name,
        db.func.count(Chapter.id).label('chapter_count'),
        db.func.count(Quiz.id).label('quiz_count')
    ).outerjoin(
        Chapter, Subject.id == Chapter.subject_id
    ).outerjoin(
        Quiz, Chapter.id == Quiz.chapter_id
    ).group_by(
        Subject.id
    ).all()
    
    # Get user activity over time
    user_activity = db.session.query(
        db.func.strftime('%Y-%m', Score.time_stamp_of_attempt).label('month'),
        db.func.count(Score.id).label('attempt_count')
    ).group_by(
        'month'
    ).order_by(
        'month'
    ).all()
    
    return render_template(
        'admin/reports_page.html',  # Updated template name
        total_users=total_users,
        total_quizzes=total_quizzes,
        total_attempts=total_attempts,
        subject_stats=subject_stats,
        user_activity=user_activity
    )


