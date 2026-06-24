from django import forms
from .models import Student, QuizAttempt, StudentAnswer

class StudentLoginForm(forms.Form):
    name = forms.CharField(max_length=100, required=True)
    roll_number = forms.CharField(max_length=20, required=True)
    
    def clean(self):
        cleaned_data = super().clean()
        name = cleaned_data.get('name')
        roll_number = cleaned_data.get('roll_number')
        
        if name and roll_number:
            try:
                student = Student.objects.get(name__iexact=name, roll_number=roll_number)
                cleaned_data['student'] = student
            except Student.DoesNotExist:
                raise forms.ValidationError("Invalid name or roll number. Please check your credentials.")
        
        return cleaned_data

class QuizForm(forms.Form):
    def __init__(self, *args, **kwargs):
        questions = kwargs.pop('questions')
        super(QuizForm, self).__init__(*args, **kwargs)
        
        for question in questions:
            self.fields[f'question_{question.id}'] = forms.ModelChoiceField(
                queryset=question.options.all(),
                widget=forms.RadioSelect,
                label=question.question_text,
                required=True
            )