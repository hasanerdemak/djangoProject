from django.db import models
from dealership.models import Dealership


class Category(models.Model):
    name = models.CharField(max_length=50, verbose_name="Category Name")

    def __str__(self):
        return f"{self.name}"


class AssociatedCategory(models.Model):
    dealership = models.ForeignKey(Dealership, on_delete=models.CASCADE, verbose_name="Dealership",
                                   related_name="associated_categories")
    category = models.ForeignKey(Category, on_delete=models.CASCADE, verbose_name="Category",
                                 related_name="associated_categories")

    class Meta:
        unique_together = (('dealership', 'category'),)

    def __str__(self):
        return f"{self.dealership.name} - {self.category.name}"
