from django.contrib import admin
from .models import Subject, Student, Quiz, Question, Option, QuizAttempt, StudentAnswer

class OptionInline(admin.TabularInline):
    model = Option
    extra = 4

class QuestionAdmin(admin.ModelAdmin):
    inlines = [OptionInline]
    list_display = ['question_text', 'quiz', 'marks']
    list_filter = ['quiz']

class QuestionInline(admin.TabularInline):
    model = Question
    extra = 1

class QuizAdmin(admin.ModelAdmin):
    inlines = [QuestionInline]
    list_display = ['title', 'subject', 'time_limit', 'is_active']
    list_filter = ['subject', 'is_active']

class StudentAnswerInline(admin.TabularInline):
    model = StudentAnswer
    readonly_fields = ['question', 'selected_option']
    can_delete = False
    extra = 0

class QuizAttemptAdmin(admin.ModelAdmin):
    list_display = ['student', 'quiz', 'started_at', 'submitted_at', 'score', 'total_marks']
    list_filter = ['quiz', 'started_at']
    readonly_fields = ['started_at', 'submitted_at']
    inlines = [StudentAnswerInline]
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('student', 'quiz')

admin.site.register(Subject)
admin.site.register(Student)
admin.site.register(Quiz, QuizAdmin)
admin.site.register(Question, QuestionAdmin)
admin.site.register(QuizAttempt, QuizAttemptAdmin)