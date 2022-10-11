import io
import json
from http.client import HTTPResponse
import pandas as pd
import numpy as np

import re

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
            path('add/', self.checkInput),
            path('add/addUserProfile/', self.addUserProfile),
        ]
        return my_urls + urls

    def checkInput(self, request, obj=None, **kwargs):
        context = {"text": None,
                   "missingSpacesRows": None,
                   "missingSpacesCols": None,
                   "nonValidSpacesRows": None,
                   "nonValidSpacesCols": None,
                   "showTable": 'false',
                   "isValid": False,
                   "error": None}

        text = request.POST.get("formTextArea")

        if text is None or len(text) == 0:
            return TemplateResponse(request, "test.html", context)

        data = io.StringIO(text)
        try:
            userProfileTable = pd.read_csv(data, sep=",")
        except pd.errors.ParserError as e:
            context = {"text": text,
                       "missingSpacesRows": None,
                       "missingSpacesCols": None,
                       "nonValidSpacesRows": None,
                       "nonValidSpacesCols": None,
                       "showTable": 'false',
                       "isValid": False,
                       "error": str(e)}
            return render(request, "test.html", context)

        missingSpacesRows = np.where(pd.isnull(userProfileTable))[0]
        missingSpacesCols = np.where(pd.isnull(userProfileTable))[1]

        missingSpacesRows = missingSpacesRows.tolist()
        missingSpacesCols = missingSpacesCols.tolist()

        int_cols = [0, 1, 2]
        bool_cols = [3]
        name_cols = [4, 5]
        email_cols = [6]

        nonValidSpacesRows = []
        nonValidSpacesCols = []

        Util = Utils()
        for i in range(len(userProfileTable.columns)):
            index_list = []
            if i in int_cols:
                index_list = Util.indexes_of_non_int_values(userProfileTable.iloc[:, i].tolist())
            if i in bool_cols:
                index_list = Util.indexes_of_non_boolean_values(userProfileTable.iloc[:, i].tolist())
            if i in name_cols:
                index_list = Util.indexes_of_non_valid_names(userProfileTable.iloc[:, i].tolist())
            if i in email_cols:
                index_list = Util.indexes_of_non_valid_emails(userProfileTable.iloc[:, i].tolist())

            for j in index_list:
                nonValidSpacesRows.append(j)
                nonValidSpacesCols.append(i)

        print(nonValidSpacesRows)
        print(nonValidSpacesCols)

        """A= [1, 2, 3, 4, 5, 7]
            B= [3, 4, 1, 6, 7, 5]
            a_indices = [x in B for x in A]

            print(a_indices)"""

        showTable = 'true'

        isValid = True if (len(nonValidSpacesRows) == 0 and len(missingSpacesRows) == 0) else False

        context = {"text": text,
                   "missingSpacesRows": missingSpacesRows,
                   "missingSpacesCols": missingSpacesCols,
                   "nonValidSpacesRows": nonValidSpacesRows,
                   "nonValidSpacesCols": nonValidSpacesCols,
                   "showTable": showTable,
                   "isValid": isValid,
                   "error": None}

        return render(request, "test.html", context)

        # return TemplateResponse(request, "test.html", context)
    def addUserProfile(self, request, obj=None, **kwargs):
        if request.method == "GET":
            return HttpResponseRedirect("../../")
        else:  # POST

            text = request.POST.get("formTextArea")
            data = io.StringIO(text)
            userProfileTable = pd.read_csv(data, sep=",")

            createIfNotExist = True if (request.POST.get("formCheckBox") is not None) else False

            characters = string.ascii_letters + string.digits + string.punctuation
            userProfileList = list()

            Util = Utils()
            exist_user_ids, nonexist_user_ids = Util.get_exist_and_nonexist_lists(list(userProfileTable['user']),
                                                                                  User)
            exist_dealership_ids, nonexist_dealership_ids = Util.get_exist_and_nonexist_lists(
                list(userProfileTable['dealership']), User)
            print(exist_user_ids, nonexist_user_ids)
            print(exist_dealership_ids, nonexist_dealership_ids)
            '''User object list for creation
            user_list_create= list()
            for user_index in enumerate(nonexist_user_ids):
                user_list_create.append(User(id=userProfileTable["user"][user_index],
                                             isActive=userProfileTable["isActive"][user_index],
                                             email=userProfileTable["email"][user_index],
                                             password=''.join(random.choice(characters) for i in range(8))
                                             )
                                        )
            '''
            user_list_create = list()
            dealership_list_create = list()
            userprofile_list_create = list()
            for index, row in userProfileTable.iterrows():
                user_list_create.append(User(id=row["user"],
                                             email=row["email"],
                                             password=''.join(random.choice(characters) for i in range(8))
                                             )
                                        )
                dealership_list_create.append(Dealership(id=row['dealership']))
                userProfileList.append(UserProfile(user=User(id=row["user"],
                                                             email=row["email"],
                                                             password=''.join(
                                                                 random.choice(characters) for i in range(8))
                                                             ),
                                                   dealership_id=Dealership(id=row['dealership']),
                                                   isActive=row['isActive'],
                                                   firstName=row['firstName'],
                                                   lastName=row['lastName'],
                                                   email=row['email'])
                                       )
            User.objects.bulk_create(user_list_create, update_conflicts=True)
            Dealership.objects.bulk_create(dealership_list_create, update_conflicts=True)
            UserProfile.objects.bulk_create(userprofile_list_create, update_conflicts=True)
            '''
            for index, row in userProfileTable.iterrows():  # enumerate
                row = userProfileTable.iloc[index]

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
'''
            """try:
                newUserProfile = UserProfile.objects.create(user, dealership, isActive=True, firstName=user.username,
                                                            lastName="", email="@")
            except:
                print("hata")"""
            return HttpResponseRedirect("..")


admin.site.register(UserProfile, UserProfileAdmin)


class Utils:
    regex = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'

    def isNaN(self, num):
        return num != num

    def indexes_of_non_int_values(self, value_list):
        output = []
        for index, value in enumerate(value_list):
            try:
                int(value)
            except ValueError:
                if not self.isNaN(value):
                    output.append(index)

        return output

    def indexes_of_non_valid_emails(self, value_list):
        if len(value_list) == 0:
            return []
        output = []
        for index, email in enumerate(value_list):
            try:
                if not re.fullmatch(self.regex, email):
                    output.append(index)
            except TypeError:
                pass

        return output

    def indexes_of_non_boolean_values(self, value_list):
        output = []
        for index, value in enumerate(value_list):
            if not isinstance(value, bool) and not self.isNaN(value):
                output.append(index)

        return output

    def indexes_of_non_valid_names(self, value_list):
        output = []
        for index, value in enumerate(value_list):
            if not str(value).replace(" ", "").isalpha():
                output.append(index)

        return output

    def get_exist_and_nonexist_lists(self, list_from_input, model):

        '''Get all ids from model objects'''
        id_list = model.objects.values_list('id', flat=True)

        not_exist_id_indexes = list()
        exist_id_indexes = list()
        for index, id in enumerate(list_from_input):
            print(id)
            if id not in list(id_list):
                not_exist_id_indexes.append(index)
            else:
                exist_id_indexes.append(index)

        return not_exist_id_indexes, exist_id_indexes
