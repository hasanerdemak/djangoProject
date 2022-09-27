import sys

from django.contrib.admin import forms
from django.contrib.admin.widgets import FilteredSelectMultiple
from django.db import models

# Create your models here.

from django.db import models
from django.contrib.auth.models import User

sys.path.append('/Users/hasanerdemak/PycharmProjects/djangoProject')
from dealership.models import Dealership


# Create your models here.

class UserProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name="userprofile_user_id")
    dealership = models.OneToOneField(Dealership, on_delete=models.CASCADE, related_name="userprofile_dealership_id")
    isActive = models.BooleanField(verbose_name="Is Active")
    firstName = models.CharField(max_length=50, verbose_name="First Name", null=False, blank=False)
    lastName = models.CharField(max_length=50, verbose_name="Last Name", null=False, blank=False)
    email = models.CharField(max_length=50, verbose_name="Email", null=False, blank=False)

    def __str__(self):
        return self.user.username

