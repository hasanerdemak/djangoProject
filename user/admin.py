import string
import csv
from io import StringIO

from django.contrib import admin
from django.db.models import Case, When, F
from django.shortcuts import render, redirect
from django.template.response import TemplateResponse
from django.urls import re_path
from django.utils.crypto import get_random_string

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
            password_list_for_users = None

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

            # user_list, dealership_list, user_profile_list = self.abc(text)

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

            non_exist_user_row_indices, exist_user_row_indices = get_exist_and_non_exist_lists(
                user_profile_dict[unique_user_field_for_dict],
                db_users.values_list(unique_user_field_for_user_query, flat=True).distinct())
            non_exist_dealership_row_indices, exist_dealership_row_indices = get_exist_and_non_exist_lists(
                user_profile_dict['dealership_id'], db_dealerships.values_list('id', flat=True).distinct())
            non_exist_user_profile_row_indices, exist_user_profile_row_indices = get_exist_and_non_exist_lists(
                merge_lists(user_profile_dict[unique_user_field_for_dict], user_profile_dict['dealership_id']),
                db_user_profiles.values_list(unique_user_field_for_user_profile_query, 'dealership_id').distinct())

            if create_if_not_exist:
                # CREATE USERS
                created_users, password_list_for_users = self.create_users(non_exist_user_row_indices,
                                                                           unique_user_field_for_dict,
                                                                           **user_profile_dict)

                # CREATE DEALERSHIPS
                created_dealerships = self.create_dealerships(non_exist_dealership_row_indices, **user_profile_dict)

                intersection_of_lists = non_exist_user_profile_row_indices
            else:  # Send only exist users and dealerships
                intersection_of_lists = set(non_exist_user_profile_row_indices) & set(exist_user_row_indices) & set(
                    exist_dealership_row_indices)

            created_user_profiles = self.create_user_profiles(intersection_of_lists, unique_user_field_for_dict,
                                                              **user_profile_dict)

            exist_users_unique_values = [user_profile_dict[unique_user_field_for_dict][i] for i in exist_user_row_indices]
            exist_users = []
            for user in db_users:
                if getattr(user, unique_user_field_for_user_query) in exist_users_unique_values \
                        and user not in exist_users:
                    exist_users.append(user)
            # Get User values to update then UPDATE USERS
            self.update_users(exist_users, exist_user_row_indices, unique_user_field_for_dict,
                              **user_profile_dict)

            exist_dealerships_unique_values = [user_profile_dict["dealership_id"][i] for i in exist_dealership_row_indices]
            exist_dealerships = []
            for dealership in db_dealerships:
                if getattr(dealership, "id") in exist_dealerships_unique_values \
                        and dealership not in exist_dealerships:
                    exist_dealerships.append(dealership)
            # Get Dealership values to update then UPDATE DEALERSHIPS
            self.update_dealerships(exist_dealerships, exist_dealership_row_indices, **user_profile_dict)

            user_profiles_user_dealership_tuples = [
                (user_profile_dict[unique_user_field_for_dict][i], user_profile_dict["dealership_id"][i]) for i in
                exist_user_profile_row_indices]
            exist_user_profiles = []
            for user_profile in db_user_profiles:
                if (
                        getattr(getattr(user_profile, "user"), unique_user_field_for_user_query),
                        getattr(user_profile, "dealership_id")) \
                        in user_profiles_user_dealership_tuples and user_profile not in exist_user_profiles:
                    exist_user_profiles.append(user_profile)
            # Get User Profile values to update then UPDATE USER PROFILES
            self.update_user_profiles(exist_user_profiles, exist_user_profile_row_indices,
                                      unique_user_field_for_dict, **user_profile_dict)

            if created_users:
                created_users = zip(created_users, password_list_for_users)
            context = {"created_users": created_users,
                       "created_dealerships": created_dealerships,
                       "created_user_profiles": created_user_profiles,
                       "updated_users": exist_users,
                       "updated_dealerships": exist_dealerships,
                       "updated_user_profiles": exist_user_profiles,
                       "password_list": password_list_for_users,
                       "show_created_and_updated_objects": True,
                       }

            return render(request, "user/user_profile_add.html", context)

    def create_users(self, non_exist_users_row_indices, unique_user_field_for_dict=None, **kwargs):
        created_users = None
        password_list_for_users = None
        try:
            if unique_user_field_for_dict == 'user_id':
                unique_fields = ['id']
                kwargs["id"] = [kwargs[unique_user_field_for_dict][i] for i in
                                non_exist_users_row_indices]
            else:
                unique_fields = ['username']
                kwargs["username"] = [kwargs[unique_user_field_for_dict][i] for i in
                                      non_exist_users_row_indices]

            field_list = [model_field[1].attname for model_field in enumerate(User._meta.fields)]

            user_list_for_create = [User(**{key: values[i] for key, values in kwargs.items() if key in field_list})
                                    for i in range(len(kwargs[unique_fields[0]]))]

            password_list_for_users = [get_random_string(8, self.characters) for _ in non_exist_users_row_indices]
            for index, user in enumerate(user_list_for_create):
                user.set_password(password_list_for_users[index])

            field_list.pop(field_list.index("id"))
            field_list.pop(field_list.index("username"))

            created_users = User.objects.bulk_create(user_list_for_create,
                                                     update_conflicts=True,
                                                     unique_fields=unique_fields,
                                                     update_fields=field_list)
        except Exception as e:
            print(f"{e} Happened When Creating User")

        return created_users, password_list_for_users

    @staticmethod
    def create_dealerships(non_exist_dealerships_row_indices, **kwargs):
        created_dealerships = None
        try:
            if "dealership_group_id" not in kwargs:
                kwargs["group_id"] = [1 for _ in non_exist_dealerships_row_indices]

            field_list = [model_field[1].attname for model_field in enumerate(Dealership._meta.fields)]

            dealership_list_for_create = [
                Dealership(**{key.replace("dealership_", ""): values[i] for key, values in kwargs.items() if
                              key.replace("dealership_", "") in field_list}) for i in non_exist_dealerships_row_indices]

            field_list.pop(field_list.index("id"))
            created_dealerships = Dealership.objects.bulk_create(
                dealership_list_for_create,
                update_conflicts=True,
                unique_fields=["id"],
                update_fields=field_list)

        except Exception as e:
            print(f"{e} Happened When Creating Dealership")

        return created_dealerships

    @staticmethod
    def create_user_profiles(non_exist_user_profiles_row_indices, unique_user_field_for_dict=None, **kwargs):
        created_user_profiles = None
        try:
            if "is_active" in kwargs:
                kwargs["is_active"] = [kwargs["is_active"][i] for i in non_exist_user_profiles_row_indices]
            else:
                kwargs["is_active"] = [True for _ in non_exist_user_profiles_row_indices]

            if unique_user_field_for_dict != "user_id":
                query_list = [kwargs["username"][i] for i in non_exist_user_profiles_row_indices]
                preserved = Case(
                    *[When(username=val, then=pos) for pos, val in enumerate(query_list)],
                    default=len(query_list))
                kwargs['user_id'] = list(User.objects.annotate(
                    my_user_id=Case(When(username__in=query_list, then='id'), )).filter(
                    id__in=F('my_user_id')).values_list('my_user_id', flat=True).order_by(preserved))

            field_list = [model_field[1].attname for model_field in enumerate(UserProfile._meta.fields)]

            # if the scenario is 2 or 3
            user_profiles_list_for_create = [
                UserProfile(**{key: values[i] for key, values in kwargs.items() if key in field_list})
                for i in non_exist_user_profiles_row_indices]

            field_list.pop(field_list.index("id"))
            field_list.pop(field_list.index("user_id"))
            field_list.pop(field_list.index("dealership_id"))
            created_user_profiles = UserProfile.objects.bulk_create(
                objs=user_profiles_list_for_create,
                update_conflicts=True,
                unique_fields=["user_id", "dealership_id"],
                update_fields=field_list)
        except Exception as e:
            print(f"{e} Happened When Creating User Profile")

        return created_user_profiles

    @staticmethod
    def update_users(updatable_users, exist_users_row_indices, unique_user_field_for_dict=None, **kwargs):
        try:
            if unique_user_field_for_dict == "user_id":
                id_list = [kwargs[unique_user_field_for_dict][i] for i in
                           exist_users_row_indices]

                unique_field_list = [updatable_user.id for updatable_user in updatable_users]
                exist_users_row_indices = reorder_list(unique_field_list, id_list)
            else:
                username_list = [kwargs[unique_user_field_for_dict][i] for i in
                                 exist_users_row_indices]

                unique_field_list = [updatable_user.username for updatable_user in updatable_users]
                exist_users_row_indices = reorder_list(unique_field_list, username_list)

            updatable_fields = []
            user_fields_list = [model_field[1].attname for model_field in enumerate(User._meta.fields)]
            for user, index in zip(updatable_users, exist_users_row_indices):
                for key, values in kwargs.items():
                    if key.replace("user_", "") in user_fields_list and key != "user_id" and key != "is_active":
                        setattr(user, key.replace("user_", ""), values[index])
                        updatable_fields.append(key.replace("user_", ""))

            User.objects.bulk_update(updatable_users, updatable_fields)
        except Exception as e:
            print(f"{e} Happened When Updating User")
        return ""

    @staticmethod
    def update_dealerships(updatable_dealerships, exist_dealerships_row_indices, **kwargs):
        try:
            kwargs["name"] = [kwargs["dealership_name"][i] for i in exist_dealerships_row_indices]
            kwargs["group_id"] = [1 for _ in exist_dealerships_row_indices]

            kwargs.pop("dealership_name")

            id_list = [kwargs["dealership_id"][i] for i in exist_dealerships_row_indices]
            unique_field_list = [updatable_object.id for updatable_object in updatable_dealerships]
            exist_objects_indices = reorder_list(unique_field_list, id_list)

            updatable_fields = []
            dealership_fields_list = [model_field[1].attname for model_field in enumerate(Dealership._meta.fields)]
            for obj, index in zip(updatable_dealerships, exist_objects_indices):
                for key, values in kwargs.items():
                    if key.replace("dealership_", "") in dealership_fields_list and key != "dealership_id":
                        setattr(obj, key.replace("dealership_", ""), values[index])
                        updatable_fields.append(key.replace("dealership_", ""))

            Dealership.objects.bulk_update(updatable_dealerships, updatable_fields)
        except Exception as e:
            print(f"{e} Happened When Updating Dealership")
        return ""

    @staticmethod
    def update_user_profiles(updatable_user_profiles, exist_user_profiles_row_indices, unique_user_field_for_dict,
                             **kwargs):
        try:
            if "is_active" in kwargs:
                kwargs["is_active"] = [kwargs["is_active"][i] for i in exist_user_profiles_row_indices]

            if unique_user_field_for_dict != "user_id":
                query_list = [kwargs["username"][i] for i in exist_user_profiles_row_indices]
                preserved = Case(
                    *[When(username=val, then=pos) for pos, val in enumerate(query_list)],
                    default=len(query_list))
                kwargs['user_id'] = list(User.objects.annotate(
                    my_user_id=Case(When(username__in=query_list, then='id'), )).filter(
                    id__in=F('my_user_id')).values_list('my_user_id', flat=True).order_by(preserved))

            unique_field_list = [(updatable_object.user.id, updatable_object.dealership.id) for updatable_object
                                 in updatable_user_profiles]
            exist_user_profiles_row_indices = reorder_list(
                unique_field_list, merge_lists(kwargs["user_id"], kwargs['dealership_id']))

            updatable_fields = []
            user_profile_fields_list = [model_field[1].attname for model_field in enumerate(UserProfile._meta.fields)]
            for user_profile, index in zip(updatable_user_profiles, exist_user_profiles_row_indices):
                for key, values in kwargs.items():
                    if key in user_profile_fields_list and key != "is_active":
                        setattr(user_profile, key, values[index])
                        updatable_fields.append(key)

            UserProfile.objects.bulk_update(updatable_user_profiles, updatable_fields)
        except Exception as e:
            print(f"{e} Happened When Updating User Profile")
        return ""

    def abc(self, csv_string):
        user_list = []
        dealership_list = []
        user_profile_list = []

        user_fields_list = [model_field[1].attname for model_field in enumerate(User._meta.fields)]
        dealership_fields_list = [model_field[1].attname for model_field in enumerate(Dealership._meta.fields)]
        user_profile_fields_list = [model_field[1].attname for model_field in enumerate(UserProfile._meta.fields)]

        # Use the StringIO class to create a file-like object from the CSV string
        f = StringIO(csv_string)
        # Create a DictReader object
        reader = csv.DictReader(f)

        # Read the CSV string into a list of dictionaries
        data = list(reader)

        # Loop through the list of dictionaries
        for row in data:
            user = User()
            dealership = Dealership()
            user_profile = UserProfile()
            for key, value in row.items():
                if key.replace("user_", "") in user_fields_list and key != "is_active":
                    user.__setattr__(key.replace("user_", ""), value)
                if key.replace("dealership_", "") in dealership_fields_list:
                    dealership.__setattr__(key.replace("dealership_", ""), value)
                if key in user_profile_fields_list:
                    user_profile.__setattr__(key, value)
            user_list.append(user)
            dealership_list.append(dealership)
            user_profile_list.append(user_profile)

        return user_list, dealership_list, user_profile_list


admin.site.register(UserProfile, UserProfileAdmin)
