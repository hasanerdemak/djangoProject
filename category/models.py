from django.db import models

from dealership.models import Dealership


# Create your models here.
class Category(models.Model):
    name = models.CharField(max_length=50, verbose_name="Category Name")

    def __str__(self):
        return self.name


class AssociatedCategory(models.Model): # related_name associated_categories
    dealership = models.ForeignKey(Dealership, on_delete=models.DO_NOTHING, verbose_name="Dealership",
                                   related_name="ac_dealership")
    category = models.ForeignKey(Category, on_delete=models.DO_NOTHING, verbose_name="Category",
                                 related_name="ac_category")

    class Meta:
        unique_together = (('dealership',
                            'category'),)

    def __str__(self):
        return self.dealership.name + " - " + self.category.name
