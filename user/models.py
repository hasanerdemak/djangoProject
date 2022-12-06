from django.db import models
from django.contrib.auth.models import User
from dealership.models import Dealership


class UserProfile(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, verbose_name="User", related_name="user_profiles")
    dealership = models.ForeignKey(Dealership, on_delete=models.CASCADE, verbose_name="Dealership",
                                   related_name="user_profiles")

    @property
    def dealership_name(self):
        return self.dealership.name

    @property
    def is_active(self):
        return self.user.is_active

    @property
    def first_name(self):
        return self.user.first_name

    @property
    def last_name(self):
        return self.user.last_name

    @property
    def email(self) -> models.EmailField:
        return self.user.email

    def property_names(self):
        return self._meta._property_names

    class Meta:
        unique_together = (('user', 'dealership'),)

    def __str__(self):
        return f"{self.user.username} - {self.dealership.name}"
