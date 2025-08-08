# Generated manually for Notification model

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('accounts', '0002_verificationcode'),
    ]

    operations = [
        migrations.CreateModel(
            name='Notification',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('title', models.CharField(max_length=100, verbose_name='알림 제목')),
                ('message', models.TextField(verbose_name='알림 내용')),
                ('notification_type', models.CharField(choices=[('parking_complete', '주차 완료'), ('grade_upgrade', '등급 승급'), ('system', '시스템'), ('maintenance', '점검')], default='system', max_length=20, verbose_name='알림 종류')),
                ('data', models.JSONField(blank=True, default=dict, verbose_name='추가 데이터')),
                ('is_read', models.BooleanField(default=False, verbose_name='읽음 상태')),
                ('created_at', models.DateTimeField(auto_now_add=True, verbose_name='생성일시')),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='notifications', to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'verbose_name': '알림',
                'verbose_name_plural': '알림',
                'db_table': 'accounts_notification',
                'ordering': ['-created_at'],
            },
        ),
    ]