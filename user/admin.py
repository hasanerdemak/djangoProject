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


class UserProfileAdmin(admin.ModelAdmin):
    list_display = ["user", "dealership"]

    class Meta:
        model = UserProfile

    def get_urls(self):
        urls = super().get_urls()
        my_urls = [
            path('add/', self.check_input),
            path('add/addUserProfile/', self.add_userprofile),
        ]
        return my_urls + urls

    def check_input(self, request, obj=None, **kwargs):
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

        text = request.POST.get("formTextArea")

        if text is None or len(text) == 0:
            return TemplateResponse(request, "user/add_userprofile.html", context)

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

        missing_spaces_rows = np.where(pd.isnull(user_profile_table))[0]
        missing_spaces_cols = np.where(pd.isnull(user_profile_table))[1]

        missing_spaces_rows = missing_spaces_rows.tolist()
        missing_spaces_cols = missing_spaces_cols.tolist()

        missing_spaces_messages = ''
        if len(missing_spaces_cols) != 0:
            missing_spaces_cols_unique_elements = [*set(missing_spaces_cols)]  # remove duplicates
            for value in missing_spaces_cols_unique_elements:
                missing_spaces_messages += '"' + user_profile_table.iloc[:, value].name + '" fields at row(s): '
                value_indexes = [i for i, x in enumerate(missing_spaces_cols) if x == value]

                for i in value_indexes:
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

        print(non_unique_messages)

        show_table = 'true'

        is_valid = True if (len(non_valid_spaces_rows) == 0 and len(missing_spaces_rows) == 0 and len(
            non_unique_rows) == 0) else False

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

    def add_userprofile(self, request, obj=None, **kwargs):
        if request.method == "GET":
            return HttpResponseRedirect("../../")
        else:  # POST

            text = request.POST.get("formTextArea")
            data = io.StringIO(text)
            user_profile_table = pd.read_csv(data, sep=",")

            create_if_not_exist = True if (request.POST.get("formCheckBox") is not None) else False

            characters = string.ascii_letters + string.digits + string.punctuation

            nonexist_user_ids, exist_user_ids = self.get_exist_and_nonexist_lists(list(user_profile_table['user']),
                                                                                  User)
            nonexist_dealership_ids, exist_dealership_ids = self.get_exist_and_nonexist_lists(
                list(user_profile_table['dealership']),
                Dealership)

            self.create_user(user_profile_table, nonexist_user_ids, characters)

            self.update_user(user_profile_table, exist_user_ids)

            self.create_dealership(user_profile_table, nonexist_dealership_ids)

            self.update_dealership(user_profile_table, exist_dealership_ids)

            nonexist_userprofile_ids, exist_userprofile_ids = self.get_exist_and_nonexist_lists(
                list(user_profile_table['id']),
                UserProfile)

            self.create_userprofile(user_profile_table, nonexist_userprofile_ids, characters)

            self.update_userprofile(user_profile_table, exist_userprofile_ids, characters)

            return HttpResponseRedirect("..")

    def create_user(self, user_profile_table, nonexist_user_ids, characters):
        user_list_create = []

        # For user
        for index, user_index in enumerate(nonexist_user_ids):
            user_list_create.append(User(id=user_profile_table["user"][user_index],
                                         is_active=user_profile_table["isActive"][user_index],
                                         email=user_profile_table["email"][user_index],
                                         password=''.join(random.choice(characters) for i in range(8)),
                                         username=user_profile_table["firstName"][user_index] +
                                                  user_profile_table["lastName"][user_index]
                                         )
                                    )
        try:
            User.objects.bulk_create(user_list_create)
        except Exception as e:
            print(f"Exception Happened for {user_list_create} | {e}")

        return ""

    def update_user(self, user_profile_table, exist_user_ids):

        try:

            updatable_objects = User.objects.filter(id__in=list(user_profile_table['user'][exist_user_ids]))
            Util = Utils()
            exist_user_ids = Util.reorder_list(updatable_objects, user_profile_table, "User")
            for user, user_index in zip(updatable_objects, exist_user_ids):
                user.is_active = user_profile_table['isActive'][user_index]
                user.email = user_profile_table['email'][user_index]
                user.first_name = user_profile_table['firstName'][user_index]
                user.last_name = user_profile_table['lastName'][user_index]
                user.save()
        except Exception as e:
            print(f"Exception Happened for {updatable_objects} | {e}")
        return ""

    def create_dealership(self, user_profile_table, nonexist_dealership_ids):

        dealership_list_create = []

        try:
            # For dealership
            for index, dealership_index in enumerate(nonexist_dealership_ids):
                dealership_list_create.append(Dealership(id=user_profile_table["dealership"][dealership_index],
                                                         name="D " + str(random.randint(3, 1000)),
                                                         group_id=1
                                                         )
                                              )
            Dealership.objects.bulk_create(dealership_list_create)
        except Exception as e:
            print(f"Exception Happened for {dealership_list_create} | {e}")

        return ""

    def update_dealership(self, user_profile_table, exist_dealership_ids):

        try:

            updatable_objects = Dealership.objects.filter(
                id__in=list(user_profile_table['dealership'][exist_dealership_ids]))
            Util = Utils()
            exist_dealership_ids = Util.reorder_list(updatable_objects, user_profile_table, "Dealership")
            for dealership, dealership_index in zip(updatable_objects, exist_dealership_ids):
                dealership.name = user_profile_table['dealershipName'][dealership_index]
                dealership.save()
        except Exception as e:
            print(f"Exception Happened for {updatable_objects} | {e}")
        return ""

    def create_userprofile(self, user_profile_table, nonexist_userprofile_ids, characters):

        userprofile_list_forcreate = []
        try:
            for index, row in user_profile_table.iterrows():
                if row['id'] in list(user_profile_table['id'][nonexist_userprofile_ids]):
                    userprofile_list_forcreate.append(UserProfile(id=row['id'],
                                                                  user=User(id=row['user'],
                                                                            is_active=row["isActive"],
                                                                            email=row["email"],
                                                                            password=''.join(
                                                                                random.choice(characters) for i in
                                                                                range(8)),
                                                                            username=row["firstName"] + row["lastName"]
                                                                            ),
                                                                  dealership=Dealership(id=row["dealership"],
                                                                                        name="D " + str(
                                                                                            random.randint(3, 1000)),
                                                                                        group_id=1
                                                                                        ),
                                                                  dealership_name=row['dealershipName'],
                                                                  is_active=True,
                                                                  first_name=row['firstName'],
                                                                  last_name=row['lastName'],
                                                                  email=row['email'])
                                                      )
            UserProfile.objects.bulk_create(userprofile_list_forcreate)
        except Exception as e:
            print(f"Exception Happened for {userprofile_list_forcreate} | {e}")

        return ""

    def update_userprofile(self, user_profile_table, exist_userprofile_ids, characters):

        try:
            updatable_objects = UserProfile.objects.filter(id__in=list(user_profile_table['id'][exist_userprofile_ids]))
            Util = Utils()
            exist_userprofile_ids = Util.reorder_list(updatable_objects, user_profile_table, "UserProfile")
            # update userprofiles
            for userprofile, userprofile_index in zip(updatable_objects, exist_userprofile_ids):
                userprofile.user = User(id=user_profile_table['user'][userprofile_index],
                                        is_active=user_profile_table['isActive'][userprofile_index],
                                        email=user_profile_table['email'][userprofile_index],
                                        password=''.join(
                                            random.choice(characters) for i in
                                            range(8)),
                                        username=user_profile_table["firstName"] + user_profile_table["lastName"]
                                        )

                userprofile.dealership = Dealership(id=user_profile_table["dealership"][userprofile_index], )
                userprofile.dealership_name = user_profile_table['dealershipName'][userprofile_index]
                userprofile.is_active = user_profile_table['isActive'][userprofile_index]
                userprofile.first_name = user_profile_table['firstName'][userprofile_index]
                userprofile.last_name = user_profile_table['lastName'][userprofile_index]
                userprofile.email = user_profile_table['email'][userprofile_index]
                userprofile.save()

        except Exception as e:
            print(f"Exception Happened for {updatable_objects} | {e}")

        return ""

    def get_exist_and_nonexist_lists(self, list_from_input, model):

        # Get all ids from model objects
        try:
            id_list = model.objects.values_list('id', flat=True)

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
        output = []
        for value in value_list:
            output.append(value + increase_amount)
        return output

    def reorder_list(self, updatable_list, table, model_str):
        output = []
        for value in updatable_list:
            if model_str == 'User':
                output.append(table['user'].values.tolist().index(value.id))
            if model_str == 'Dealership':
                output.append(table['dealership'].values.tolist().index(value.id))
            if model_str == 'UserProfile':
                output.append(table['id'].values.tolist().index(value.user_id))
        return output
