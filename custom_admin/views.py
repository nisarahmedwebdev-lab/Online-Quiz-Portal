from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, logout, authenticate
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib import messages
from django.http import JsonResponse, HttpResponse
from django.db.models import Count, Avg, Sum
from django.utils import timezone
from datetime import timedelta, datetime
import json
import csv
import xlwt
from io import StringIO
from quiz.models import Subject, Student, Quiz, Question, Option, QuizAttempt
from .models import AdminSettings, SystemLog
from .forms import (
    CustomAdminLoginForm, SubjectForm, StudentForm, QuizForm, QuestionForm, 
    OptionForm, BulkStudentForm, SettingsForm, BulkQuizUploadForm, QuickQuestionForm
)

def admin_required(view_func):
    actual_decorator = user_passes_test(
        lambda u: u.is_active and u.is_staff,
        login_url='/custom-admin/login/'
    )
    return actual_decorator(view_func)

def custom_admin_login(request):
    if request.user.is_authenticated and request.user.is_staff:
        return redirect('custom_admin_dashboard')
    
    if request.method == 'POST':
        form = CustomAdminLoginForm(request, data=request.POST)
        if form.is_valid():
            username = form.cleaned_data.get('username')
            password = form.cleaned_data.get('password')
            user = authenticate(username=username, password=password)
            if user is not None and user.is_staff:
                login(request, user)
                SystemLog.objects.create(
                    log_type='SUCCESS',
                    message=f'Admin user {username} logged in',
                    user=user
                )
                return redirect('custom_admin_dashboard')
    else:
        form = CustomAdminLoginForm()
    
    return render(request, 'custom_admin/login.html', {'form': form})

@login_required
@admin_required
def custom_admin_logout(request):
    SystemLog.objects.create(
        log_type='INFO',
        message=f'Admin user {request.user.username} logged out',
        user=request.user
    )
    logout(request)
    return redirect('custom_admin_login')

@login_required
@admin_required
def custom_admin_dashboard(request):
    # Statistics
    total_students = Student.objects.count()
    total_quizzes = Quiz.objects.count()
    total_attempts = QuizAttempt.objects.count()
    total_subjects = Subject.objects.count()
    
    # Recent attempts
    recent_attempts = QuizAttempt.objects.select_related('student', 'quiz').order_by('-started_at')[:10]
    
    # Chart data - Attempts per day (last 7 days)
    today = timezone.now().date()
    seven_days_ago = today - timedelta(days=6)
    
    attempts_data = []
    for i in range(7):
        date = seven_days_ago + timedelta(days=i)
        count = QuizAttempt.objects.filter(started_at__date=date).count()
        attempts_data.append({
            'date': date.strftime('%Y-%m-%d'),
            'count': count
        })
    
    # Subject-wise quiz count
    subject_stats = Subject.objects.annotate(
        quiz_count=Count('quiz'),
        attempt_count=Count('quiz__quizattempt')
    ).values('name', 'quiz_count', 'attempt_count')
    
    # Top performing students
    top_students = QuizAttempt.objects.filter(
        submitted_at__isnull=False
    ).values(
        'student__name', 'student__roll_number'
    ).annotate(
        avg_score=Avg('score'),
        total_attempts=Count('id')
    ).order_by('-avg_score')[:5]
    
    context = {
        'total_students': total_students,
        'total_quizzes': total_quizzes,
        'total_attempts': total_attempts,
        'total_subjects': total_subjects,
        'recent_attempts': recent_attempts,
        'attempts_data': json.dumps(attempts_data),
        'subject_stats': subject_stats,
        'top_students': top_students,
    }
    
    return render(request, 'custom_admin/dashboard.html', context)

@login_required
@admin_required
def normalize_class_names(request):
    import re

    def normalize_value(value):
        if not value:
            return value
        return re.sub(r'[^A-Za-z0-9]+', '_', value).strip('_')

    updated_student_count = 0
    updated_quiz_count = 0

    for student in Student.objects.exclude(student_class__isnull=True).exclude(student_class__exact=''):
        normalized = normalize_value(student.student_class)
        if normalized != student.student_class:
            student.student_class = normalized
            student.save(update_fields=['student_class'])
            updated_student_count += 1

    for quiz in Quiz.objects.exclude(student_class__isnull=True).exclude(student_class__exact=''):
        normalized = normalize_value(quiz.student_class)
        if normalized != quiz.student_class:
            quiz.student_class = normalized
            quiz.save(update_fields=['student_class'])
            updated_quiz_count += 1

    SystemLog.objects.create(
        log_type='INFO',
        message=f'Normalized class names: students={updated_student_count}, quizzes={updated_quiz_count}',
        user=request.user
    )

    messages.success(request, f'Class normalization complete. Students updated: {updated_student_count}, Quizzes updated: {updated_quiz_count}.')
    return redirect('custom_admin_dashboard')

@login_required
@admin_required
def manage_subjects(request):
    subjects = Subject.objects.all().order_by('-created_at')
    
    if request.method == 'POST':
        form = SubjectForm(request.POST)
        if form.is_valid():
            subject = form.save()
            SystemLog.objects.create(
                log_type='SUCCESS',
                message=f'Subject "{subject.name}" created',
                user=request.user
            )
            return redirect('manage_subjects')
    else:
        form = SubjectForm()
    
    return render(request, 'custom_admin/manage_subjects.html', {
        'subjects': subjects,
        'form': form
    })

@login_required
@admin_required
def edit_subject(request, subject_id):
    subject = get_object_or_404(Subject, id=subject_id)
    
    if request.method == 'POST':
        form = SubjectForm(request.POST, instance=subject)
        if form.is_valid():
            form.save()
            SystemLog.objects.create(
                log_type='INFO',
                message=f'Subject "{subject.name}" updated',
                user=request.user
            )
            return redirect('manage_subjects')
    else:
        form = SubjectForm(instance=subject)
    
    return render(request, 'custom_admin/edit_subject.html', {
        'form': form,
        'subject': subject
    })

@login_required
@admin_required
def delete_subject(request, subject_id):
    subject = get_object_or_404(Subject, id=subject_id)
    subject_name = subject.name
    subject.delete()
    
    SystemLog.objects.create(
        log_type='WARNING',
        message=f'Subject "{subject_name}" deleted',
        user=request.user
    )
    
    return redirect('manage_subjects')

@login_required
@admin_required
def manage_students(request):
    students = Student.objects.all().order_by('-created_at')
    
    if request.method == 'POST' and 'bulk_upload' in request.POST:
        bulk_form = BulkStudentForm(request.POST)
        if bulk_form.is_valid():
            data = bulk_form.cleaned_data['student_data']
            lines = data.strip().split('\n')
            created_count = 0
            
            for line in lines:
                parts = [part.strip() for part in line.split(',')]
                if len(parts) >= 2:
                    name = parts[0]
                    roll_number = parts[1]
                    email = parts[2] if len(parts) > 2 else ''
                    student_class = parts[3] if len(parts) > 3 else ''
                    
                    if not Student.objects.filter(roll_number=roll_number).exists():
                        Student.objects.create(
                            name=name,
                            roll_number=roll_number,
                            email=email,
                            student_class=student_class
                        )
                        created_count += 1
            
            SystemLog.objects.create(
                log_type='SUCCESS',
                message=f'Bulk student upload: {created_count} students created',
                user=request.user
            )
            return redirect('manage_students')
    else:
        bulk_form = BulkStudentForm()
    
    if request.method == 'POST' and 'add_student' in request.POST:
        form = StudentForm(request.POST)
        if form.is_valid():
            student = form.save()
            SystemLog.objects.create(
                log_type='SUCCESS',
                message=f'Student "{student.name}" created in class "{student.student_class or "Unassigned"}"',
                user=request.user
            )
            return redirect('manage_students')
    else:
        form = StudentForm()
    
    return render(request, 'custom_admin/manage_students.html', {
        'students': students,
        'form': form,
        'bulk_form': bulk_form
    })

@login_required
@admin_required
def edit_student(request, student_id):
    student = get_object_or_404(Student, id=student_id)
    
    if request.method == 'POST':
        form = StudentForm(request.POST, instance=student)
        if form.is_valid():
            form.save()
            SystemLog.objects.create(
                log_type='INFO',
                message=f'Student "{student.name}" updated',
                user=request.user
            )
            return redirect('manage_students')
    else:
        form = StudentForm(instance=student)
    
    return render(request, 'custom_admin/edit_student.html', {
        'form': form,
        'student': student
    })

@login_required
@admin_required
def delete_student(request, student_id):
    student = get_object_or_404(Student, id=student_id)
    student_name = student.name
    student.delete()
    
    SystemLog.objects.create(
        log_type='WARNING',
        message=f'Student "{student_name}" deleted',
        user=request.user
    )
    
    return redirect('manage_students')

@login_required
@admin_required
def manage_quizzes(request):
    quizzes = Quiz.objects.all().select_related('subject').order_by('-created_at')
    
    if request.method == 'POST':
        form = QuizForm(request.POST)
        if form.is_valid():
            quiz = form.save()
            SystemLog.objects.create(
                log_type='SUCCESS',
                message=f'Quiz "{quiz.title}" created',
                user=request.user
            )
            return redirect('manage_quizzes')
    else:
        form = QuizForm()
    
    return render(request, 'custom_admin/manage_quizzes.html', {
        'quizzes': quizzes,
        'form': form
    })

@login_required
@admin_required
def edit_quiz(request, quiz_id):
    quiz = get_object_or_404(Quiz, id=quiz_id)
    
    if request.method == 'POST':
        form = QuizForm(request.POST, instance=quiz)
        if form.is_valid():
            form.save()
            SystemLog.objects.create(
                log_type='INFO',
                message=f'Quiz "{quiz.title}" updated',
                user=request.user
            )
            return redirect('manage_quizzes')
    else:
        form = QuizForm(instance=quiz)
    
    return render(request, 'custom_admin/edit_quiz.html', {
        'form': form,
        'quiz': quiz
    })

@login_required
@admin_required
def delete_quiz(request, quiz_id):
    quiz = get_object_or_404(Quiz, id=quiz_id)
    quiz_title = quiz.title
    quiz.delete()
    
    SystemLog.objects.create(
        log_type='WARNING',
        message=f'Quiz "{quiz_title}" deleted',
        user=request.user
    )
    
    return redirect('manage_quizzes')

@login_required
@admin_required
def manage_questions(request, quiz_id=None):
    quiz = None
    if quiz_id:
        quiz = get_object_or_404(Quiz, id=quiz_id)
        questions = Question.objects.filter(quiz=quiz).select_related('quiz')
    else:
        questions = Question.objects.all().select_related('quiz')
    
    if request.method == 'POST':
        form = QuestionForm(request.POST)
        if form.is_valid():
            question = form.save()
            SystemLog.objects.create(
                log_type='SUCCESS',
                message=f'Question added to quiz "{question.quiz.title}"',
                user=request.user
            )
            # Redirect to add options for this question
            return redirect('manage_options', question_id=question.id)
    else:
        form = QuestionForm()
        if quiz:
            form.fields['quiz'].initial = quiz
    
    return render(request, 'custom_admin/manage_questions.html', {
        'questions': questions,
        'form': form,
        'quiz': quiz
    })

@login_required
@admin_required
def edit_question(request, question_id):
    question = get_object_or_404(Question, id=question_id)
    
    if request.method == 'POST':
        form = QuestionForm(request.POST, instance=question)
        if form.is_valid():
            form.save()
            SystemLog.objects.create(
                log_type='INFO',
                message=f'Question updated in quiz "{question.quiz.title}"',
                user=request.user
            )
            return redirect('manage_questions')
    else:
        form = QuestionForm(instance=question)
    
    return render(request, 'custom_admin/edit_question.html', {
        'form': form,
        'question': question
    })

@login_required
@admin_required
def delete_question(request, question_id):
    question = get_object_or_404(Question, id=question_id)
    quiz_title = question.quiz.title
    question.delete()
    
    SystemLog.objects.create(
        log_type='WARNING',
        message=f'Question deleted from quiz "{quiz_title}"',
        user=request.user
    )
    
    return redirect('manage_questions')

@login_required
@admin_required
def manage_options(request, question_id):
    question = get_object_or_404(Question, id=question_id)
    options = Option.objects.filter(question=question)
    
    if request.method == 'POST':
        form = OptionForm(request.POST)
        if form.is_valid():
            option = form.save()
            SystemLog.objects.create(
                log_type='SUCCESS',
                message=f'Option added to question in quiz "{question.quiz.title}"',
                user=request.user
            )
            # Stay on the same page after adding option
            return redirect('manage_options', question_id=question_id)
    else:
        form = OptionForm()
        form.fields['question'].initial = question
    
    # Check if we have at least one correct option
    has_correct_option = options.filter(is_correct=True).exists()
    
    return render(request, 'custom_admin/manage_options.html', {
        'question': question,
        'options': options,
        'form': form,
        'has_correct_option': has_correct_option
    })

@login_required
@admin_required
def edit_option(request, option_id):
    option = get_object_or_404(Option, id=option_id)
    
    if request.method == 'POST':
        form = OptionForm(request.POST, instance=option)
        if form.is_valid():
            form.save()
            SystemLog.objects.create(
                log_type='INFO',
                message=f'Option updated in quiz "{option.question.quiz.title}"',
                user=request.user
            )
            return redirect('manage_options', question_id=option.question.id)
    else:
        form = OptionForm(instance=option)
    
    return render(request, 'custom_admin/edit_option.html', {
        'form': form,
        'option': option
    })

@login_required
@admin_required
def delete_option(request, option_id):
    option = get_object_or_404(Option, id=option_id)
    question_id = option.question.id
    option.delete()
    
    SystemLog.objects.create(
        log_type='WARNING',
        message=f'Option deleted from quiz "{option.question.quiz.title}"',
        user=request.user
    )
    
    return redirect('manage_options', question_id=question_id)

@login_required
@admin_required
def _get_filtered_attempts(request):
    attempts = QuizAttempt.objects.filter(
        submitted_at__isnull=False
    ).select_related('student', 'quiz', 'quiz__subject').order_by('-submitted_at')

    selected_class = request.GET.get('student_class')
    selected_subject = request.GET.get('subject_id')

    if selected_class:
        attempts = attempts.filter(student__student_class=selected_class)

    if selected_subject:
        try:
            selected_subject_id = int(selected_subject)
            attempts = attempts.filter(quiz__subject_id=selected_subject_id)
        except (TypeError, ValueError):
            pass

    return attempts

@login_required
@admin_required
def view_results(request):
    selected_class = request.GET.get('student_class', '')
    selected_subject = request.GET.get('subject_id', '')
    attempts = _get_filtered_attempts(request)
    
    # Statistics for charts
    quiz_performance = QuizAttempt.objects.filter(
        submitted_at__isnull=False
    ).values('quiz__title').annotate(
        avg_score=Avg('score'),
        total_attempts=Count('id')
    )
    
    student_performance = QuizAttempt.objects.filter(
        submitted_at__isnull=False
    ).values('student__name').annotate(
        avg_score=Avg('score'),
        total_attempts=Count('id')
    ).order_by('-avg_score')[:10]
    
    students_count = Student.objects.count()
    
    class_choices = Student.objects.exclude(student_class__isnull=True).exclude(student_class__exact='').values_list('student_class', flat=True).distinct().order_by('student_class')
    subjects = Subject.objects.all().order_by('name')

    # Class-wise absent counts: students assigned to a quiz class who did not submit any quiz.
    class_summary = []
    quiz_classes = Quiz.objects.exclude(student_class__isnull=True).exclude(student_class__exact='').values_list('student_class', flat=True).distinct()
    for class_name in quiz_classes:
        expected_students = Student.objects.filter(student_class=class_name).count()
        attempted_students = Student.objects.filter(
            quizattempt__quiz__student_class=class_name,
            quizattempt__submitted_at__isnull=False
        ).distinct().count()
        class_summary.append({
            'student_class': class_name,
            'expected_students': expected_students,
            'attempted_students': attempted_students,
            'absent_students': max(expected_students - attempted_students, 0)
        })

    # Subject-wise absent counts: unique students in classes mapped to quizzes within each subject.
    subject_summary = []
    all_subjects = Subject.objects.all()
    for subject in all_subjects:
        class_names = Quiz.objects.filter(subject=subject).exclude(student_class__isnull=True).exclude(student_class__exact='').values_list('student_class', flat=True).distinct()
        expected_students = Student.objects.filter(student_class__in=class_names).count() if class_names else 0
        attempted_students = Student.objects.filter(
            quizattempt__quiz__subject=subject,
            quizattempt__submitted_at__isnull=False
        ).distinct().count()
        subject_summary.append({
            'subject_name': subject.name,
            'expected_students': expected_students,
            'attempted_students': attempted_students,
            'absent_students': max(expected_students - attempted_students, 0)
        })
    
    query_params = []
    if selected_class:
        query_params.append(f'student_class={selected_class}')
    if selected_subject:
        query_params.append(f'subject_id={selected_subject}')
    export_query = f'?{'&'.join(query_params)}' if query_params else ''

    context = {
        'attempts': attempts,
        'quiz_performance': list(quiz_performance),
        'student_performance': list(student_performance),
        'students_count': students_count,
        'class_summary': class_summary,
        'subject_summary': subject_summary,
        'class_choices': class_choices,
        'subjects': subjects,
        'selected_class': selected_class,
        'selected_subject': selected_subject,
        'export_query': export_query,
    }
    
    return render(request, 'custom_admin/view_results.html', context)

@login_required
@admin_required
def view_attempt_detail(request, attempt_id):
    attempt = get_object_or_404(QuizAttempt, id=attempt_id)
    answers = attempt.answers.select_related('question', 'selected_option')
    
    return render(request, 'custom_admin/attempt_detail.html', {
        'attempt': attempt,
        'answers': answers
    })

@login_required
@admin_required
def system_settings(request):
    settings_obj, created = AdminSettings.objects.get_or_create(pk=1)
    
    if request.method == 'POST':
        form = SettingsForm(request.POST, instance=settings_obj)
        if form.is_valid():
            form.save()
            SystemLog.objects.create(
                log_type='INFO',
                message='System settings updated',
                user=request.user
            )
            return redirect('system_settings')
    else:
        form = SettingsForm(instance=settings_obj)
    
    return render(request, 'custom_admin/system_settings.html', {'form': form})

@login_required
@admin_required
def system_logs(request):
    logs = SystemLog.objects.all().select_related('user').order_by('-timestamp')
    
    return render(request, 'custom_admin/system_logs.html', {'logs': logs})

@login_required
@admin_required
def get_chart_data(request):
    # Attempts per day for last 30 days
    today = timezone.now().date()
    thirty_days_ago = today - timedelta(days=29)
    
    attempts_data = []
    for i in range(30):
        date = thirty_days_ago + timedelta(days=i)
        count = QuizAttempt.objects.filter(started_at__date=date).count()
        attempts_data.append({
            'date': date.strftime('%m-%d'),
            'count': count
        })
    
    # Subject-wise distribution
    subject_data = list(Subject.objects.annotate(
        quiz_count=Count('quiz'),
        attempt_count=Count('quiz__quizattempt')
    ).values('name', 'quiz_count', 'attempt_count'))
    
    return JsonResponse({
        'attempts_data': attempts_data,
        'subject_data': subject_data,
    })

@login_required
@admin_required
def download_results_csv(request):
    """Download quiz results as CSV"""
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = f'attachment; filename="quiz_results_{datetime.now().strftime("%Y%m%d_%H%M%S")}.csv"'
    
    writer = csv.writer(response)
    writer.writerow(['Student Name', 'Roll Number', 'Quiz Title', 'Subject', 
                    'Score', 'Total Marks', 'Percentage', 'Started At', 'Submitted At'])
    
    attempts = _get_filtered_attempts(request)
    
    for attempt in attempts:
        percentage = (attempt.score / attempt.total_marks) * 100 if attempt.total_marks > 0 else 0
        writer.writerow([
            attempt.student.name,
            attempt.student.roll_number,
            attempt.quiz.title,
            attempt.quiz.subject.name,
            attempt.score,
            attempt.total_marks,
            f"{percentage:.2f}%",
            attempt.started_at.strftime("%Y-%m-%d %H:%M:%S"),
            attempt.submitted_at.strftime("%Y-%m-%d %H:%M:%S") if attempt.submitted_at else "N/A"
        ])
    
    SystemLog.objects.create(
        log_type='INFO',
        message='Quiz results downloaded as CSV',
        user=request.user
    )
    
    return response

@login_required
@admin_required
def download_results_excel(request):
    """Download quiz results as Excel"""
    response = HttpResponse(content_type='application/ms-excel')
    response['Content-Disposition'] = f'attachment; filename="quiz_results_{datetime.now().strftime("%Y%m%d_%H%M%S")}.xls"'
    
    wb = xlwt.Workbook(encoding='utf-8')
    ws = wb.add_sheet('Quiz Results')
    
    # Sheet header, first row
    row_num = 0
    
    font_style = xlwt.XFStyle()
    font_style.font.bold = True
    
    columns = ['Student Name', 'Roll Number', 'Quiz Title', 'Subject', 
              'Score', 'Total Marks', 'Percentage', 'Started At', 'Submitted At']
    
    for col_num, column_title in enumerate(columns):
        ws.write(row_num, col_num, column_title, font_style)
    
    # Sheet body, remaining rows
    font_style = xlwt.XFStyle()
    
    attempts = _get_filtered_attempts(request)
    
    for attempt in attempts:
        row_num += 1
        percentage = (attempt.score / attempt.total_marks) * 100 if attempt.total_marks > 0 else 0
        
        ws.write(row_num, 0, attempt.student.name, font_style)
        ws.write(row_num, 1, attempt.student.roll_number, font_style)
        ws.write(row_num, 2, attempt.quiz.title, font_style)
        ws.write(row_num, 3, attempt.quiz.subject.name, font_style)
        ws.write(row_num, 4, attempt.score, font_style)
        ws.write(row_num, 5, attempt.total_marks, font_style)
        ws.write(row_num, 6, f"{percentage:.2f}%", font_style)
        ws.write(row_num, 7, attempt.started_at.strftime("%Y-%m-%d %H:%M:%S"), font_style)
        ws.write(row_num, 8, attempt.submitted_at.strftime("%Y-%m-%d %H:%M:%S") if attempt.submitted_at else "N/A", font_style)
    
    wb.save(response)
    
    SystemLog.objects.create(
        log_type='INFO',
        message='Quiz results downloaded as Excel',
        user=request.user
    )
    
    return response
    """Download quiz results as Excel"""
    response = HttpResponse(content_type='application/ms-excel')
    response['Content-Disposition'] = f'attachment; filename="quiz_results_{datetime.now().strftime("%Y%m%d_%H%M%S")}.xls"'
    
    wb = xlwt.Workbook(encoding='utf-8')
    ws = wb.add_sheet('Quiz Results')
    
    # Sheet header, first row
    row_num = 0
    
    font_style = xlwt.XFStyle()
    font_style.font.bold = True
    
    columns = ['Student Name', 'Roll Number', 'Quiz Title', 'Subject', 
              'Score', 'Total Marks', 'Percentage', 'Started At', 'Submitted At']
    
    for col_num, column_title in enumerate(columns):
        ws.write(row_num, col_num, column_title, font_style)
    
    # Sheet body, remaining rows
    font_style = xlwt.XFStyle()
    
    attempts = QuizAttempt.objects.filter(
        submitted_at__isnull=False
    ).select_related('student', 'quiz', 'quiz__subject').order_by('-submitted_at')
    
    for attempt in attempts:
        row_num += 1
        percentage = (attempt.score / attempt.total_marks) * 100 if attempt.total_marks > 0 else 0
        
        ws.write(row_num, 0, attempt.student.name, font_style)
        ws.write(row_num, 1, attempt.student.roll_number, font_style)
        ws.write(row_num, 2, attempt.quiz.title, font_style)
        ws.write(row_num, 3, attempt.quiz.subject.name, font_style)
        ws.write(row_num, 4, attempt.score, font_style)
        ws.write(row_num, 5, attempt.total_marks, font_style)
        ws.write(row_num, 6, f"{percentage:.2f}%", font_style)
        ws.write(row_num, 7, attempt.started_at.strftime("%Y-%m-%d %H:%M:%S"), font_style)
        ws.write(row_num, 8, attempt.submitted_at.strftime("%Y-%m-%d %H:%M:%S") if attempt.submitted_at else "N/A", font_style)
    
    wb.save(response)
    
    SystemLog.objects.create(
        log_type='INFO',
        message='Quiz results downloaded as Excel',
        user=request.user
    )
    
    return response

@login_required
@admin_required
def download_student_list(request):
    """Download student list as CSV"""
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = f'attachment; filename="students_list_{datetime.now().strftime("%Y%m%d_%H%M%S")}.csv"'
    
    writer = csv.writer(response)
    writer.writerow(['Name', 'Roll Number', 'Email', 'Class', 'Created At', 'Total Quiz Attempts'])
    
    students = Student.objects.all().order_by('roll_number')
    
    for student in students:
        total_attempts = student.quizattempt_set.count()
        writer.writerow([
            student.name,
            student.roll_number,
            student.email or "",
            student.student_class or "",
            student.created_at.strftime("%Y-%m-%d"),
            total_attempts
        ])
    
    SystemLog.objects.create(
        log_type='INFO',
        message='Student list downloaded as CSV',
        user=request.user
    )
    
    return response

@login_required
@admin_required
def bulk_quiz_upload(request):
    """Bulk upload quizzes with questions and options"""
    if request.method == 'POST':
        form = BulkQuizUploadForm(request.POST)
        if form.is_valid():
            subject = form.cleaned_data['subject']
            time_limit = form.cleaned_data['time_limit']
            upload_format = form.cleaned_data['upload_format']
            quiz_data = form.cleaned_data['quiz_data']
            
            try:
                if upload_format == 'json':
                    success_count, error_count = process_json_upload(quiz_data, subject, time_limit, request.user)
                else:
                    success_count, error_count = process_csv_upload(quiz_data, subject, time_limit, request.user)
                
                if success_count > 0:
                    messages.success(request, f'Successfully uploaded {success_count} questions. Errors: {error_count}')
                else:
                    messages.error(request, f'No questions were uploaded. Please check your JSON format. Errors: {error_count}')
                
                return redirect('manage_questions')
                
            except json.JSONDecodeError as e:
                messages.error(request, f'Invalid JSON format: {str(e)}')
            except Exception as e:
                messages.error(request, f'Error processing upload: {str(e)}')
    else:
        form = BulkQuizUploadForm()
    
    return render(request, 'custom_admin/bulk_quiz_upload.html', {'form': form})

@login_required
@admin_required
def quick_question_add(request):
    """Quickly add single question with options"""
    if request.method == 'POST':
        form = QuickQuestionForm(request.POST)
        if form.is_valid():
            try:
                # Create or get question
                question = Question.objects.create(
                    quiz=form.cleaned_data['quiz'],
                    question_text=form.cleaned_data['question_text'],
                    marks=form.cleaned_data['marks']
                )
                
                # Create options
                options_data = [
                    (form.cleaned_data['option1'], 1),
                    (form.cleaned_data['option2'], 2),
                    (form.cleaned_data['option3'], 3),
                    (form.cleaned_data['option4'], 4)
                ]
                
                correct_option_num = int(form.cleaned_data['correct_option'])
                
                for i, (option_text, option_num) in enumerate(options_data, 1):
                    if option_text:  # Only create if option text is provided
                        Option.objects.create(
                            question=question,
                            option_text=option_text,
                            is_correct=(i == correct_option_num)
                        )
                
                SystemLog.objects.create(
                    log_type='SUCCESS',
                    message=f'Quick question added to quiz "{question.quiz.title}"',
                    user=request.user
                )
                
                messages.success(request, 'Question added successfully!')
                
                # Check if user wants to add another
                if 'add_another' in request.POST:
                    return redirect('quick_question_add')
                else:
                    return redirect('manage_questions')
                
            except Exception as e:
                messages.error(request, f'Error adding question: {str(e)}')
    else:
        form = QuickQuestionForm()
    
    return render(request, 'custom_admin/quick_question_add.html', {'form': form})

# Helper functions for bulk upload
def process_json_upload(quiz_data, subject, time_limit, user):
    """Process JSON format quiz data - handles both single quiz and array of quizzes"""
    data = json.loads(quiz_data)
    success_count = 0
    error_count = 0
    
    # Handle both single quiz object and array of quizzes
    if isinstance(data, dict):
        # Single quiz object
        quizzes_to_process = [data]
    elif isinstance(data, list):
        # Array of quiz objects
        quizzes_to_process = data
    else:
        SystemLog.objects.create(
            log_type='ERROR',
            message='Invalid JSON format: expected object or array',
            user=user
        )
        return 0, 1
    
    for quiz_item in quizzes_to_process:
        try:
            # Create quiz
            quiz_title = quiz_item.get('quiz_title', 'Untitled Quiz')
            quiz_description = quiz_item.get('quiz_description', '')
            
            quiz = Quiz.objects.create(
                title=quiz_title,
                subject=subject,
                description=quiz_description,
                time_limit=time_limit,
                is_active=True
            )
            
            # Add questions
            questions = quiz_item.get('questions', [])
            for question_data in questions:
                question = Question.objects.create(
                    quiz=quiz,
                    question_text=question_data['question_text'],
                    marks=question_data.get('marks', 1)
                )
                
                # Add options
                options = question_data.get('options', [])
                correct_option = question_data.get('correct_option', 1)
                
                for i, option_text in enumerate(options, 1):
                    if option_text:  # Only create if option text is not empty
                        Option.objects.create(
                            question=question,
                            option_text=option_text,
                            is_correct=(i == correct_option)
                        )
                
                success_count += 1
                
        except Exception as e:
            error_count += 1
            SystemLog.objects.create(
                log_type='ERROR',
                message=f'Error in JSON upload: {str(e)}',
                user=user
            )
            # Continue processing other quizzes even if one fails
            continue
    
    return success_count, error_count

def process_csv_upload(quiz_data, subject, time_limit, user):
    """Process CSV format quiz data"""
    success_count = 0
    error_count = 0
    
    # Read CSV data
    csv_file = StringIO(quiz_data)
    reader = csv.DictReader(csv_file)
    
    current_quiz = None
    
    for row in reader:
        try:
            # Create quiz if needed
            quiz_title = row.get('quiz_title', 'Untitled Quiz')
            if not current_quiz or current_quiz.title != quiz_title:
                current_quiz, created = Quiz.objects.get_or_create(
                    title=quiz_title,
                    subject=subject,
                    defaults={
                        'description': row.get('quiz_description', ''),
                        'time_limit': time_limit,
                        'is_active': True
                    }
                )
            
            # Create question
            question = Question.objects.create(
                quiz=current_quiz,
                question_text=row['question_text'],
                marks=int(row.get('marks', 1))
            )
            
            # Create options
            for i in range(1, 5):
                option_text = row.get(f'option_{i}', '')
                if option_text:
                    Option.objects.create(
                        question=question,
                        option_text=option_text,
                        is_correct=(int(row['correct_option']) == i)
                    )
            
            success_count += 1
            
        except Exception as e:
            error_count += 1
            SystemLog.objects.create(
                log_type='ERROR',
                message=f'Error in CSV upload: {str(e)}',
                user=user
            )
    
    return success_count, error_count

@login_required
@admin_required
def download_quiz_template(request, format_type):
    """Download quiz template for bulk upload"""
    if format_type == 'json':
        return download_json_template(request)
    else:
        return download_csv_template(request)

def download_json_template(request):
    """Download JSON template with both single quiz and array formats"""
    template = {
        "single_quiz_format": {
            "quiz_title": "Sample Quiz",
            "quiz_description": "Description of the quiz", 
            "questions": [
                {
                    "question_text": "What is 2+2?",
                    "marks": 1,
                    "options": ["3", "4", "5", "6"],
                    "correct_option": 2
                },
                {
                    "question_text": "What is the capital of France?",
                    "marks": 1,
                    "options": ["London", "Berlin", "Paris", "Madrid"],
                    "correct_option": 3
                }
            ]
        }
    }
    
    response = HttpResponse(json.dumps(template, indent=2), content_type='application/json')
    response['Content-Disposition'] = 'attachment; filename="quiz_template.json"'
    return response

def download_csv_template(request):
    """Download CSV template"""
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename="quiz_template.csv"'
    
    writer = csv.writer(response)
    writer.writerow(['quiz_title', 'quiz_description', 'question_text', 'marks', 'option_1', 'option_2', 'option_3', 'option_4', 'correct_option'])
    writer.writerow(['Mathematics Quiz', 'Basic math questions', 'What is 2+2?', '1', '3', '4', '5', '6', '2'])
    writer.writerow(['Mathematics Quiz', 'Basic math questions', 'What is 5*3?', '1', '10', '15', '20', '25', '2'])
    
    return response