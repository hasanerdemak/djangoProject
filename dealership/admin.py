from django.contrib import admin
from django.http import HttpResponseRedirect
from django.shortcuts import redirect
from django.template.response import TemplateResponse
from django.urls import re_path

from category.models import AssociatedCategory
from .forms import DealershipForm
from .models import Dealership, DealershipGroup


class AssociatedCategoryInline(admin.StackedInline):
    model = AssociatedCategory
    verbose_name_plural = "Associated Categories"
    extra = 1


class DealershipAdmin(admin.ModelAdmin):
    change_list_template = "dealership/my_dealership_change_list.html"
    inlines = [AssociatedCategoryInline]

    class Meta:
        model = Dealership

    def get_urls(self):
        urls = super().get_urls()
        my_urls = [
            re_path(r'^updateDealerships$', self.admin_site.admin_view(self.check_buttons), name='updateDealerships'),
        ]
        return my_urls + urls

    def check_buttons(self, request, obj=None, **kwargs):
        get_field_button = request.POST.get("get-fields-button")
        update_button = request.POST.get("update-button")

        if get_field_button is None and update_button is None:  # Page first opened
            are_fields_taken = False
            selected_dealerships_list = []
            selected_fields_list = []
            form = None
        elif update_button is None:  # Get Fields button is clicked.
            are_fields_taken = True
            selected_dealerships_list = request.POST.get("select-dealership").split(',')
            selected_fields_list = request.POST.get("select-field").split(',')
            # Create form after selecting dealerships and fields
            form = DealershipForm(show_fields=selected_fields_list)
        else:  # Update Edited Fields button is clicked.
            return self.update_dealerships(request)  # update

        context = {"dealership_opts": DealershipGroup.objects.prefetch_related('dealerships').all(),
                   "field_opts": Dealership._meta.fields,
                   "form": form,
                   "selected_dealerships": selected_dealerships_list,
                   "selected_fields": selected_fields_list,
                   "are_fields_taken": are_fields_taken,
                   }

        return TemplateResponse(request, "dealership/dealership_edit.html", context)

    @staticmethod
    def update_dealerships(request):
        if request.method == "GET":
            return redirect("/admin/dealership/dealership")
            # return HttpResponseRedirect("../../")
        else:  # POST
            selected_fields_list = request.POST.get("select-field").split(',')
            selected_dealerships_list = request.POST.get("select-dealership").split(',')

            try:
                dealerships = Dealership.objects.filter(id__in=selected_dealerships_list)
                for selected_field in selected_fields_list:
                    if selected_field == "category":
                        associated_category_list = []
                        dealerships_ids_list = list(dealerships.values_list("id", flat=True))
                        AssociatedCategory.objects.filter(dealership_id__in=dealerships_ids_list).delete()
                        selected_categories = request.POST.get('category').split(',')
                        for dealership_id in dealerships_ids_list:
                            for category_id in selected_categories:
                                associated_category_list.append(
                                    AssociatedCategory(dealership_id=dealership_id, category_id=int(category_id)))
                        AssociatedCategory.objects.bulk_create(associated_category_list)
                    else:
                        dealerships.update(**{selected_field: request.POST.get(selected_field)})
            except Exception as e:
                print(e)

            # return HttpResponseRedirect("../dealership")
            return redirect("/admin/dealership/dealership")


admin.site.register(Dealership, DealershipAdmin)
admin.site.register(DealershipGroup)
