import random
import string
from operator import itemgetter

from django.contrib import admin
from django.contrib.auth.models import User
from django.db import models
from django.shortcuts import render, redirect
from django.template.response import TemplateResponse
from django.urls import re_path

from dealership.models import Dealership
from user import utils
from .models import UserProfile


class UserProfileAdmin(admin.ModelAdmin):
    change_list_template = "user/my_user_profile_change_list.html"
    list_display = ["user", "dealership"]
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
        create_if_not_exist = True if (request.POST.get("form-check-box") is not None) else False
        text = request.POST.get("form-text-area").rstrip("\r\n")

        user_profile_dict = utils.read_csv(text)

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

            col_index = 0
            for key in user_profile_dict.keys():
                index_list = []
                if col_index not in non_valid_field_indices:
                    col_type = type(UserProfile._meta.get_field(key))
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

            unique_cols = ["id", ["user_id", "dealership_id"]]
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
                        non_unique_messages += '"' + col + '" fields at row(s): ' + str(
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
            text = request.POST.get("form-text-area").rstrip("\r\n")

            user_profile_dict = utils.read_csv(text)

            create_if_not_exist = True if (request.POST.get("form-check-box") is not None) else False

            non_exist_user_ids, exist_user_ids = self.get_exist_and_non_exist_lists(
                list(user_profile_dict['user_id']), 'user')
            non_exist_dealership_ids, exist_dealership_ids = self.get_exist_and_non_exist_lists(
                list(user_profile_dict['dealership_id']), 'dealership')
            non_exist_user_profile_ids, exist_user_profile_ids = self.get_exist_and_non_exist_lists(
                list(user_profile_dict['id']), 'userprofile')

            if create_if_not_exist:
                # CREATE USERS
                new_users_values_to_create_dict = self.get_obj_values_as_dict(user_profile_dict, User(),
                                                                              non_exist_user_ids)
                self.create_objects("user", **new_users_values_to_create_dict)

                # CREATE DEALERSHIPS
                new_dealerships_values_to_create_dict = self.get_obj_values_as_dict(user_profile_dict, Dealership(),
                                                                                    non_exist_dealership_ids)
                self.create_objects("dealership", **new_dealerships_values_to_create_dict)

                intersection_of_lists = non_exist_user_profile_ids
            else:  # Send only exist users and dealerships
                intersection_of_lists = list(
                    set(non_exist_user_profile_ids) & set(exist_user_ids) & set(exist_dealership_ids))

            # CREATE USER PROFILES
            user_profiles_values_to_create_dict = self.get_obj_values_as_dict(user_profile_dict, UserProfile(),
                                                                              intersection_of_lists)
            self.create_objects("userprofile", **user_profiles_values_to_create_dict)

            # Get User values to update then UPDATE USERS
            users_values_to_update_dict = self.get_obj_values_as_dict(user_profile_dict, User(),
                                                                      exist_user_ids)
            self.update_objects("user", **users_values_to_update_dict)

            # Get Dealership values to update then UPDATE DEALERSHIPS
            dealerships_values_to_update_dict = self.get_obj_values_as_dict(user_profile_dict, Dealership(),
                                                                            exist_dealership_ids)
            self.update_objects("dealership", **dealerships_values_to_update_dict)

            # Get User Profile values to update then UPDATE USER PROFILES
            user_profiles_values_to_update_dict = self.get_obj_values_as_dict(user_profile_dict, UserProfile(),
                                                                              exist_user_profile_ids)
            self.update_objects("userprofile", **user_profiles_values_to_update_dict)

            return redirect("/admin/user/userprofile")

    @staticmethod
    def get_obj_values_as_dict(user_profile_dict, model_instance, wanted_rows_indices):
        new_obj_values_dict = dict()

        if len(wanted_rows_indices) == 0:
            return new_obj_values_dict

        for field in model_instance._meta.fields:
            if field.name in user_profile_dict.keys():
                new_obj_values_dict[field.name] = list(itemgetter(*wanted_rows_indices)(user_profile_dict[field.name]))

        if model_instance._meta.model.__name__ == 'User':
            new_obj_values_dict["id"] = list(itemgetter(*wanted_rows_indices)(user_profile_dict["user_id"]))
        elif model_instance._meta.model.__name__ == 'Dealership':
            new_obj_values_dict["id"] = list(itemgetter(*wanted_rows_indices)(user_profile_dict["dealership_id"]))
            new_obj_values_dict["name"] = list(itemgetter(*wanted_rows_indices)(user_profile_dict["dealership_name"]))
        elif model_instance._meta.model.__name__ == 'UserProfile':
            new_obj_values_dict["user_id"] = list(itemgetter(*wanted_rows_indices)(user_profile_dict["user_id"]))
            new_obj_values_dict["dealership_id"] = list(
                itemgetter(*wanted_rows_indices)(user_profile_dict["dealership_id"]))
        else:
            raise Exception('Unknown Model')

        return new_obj_values_dict

    def create_objects(self, model_str, **kwargs):
        if len(kwargs) == 0:
            return ""
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
                                                 for i in range(len(kwargs["id"]))])
            else:
                raise Exception('Unknown Model')
        except Exception as e:
            print(f"{e} Happened When Creating {model_str}")

        return ""

    @staticmethod
    def update_objects(model_str, **kwargs):
        if len(kwargs) == 0:
            return ""
        try:
            if model_str == 'user':
                updatable_objects = User.objects.filter(id__in=kwargs["id"])
            elif model_str == 'dealership':
                updatable_objects = Dealership.objects.filter(id__in=kwargs["id"])
            elif model_str == 'userprofile':
                updatable_objects = UserProfile.objects.filter(id__in=kwargs["id"])
            else:
                raise Exception('Unknown Model')

            exist_objects_indices = utils.reorder_list(list(updatable_objects.values_list("id", flat=True)),
                                                       list(map(int, kwargs["id"])))
            kwargs.pop("id")

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
    def get_exist_and_non_exist_lists(list_from_input, model_str):
        # Get all ids from model objects
        not_exist_id_indices = []
        exist_id_indices = []
        id_list = []
        try:
            if model_str == 'user':
                id_list = list(User.objects.values_list('id', flat=True))
            elif model_str == 'dealership':
                id_list = list(Dealership.objects.values_list('id', flat=True))
            elif model_str == 'userprofile':
                id_list = list(UserProfile.objects.values_list('id', flat=True))
            else:
                raise Exception('Unknown Model')

            for obj_id in list_from_input:
                index = list_from_input.index(obj_id)
                if int(obj_id) in id_list:
                    exist_id_indices.append(index)
                else:
                    not_exist_id_indices.append(index)
        except Exception as e:
            print(f"Exception Happened for {id_list} | {e}")

        return not_exist_id_indices, exist_id_indices


admin.site.register(UserProfile, UserProfileAdmin)
