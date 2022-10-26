from django.contrib import admin

from category.models import Category, AssociatedCategory

# Register your models here.

admin.site.register(Category)
admin.site.register(AssociatedCategory)
