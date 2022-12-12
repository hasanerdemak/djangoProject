import contextlib
import random
import string

from django.contrib import admin
from django.contrib.auth.hashers import make_password
from django.shortcuts import render, redirect
from django.template.response import TemplateResponse
from django.urls import re_path

from user.utils import *
from .models import UserProfile

# TODO add comments

# A list of required fields that must be present in the CSV file
REQUIRED_FIELDS = ("user_id", "dealership_id", "dealership_name", "first_name", "last_name")


class UserProfileAdmin(admin.ModelAdmin):
    change_list_template = "user/my_user_profile_change_list.html"
    list_display = ["user", "dealership", "is_active"]
    readonly_fields = ["dealership_name", "first_name", "last_name", "email"]
    fields = ["user", "dealership", "is_active", "dealership_name", "first_name", "last_name", "email"]
    search_fields = ["user__username", "user__first_name", "user__last_name", "user__email", "dealership__name"]
    # A string containing all the allowed characters for the random password generator
    characters = string.ascii_letters + string.digits + string.punctuation

    class Meta:
        model = UserProfile

    def get_urls(self):
        # Get the default URLs for the UserProfileAdmin view
        urls = super().get_urls()
        # Add a custom URL for the addUserProfile view
        my_urls = [
            re_path(r'^addUserProfile$', self.admin_site.admin_view(self.check_buttons), name='addUserProfile'),
        ]
        return my_urls + urls

    def get_queryset(self, request):
        query = super(UserProfileAdmin, self).get_queryset(request)
        filtered_query = query.filter(is_active=True)
        return filtered_query

    def check_buttons(self, request):
        # Initialize the context dictionary with default values
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
                   "error": None,
                   "show_created_and_updated_objects": True,
                   "created_users": User.objects.all()}

        # Get the values of the "error_check_button" and "create_button" fields
        error_check_button = request.POST.get("error-check-button")
        create_button = request.POST.get("create-button")

        # If neither button was clicked (i.e. the page was just opened)
        if error_check_button is None and create_button is None:
            return TemplateResponse(request, "user/user_profile_add.html", context)
        # If the Error Check button was clicked.
        elif create_button is None:
            # Call the error_check() method to check for errors in the input
            return self.error_check(request)
        # If the Create User Profile button was clicked.
        else:
            # Call the add_user_profile() method to create and update user, dealership and user profile
            return self.add_user_profile(request)

    @staticmethod
    def error_check(request):
        # Check if form-check-box-1 is clicked
        create_if_not_exist = True if (request.POST.get("form-check-box-1") is not None) else False

        # Get the text in the "form-text-area" and remove any trailing new line characters
        text = request.POST.get("form-text-area").rstrip("\r\n")

        user_profile_dict = read_csv_as_dict(text)

        # Initialize the first values of the variables that will pass to the template as context
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

        non_valid_field_indices = get_non_valid_field_indices(user_profile_dict.keys())
        # If there is no non-valid field then check other errors
        if not non_valid_field_indices:
            non_exist_required_fields_list = [field for field in REQUIRED_FIELDS if field not in user_profile_dict]
            # If there is no non-exist required field then check other errors
            if not non_exist_required_fields_list:
                # Missing spaces check
                missing_spaces_rows, missing_spaces_cols, missing_spaces_messages = \
                    get_missing_spaces_indices_and_messages(user_profile_dict)

                # Non-valid spaces check
                non_valid_spaces_rows, non_valid_spaces_cols, non_valid_messages = \
                    get_non_valid_spaces_indices_and_messages(user_profile_dict)

                # Non-unique spaces check
                non_unique_rows, non_unique_cols, non_unique_messages = \
                    get_non_unique_spaces_indices_and_messages(user_profile_dict)

                if not (len(missing_spaces_rows) or len(non_valid_spaces_rows) or len(non_unique_rows)):
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

            user_profile_dict = read_csv_as_dict(text)

            for key in user_profile_dict:
                col_type = get_col_type(key)
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
            # 2- username
            # 3- firstname+lastname

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
