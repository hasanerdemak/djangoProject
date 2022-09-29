import io
from http.client import HTTPResponse
import pandas as pd

from django.contrib import admin
from django.contrib.auth.models import User
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
            data = io.StringIO(text)
            df = pd.read_csv(data, sep=",")
            """textLines = text.split("\n")
            for i in range(len(textLines)):
                textLines[i] = textLines[i].split(",")"""
            print(df)

            print(User.objects.filter(id=1).exists())
            print(User.objects.filter(id=2).exists())


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
