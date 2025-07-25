# accounts/models.py
from django.db import models


class Member(models.Model):
    name = models.CharField(max_length=50)
    nickname = models.CharField(max_length=50)
    email = models.EmailField(unique=True)
    password_hash = models.CharField(max_length=128)
    phone = models.CharField(max_length=20)
    plate_number = models.CharField(max_length=20, unique=True)
    push_enabled = models.BooleanField(default=False)

    def __str__(self):
        return f"{self.nickname} <{self.email}>"


class PushSubscription(models.Model):
    user = models.ForeignKey(Member, on_delete=models.CASCADE)
    endpoint = models.URLField()
    p256dh = models.CharField(max_length=255)
    auth = models.CharField(max_length=255)
