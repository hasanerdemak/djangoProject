from django.db import models

from dealership.models import Dealership


# Create your models here.
class Category(models.Model):
    name = models.CharField(max_length=50, verbose_name="Category Name")

    def __str__(self):
        return self.name


class AssociatedCategory(models.Model):
    dealership = models.ForeignKey(Dealership, on_delete=models.CASCADE, verbose_name="Dealership")
    category = models.ForeignKey(Category, on_delete=models.CASCADE, verbose_name="Category")

    class Meta:
        unique_together = (('dealership',
                            'category'),)

    def __str__(self):
        return self.dealership.name + " - " + self.category.name
