from django.contrib import admin
from django.http import HttpResponseRedirect
from django.template.response import TemplateResponse
from django.urls import path

from category.models import AssociatedCategory
from .forms import DealershipForm
from .models import Dealership, DealershipGroup


class AssociatedCategoryInline(admin.StackedInline):
    model = AssociatedCategory
    verbose_name_plural = "Associated Categories"
    extra = 1


class DealershipAdmin(admin.ModelAdmin):
    change_list_template = "dealership/my_change_list.html"
    inlines = [AssociatedCategoryInline]

    class Meta:
        model = Dealership

    def get_urls(self):
        urls = super().get_urls()
        my_urls = [
            path('updateDealerships', self.check_buttons),
            # path('updateDealerships/updateDealerships/', self.update_dealerships),
        ]
        return my_urls + urls

    def check_buttons(self, request, obj=None, **kwargs):
        get_field_button = request.POST.get("get-fields-button")
        update_button = request.POST.get("update-button")
        form = None
        selected_dealerships_list = []
        selected_fields_list = []

        if get_field_button is None and update_button is None:  # Page first open
            dealership_opts, field_opts = self.get_select_lists_opts()
            fields_taken = False
        elif update_button is None:  # Get Fields button is clicked.
            dealership_opts, field_opts = self.get_select_lists_opts()
            fields_taken = True
            # Create form after selecting dealerships and fields
            form = self.create_form(request)
            selected_dealerships_list = request.POST.get("dealerships").split(',')
            selected_fields_list = request.POST.get("fields").split(',')
        else:  # Update Edited Fields button is clicked.
            return self.update_dealerships(request)  # update

        context = {"dealership_opts": dealership_opts,
                   "field_opts": field_opts,
                   "form": form,
                   "selected_dealerships": selected_dealerships_list,
                   "selected_fields": selected_fields_list,
                   "fields_taken": fields_taken
                   }

        return TemplateResponse(request, "dealership/dealership_edit.html", context)

    def get_select_lists_opts(self):
        dealerships = Dealership.objects.select_related("group").all()
        dealerships2 = AssociatedCategory.objects.select_related('dealership', 'category', 'dealership__group').all()

        dealership_opts = []
        for dealership in dealerships:  # !!!!!!!!!!!! select2
            does_group_find = False
            dealership_dict = {"label": dealership.name, "value": dealership.id}
            for dealership_opt in dealership_opts:
                if dealership_opt["label"] == dealership.group.name:
                    does_group_find = True
                    dealership_opt["options"].append(dealership_dict)
            if not does_group_find:
                dealership_group_dict = {"label": dealership.group.name, "options": [dealership_dict]}
                dealership_opts.append(dealership_group_dict)

        dealership_opts.sort(key=self.get_group_name)

        # select2

        """[{'label': 'DG 1', 'options': [{'label': 'D 1', 'value': 5}]},
            {'label': 'DG 2', 'options': [{'label': 'Toyota 1', 'value': 2}]}, 
            {'label': 'DG 3', 'options': [{'label': 'Ford 1', 'value': 1}, {'label': 'Tesla 1', 'value': 3}, {'label': 'Hyundai 1', 'value': 4}]}]"""

        field_opts = []
        for index, field in enumerate(Dealership._meta.fields):
            if index != 0:
                field_dict = {"label": field.verbose_name, "value": field.name}
                field_opts.append(field_dict)
        field_opts.append({"label": 'Category', "value": 'category'})

        return dealership_opts, field_opts

    def create_form(self, request):
        selected_fields_list = request.POST.get("fields").split(',')
        form = DealershipForm(show_fields=selected_fields_list)

        return form

    def get_group_name(self, dealership_group):
        return dealership_group.get('label')

    def update_dealerships(self, request):
        if request.method == "GET":
            return HttpResponseRedirect("../../")
        else:  # POST
            selected_fields_list = request.POST.get("fields").split(',')
            selected_dealerships_list = request.POST.get("dealerships").split(',')
            print(selected_dealerships_list)
            print(selected_fields_list)
            associated_category_list = []

            try:
                dealerships = Dealership.objects.filter(id__in=selected_dealerships_list)
                for selected_field in selected_fields_list:
                    if selected_field == "category":
                        dealerships_ids_list = list(dealerships.values_list("id", flat=True))
                        AssociatedCategory.objects.filter(dealership_id__in=dealerships_ids_list).delete()
                        selected_categories = request.POST.getlist('category')
                        for dealership_id in dealerships_ids_list:
                            for category in selected_categories:
                                associated_category_list.append(
                                    AssociatedCategory(dealership_id=dealership_id, category_id=int(category)))
                        AssociatedCategory.objects.bulk_create(associated_category_list)
                    else:
                        dealerships.update(**{selected_field: request.POST.get(selected_field)})
            except Exception as e:
                print(f"Exception Happened for {associated_category_list} | {e}")

            return HttpResponseRedirect("../dealership")


admin.site.register(Dealership, DealershipAdmin)
admin.site.register(DealershipGroup)
