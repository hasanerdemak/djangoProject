import io

from django.contrib import admin
from django.http import HttpResponseRedirect
from django.template.response import TemplateResponse
from django.urls import path

from .forms import DealershipForm
from .models import Dealership, DealershipGroup


# Register your models here.

class DealershipAdmin(admin.ModelAdmin):
    change_list_template = "my_change_list.html"
    class Meta:
        model = Dealership

    def get_urls(self):
        urls = super().get_urls()
        my_urls = [
            path('updateDealerships/', self.check_input),
            path('updateDealerships/updateDealerships/', self.update_dealerships),
        ]
        return my_urls + urls

    def get_model_fields(self, model):
        return model._meta.fields

    def check_input(self, request, obj=None, **kwargs):
        # fill multiselect lists
        dealership_groups = DealershipGroup.objects.all()
        dealership_opts = []
        for dealership_group in dealership_groups:
            dealership_ids_and_names_list = list(
                Dealership.objects.filter(group_id=dealership_group.id).values_list('id', 'name'))
            if len(dealership_ids_and_names_list) != 0:
                dealership_group_dict = {"label": dealership_group.name, "options": []}
                for dealership_id, dealership_name in dealership_ids_and_names_list:
                    dealership_dict = {"label": dealership_name, "value": dealership_id}
                    dealership_group_dict["options"].append(dealership_dict)
                dealership_opts.append(dealership_group_dict)
        """dealership_dict = dict()
        for dealership_group in dealership_groups:
            dealerships_list = list(Dealership.objects.filter(group_id=dealership_group.id).values_list('name', flat=True))
            if len(dealerships_list) != 0:
                dealership_dict[dealership_group.name] = dealerships_list
        """

        field_opts = []
        for index, field in enumerate(self.get_model_fields(Dealership)):
            if index != 0:
                field_dict = {"label": field.verbose_name, "value": field.name}
                field_opts.append(field_dict)
        """field_dict = dict()
        for index, field in enumerate(self.get_model_fields(Dealership)):
            if index != 0:
                field_dict[field.name] = field.verbose_name"""

        selected_fields = request.POST.get("fields")
        selected_dealerships = request.POST.get("dealerships")

        if selected_dealerships is None or len(selected_dealerships) == 0 or \
                selected_fields is None or len(selected_fields) == 0:
            context = {"dealership_opts": dealership_opts,
                       "field_opts": field_opts,
                       "form": None,
                       "selected_dealerships": [],
                       "selected_fields": [],
                       "non_unique_rows": None,
                       "non_unique_cols": None,
                       "show_table": 'false',
                       "fields_taken": False,
                       "error": "Please select both dealerships and fields"}
            return TemplateResponse(request, "dealership_edit.html", context)

        selected_dealerships_list = selected_dealerships.split(',')
        selected_fields_list = selected_fields.split(',')
        form = DealershipForm(show_fields=selected_fields_list)

        context = {"dealership_opts": dealership_opts,
                   "field_opts": field_opts,
                   "form": form,
                   "selected_dealerships": selected_dealerships_list,
                   "selected_fields": selected_fields_list,
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
            selected_fields_list = request.POST.get("fields").split(',')
            selected_dealerships_list = request.POST.get("dealerships").split(',')

            dealerships = Dealership.objects.filter(id__in=selected_dealerships_list)
            for selected_field in selected_fields_list:
                dealerships.update(**{selected_field: request.POST.get(selected_field)})

            return HttpResponseRedirect("../../")


admin.site.register(Dealership, DealershipAdmin)
admin.site.register(DealershipGroup)
