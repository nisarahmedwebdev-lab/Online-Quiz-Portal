import re
from django.core.management.base import BaseCommand
from quiz.models import Student, Quiz

NORMALIZE_PATTERN = re.compile(r'[^A-Za-z0-9]+')


def normalize_class_value(value):
    if not value:
        return value
    normalized = NORMALIZE_PATTERN.sub('_', value).strip('_')
    return normalized


class Command(BaseCommand):
    help = 'Normalize student and quiz class names by replacing separators with underscores.'

    def handle(self, *args, **options):
        student_updates = 0
        quiz_updates = 0

        self.stdout.write('Normalizing Student.student_class values...')
        for student in Student.objects.exclude(student_class__isnull=True).exclude(student_class__exact=''):
            original = student.student_class
            normalized = normalize_class_value(original)
            if normalized != original:
                student.student_class = normalized
                student.save(update_fields=['student_class'])
                student_updates += 1
                self.stdout.write(f'Updated Student {student.roll_number}: "{original}" -> "{normalized}"')

        self.stdout.write('Normalizing Quiz.student_class values...')
        for quiz in Quiz.objects.exclude(student_class__isnull=True).exclude(student_class__exact=''):
            original = quiz.student_class
            normalized = normalize_class_value(original)
            if normalized != original:
                quiz.student_class = normalized
                quiz.save(update_fields=['student_class'])
                quiz_updates += 1
                self.stdout.write(f'Updated Quiz {quiz.id}: "{original}" -> "{normalized}"')

        self.stdout.write(self.style.SUCCESS(
            f'Normalization complete. Students updated: {student_updates}, Quizzes updated: {quiz_updates}.'
        ))
