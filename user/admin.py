import operator
import random
import string
from functools import reduce

from django.contrib import admin
from django.contrib.auth.models import User
from django.db import models
from django.db.models import Q
from django.shortcuts import render, redirect
from django.template.response import TemplateResponse
from django.urls import re_path

from dealership.models import Dealership
from user import utils
from .models import UserProfile


class UserProfileAdmin(admin.ModelAdmin):
    change_list_template = "user/my_user_profile_change_list.html"
    list_display = ["user", "dealership"]
    readonly_fields = ["dealership_name", "is_active", "first_name", "last_name", "email"]
    fields = ["user", "dealership", "dealership_name", "is_active", "first_name", "last_name", "email"]
    search_fields = ["first_name", "last_name", "email", "dealership_name"]
    characters = string.ascii_letters + string.digits + string.punctuation

    class Meta:
        model = UserProfile

    def get_urls(self):
        urls = super().get_urls()
        my_urls = [
            re_path(r'^addUserProfile$', self.admin_site.admin_view(self.check_buttons), name='addUserProfile'),
        ]
        return my_urls + urls

    def check_buttons(self, request):
        context = {"text": None,
                   "create_if_not_exist": True,
                   "missing_spaces_rows": None,
                   "missing_spaces_cols": None,
                   "missing_spaces_messages": None,
                   "non_valid_spaces_rows": None,
                   "non_valid_spaces_cols": None,
                   "non_valid_messages": None,
                   "non_unique_rows": None,
                   "non_unique_cols": None,
                   "non_valid_field_indices": None,
                   "show_table": 'false',
                   "is_valid": False,
                   "error": None}

        error_check_button = request.POST.get("error-check-button")
        create_button = request.POST.get("create-button")

        if error_check_button is None and create_button is None:  # Page first open
            return TemplateResponse(request, "user/user_profile_add.html", context)
        elif create_button is None:  # Error Check button was clicked.
            return self.error_check(request)
        else:  # Create User Profile button was clicked.
            return self.add_user_profile(request)

    @staticmethod
    def error_check(request):
        create_if_not_exist = True if (request.POST.get("form-check-box-1") is not None) else False

        text = request.POST.get("form-text-area").rstrip("\r\n")

        user_profile_dict = utils.read_csv_as_dict(text)

        missing_spaces_rows = []
        missing_spaces_cols = []
        missing_spaces_messages = ''
        non_valid_spaces_rows = []
        non_valid_spaces_cols = []
        non_valid_messages = ''
        non_unique_rows = []
        non_unique_cols = []
        non_unique_messages = ''
        show_table = 'true'
        is_valid = False

        non_valid_field_indices = utils.non_valid_field_indices(user_profile_dict.keys())
        # If There is not non-valid field then check other errors
        if len(non_valid_field_indices) == 0:
            col_index = 0
            for key in user_profile_dict.keys():
                index_list = [index for index, value in enumerate(user_profile_dict[key]) if not value or value == ""]

                for j in index_list:
                    missing_spaces_rows.append(j)
                    missing_spaces_cols.append(col_index)
                if len(index_list) != 0:
                    missing_spaces_messages += '"' + key + '" field at row(s): ' + str(
                        utils.increase_list_values(index_list, 1)) + ' is/are required. \r\n'
                col_index += 1

            model_field_types_dict = {"int": [models.AutoField, models.BigAutoField,
                                              models.IntegerField, models.BigIntegerField, models.SmallIntegerField,
                                              models.PositiveIntegerField, models.PositiveBigIntegerField,
                                              models.PositiveSmallIntegerField,
                                              models.ForeignKey],
                                      "bool": [models.BooleanField, models.NullBooleanField],
                                      "name": [models.CharField],
                                      "email": [models.EmailField]}

            # NON VALID CHECK
            col_index = 0
            for key in user_profile_dict.keys():
                index_list = []
                if col_index not in non_valid_field_indices:
                    col_type = utils.get_col_type(key)
                    if col_type in model_field_types_dict["int"]:
                        index_list = utils.indices_of_non_int_values(user_profile_dict[key])
                    elif col_type in model_field_types_dict["bool"]:
                        index_list = utils.indices_of_non_boolean_values(user_profile_dict[key])
                    elif col_type in model_field_types_dict["name"] and key != "dealership_name":
                        index_list = utils.indices_of_non_valid_names(user_profile_dict[key])
                    elif col_type in model_field_types_dict["email"]:
                        index_list = utils.indices_of_non_valid_emails(user_profile_dict[key])

                    for j in index_list:
                        non_valid_spaces_rows.append(j)
                        non_valid_spaces_cols.append(col_index)
                    if len(index_list) != 0:
                        non_valid_messages += '"' + key + '" fields at row(s): ' + str(
                            utils.increase_list_values(index_list, 1)) + ' is/are not valid. \r\n'
                col_index += 1

            unique_cols = [["user_id", "dealership_id"]]
            col_index = 0
            for col in unique_cols:
                if isinstance(col, list):
                    list_to_give = utils.merge_lists(*[user_profile_dict[col[i]] for i in range(len(col))])
                else:
                    list_to_give = user_profile_dict[col]
                index_list = utils.indices_of_non_unique_cells(list_to_give)

                if len(index_list) != 0:
                    if isinstance(col, list):
                        for _ in col:
                            for j in index_list:
                                non_unique_rows.append(j)
                                non_unique_cols.append(col_index)
                            col_index += 1

                        non_unique_messages += str(col) + ' pairs at row(s): '
                        for index in index_list:
                            non_unique_messages += str(index + 1) + ', '

                        non_unique_messages = non_unique_messages[:len(non_unique_messages) - 2]
                        non_unique_messages += ' must be unique. \r\n'
                    else:
                        for j in index_list:
                            non_unique_rows.append(j)
                            non_unique_cols.append(col_index)
                        non_unique_messages += '"' + str(col) + '" fields at row(s): ' + str(
                            utils.increase_list_values(index_list, 1)) + ' must be unique. \r\n'
                col_index += 1

            if not (len(non_valid_spaces_rows) or len(missing_spaces_rows) or len(non_unique_rows) or len(
                    non_valid_field_indices)):
                is_valid = True

            error = None if is_valid else "Please Click On The Wrong Cells To Edit The Text"
        else:
            error = "Please Correct The Field Names First"

        context = {"text": text,
                   "create_if_not_exist": create_if_not_exist,
                   "missing_spaces_rows": missing_spaces_rows,
                   "missing_spaces_cols": missing_spaces_cols,
                   "missing_spaces_messages": missing_spaces_messages,
                   "non_valid_spaces_rows": non_valid_spaces_rows,
                   "non_valid_spaces_cols": non_valid_spaces_cols,
                   "non_valid_messages": non_valid_messages,
                   "non_unique_rows": non_unique_rows,
                   "non_unique_cols": non_unique_cols,
                   "non_unique_messages": non_unique_messages,
                   "non_valid_field_indices": non_valid_field_indices,
                   "show_table": show_table,
                   "is_valid": is_valid,
                   "error": error}
        return render(request, "user/user_profile_add.html", context)

    def add_user_profile(self, request):
        if request.method == "GET":
            return redirect("/admin/user/userprofile")
        else:  # POST
            db_users = None
            db_dealerships = None
            db_user_profiles = None
            try:
                db_users = User.objects.all()
                db_dealerships = Dealership.objects.all()
                db_user_profiles = UserProfile.objects.all()
            except Exception as e:
                print(f"{e} Happened When Fetching Objects From DB")

            text = request.POST.get("form-text-area").rstrip("\r\n")

            user_profile_dict = utils.read_csv_as_dict(text)

            int_field_types_list = [models.AutoField, models.BigAutoField,
                                    models.IntegerField, models.BigIntegerField, models.SmallIntegerField,
                                    models.PositiveIntegerField, models.PositiveBigIntegerField,
                                    models.PositiveSmallIntegerField,
                                    models.ForeignKey]

            for key in user_profile_dict.keys():
                col_type = utils.get_col_type(key)
                if col_type in int_field_types_list:
                    user_profile_dict[key] = list(map(int, user_profile_dict[key]))

            create_if_not_exist = True if (request.POST.get("form-check-box-1") is not None) else False

            non_exist_user_id_indices, exist_user_id_indices = self.get_exist_and_non_exist_lists(list(
                user_profile_dict['user_id']), db_users.values_list('id', flat=True))
            non_exist_dealership_id_indices, exist_dealership_id_indices = self.get_exist_and_non_exist_lists(
                list(user_profile_dict['dealership_id']), db_dealerships.values_list('id', flat=True))
            non_exist_user_profile_id_indices, exist_user_profile_id_indices = self.get_exist_and_non_exist_lists(
                utils.merge_lists(list(user_profile_dict['user_id']), list(user_profile_dict['dealership_id'])),
                db_user_profiles.values_list('user_id', 'dealership_id'))

            if create_if_not_exist:
                # CREATE USERS
                new_users_values_to_create_dict = self.get_obj_values_as_dict("user", user_profile_dict,
                                                                              non_exist_user_id_indices)
                self.create_objects("user", **new_users_values_to_create_dict)

                # CREATE DEALERSHIPS
                new_dealerships_values_to_create_dict = self.get_obj_values_as_dict("dealership", user_profile_dict,
                                                                                    non_exist_dealership_id_indices)
                self.create_objects("dealership", **new_dealerships_values_to_create_dict)

                intersection_of_lists = non_exist_user_profile_id_indices
            else:  # Send only exist users and dealerships
                intersection_of_lists = list(set(non_exist_user_profile_id_indices) & set(exist_user_id_indices) & set(
                    exist_dealership_id_indices))

            # CREATE USER PROFILES
            user_profiles_values_to_create_dict = self.get_obj_values_as_dict("userprofile", user_profile_dict,
                                                                              intersection_of_lists)
            self.create_objects("userprofile", **user_profiles_values_to_create_dict)

            # Get User values to update then UPDATE USERS
            users_values_to_update_dict = self.get_obj_values_as_dict("user", user_profile_dict, exist_user_id_indices)
            updatable_users = db_users.filter(id__in=users_values_to_update_dict["id"])
            self.update_objects("user", updatable_users, **users_values_to_update_dict)

            # Get Dealership values to update then UPDATE DEALERSHIPS
            dealerships_values_to_update_dict = self.get_obj_values_as_dict("dealership", user_profile_dict,
                                                                            exist_dealership_id_indices)
            updatable_dealerships = db_dealerships.filter(id__in=dealerships_values_to_update_dict["id"])
            self.update_objects("dealership", updatable_dealerships, **dealerships_values_to_update_dict)

            return redirect("/admin/user/userprofile")

    @staticmethod
    def get_obj_values_as_dict(model_str, user_profile_dict, wanted_rows_indices):
        new_obj_values_dict = dict()

        model_str = str(model_str).strip().lower()

        if model_str == 'user':
            model_instance = User()
            new_obj_values_dict["id"] = [user_profile_dict["user_id"][i] for i in wanted_rows_indices]
        elif model_str == 'dealership':
            model_instance = Dealership()
            new_obj_values_dict["id"] = [user_profile_dict["dealership_id"][i] for i in wanted_rows_indices]
            new_obj_values_dict["name"] = [user_profile_dict["dealership_name"][i] for i in wanted_rows_indices]
        elif model_str == "userprofile":
            model_instance = UserProfile()
            new_obj_values_dict["user_id"] = [user_profile_dict["user_id"][i] for i in wanted_rows_indices]
            new_obj_values_dict["dealership_id"] = [user_profile_dict["dealership_id"][i] for i in wanted_rows_indices]
        else:
            raise Exception('Unknown Model')

        for field in model_instance._meta.fields:
            if field.name in user_profile_dict.keys():
                new_obj_values_dict[field.name] = [user_profile_dict[field.name][i] for i in wanted_rows_indices]

        return new_obj_values_dict

    def create_objects(self, model_str, **kwargs):
        try:
            if model_str == 'user':
                kwargs["password"] = [''.join(random.choice(self.characters) for _ in range(8))
                                      for _ in range(len(kwargs["id"]))]
                kwargs["username"] = [kwargs["first_name"][user_index] +
                                      kwargs["last_name"][user_index]
                                      for user_index in range(len(kwargs["id"]))]

                User.objects.bulk_create([User(**{key: values[i] for key, values in kwargs.items()})
                                          for i in range(len(kwargs["id"]))])
            elif model_str == 'dealership':
                kwargs["group_id"] = [1 for _ in range(len(kwargs["id"]))]

                Dealership.objects.bulk_create([Dealership(**{key: values[i] for key, values in kwargs.items()})
                                                for i in range(len(kwargs["id"]))])
            elif model_str == 'userprofile':
                UserProfile.objects.bulk_create([UserProfile(**{key: values[i] for key, values in kwargs.items()})
                                                 for i in range(len(kwargs["user_id"]))])
            else:
                raise Exception('Unknown Model')
        except Exception as e:
            print(f"{e} Happened When Creating {model_str}")

        return ""

    @staticmethod
    def update_objects(model_str, updatable_objects, **kwargs):
        try:
            if model_str == 'user':
                exist_objects_indices = utils.reorder_list(list(updatable_objects.values_list("id", flat=True)),
                                                           kwargs["id"])
                kwargs.pop("id")
            elif model_str == 'dealership':
                exist_objects_indices = utils.reorder_list(list(updatable_objects.values_list("id", flat=True)),
                                                           kwargs["id"])
                kwargs.pop("id")
            elif model_str == 'userprofile':
                query = reduce(operator.or_, (Q(user_id=u_id, dealership_id=d_id) for u_id, d_id in
                                              zip(kwargs['user_id'], kwargs['dealership_id'])))

                updatable_objects = UserProfile.objects.filter(query)
                exist_objects_indices = utils.reorder_list(
                    list(updatable_objects.values_list('user_id', 'dealership_id')),
                    utils.merge_lists(kwargs['user_id'], kwargs['dealership_id']))
            else:
                raise Exception('Unknown Model')

            for obj, index in zip(updatable_objects, exist_objects_indices):
                for key, values in kwargs.items():
                    setattr(obj, key, values[index])

            if model_str == 'user':
                User.objects.bulk_update(updatable_objects, kwargs.keys())
            elif model_str == 'dealership':
                Dealership.objects.bulk_update(updatable_objects, kwargs.keys())
            elif model_str == 'userprofile':
                UserProfile.objects.bulk_update(updatable_objects, kwargs.keys())
        except Exception as e:
            print(f"{e} Happened When Updating {model_str}")
        return ""

    @staticmethod
    def get_exist_and_non_exist_lists(list_from_input, id_list):
        # Get all ids from model objects
        not_exist_id_indices = []
        exist_id_indices = []
        try:
            index = 0
            for obj_id in list_from_input:
                if obj_id in id_list:
                    exist_id_indices.append(index)
                else:
                    not_exist_id_indices.append(index)
                index += 1
        except Exception as e:
            print(f"Exception Happened for {id_list} | {e}")

        return not_exist_id_indices, exist_id_indices


admin.site.register(UserProfile, UserProfileAdmin)
