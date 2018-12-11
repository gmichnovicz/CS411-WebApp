from django.db import models
# users/models.py
from django.contrib.auth.models import AbstractUser, UserManager

class CustomUserManager(UserManager):
    pass

class CustomUser(AbstractUser):
    objects = CustomUserManager()
    location = models.CharField(max_length=30, blank=True)
    spotifyid = models.CharField(max_length=30, blank=True)

    def publish(self):
        self.added_date = timezone.now()
        self.save()
    