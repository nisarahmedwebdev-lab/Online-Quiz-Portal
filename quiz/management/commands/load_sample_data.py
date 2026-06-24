from django.core.management.base import BaseCommand
from quiz.models import Subject, Student, Quiz, Question, Option

class Command(BaseCommand):
    help = 'Load sample data for the quiz application'

    def handle(self, *args, **options):
        # Create Subjects
        math_subject = Subject.objects.create(
            name="Mathematics",
            description="Test your math skills with various topics"
        )
        
        science_subject = Subject.objects.create(
            name="Science",
            description="Explore scientific concepts and principles"
        )
        
        # Create Students
        Student.objects.create(
            name="John Doe",
            roll_number="2024001",
            email="john.doe@example.com",
            student_class="10th Grade"
        )
        
        Student.objects.create(
            name="Jane Smith",
            roll_number="2024002",
            email="jane.smith@example.com",
            student_class="10th Grade"
        )
        
        # Create Math Quiz
        math_quiz = Quiz.objects.create(
            title="Basic Mathematics Quiz",
            subject=math_subject,
            student_class="10th Grade",
            description="A quiz covering basic mathematical concepts",
            time_limit=30,
            is_active=True
        )
        
        # Math Questions
        q1 = Question.objects.create(
            quiz=math_quiz,
            question_text="What is 15 + 27?",
            marks=1
        )
        Option.objects.create(question=q1, option_text="32", is_correct=False)
        Option.objects.create(question=q1, option_text="42", is_correct=True)
        Option.objects.create(question=q1, option_text="52", is_correct=False)
        Option.objects.create(question=q1, option_text="62", is_correct=False)
        
        q2 = Question.objects.create(
            quiz=math_quiz,
            question_text="What is the value of π (pi) approximately?",
            marks=1
        )
        Option.objects.create(question=q2, option_text="3.14", is_correct=True)
        Option.objects.create(question=q2, option_text="2.71", is_correct=False)
        Option.objects.create(question=q2, option_text="1.61", is_correct=False)
        Option.objects.create(question=q2, option_text="4.20", is_correct=False)
        
        # Create Science Quiz
        science_quiz = Quiz.objects.create(
            title="General Science Quiz",
            subject=science_subject,
            student_class="10th Grade",
            description="Test your knowledge of general science",
            time_limit=20,
            is_active=True
        )
        
        # Science Questions
        q3 = Question.objects.create(
            quiz=science_quiz,
            question_text="What is the chemical symbol for water?",
            marks=1
        )
        Option.objects.create(question=q3, option_text="H2O", is_correct=True)
        Option.objects.create(question=q3, option_text="CO2", is_correct=False)
        Option.objects.create(question=q3, option_text="O2", is_correct=False)
        Option.objects.create(question=q3, option_text="NaCl", is_correct=False)
        
        q4 = Question.objects.create(
            quiz=science_quiz,
            question_text="Which planet is known as the Red Planet?",
            marks=1
        )
        Option.objects.create(question=q4, option_text="Earth", is_correct=False)
        Option.objects.create(question=q4, option_text="Mars", is_correct=True)
        Option.objects.create(question=q4, option_text="Jupiter", is_correct=False)
        Option.objects.create(question=q4, option_text="Venus", is_correct=False)
        
        self.stdout.write(
            self.style.SUCCESS('Successfully loaded sample data')
        )