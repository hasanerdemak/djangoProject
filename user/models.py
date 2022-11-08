import sys

from django.db import models
from django.contrib.auth.models import User

sys.path.append('/Users/hasanerdemak/PycharmProjects/djangoProject')
from dealership.models import Dealership


class UserProfile(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    dealership = models.ForeignKey(Dealership, on_delete=models.CASCADE)
    dealership_name = models.CharField(max_length=50, verbose_name="Dealership Name", null=False, blank=False)
    is_active = models.BooleanField(verbose_name="Is Active")
    first_name = models.CharField(max_length=50, verbose_name="First Name", null=False, blank=False)
    last_name = models.CharField(max_length=50, verbose_name="Last Name", null=False, blank=False)
    email = models.CharField(max_length=50, verbose_name="Email", null=False, blank=False)

    class Meta:
        unique_together = (('user', 'dealership'),)

    def __str__(self):
        return self.user.username + " - " + self.dealership.name
