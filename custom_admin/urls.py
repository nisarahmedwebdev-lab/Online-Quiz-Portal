from django.urls import path
from . import views

urlpatterns = [
    path('login/', views.custom_admin_login, name='custom_admin_login'),
    path('logout/', views.custom_admin_logout, name='custom_admin_logout'),
    path('', views.custom_admin_dashboard, name='custom_admin_dashboard'),
    path('normalize-class-names/', views.normalize_class_names, name='normalize_class_names'),
    
    # Management URLs
    path('subjects/', views.manage_subjects, name='manage_subjects'),
    path('subjects/edit/<int:subject_id>/', views.edit_subject, name='edit_subject'),
    path('subjects/delete/<int:subject_id>/', views.delete_subject, name='delete_subject'),
    
    path('students/', views.manage_students, name='manage_students'),
    path('students/edit/<int:student_id>/', views.edit_student, name='edit_student'),
    path('students/delete/<int:student_id>/', views.delete_student, name='delete_student'),
    
    path('quizzes/', views.manage_quizzes, name='manage_quizzes'),
    path('quizzes/edit/<int:quiz_id>/', views.edit_quiz, name='edit_quiz'),
    path('quizzes/delete/<int:quiz_id>/', views.delete_quiz, name='delete_quiz'),
    
    path('questions/', views.manage_questions, name='manage_questions'),
    path('questions/quiz/<int:quiz_id>/', views.manage_questions, name='manage_quiz_questions'),
    path('questions/edit/<int:question_id>/', views.edit_question, name='edit_question'),
    path('questions/delete/<int:question_id>/', views.delete_question, name='delete_question'),
    
    path('options/<int:question_id>/', views.manage_options, name='manage_options'),
    path('options/edit/<int:option_id>/', views.edit_option, name='edit_option'),
    path('options/delete/<int:option_id>/', views.delete_option, name='delete_option'),
    
    # Results and Analytics
    path('results/', views.view_results, name='view_results'),
    path('results/attempt/<int:attempt_id>/', views.view_attempt_detail, name='view_attempt_detail'),
    
    # Download URLs
    path('results/download/csv/', views.download_results_csv, name='download_results_csv'),
    path('results/download/excel/', views.download_results_excel, name='download_results_excel'),
    path('students/download/', views.download_student_list, name='download_student_list'),
    
    # Bulk Upload URLs
    path('bulk-upload/', views.bulk_quiz_upload, name='bulk_quiz_upload'),
    path('quick-add/', views.quick_question_add, name='quick_question_add'),
    path('download-template/<str:format_type>/', views.download_quiz_template, name='download_quiz_template'),
    
    # System
    path('settings/', views.system_settings, name='system_settings'),
    path('logs/', views.system_logs, name='system_logs'),
    
    # API for charts
    path('api/chart-data/', views.get_chart_data, name='get_chart_data'),
]