import io

from django.contrib import admin
from django.http import HttpResponseRedirect
from django.template.response import TemplateResponse
from django.urls import path

from .forms import DealershipForm
from .models import Dealership, DealershipGroup


# Register your models here.

class DealershipAdmin(admin.ModelAdmin):
    class Meta:
        model = Dealership

    def get_urls(self):
        urls = super().get_urls()
        my_urls = [
            path('add/', self.check_input),
            path('add/updateDealerships/', self.update_dealerships),
        ]
        return my_urls + urls

    def get_model_fields(self, model):
        return model._meta.fields

    def check_input(self, request, obj=None, **kwargs):
        context = {"dealership_dict": None,
                   "field_dict": None,
                   "form": None,
                   "non_unique_rows": None,
                   "non_unique_cols": None,
                   "show_table": 'false',
                   "fields_taken": True,
                   "error": None}

        dealership_dict = {
            "DG 1": [
                "D1", "D2"
            ],
            "DG 2": [
                "D3", "D4"
            ],
            "DG 3": [
                "D5", "D6"
            ],
            "DG 4": [
                "D7", "D8", "D9"
            ]
        }

        field_dict = dict()
        for index, field in enumerate(self.get_model_fields(Dealership)):
            if index != 0:
                field_dict[field.name] = field.verbose_name

        fields = request.POST.get("fields")
        dealerships = request.POST.get("dealerships")

        if dealerships is None or len(dealerships) == 0 or fields is None or len(fields) == 0:
            context = {"dealership_dict": dealership_dict,
                       "field_dict": field_dict,
                       "form": None,
                       "non_unique_rows": None,
                       "non_unique_cols": None,
                       "show_table": 'false',
                       "fields_taken": True,
                       "error": None}
            return TemplateResponse(request, "dealership_edit.html", context)

        form = DealershipForm(show_fields=fields.split(','))

        context = {"dealership_dict": dealership_dict,
                   "field_dict": field_dict,
                   "form": form,
                   "non_unique_rows": None,
                   "non_unique_cols": None,
                   "show_table": 'false',
                   "fields_taken": True,
                   "error": None}

        return TemplateResponse(request, "dealership_edit.html", context)

    def update_dealerships(self, request, obj=None, **kwargs):
        if request.method == "GET":
            return HttpResponseRedirect("../../")
        else:  # POST

            text = request.POST.get("formTextArea")

            # self.update_dealership(user_profile_table, exist_dealership_ids)

            return HttpResponseRedirect("..")

    """
    def update_dealerships(self, user_profile_table, exist_dealership_ids):
    
        try:
    
            updatable_objects = Dealership.objects.filter(id__in=list(user_profile_table['dealership'][exist_dealership_ids]))
            Util = Utils()
            exist_dealership_ids = Util.reorder_list(updatable_objects, user_profile_table, "Dealership")
            for dealership, dealership_index in zip(updatable_objects, exist_dealership_ids):
                dealership.name = user_profile_table['dealershipName'][dealership_index]
                dealership.save()
        except Exception as e:
            print(f"Exception Happened for {updatable_objects} | {e}")
        return ""
    """


admin.site.register(Dealership, DealershipAdmin)
admin.site.register(DealershipGroup)
