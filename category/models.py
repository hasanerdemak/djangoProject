from django.db import models

from dealership.models import Dealership


# Create your models here.
class Category(models.Model):
    name = models.CharField(max_length=50, verbose_name="Category Name")

    def __str__(self):
        return f"{self.name}"


class AssociatedCategory(models.Model):
    dealership = models.ForeignKey(Dealership, on_delete=models.DO_NOTHING, verbose_name="Dealership",
                                   related_name="dealerships")
    category = models.ForeignKey(Category, on_delete=models.DO_NOTHING, verbose_name="Category",
                                 related_name="categories")

    class Meta:
        unique_together = (('dealership',
                            'category'),)

    def __str__(self):
        return f"{self.dealership.name} - {self.category.name}"
