import io
from http.client import HTTPResponse
import pandas as pd
import numpy as np

from django.contrib import admin
from django.contrib.auth.models import User
from django.http import HttpResponseRedirect, JsonResponse
from django.shortcuts import render
from django.template.response import TemplateResponse
from django.urls import path

from dealership.models import Dealership, DealershipGroup
from . import views
from .models import UserProfile

import random
import string


# Register your models here.
class UserProfileAdmin(admin.ModelAdmin):
    list_display = ["user", "dealership"]
    # fields = ("user", "dealership")
    # add_form_template = "test.html"

    class Meta:
        model = UserProfile

    def get_urls(self):
        urls = super().get_urls()
        my_urls = [
            path('add/', self.my_view),
            path('add/addUserProfile/', self.addUserProfile),
        ]
        return my_urls + urls

    def addUserProfile(self, request, obj=None, **kwargs):
        if request.method == "GET":
            return HttpResponseRedirect("../../")
        else:  # POST

            text = request.POST.get("formTextArea")

            if len(text) == 0:
                return HttpResponseRedirect("../../")
            data = io.StringIO(text)
            userProfileTable = pd.read_csv(data, sep=",")


            createIfNotExist = True if (request.POST.get("formCheckBox") is not None) else False
            typeCheckButton = True if (request.POST.get("typeCheckButton") is not None) else False
            if typeCheckButton:
                errors = [[1, 2], [4, 3]]
                print(userProfileTable.iloc[:, 1:2])
                missingSpacesRows = np.where(pd.isnull(userProfileTable))[0]
                missingSpacesCols = np.where(pd.isnull(userProfileTable))[1]

                showTable = 'true'

                context = {"text": text,
                           "errors": errors,
                           "missingSpacesRows": missingSpacesRows,
                           "missingSpacesCols": missingSpacesCols,
                           "showTable": showTable}
                #return render(request, "test.html", context)
                return render(request, "test.html", context)

            characters = string.ascii_letters + string.digits + string.punctuation
            userProfileList = list()

            for i in range(len(userProfileTable)):
                row = userProfileTable.iloc[i]

                if User.objects.filter(id=row['user']).exists():
                    username = User.objects.get(id=row['user']).username
                else:
                    username = row['firstName'] + row['lastName']

                userObject, created = User.objects.update_or_create(
                    username=username,
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
            return HttpResponseRedirect("..")

    def my_view(self, request):
        context = {"text": None,
                    "errors": None,
                   "missingSpacesRows": None,
                   "missingSpacesCols": None,
                    "showTable": 'false'}
        return TemplateResponse(request, "test.html", context)


admin.site.register(UserProfile, UserProfileAdmin)
