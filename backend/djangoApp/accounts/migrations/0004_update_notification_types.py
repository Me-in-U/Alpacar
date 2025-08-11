# Generated for updated Notification types

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('accounts', '0003_notification'),
    ]

    operations = [
        migrations.AlterField(
            model_name='notification',
            name='notification_type',
            field=models.CharField(
                choices=[
                    ('vehicle_entry', '입차 알림'),
                    ('parking_complete', '주차 완료'),
                    ('grade_upgrade', '등급 승급'),
                    ('system', '시스템'),
                    ('maintenance', '점검')
                ],
                default='system',
                max_length=20,
                verbose_name='알림 종류'
            ),
        ),
    ]