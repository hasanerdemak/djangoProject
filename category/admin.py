from django.contrib import admin

from category.models import Category, AssociatedCategory

admin.site.register(Category)
admin.site.register(AssociatedCategory)
