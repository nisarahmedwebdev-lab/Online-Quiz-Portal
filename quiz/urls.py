from django.urls import path
from . import views

urlpatterns = [
    path('', views.home, name='home'),
    path('login/', views.student_login, name='student_login'),
    path('logout/', views.student_logout, name='student_logout'),
    path('quizzes/', views.quiz_list, name='quiz_list'),
    path('subject/<int:subject_id>/', views.subject_quizzes, name='subject_quizzes'),
    path('quiz/<int:quiz_id>/', views.take_quiz, name='take_quiz'),
    path('submitted/', views.quiz_submitted, name='quiz_submitted'),
]