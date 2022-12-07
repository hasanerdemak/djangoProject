from django.contrib import admin

from category.models import Category, AssociatedCategory


class AssociatedCategoryAdmin(admin.ModelAdmin):
    def get_queryset(self, request):
        query = super(AssociatedCategoryAdmin, self).get_queryset(request)
        filtered_query = query.filter(is_active=True)
        return filtered_query


admin.site.register(Category)
admin.site.register(AssociatedCategory, AssociatedCategoryAdmin)
