from django.db import models
from dealership.models import Dealership


class Category(models.Model):
    name = models.CharField(max_length=50, verbose_name="Category Name")

    def __str__(self):
        return f"{self.name}"


# Todo Do_nothing
class AssociatedCategory(models.Model):
    dealership = models.ForeignKey(Dealership, on_delete=models.DO_NOTHING, verbose_name="Dealership",
                                   related_name="associated_categories", blank=True, null=True)
    category = models.ForeignKey(Category, on_delete=models.DO_NOTHING, verbose_name="Category",
                                 related_name="associated_categories", blank=True, null=True)
    is_active = models.BooleanField(verbose_name="is_active", default=True)

    class Meta:
        unique_together = ('dealership', 'category')

    def __str__(self):
        return f"{self.dealership.name} - {self.category.name} - {self.is_active}"
