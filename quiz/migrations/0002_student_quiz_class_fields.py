from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('quiz', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='student',
            name='student_class',
            field=models.CharField(blank=True, max_length=100, null=True),
        ),
        migrations.AddField(
            model_name='quiz',
            name='student_class',
            field=models.CharField(blank=True, max_length=100, null=True),
        ),
    ]
