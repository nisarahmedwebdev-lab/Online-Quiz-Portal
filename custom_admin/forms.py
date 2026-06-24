from django import forms
from django.contrib.auth.forms import AuthenticationForm
from quiz.models import Subject, Student, Quiz, Question, Option
from .models import AdminSettings

class CustomAdminLoginForm(AuthenticationForm):
    username = forms.CharField(widget=forms.TextInput(attrs={
        'class': 'form-control',
        'placeholder': 'Username'
    }))
    password = forms.CharField(widget=forms.PasswordInput(attrs={
        'class': 'form-control',
        'placeholder': 'Password'
    }))

class SubjectForm(forms.ModelForm):
    class Meta:
        model = Subject
        fields = ['name', 'description']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
        }

class StudentForm(forms.ModelForm):
    class Meta:
        model = Student
        fields = ['name', 'roll_number', 'email', 'student_class']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'roll_number': forms.TextInput(attrs={'class': 'form-control'}),
            'email': forms.EmailInput(attrs={'class': 'form-control'}),
            'student_class': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Enter class or grade'}),
        }

class QuizForm(forms.ModelForm):
    class Meta:
        model = Quiz
        fields = ['title', 'subject', 'student_class', 'description', 'time_limit', 'is_active']
        widgets = {
            'title': forms.TextInput(attrs={'class': 'form-control'}),
            'subject': forms.Select(attrs={'class': 'form-control'}),
            'student_class': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Enter target class or grade'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'time_limit': forms.NumberInput(attrs={'class': 'form-control'}),
            'is_active': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }

class QuestionForm(forms.ModelForm):
    class Meta:
        model = Question
        fields = ['quiz', 'question_text', 'marks']
        widgets = {
            'quiz': forms.Select(attrs={'class': 'form-control'}),
            'question_text': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'marks': forms.NumberInput(attrs={'class': 'form-control'}),
        }

class OptionForm(forms.ModelForm):
    class Meta:
        model = Option
        fields = ['question', 'option_text', 'is_correct']
        widgets = {
            'question': forms.Select(attrs={'class': 'form-control'}),
            'option_text': forms.TextInput(attrs={'class': 'form-control'}),
            'is_correct': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }

class BulkStudentForm(forms.Form):
    student_data = forms.CharField(
        widget=forms.Textarea(attrs={
            'class': 'form-control',
            'rows': 10,
            'placeholder': 'Enter student data in format:\nName,Roll Number,Email\nJohn Doe,2024001,john@example.com\nJane Smith,2024002,jane@example.com'
        }),
        help_text="Enter student data with each line containing: Name, Roll Number, Email, Class (comma-separated). Class is optional."
    )

class SettingsForm(forms.ModelForm):
    class Meta:
        model = AdminSettings
        fields = '__all__'
        widgets = {
            'site_name': forms.TextInput(attrs={'class': 'form-control'}),
            'site_description': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'max_quiz_time': forms.NumberInput(attrs={'class': 'form-control'}),
            'allow_retakes': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'show_results_to_students': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'maintenance_mode': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }

class BulkQuizUploadForm(forms.Form):
    QUIZ_FORMATS = [
        ('json', 'JSON Format'),
        ('csv', 'CSV Format'),
    ]
    
    upload_format = forms.ChoiceField(
        choices=QUIZ_FORMATS,
        widget=forms.RadioSelect,
        initial='json'
    )
    
    quiz_data = forms.CharField(
        widget=forms.Textarea(attrs={
            'class': 'form-control',
            'rows': 15,
            'placeholder': 'Paste your quiz data in JSON or CSV format here...'
        }),
        help_text="Upload multiple questions with options at once"
    )
    
    subject = forms.ModelChoiceField(
        queryset=Subject.objects.all(),
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    
    time_limit = forms.IntegerField(
        initial=30,
        widget=forms.NumberInput(attrs={'class': 'form-control'}),
        help_text="Time limit in minutes for the entire quiz"
    )

class QuickQuestionForm(forms.Form):
    quiz = forms.ModelChoiceField(
        queryset=Quiz.objects.all(),
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    
    question_text = forms.CharField(
        widget=forms.Textarea(attrs={
            'class': 'form-control',
            'rows': 3,
            'placeholder': 'Enter question text...'
        })
    )
    
    marks = forms.IntegerField(
        initial=1,
        widget=forms.NumberInput(attrs={'class': 'form-control'})
    )
    
    option1 = forms.CharField(
        widget=forms.TextInput(attrs={'class': 'form-control'}),
        label="Option 1"
    )
    option2 = forms.CharField(
        widget=forms.TextInput(attrs={'class': 'form-control'}),
        label="Option 2"
    )
    option3 = forms.CharField(
        widget=forms.TextInput(attrs={'class': 'form-control'}),
        required=False,
        label="Option 3"
    )
    option4 = forms.CharField(
        widget=forms.TextInput(attrs={'class': 'form-control'}),
        required=False,
        label="Option 4"
    )
    
    correct_option = forms.ChoiceField(
        choices=[(1, 'Option 1'), (2, 'Option 2'), (3, 'Option 3'), (4, 'Option 4')],
        widget=forms.RadioSelect,
        initial=1
    )