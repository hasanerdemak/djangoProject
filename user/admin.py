import io
from http.client import HTTPResponse
import pandas as pd

from django.contrib import admin
from django.contrib.auth.models import User
from django.http import HttpResponseRedirect
from django.template.response import TemplateResponse
from django.urls import path

from dealership.models import Dealership, DealershipGroup
from .models import UserProfile

import random
import string


# Register your models here.
class UserProfileAdmin(admin.ModelAdmin):
    # list_display = ["user", "dealership"]
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
            userProfileTable = pd.read_csv(data, sep=",")
            print(userProfileTable)

            characters = string.ascii_letters + string.digits + string.punctuation
            userProfileList = list()

            for i in range(len(userProfileTable)):
                row = userProfileTable.iloc[i]

                if User.objects.filter(id=row['user']).exists():
                    username = User.objects.get(id=row['user']).username
                else:
                    username = row['firstName'] + row['lastName']

                userObject, created = User.objects.update_or_create(
                    username= username,
                    defaults={'email': row["email"],
                              'password': ''.join(random.choice(characters) for i in range(8))},
                )


                if Dealership.objects.filter(id=row['dealership']).exists():
                    dealershipName = Dealership.objects.get(id=row['dealership']).name
                else:
                    dealershipName = "D " + str(random.randint(3, 1000))

                dealershipObject, created = Dealership.objects.update_or_create(
                    name=dealershipName,
                    defaults={'group': DealershipGroup.objects.get(id=1)},
                )


                userProfileList.append(UserProfile(user=userObject, dealership=dealershipObject, isActive=True,
                                                   firstName=row['firstName'], lastName=row['lastName'],
                                                   email=row['email'])
                                       )

            UserProfile.objects.bulk_create(userProfileList)

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
