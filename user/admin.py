import contextlib
import random
import string

from django.contrib import admin
from django.contrib.auth.hashers import make_password
from django.contrib.auth.models import User
from django.core.exceptions import FieldDoesNotExist
from django.db import models
from django.shortcuts import render, redirect
from django.template.response import TemplateResponse
from django.urls import re_path

from dealership.models import Dealership
from user import utils
from .models import UserProfile

MODEL_FIELD_TYPES = {"int": (models.AutoField, models.BigAutoField,
                             models.IntegerField, models.BigIntegerField, models.SmallIntegerField,
                             models.PositiveIntegerField, models.PositiveBigIntegerField,
                             models.PositiveSmallIntegerField,
                             models.ForeignKey),
                     "bool": (models.BooleanField, models.NullBooleanField),
                     "name": [models.CharField],
                     "email": [models.EmailField]}

REQUIRED_FIELDS = ("user_id", "dealership_id", "dealership_name", "first_name", "last_name")


class UserProfileAdmin(admin.ModelAdmin):
    change_list_template = "user/my_user_profile_change_list.html"
    list_display = ["user", "dealership", "is_active"]
    readonly_fields = ["dealership_name", "first_name", "last_name", "email"]
    fields = ["user", "dealership", "is_active", "dealership_name", "first_name", "last_name", "email"]
    search_fields = ["user__username", "user__first_name", "user__last_name", "user__email", "dealership__name"]
    characters = string.ascii_letters + string.digits + string.punctuation

    class Meta:
        model = UserProfile

    def get_urls(self):
        urls = super().get_urls()
        my_urls = [
            re_path(r'^addUserProfile$', self.admin_site.admin_view(self.check_buttons), name='addUserProfile'),
        ]
        return my_urls + urls

    def get_queryset(self, request):
        query = super(UserProfileAdmin, self).get_queryset(request)
        filtered_query = query.filter(is_active=True)
        return filtered_query

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
        if not non_valid_field_indices:
            non_exist_required_fields_list = [field for field in REQUIRED_FIELDS if field not in user_profile_dict]

            if not non_exist_required_fields_list:
                col_index = 0
                for key in user_profile_dict:
                    index_list = [index for index, value in enumerate(user_profile_dict[key]) if
                                  not value or value == ""]

                    for j in index_list:
                        missing_spaces_rows.append(j)
                        missing_spaces_cols.append(col_index)
                    if len(index_list) != 0:
                        missing_spaces_messages += '"' + key + '" field at row(s): ' + str(
                            utils.increase_list_values(index_list, 1)) + ' is/are required. \r\n'
                    col_index += 1

                # NON VALID CHECK
                col_index = 0
                for key in user_profile_dict:
                    index_list = []
                    if col_index not in non_valid_field_indices:
                        col_type = utils.get_col_type(key)
                        if col_type in MODEL_FIELD_TYPES["int"]:
                            index_list = utils.indices_of_non_int_values(user_profile_dict[key])
                        elif col_type in MODEL_FIELD_TYPES["bool"]:
                            index_list = utils.indices_of_non_boolean_values(user_profile_dict[key])
                        elif col_type in MODEL_FIELD_TYPES["name"] and key != "dealership_name":
                            index_list = utils.indices_of_non_valid_names(user_profile_dict[key])
                        elif col_type in MODEL_FIELD_TYPES["email"]:
                            index_list = utils.indices_of_non_valid_emails(user_profile_dict[key])

                        for j in index_list:
                            non_valid_spaces_rows.append(j)
                            non_valid_spaces_cols.append(col_index)
                        if len(index_list) != 0:
                            non_valid_messages += '"' + key + '" fields at row(s): ' + str(
                                utils.increase_list_values(index_list, 1)) + ' is/are not valid. \r\n'
                    col_index += 1

                #TODO add comments
                # Todo methodise
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
                non_valid_field_indices = []
                show_table = "false"
                error = f"{non_exist_required_fields_list} Field(s) Must Be Exist"
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
            db_user_profiles_fk_ids = None
            try:
                db_user_profiles_fk_ids = UserProfile.objects.select_related("user", "dealership").values(
                    "user_id", "dealership_id")
            except Exception as e:
                print(f"{e} Happened When Fetching Objects From DB")

            text = request.POST.get("form-text-area").rstrip("\r\n")

            user_profile_dict = utils.read_csv_as_dict(text)

            for key in user_profile_dict:
                col_type = utils.get_col_type(key)
                if col_type in MODEL_FIELD_TYPES['int']:
                    user_profile_dict[key] = list(map(int, user_profile_dict[key]))

            create_if_not_exist = True if (request.POST.get("form-check-box-1") is not None) else False

            wanted_user_id_indices = wanted_dealership_id_indices = all_indices_list = list(
                range(0, len(user_profile_dict["user_id"])))

            if not create_if_not_exist:
                wanted_user_id_indices = self.get_exist_lists(user_profile_dict['user_id'],
                                                              db_user_profiles_fk_ids.values_list("user_id",
                                                                                                  flat=True).distinct())
                wanted_dealership_id_indices = self.get_exist_lists(user_profile_dict['dealership_id'],
                                                                    db_user_profiles_fk_ids.values_list("dealership_id",
                                                                                                        flat=True).
                                                                    distinct())
            # 1- user_id
            # 2- firstname+lastname

            new_users_values_to_create_dict = self.get_obj_values_as_dict("user", user_profile_dict,
                                                                          wanted_user_id_indices)
            new_dealerships_values_to_create_dict = self.get_obj_values_as_dict("dealership", user_profile_dict,
                                                                                wanted_dealership_id_indices)

            self.create_objects("user", **new_users_values_to_create_dict)
            self.create_objects("dealership", **new_dealerships_values_to_create_dict)

            user_profiles_values_to_create_dict = self.get_obj_values_as_dict("userprofile", user_profile_dict,
                                                                              all_indices_list)
            self.create_objects("userprofile", **user_profiles_values_to_create_dict)

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
            if "is_active" in user_profile_dict:
                new_obj_values_dict["is_active"] = [user_profile_dict["is_active"][i] for i in wanted_rows_indices]
            else:
                new_obj_values_dict["is_active"] = [True for _ in wanted_rows_indices]
        else:
            raise Exception('Unknown Model')

        for key in user_profile_dict:
            if key != "is_active":
                with contextlib.suppress(KeyError, FieldDoesNotExist):
                    model_instance._meta.get_field(key)
                    new_obj_values_dict[key] = [user_profile_dict[key][i] for i in wanted_rows_indices]

        return new_obj_values_dict

    def create_objects(self, model_str, **kwargs):
        try:
            if model_str == 'user':
                kwargs["password"] = [make_password(''.join(random.choice(self.characters) for _ in range(8)))
                                      for _ in range(len(kwargs["id"]))]
                kwargs["username"] = [kwargs["first_name"][user_index] +
                                      kwargs["last_name"][user_index]
                                      for user_index in range(len(kwargs["id"]))]

                field_list = [model_field[1].attname for model_field in enumerate(User._meta.fields)]
                field_list.pop(field_list.index("id"))
                field_list.pop(field_list.index("username"))

                User.objects.bulk_create([User(**{key: values[i] for key, values in kwargs.items()})
                                          for i in range(len(kwargs["id"]))],
                                         update_conflicts=True,
                                         unique_fields=["id"],
                                         update_fields=field_list)
            elif model_str == 'dealership':
                kwargs["group_id"] = [1 for _ in range(len(kwargs["id"]))]

                field_list = [model_field[1].attname for model_field in enumerate(Dealership._meta.fields)]
                field_list.pop(field_list.index("id"))
                Dealership.objects.bulk_create([Dealership(**{key: values[i] for key, values in kwargs.items()})
                                                for i in range(len(kwargs["id"]))],
                                               update_conflicts=True,
                                               unique_fields=["id"],
                                               update_fields=field_list)
            elif model_str == 'userprofile':
                field_list = [model_field[1].attname for model_field in enumerate(UserProfile._meta.fields)]
                field_list.pop(field_list.index("id"))
                field_list.pop(field_list.index("user_id"))
                field_list.pop(field_list.index("dealership_id"))
                UserProfile.objects.bulk_create(objs=[UserProfile(**{key: values[i] for key, values in kwargs.items()})
                                                      for i in range(len(kwargs["user_id"]))],
                                                update_conflicts=True,
                                                unique_fields=["user_id", "dealership_id"],
                                                update_fields=field_list)
            else:
                raise Exception('Unknown Model')
        except Exception as e:
            print(f"{e} Happened When Creating {model_str}")

        return ""

    @staticmethod
    def get_exist_lists(list_from_input, id_list):
        # Get all ids from model objects
        exist_id_indices = []
        try:
            index = 0
            for obj_id in list_from_input:
                if obj_id in id_list:
                    exist_id_indices.append(index)
                index += 1

        except Exception as e:
            print(f"Exception Happened for {id_list} | {e}")

        return exist_id_indices


admin.site.register(UserProfile, UserProfileAdmin)
