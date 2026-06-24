from django.db import models
from django.contrib.auth.models import User

class AdminSettings(models.Model):
    site_name = models.CharField(max_length=100, default="Online Quiz Portal")
    site_description = models.TextField(blank=True)
    max_quiz_time = models.IntegerField(default=30, help_text="Maximum time limit for quizzes in minutes")
    allow_retakes = models.BooleanField(default=False)
    show_results_to_students = models.BooleanField(default=False)
    maintenance_mode = models.BooleanField(default=False)
    
    class Meta:
        verbose_name_plural = "Admin Settings"
    
    def __str__(self):
        return "System Settings"

class SystemLog(models.Model):
    LOG_TYPES = [
        ('INFO', 'Information'),
        ('WARNING', 'Warning'),
        ('ERROR', 'Error'),
        ('SUCCESS', 'Success'),
    ]
    
    log_type = models.CharField(max_length=10, choices=LOG_TYPES)
    message = models.TextField()
    timestamp = models.DateTimeField(auto_now_add=True)
    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    
    def __str__(self):
        return f"{self.log_type} - {self.message[:50]}"