from django.shortcuts import render, redirect, get_object_or_404
from django.http import JsonResponse
from django.utils import timezone
from django.contrib import messages
from .models import Student, Quiz, QuizAttempt, StudentAnswer, Subject
from .forms import StudentLoginForm, QuizForm

def home(request):
    subjects = Subject.objects.all()
    return render(request, 'quiz/home.html', {'subjects': subjects})

def student_login(request):
    # Clear any existing session to allow new student login
    if 'student_id' in request.session:
        del request.session['student_id']
    
    if request.method == 'POST':
        form = StudentLoginForm(request.POST)
        if form.is_valid():
            student = form.cleaned_data['student']
            request.session['student_id'] = student.id
            request.session['student_name'] = student.name
            messages.success(request, f'Welcome {student.name}! You can now take available quizzes.')
            return redirect('quiz_list')
    else:
        form = StudentLoginForm()
    
    return render(request, 'quiz/student_login.html', {'form': form})

def student_logout(request):
    """Logout student and clear session"""
    student_name = request.session.get('student_name', 'Student')
    if 'student_id' in request.session:
        del request.session['student_id']
    if 'student_name' in request.session:
        del request.session['student_name']
    
    messages.info(request, f'Goodbye {student_name}! You have been logged out successfully.')
    return redirect('home')

def quiz_list(request):
    if 'student_id' not in request.session:
        messages.warning(request, 'Please login first to view available quizzes.')
        return redirect('student_login')
    
    student = get_object_or_404(Student, id=request.session['student_id'])
    quizzes = Quiz.objects.filter(is_active=True)
    if student.student_class:
        quizzes = quizzes.filter(student_class=student.student_class)
    
    # Filter out quizzes already attempted by student
    attempted_quizzes = QuizAttempt.objects.filter(
        student=student, 
        submitted_at__isnull=False
    ).values_list('quiz_id', flat=True)
    
    available_quizzes = quizzes.exclude(id__in=attempted_quizzes)
    
    return render(request, 'quiz/quiz_list.html', {
        'student': student,
        'quizzes': available_quizzes
    })

def take_quiz(request, quiz_id):
    if 'student_id' not in request.session:
        messages.warning(request, 'Please login first to take the quiz.')
        return redirect('student_login')
    
    student = get_object_or_404(Student, id=request.session['student_id'])
    quiz = get_object_or_404(Quiz, id=quiz_id, is_active=True)
    
    # Check if student has already attempted this quiz
    existing_attempt = QuizAttempt.objects.filter(
        student=student, 
        quiz=quiz,
        submitted_at__isnull=False
    ).first()
    
    if existing_attempt:
        messages.warning(request, "You have already attempted this quiz.")
        return redirect('quiz_list')
    
    # Get or create quiz attempt
    attempt, created = QuizAttempt.objects.get_or_create(
        student=student,
        quiz=quiz,
        submitted_at__isnull=True,
        defaults={'started_at': timezone.now()}
    )
    
    questions = quiz.questions.all().prefetch_related('options')
    
    if request.method == 'POST':
        form = QuizForm(request.POST, questions=questions)
        if form.is_valid():
            # Save student answers
            for question in questions:
                field_name = f'question_{question.id}'
                selected_option = form.cleaned_data[field_name]
                
                StudentAnswer.objects.update_or_create(
                    attempt=attempt,
                    question=question,
                    defaults={'selected_option': selected_option}
                )
            
            # Calculate score and mark as submitted
            attempt.calculate_score()
            attempt.submitted_at = timezone.now()
            attempt.save()
            
            # Show success message but don't clear session yet
            messages.success(request, 'Quiz submitted successfully! Thank you for taking the test.')
            return redirect('quiz_submitted')
    else:
        form = QuizForm(questions=questions)
    
    return render(request, 'quiz/take_quiz.html', {
        'quiz': quiz,
        'form': form,
        'time_limit': quiz.time_limit * 60  # Convert to seconds
    })

def quiz_submitted(request):
    """Show quiz submitted confirmation page"""
    # Don't require login for this page since we might have just submitted
    student_name = request.session.get('student_name', 'Student')
    
    return render(request, 'quiz/quiz_submitted.html', {
        'student_name': student_name
    })

def subject_quizzes(request, subject_id):
    if 'student_id' not in request.session:
        messages.warning(request, 'Please login first to view quizzes.')
        return redirect('student_login')
    
    subject = get_object_or_404(Subject, id=subject_id)
    student = get_object_or_404(Student, id=request.session['student_id'])
    quizzes = Quiz.objects.filter(subject=subject, is_active=True)
    if student.student_class:
        quizzes = quizzes.filter(student_class=student.student_class)
    
    # Filter out attempted quizzes
    attempted_quizzes = QuizAttempt.objects.filter(
        student=student, 
        submitted_at__isnull=False
    ).values_list('quiz_id', flat=True)
    
    available_quizzes = quizzes.exclude(id__in=attempted_quizzes)
    
    return render(request, 'quiz/subject_quizzes.html', {
        'subject': subject,
        'quizzes': available_quizzes
    })