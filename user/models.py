from django.db import models
from django.contrib.auth.models import User
from dealership.models import Dealership


# from django.conf import settings
# settings.AUTH_USER_MODEL

class UserProfile(models.Model):
    user = models.ForeignKey(User, on_delete=models.DO_NOTHING, verbose_name="User", related_name="user_profiles",
                             blank=True, null=True)
    dealership = models.ForeignKey(Dealership, on_delete=models.DO_NOTHING, verbose_name="Dealership",
                                   related_name="user_profiles", blank=True, null=True)
    is_active = models.BooleanField(verbose_name="is_active", default=True)

    @property
    def dealership_name(self):
        return self.dealership.name

    @property
    def username(self):
        return self.user.username

    @property
    def first_name(self):
        return self.user.first_name

    @property
    def last_name(self):
        return self.user.last_name

    @property
    def email(self):
        return self.user.email

    def property_names(self):
        return self._meta._property_names

    class Meta:
        unique_together = ('user', 'dealership')

    def __str__(self):
        return f"{self.user.username} - {self.dealership.name}"
