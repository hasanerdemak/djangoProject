from http.client import HTTPResponse

from django.contrib import admin
from django.urls import path

from dealership.models import Dealership
from .models import UserProfile
from django import forms
from django.http import HttpResponseRedirect


class UserProfileForm(forms.ModelForm):
    extra_field = forms.CharField()

    def save(self, commit=True):
        extra_field = self.cleaned_data.get('extra_field', None)

        # Do something with extra_field here

        return super().save(commit=commit)


# Register your models here.
@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    list_display = ["user", "dealership"]
    # fields = ("user", "dealership")
    form = UserProfileForm
    change_list_template = "admin/changelist.html"
    class Meta:
        model = UserProfile

    '''def get_form(self, request, obj=None, change=False, **kwargs):
        form = super(UserProfileAdmin, self).get_form(request,obj,**kwargs)
        return form'''
    def get_urls(self):
        urls = super().get_urls()
        my_urls = [
            path('import/',self.set_data_onclick)
        ]
        return my_urls + urls
    def set_data_onclick(self,request):
        print(self.model.objects.all())
        value = request.POST.get('text-value')
        print(value)
        return HttpResponseRedirect("../")
    """def get_urls(self):
        urls = super().get_urls()
        my_urls = [
            path('add/', self.my_view),
        ]
        return my_urls + urls

    def my_view(self, request):
        # ...
        context = dict(
            # Include common variables for rendering the admin template.
            self.admin_site.each_context(request),
            # Anything else you want in the context...

        )
        return TemplateResponse(request, "user.admin", context)

    def addUserProfile(request):
        if request.method == "GET":
            return redirect("index")  # go to home page
        else:  # POST
            users = request.POST.get("users")
            print(users.username)
            """"""dealerships = request.POST.get("dealerships")
            try:
                newUserProfile = UserProfile.objects.create(users, dealerships, isActive=True, firstName=users.username, lastName="", email="@")
            except:
                print("hata")

            newUserProfile.save()""""""
            return redirect("index")  # go to home page

    def save_model(self, request, obj, form, change):
        print(request)
        print(obj)
        print(obj.user)
        print(obj.firstName)
        print(obj.lastName)
        obj.user = request.user
        obj.dealership = obj.dealership
        obj.isActive = True
        obj.firstName = obj.user.firstName
        obj.lastName = obj.user.lastName
        obj.email = obj.user.email

        super().save_model(request, obj, form, change)"""


"""class UserProfileAdminForm(ModelForm):
    users = ModelMultipleChoiceField(queryset=User.objects.all(),
                                           widget=FilteredSelectMultiple('Users', False),
                                           required=False)
    dealership = ModelMultipleChoiceField(queryset=Dealership.objects.all(),
                                                widget=FilteredSelectMultiple('Dealership', False),
                                                required=False)

    class Meta:
        model = UserProfile

    def __init__(self, *args, **kwargs):
        instance = kwargs.get('instance', None)
        if instance is not None:
            initial = kwargs.get('initial', {})
            initial['users'] = instance.user_set.all()
            initial['locations'] = instance.c_locations.all()
            kwargs['initial'] = initial
        super(UserProfileAdminForm, self).__init__(*args, **kwargs)

    def save(self, commit=True):
        group = super(UserProfileAdminForm, self).save(commit=commit)

        if commit:
            group.user_set = self.cleaned_data['users']
            group.locations = self.cleaned_data['locations']
        else:
            old_save_m2m = self.save_m2m

            def new_save_m2m():
                old_save_m2m()
                group.user_set = self.cleaned_data['users']
                group.location_set = self.cleaned_data['locations']

            self.save_m2m = new_save_m2m
        return group"""
