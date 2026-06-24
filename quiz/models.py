from django.db import models
from django.contrib.auth.models import User

class Subject(models.Model):
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return self.name

class Student(models.Model):
    name = models.CharField(max_length=100)
    roll_number = models.CharField(max_length=20, unique=True)
    email = models.EmailField(blank=True)
    student_class = models.CharField(max_length=100, blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"{self.name} ({self.roll_number})"

class Quiz(models.Model):
    title = models.CharField(max_length=200)
    subject = models.ForeignKey(Subject, on_delete=models.CASCADE)
    student_class = models.CharField(max_length=100, blank=True, null=True)
    description = models.TextField(blank=True)
    time_limit = models.IntegerField(help_text="Time limit in minutes")
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return self.title

class Question(models.Model):
    quiz = models.ForeignKey(Quiz, on_delete=models.CASCADE, related_name='questions')
    question_text = models.TextField()
    marks = models.IntegerField(default=1)
    
    def __str__(self):
        return self.question_text[:50] + "..." if len(self.question_text) > 50 else self.question_text

class Option(models.Model):
    question = models.ForeignKey(Question, on_delete=models.CASCADE, related_name='options')
    option_text = models.CharField(max_length=200)
    is_correct = models.BooleanField(default=False)
    
    def __str__(self):
        return self.option_text

class QuizAttempt(models.Model):
    student = models.ForeignKey(Student, on_delete=models.CASCADE)
    quiz = models.ForeignKey(Quiz, on_delete=models.CASCADE)
    started_at = models.DateTimeField(auto_now_add=True)
    submitted_at = models.DateTimeField(null=True, blank=True)
    score = models.IntegerField(default=0)
    total_marks = models.IntegerField(default=0)
    
    def __str__(self):
        return f"{self.student.name} - {self.quiz.title}"
    
    def calculate_score(self):
        # Calculate score based on student's answers
        answers = self.answers.select_related('question', 'selected_option')
        total_score = 0
        total_marks = 0
        
        for answer in answers:
            total_marks += answer.question.marks
            if answer.selected_option and answer.selected_option.is_correct:
                total_score += answer.question.marks
        
        self.score = total_score
        self.total_marks = total_marks
        self.save()
        return total_score

class StudentAnswer(models.Model):
    attempt = models.ForeignKey(QuizAttempt, on_delete=models.CASCADE, related_name='answers')
    question = models.ForeignKey(Question, on_delete=models.CASCADE)
    selected_option = models.ForeignKey(Option, on_delete=models.CASCADE, null=True, blank=True)
    
    class Meta:
        unique_together = ('attempt', 'question')