from http.client import HTTPResponse

from django.contrib import admin
from django.http import HttpResponseRedirect
from django.template.response import TemplateResponse
from django.urls import path

from dealership.models import Dealership
from .models import UserProfile


# Register your models here.
class UserProfileAdmin(admin.ModelAdmin):
    #list_display = ["user", "dealership"]
    # fields = ("user", "dealership")
    add_form_template = "test.html"

    class Meta:
        model = UserProfile

    def get_urls(self):
        urls = super().get_urls()
        my_urls = [
            # path('add/', self.my_view),
            path('add/addUserProfile/', self.addUserProfile),
        ]
        return my_urls + urls

    def addUserProfile(self, request, obj=None, **kwargs):
        if request.method == "GET":
            return HttpResponseRedirect("../../")
        else:  # POST

            text = request.POST.get("formTextArea")
            print(text)
            splittedText = text.split(",")
            for element in splittedText:
                print(element)

            """try:
                newUserProfile = UserProfile.objects.create(user, dealership, isActive=True, firstName=user.username,
                                                            lastName="", email="@")
            except:
                print("hata")"""
            return HttpResponseRedirect("../../")

    def my_view(self, request):
        # ...
        context = dict(
            # Include common variables for rendering the admin template.
            self.admin_site.each_context(request),
            # Anything else you want in the context...

        )
        return TemplateResponse(request, "test.html", context)


admin.site.register(UserProfile, UserProfileAdmin)
