import contextlib
import io
from collections import Counter
import pandas as pd
import numpy as np

import re

from django.contrib import admin
from django.contrib.auth.models import User
from django.http import HttpResponseRedirect
from django.shortcuts import render
from django.template.response import TemplateResponse
from django.urls import path

from dealership.models import Dealership
from .models import UserProfile

import random
import string

REGEX_VALID_EMAIL = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'


class UserProfileAdmin(admin.ModelAdmin):
    change_list_template = "user/my_userprofile_change_list.html"
    list_display = ["user", "dealership"]
    characters = string.ascii_letters + string.digits + string.punctuation

    class Meta:
        model = UserProfile

    def get_urls(self):
        urls = super().get_urls()
        my_urls = [
            path('addUserProfile/', self.check_buttons),
            # path('add/addUserProfile/', self.add_userprofile),
        ]
        return my_urls + urls

    def check_buttons(self, request, obj=None, **kwargs):
        context = {"text": None,
                   "missing_spaces_rows": None,
                   "missing_spaces_cols": None,
                   "missing_spaces_messages": None,
                   "non_valid_spaces_rows": None,
                   "non_valid_spaces_cols": None,
                   "non_valid_messages": None,
                   "non_unique_rows": None,
                   "non_unique_cols": None,
                   "show_table": 'false',
                   "is_valid": False,
                   "error": None}

        error_check_button = request.POST.get("error-check-button")
        create_button = request.POST.get("create-button")

        if error_check_button is None and create_button is None:  # Page first open
            return TemplateResponse(request, "user/add_userprofile.html", context)
        elif create_button is None:  # Error Check button was clicked.
            return self.error_check(request)
        else:  # Create User Profile button was clicked.
            return self.add_userprofile(request)

    def error_check(self, request):
        text = request.POST.get("form-text-area")

        text = text.rstrip("\r\n")
        data = io.StringIO(text)
        try:
            user_profile_table = pd.read_csv(data, sep=",")
        except pd.errors.ParserError as e:
            context = {"text": text,
                       "missing_spaces_rows": None,
                       "missing_spaces_cols": None,
                       "missing_spaces_messages": None,
                       "non_valid_spaces_rows": None,
                       "non_valid_spaces_cols": None,
                       "non_valid_messages": None,
                       "non_unique_rows": None,
                       "non_unique_cols": None,
                       "show_table": 'false',
                       "is_valid": False,
                       "error": str(e)}
            return render(request, "user/add_userprofile.html", context)

        missing_spaces_rows = np.where(pd.isnull(user_profile_table))[0].tolist()
        missing_spaces_cols = np.where(pd.isnull(user_profile_table))[1].tolist()

        missing_spaces_messages = ''
        if len(missing_spaces_cols) != 0:
            missing_spaces_cols_unique_elements = [*set(missing_spaces_cols)]  # remove duplicates
            for value in missing_spaces_cols_unique_elements:
                missing_spaces_messages += '"' + user_profile_table.iloc[:, value].name + '" fields at row(s): '
                value_indices = [i for i, x in enumerate(missing_spaces_cols) if x == value]

                for i in value_indices:
                    missing_spaces_messages += str(missing_spaces_rows[i] + 1) + ', '

                missing_spaces_messages = missing_spaces_messages[:len(missing_spaces_messages) - 2]
                missing_spaces_messages += ' is/are required. \r\n'

        """unique_cols = [0, [1, 2]]
        int_cols = [0, 1, 2]
        bool_cols = [4]
        name_cols = [5, 6]
        email_cols = [7]"""
        unique_cols = ["id", ["user", "dealership"]]

        int_cols = ["id", "user", "dealership"]
        bool_cols = ["isActive"]
        name_cols = ["firstName", "lastName"]
        email_cols = ["email"]

        non_valid_spaces_rows = []
        non_valid_spaces_cols = []

        Util = Utils()
        non_valid_messages = ''
        for col in user_profile_table.columns:
            index_list = []
            if col in int_cols:
                index_list = Util.indexes_of_non_int_values(user_profile_table[col].tolist())
            if col in bool_cols:
                index_list = Util.indexes_of_non_boolean_values(user_profile_table[col].tolist())
            if col in name_cols:
                index_list = Util.indexes_of_non_valid_names(user_profile_table[col].tolist())
            if col in email_cols:
                index_list = Util.indexes_of_non_valid_emails(user_profile_table[col].tolist())

            i = user_profile_table.columns.get_loc(col)
            for j in index_list:
                non_valid_spaces_rows.append(j)
                non_valid_spaces_cols.append(i)
            if len(index_list) != 0:
                non_valid_messages += '"' + user_profile_table[col].name + '" fields at row(s): ' + str(
                    Util.increase_list_values(index_list, 1)) + ' is/are not valid. \r\n'

        non_unique_rows = []
        non_unique_cols = []
        non_unique_messages = ''
        for col in unique_cols:
            index_list = Util.indexes_of_non_unique_cells(user_profile_table[col])
            if len(index_list) != 0:
                if isinstance(col, list):
                    for j in index_list:
                        for c in col:
                            i = user_profile_table.columns.get_loc(c)
                            non_unique_rows.append(j)
                            non_unique_cols.append(i)

                    non_unique_messages += str(col) + ' pairs at row(s): '
                    for index in index_list:
                        non_unique_messages += str(index + 1) + ', '

                    non_unique_messages = non_unique_messages[:len(non_unique_messages) - 2]
                    non_unique_messages += ' must be unique. \r\n'
                else:
                    i = user_profile_table.columns.get_loc(col)
                    for j in index_list:
                        non_unique_rows.append(j)
                        non_unique_cols.append(i)
                    non_unique_messages += '"' + user_profile_table[col].name + '" fields at row(s): ' + str(
                        Util.increase_list_values(index_list, 1)) + ' must be unique. \r\n'

        show_table = 'true'
        is_valid = False

        if not(len(non_valid_spaces_rows) or len(missing_spaces_rows) or len(non_unique_rows)):
            is_valid = True

        context = {"text": text,
                   "missing_spaces_rows": missing_spaces_rows,
                   "missing_spaces_cols": missing_spaces_cols,
                   "missing_spaces_messages": missing_spaces_messages,
                   "non_valid_spaces_rows": non_valid_spaces_rows,
                   "non_valid_spaces_cols": non_valid_spaces_cols,
                   "non_valid_messages": non_valid_messages,
                   "non_unique_rows": non_unique_rows,
                   "non_unique_cols": non_unique_cols,
                   "non_unique_messages": non_unique_messages,
                   "show_table": show_table,
                   "is_valid": is_valid,
                   "error": None}

        return render(request, "user/add_userprofile.html", context)

    def add_userprofile(self, request):
        if request.method == "GET":
            return HttpResponseRedirect("../../")
        else:  # POST

            text = request.POST.get("form-text-area")
            data = io.StringIO(text)
            user_profile_table = pd.read_csv(data, sep=",")

            create_if_not_exist = True if (request.POST.get("form-check-box") is not None) else False

            ### !!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!! Model'i pass etmeye meylediyorsun, etme!
            nonexist_user_ids, \
            exist_user_ids = self.get_exist_and_nonexist_lists(list(user_profile_table['user']),
                                                               'user')
            nonexist_dealership_ids, \
            exist_dealership_ids = self.get_exist_and_nonexist_lists(list(user_profile_table['dealership']),
                                                                     'dealership')
#id,user,dealership,isActive,dealershipName,firstName,lastName,email
            self.create_user(user_profile_table['user'],
                             user_profile_table['isActive'],
                             user_profile_table['email'],
                             user_profile_table['firstName'],
                             user_profile_table['lastName'],
                             nonexist_user_ids)

            self.update_user(user_profile_table['user'],
                             user_profile_table['isActive'],
                             user_profile_table['email'],
                             user_profile_table['firstName'],
                             user_profile_table['lastName'],
                             exist_user_ids)

            self.create_dealership(user_profile_table['dealership'],
                                   nonexist_dealership_ids)

            self.update_dealership(user_profile_table['dealership'],
                                   user_profile_table['dealershipName'],
                                   exist_dealership_ids)

            nonexist_userprofile_ids, \
            exist_userprofile_ids = self.get_exist_and_nonexist_lists(list(user_profile_table['id']),
                                                                      'userprofile')

            self.create_userprofile(user_profile_table['id'],
                                    user_profile_table['user'],
                                    user_profile_table['dealership'],
                                    user_profile_table['dealershipName'],
                                    user_profile_table['isActive'],
                                    user_profile_table['email'],
                                    user_profile_table['firstName'],
                                    user_profile_table['lastName'],
                                    nonexist_userprofile_ids)

            self.update_userprofile(user_profile_table['id'],
                                    user_profile_table['user'],
                                    user_profile_table['dealership'],
                                    user_profile_table['dealershipName'],
                                    user_profile_table['isActive'],
                                    user_profile_table['email'],
                                    user_profile_table['firstName'],
                                    user_profile_table['lastName'],
                                    exist_userprofile_ids)

            return HttpResponseRedirect("..")

    # Todo:  bütün tabloyu yollama, ilgili sütunları yolla
    def create_user(self, user_list, is_active_list, email_list, first_name_list, last_name_list, nonexist_user_ids):
        user_list_create = []

        user_list_create = [User(id=user_list[user_index],
                                 is_active=is_active_list.get(user_index),
                                 email=email_list.get(user_index),
                                 password=''.join(random.choice(self.characters) for i in range(8)),
                                 username=first_name_list.get(user_index)+
                                           last_name_list.get(user_index)
                                 ) for index, user_index in enumerate(nonexist_user_ids)]

        try:
            User.objects.bulk_create(user_list_create)
        except Exception as e:
            print(f"Exception Happened When Creating User for {user_list_create} | {e}")

        return ""

    def update_user(self, user_list,is_active_list, email_list, first_name_list, last_name_list, exist_user_ids):

        try:

            updatable_objects = User.objects.filter(id__in=list(user_list[exist_user_ids]))
            #Todo bulk update and if its same length remove zip
            exist_user_ids = Utils().reorder_list(updatable_objects, user_list)

            '''User.objects.bulk_update(
                [
                    User(id=user.get("id"),
                         is_active=user_profile_table['isActive'][user_index],
                         email= user_profile_table['email'][user_index],
                         first_name=user_profile_table['firstName'][user_index],
                         last_name=user_profile_table['lastName'][user_index])
                    for user, user_index in zip(updatable_objects, exist_user_ids)
                ],
                ["id","is_active","email","first_name","last_name"],
                batch_size=1000
            )
            '''
            for user, user_index in zip(updatable_objects, exist_user_ids):
                user.is_active = is_active_list[user_index]
                user.email = email_list[user_index]
                user.first_name = first_name_list[user_index]
                user.last_name = last_name_list[user_index]

            User.objects.bulk_update(updatable_objects,['is_active','email','first_name','last_name'])
        except Exception as e:
            print(f"Exception Happened When Updating User for {updatable_objects} | {e}")
        return ""


    def create_dealership(self, dealership_list, nonexist_dealership_ids):
        #When we are creating dealership, default dealership group id is 1
        try:
            dealership_list_create = [Dealership(id=dealership_list[dealership_index],
                                                 name="D " + str(random.randint(3, 1000)),
                                                 group_id=1
                                                 )
                                      for index, dealership_index in enumerate(nonexist_dealership_ids)
                                      ]

            Dealership.objects.bulk_create(dealership_list_create)
        except Exception as e:
            print(f"Exception Happened Creating Dealership for {dealership_list_create} | {e}")

        return ""

    def update_dealership(self, dealership_list, dealership_name_list, exist_dealership_ids):

        try:

            updatable_objects = Dealership.objects.filter(id__in=list(dealership_list[exist_dealership_ids]))
            exist_dealership_ids = Utils().reorder_list(updatable_objects, dealership_list)

            for dealership, dealership_index in zip(updatable_objects, exist_dealership_ids):
                dealership.name = dealership_name_list[dealership_index]

            Dealership.objects.bulk_update(updatable_objects,['name'])
        except Exception as e:
            print(f"Exception Happened When Updating Dealership for {updatable_objects} | {e}")
        return ""

    def create_userprofile(self, userprofile_id_list,user_list,dealership_list,dealership_name,
                           is_active_list, email_list, first_name_list, last_name_list, nonexist_userprofile_ids):


        try:
            userprofile_list_forcreate = [UserProfile(id=userprofile_id_list[index],
                                                      user_id=user_list,
                                                      dealership_id=dealership_list,
                                                      dealership_name=dealership_name,
                                                      is_active=bool(is_active_list[index]),
                                                      first_name=first_name_list,
                                                      last_name=last_name_list,
                                                      email=email_list)
                                          for index, row in userprofile_id_list.iterrows()
                                          if row['id'] in list(userprofile_id_list[nonexist_userprofile_ids])]

            UserProfile.objects.bulk_create(userprofile_list_forcreate)
        except Exception as e:
            print(f"Exception Happened When Creating Userprofile for {userprofile_list_forcreate} | {e}")

        return ""

    def update_userprofile(self, userprofile_id_list,user_list,dealership_list,dealership_name,
                           is_active_list, email_list, first_name_list, last_name_list, exist_userprofile_ids):

        try:
            updatable_objects = UserProfile.objects.filter(id__in=list(userprofile_id_list[exist_userprofile_ids]))

            exist_userprofile_ids = Utils().reorder_list(updatable_objects, userprofile_id_list)
            # update userprofiles
            for userprofile, userprofile_index in zip(updatable_objects, exist_userprofile_ids):
                userprofile.user = User(id=user_list[userprofile_index],
                                        is_active=is_active_list[userprofile_index],
                                        email=email_list[userprofile_index],
                                        username=first_name_list[userprofile_index] + last_name_list[userprofile_index]
                                        )
                userprofile.dealership = Dealership(id=dealership_list[userprofile_index], )
                userprofile.dealership_name = dealership_name[userprofile_index]
                userprofile.is_active = is_active_list[userprofile_index]
                userprofile.first_name = first_name_list[userprofile_index]
                userprofile.last_name = last_name_list[userprofile_index]
                userprofile.email = email_list[userprofile_index]

            UserProfile.objects.bulk_update(updatable_objects,['user','dealership','dealership_name','is_active','first_name','last_name','email'])

        except Exception as e:
            print(f"Exception Happened When Updating Userprofile for {updatable_objects} | {e}")

        return ""

    def get_exist_and_nonexist_lists(self, list_from_input, model_str):

        # Get all ids from model objects
        try:
            if model_str== 'user':
                id_list = User.objects.values_list('id', flat=True)
            elif model_str== 'dealership':
                id_list = Dealership.objects.values_list('id', flat=True)
            elif model_str== 'userprofile':
                id_list = UserProfile.objects.values_list('id', flat=True)
            else:
                raise Exception('Unknown Model')

            not_exist_id_indexes = []
            exist_id_indexes = []

            for index, id in enumerate(list_from_input):
                if id not in list(id_list):
                    not_exist_id_indexes.append(index)
                else:
                    exist_id_indexes.append(index)
        except Exception as e:
            print(f"Exception Happened for {id_list} | {e}")

        return not_exist_id_indexes, exist_id_indexes

admin.site.register(UserProfile, UserProfileAdmin)


class Utils:

    def is_NaN(self, num):
        """to type check float('NaN') while reading csv"""
        return num != num

    def indexes_of_non_int_values(self, value_list):
        output = []
        for index, value in enumerate(value_list):
            try:
                int(value)
            except ValueError:
                if not self.is_NaN(value):
                    output.append(index)

        return output

    def indexes_of_non_valid_emails(self, value_list):
        output = []
        if len(value_list):
            for index, email in enumerate(value_list):
                with contextlib.suppress(TypeError):
                    if not re.fullmatch(REGEX_VALID_EMAIL, email):
                        output.append(index)
        return output

    def indexes_of_non_boolean_values(self, value_list):
        output = []
        for index, value in enumerate(value_list):
            # if not isinstance(value, bool) and not self.isNaN(value):
            try:
                if int(value) != 0 and int(value) != 1:
                    output.append(index)
            except ValueError:
                if not self.is_NaN(value):
                    output.append(index)

        return output

    def indexes_of_non_valid_names(self, value_list):
        output = []
        for index, value in enumerate(value_list):
            if not str(value).replace(" ", "").isalpha():
                output.append(index)

        return output

    def indexes_of_non_unique_cells(self, value_df):
        output = []
        if isinstance(value_df, pd.Series):
            value_list = value_df.tolist()
        else:
            value_list = list(value_df.itertuples(index=False, name=None))

        freq = Counter(value_list)
        for index, value in enumerate(value_list):
            if freq[value] > 1:
                output.append(index)

        return output

    def increase_list_values(self, value_list, increase_amount):

        return [value + increase_amount
                for value in value_list]

    # Todo: tabloyu yollama
    def reorder_list(self, updatable_list, model_id_list):

        return [model_id_list.values.tolist().index(value.id)
                for value in updatable_list]
