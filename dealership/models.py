from django.db import models


class DealershipGroup(models.Model):
    name = models.CharField(max_length=50, verbose_name="Name")

    def __str__(self):
        return f"{self.name}"

#Todo add new fields for demo
class Dealership(models.Model):
    group = models.ForeignKey(DealershipGroup, related_name='dealerships', on_delete=models.DO_NOTHING,
                              verbose_name="Dealership Group", blank=True, null=True)
    name = models.CharField(max_length=50, verbose_name="Name")

    def __str__(self):
        return f"{self.name}"
