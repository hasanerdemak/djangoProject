import contextlib
import random
import string

from django.contrib import admin
from django.contrib.auth.hashers import make_password
from django.db.models import Case, When, F
from django.shortcuts import render, redirect
from django.template.response import TemplateResponse
from django.urls import re_path

from user.utils import *
from .models import UserProfile


# TODO add comments


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
                   "show_created_and_updated_objects": False,
                   }

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
        # Convert the text to dictionary
        user_profile_dict = read_csv_as_dict(text)
        # Setting up required fields for scenarios
        required_fields = ["dealership_id", "dealership_name"]
        required_fields, scenario = set_required_fields_with_scenario(required_fields, user_profile_dict.keys())

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
        error = None

        non_valid_field_indices = get_non_valid_field_indices(user_profile_dict.keys())
        # If there is no non-valid field then check other errors
        if not non_valid_field_indices:
            non_exist_required_fields_list = [field for field in required_fields if field not in user_profile_dict]
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
                    get_non_unique_spaces_indices_and_messages(user_profile_dict, scenario)

                # If there is no error then is_valid is true
                if not (len(missing_spaces_rows) or len(non_valid_spaces_rows) or len(non_unique_rows)):
                    is_valid = True
                else:  # is_valid is false
                    error = "Please Click On The Wrong Cells To Edit The Text"

            else:  # If there is non-exist required field
                non_valid_field_indices = []
                show_table = "false"
                error = f"{non_exist_required_fields_list} Field(s) Must Be Exist"
        else:  # If there is non-valid field name
            error = "Please Correct The Field Names First"

        # Assign final values of the variables that will pass to the template as context
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
                   "error": error,
                   "show_created_and_updated_objects": False}
        return render(request, "user/user_profile_add.html", context)

    def add_user_profile(self, request):
        if request.method == "GET":
            return redirect("/admin/user/userprofile")
        else:  # POST
            created_users = None
            created_dealerships = None
            password_list = None

            db_users = None
            db_dealerships = None
            db_user_profiles = None
            try:
                # Fetch all user and dealership ids over UserProfile table
                db_users = User.objects.all()
                db_dealerships = Dealership.objects.all()
                db_user_profiles = UserProfile.objects.select_related("user", "dealership")
            except Exception as e:
                print(f"{e} Happened When Fetching Objects From DB")

            create_if_not_exist = True if (request.POST.get("form-check-box-1") is not None) else False
            # Get the text in the "form-text-area" and remove any trailing new line characters
            text = request.POST.get("form-text-area").rstrip("\r\n")
            # Convert the text to dictionary
            user_profile_dict = read_csv_as_dict(text)

            for key in user_profile_dict:
                col_type = get_col_type(key)
                if col_type in MODEL_FIELD_TYPES['int']:
                    user_profile_dict[key] = list(map(int, user_profile_dict[key]))

            """
            Scenario 1: user_id exists
            Scenario 2: user_id not exists, but username exists
            Scenario 3: user_id not exists, username not exists, but first_name and last_name exist 
            """
            unique_user_field_for_dict, unique_user_field_for_user_query, unique_user_field_for_user_profile_query, \
            scenario = get_unique_field_name_for_query_and_dict(user_profile_dict)

            # if username does not exist in the input
            if scenario != 2:
                user_profile_dict["username"] = list(
                    map(str.__add__, user_profile_dict['first_name'], user_profile_dict['last_name']))

            if scenario == 3:
                user_profile_dict["username"] = update_same_usernames(user_profile_dict["username"],
                                                                      list(db_users.values_list("username", flat=True)))

            non_exist_user_id_indices, exist_user_id_indices = self.get_exist_and_non_exist_lists(
                user_profile_dict[unique_user_field_for_dict],
                db_users.values_list(unique_user_field_for_user_query, flat=True).distinct())
            non_exist_dealership_id_indices, exist_dealership_id_indices = self.get_exist_and_non_exist_lists(
                user_profile_dict['dealership_id'], db_dealerships.values_list('id', flat=True).distinct())
            non_exist_user_profile_id_indices, exist_user_profile_id_indices = self.get_exist_and_non_exist_lists(
                merge_lists(user_profile_dict[unique_user_field_for_dict], user_profile_dict['dealership_id']),
                db_user_profiles.values_list(unique_user_field_for_user_profile_query, 'dealership_id').distinct())

            if create_if_not_exist:
                # CREATE USERS
                new_users_values_to_create_dict, password_list = self.get_obj_values_as_dict("user", user_profile_dict,
                                                                                             non_exist_user_id_indices,
                                                                                             unique_user_field_for_dict)
                created_users = self.create_objects("user", unique_user_field_for_dict,
                                                    **new_users_values_to_create_dict)

                # CREATE DEALERSHIPS
                new_dealerships_values_to_create_dict, _ = self.get_obj_values_as_dict("dealership", user_profile_dict,
                                                                                       non_exist_dealership_id_indices,
                                                                                       unique_user_field_for_dict)
                created_dealerships = self.create_objects("dealership", **new_dealerships_values_to_create_dict)

                intersection_of_lists = non_exist_user_profile_id_indices
            else:  # Send only exist users and dealerships
                intersection_of_lists = set(non_exist_user_profile_id_indices) & set(exist_user_id_indices) & set(
                    exist_dealership_id_indices)

            user_profiles_values_to_create_dict, _ = self.get_obj_values_as_dict("userprofile", user_profile_dict,
                                                                                 intersection_of_lists)
            created_user_profiles = self.create_objects("userprofile", **user_profiles_values_to_create_dict)

            # Get User values to update then UPDATE USERS
            users_values_to_update_dict, _ = self.get_obj_values_as_dict("user", user_profile_dict,
                                                                         exist_user_id_indices,
                                                                         unique_user_field_for_dict)
            wanted_users_values = [user_profile_dict[unique_user_field_for_dict][i] for i in exist_user_id_indices]
            updatable_users = self.get_exist_objects("user", wanted_users_values, db_users, unique_user_field_for_dict)
            self.update_objects("user", updatable_users, unique_user_field_for_dict,
                                **users_values_to_update_dict)

            # Get Dealership values to update then UPDATE DEALERSHIPS
            dealerships_values_to_update_dict, _ = self.get_obj_values_as_dict("dealership", user_profile_dict,
                                                                               exist_dealership_id_indices,
                                                                               unique_user_field_for_dict)
            wanted_dealerships_values = [user_profile_dict["dealership_id"][i] for i in exist_dealership_id_indices]
            updatable_dealerships = self.get_exist_objects("dealership", wanted_dealerships_values, db_dealerships)
            self.update_objects("dealership", updatable_dealerships,
                                **dealerships_values_to_update_dict)

            # Get User Profile values to update then UPDATE USER PROFILES
            user_profiles_values_to_update_dict, _ = self.get_obj_values_as_dict("userprofile", user_profile_dict,
                                                                                 exist_user_profile_id_indices)
            wanted_user_profiles_values = [
                (user_profiles_values_to_update_dict["user_id"][i], user_profile_dict["dealership_id"][i]) for i in
                exist_user_profile_id_indices]
            updatable_user_profiles = self.get_exist_objects("userprofile", wanted_user_profiles_values,
                                                             db_user_profiles)
            self.update_objects("userprofile", updatable_user_profiles,
                                unique_user_field_for_dict,
                                **user_profiles_values_to_update_dict)

            if created_users:
                created_users = zip(created_users, password_list)
            context = {"created_users": created_users,
                       "created_dealerships": created_dealerships,
                       "created_user_profiles": created_user_profiles,
                       "updated_users": updatable_users,
                       "updated_dealerships": updatable_dealerships,
                       "updated_user_profiles": updatable_user_profiles,
                       "password_list": password_list,
                       "show_created_and_updated_objects": True,
                       }

            return render(request, "user/user_profile_add.html", context)

    @staticmethod
    def create_objects(model_str, unique_user_field_for_dict=None, **kwargs):
        created_objects = None
        try:
            if model_str == 'user':
                if unique_user_field_for_dict == 'user_id':
                    unique_fields = ['id']
                else:
                    unique_fields = ['username']

                field_list = [model_field[1].attname for model_field in enumerate(User._meta.fields)]
                field_list.pop(field_list.index("id"))
                field_list.pop(field_list.index("username"))

                created_objects = User.objects.bulk_create([User(**{key: values[i] for key, values in kwargs.items()})
                                                            for i in range(len(kwargs[unique_fields[0]]))],
                                                           update_conflicts=True,
                                                           unique_fields=unique_fields,
                                                           update_fields=field_list)
            elif model_str == 'dealership':
                field_list = [model_field[1].attname for model_field in enumerate(Dealership._meta.fields)]
                field_list.pop(field_list.index("id"))
                created_objects = Dealership.objects.bulk_create(
                    [Dealership(**{key: values[i] for key, values in kwargs.items()})
                     for i in range(len(kwargs["id"]))],
                    update_conflicts=True,
                    unique_fields=["id"],
                    update_fields=field_list)
            elif model_str == 'userprofile':
                field_list = [model_field[1].attname for model_field in enumerate(UserProfile._meta.fields)]
                field_list.pop(field_list.index("id"))
                field_list.pop(field_list.index("user_id"))
                field_list.pop(field_list.index("dealership_id"))
                # if the scenario is 2 or 3

                created_objects = UserProfile.objects.bulk_create(
                    objs=[UserProfile(**{key: values[i] for key, values in kwargs.items()})
                          for i in range(len(kwargs["user_id"]))],
                    update_conflicts=True,
                    unique_fields=["user_id", "dealership_id"],
                    update_fields=field_list)
            else:
                raise Exception('Unknown Model')
        except Exception as e:
            print(f"{e} Happened When Creating {model_str}")

        return created_objects

    @staticmethod
    def update_objects(model_str, updatable_objects, unique_user_field_for_dict=None, **kwargs):
        try:
            if model_str == 'user':
                if unique_user_field_for_dict == "user_id":
                    unique_field_list = [updatable_object.id for updatable_object in updatable_objects]
                    exist_objects_indices = reorder_list(unique_field_list, kwargs["id"])
                    kwargs.pop("id")
                else:
                    unique_field_list = [updatable_object.username for updatable_object in updatable_objects]
                    exist_objects_indices = reorder_list(unique_field_list, kwargs["username"])
                    kwargs.pop("username")

            elif model_str == 'dealership':
                unique_field_list = [updatable_object.id for updatable_object in updatable_objects]
                exist_objects_indices = reorder_list(unique_field_list, kwargs["id"])
                kwargs.pop("id")
            elif model_str == 'userprofile':
                unique_field_list = [(updatable_object.user.id, updatable_object.dealership.id) for updatable_object
                                     in updatable_objects]
                exist_objects_indices = reorder_list(
                    unique_field_list, merge_lists(kwargs["user_id"], kwargs['dealership_id']))
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

    def get_obj_values_as_dict(self, model_str, user_profile_dict, wanted_rows_indices,
                               unique_user_field_for_dict=None):
        new_obj_values_dict = dict()
        password_list_for_users = None

        model_str = str(model_str).strip().lower()

        if model_str == 'user':
            model_instance = User()
            if unique_user_field_for_dict == 'username':
                new_obj_values_dict["username"] = [user_profile_dict[unique_user_field_for_dict][i] for i in
                                                   wanted_rows_indices]
            # unique_user_field_for_dict='user_id'
            else:
                new_obj_values_dict["id"] = [user_profile_dict[unique_user_field_for_dict][i] for i in
                                             wanted_rows_indices]

            password_list_for_users = [''.join(random.choice(self.characters) for _ in range(8)) for _ in
                                       wanted_rows_indices]
            new_obj_values_dict["password"] = [make_password(password) for password in password_list_for_users]
        elif model_str == 'dealership':
            model_instance = Dealership()
            new_obj_values_dict["id"] = [user_profile_dict["dealership_id"][i] for i in wanted_rows_indices]
            new_obj_values_dict["name"] = [user_profile_dict["dealership_name"][i] for i in wanted_rows_indices]
            new_obj_values_dict["group_id"] = [1 for _ in wanted_rows_indices]

        elif model_str == "userprofile":
            model_instance = UserProfile()
            if "is_active" in user_profile_dict:
                new_obj_values_dict["is_active"] = [user_profile_dict["is_active"][i] for i in wanted_rows_indices]
            else:
                new_obj_values_dict["is_active"] = [True for _ in wanted_rows_indices]

            if unique_user_field_for_dict != "user_id":
                query_list = [user_profile_dict["username"][i] for i in wanted_rows_indices]
                preserved = Case(
                    *[When(username=val, then=pos) for pos, val in enumerate(query_list)],
                    default=len(query_list))
                new_obj_values_dict['user_id'] = list(User.objects.annotate(
                    my_user_id=Case(When(username__in=query_list, then='id'), )).filter(
                    id__in=F('my_user_id')).values_list('my_user_id', flat=True).order_by(preserved))

        else:
            raise Exception('Unknown Model')

        for key in user_profile_dict:
            if key != "is_active":
                with contextlib.suppress(KeyError, FieldDoesNotExist):
                    model_instance._meta.get_field(key)
                    new_obj_values_dict[key] = [user_profile_dict[key][i] for i in wanted_rows_indices]

        return new_obj_values_dict, password_list_for_users

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

    @staticmethod
    def get_exist_objects(model_str, wanted_list_from_input, db_objects, unique_user_field_for_dict=None):
        exist_objects = []
        if model_str == "user":
            for user in db_objects:
                if unique_user_field_for_dict == "user_id":
                    if user.id in wanted_list_from_input and user not in exist_objects:
                        exist_objects.append(user)
                else:
                    if user.username in wanted_list_from_input and user not in exist_objects:
                        exist_objects.append(user)
        elif model_str == "dealership":
            for dealership in db_objects:
                if dealership.id in wanted_list_from_input and dealership not in exist_objects:
                    exist_objects.append(dealership)
        elif model_str == "userprofile":
            user_dealership_unique_field_tuples_list = [(userprofile.user.id, userprofile.dealership.id) for
                                                        userprofile in db_objects if
                                                        userprofile.user and userprofile.dealership]
            for user_profile, user_dealership_id_tuple in zip(db_objects, user_dealership_unique_field_tuples_list):
                if user_dealership_id_tuple in wanted_list_from_input and user_profile not in exist_objects:
                    exist_objects.append(user_profile)
        else:
            raise Exception('Unknown Model')
        return exist_objects


admin.site.register(UserProfile, UserProfileAdmin)
