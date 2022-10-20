from django.db import models


# Create your models here.


class DealershipGroup(models.Model):
    name = models.CharField(max_length=50, verbose_name="Name")

    def __str__(self):
        return self.name


class Dealership(models.Model):
    group = models.ForeignKey(DealershipGroup, on_delete=models.CASCADE, verbose_name="Group")
    name = models.CharField(max_length=50, verbose_name="Name")

    def __str__(self):
        return self.name
