from django.db import models


class DealershipGroup(models.Model):
    name = models.CharField(max_length=50, verbose_name="Name")

    def __str__(self):
        return f"{self.name}"


class Dealership(models.Model):
    group = models.ForeignKey(DealershipGroup, related_name='dealerships', on_delete=models.DO_NOTHING,
                              verbose_name="Dealership Group", blank=True, null=True)
    name = models.CharField(max_length=50, verbose_name="Name")
    country = models.CharField(max_length=50, verbose_name="Country", blank=True, null=True)
    city = models.CharField(max_length=50, verbose_name="City", blank=True, null=True)
    post_code = models.CharField(max_length=10, verbose_name="Post Code", blank=True, null=True)
    website = models.URLField(max_length=200, verbose_name="Website", blank=True, null=True)

    def __str__(self):
        return f"{self.name}"
