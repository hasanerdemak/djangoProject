import operator
import string
import csv
from functools import reduce
from io import StringIO

from django.contrib import admin
from django.db.models import Case, When, F, Q
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
            created_user_profiles = None
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

            user_list, dealership_list, user_profile_list, csv_keys = self.abc(text)

            """
            Scenario 1: user_id exists
            Scenario 2: user_id not exists, but username exists
            Scenario 3: user_id not exists, username not exists, but first_name and last_name exist 
            """
            unique_user_field_for_dict, unique_user_field_for_user_query, unique_user_field_for_user_profile_query, \
            scenario = get_unique_field_name_for_query_and_dict(csv_keys)

            # If scenario is 3, then update same usernames
            if scenario == 3:
                username_list = [user.username for user in user_list]
                username_list = update_same_usernames(username_list, list(db_users.values_list("username", flat=True)))
                for i in range(len(user_list)):
                    user_list[i].username = username_list[i]

            db_users_unique_value_list = db_users.values_list(unique_user_field_for_user_query, flat=True)
            exist_users = []
            non_exist_users = []
            for user in reversed(
                    user_list):  # I traversed the list in reverse to make sure the last entity of the object is in the list
                if getattr(user, unique_user_field_for_user_query) in db_users_unique_value_list:
                    if user not in exist_users:
                        exist_users.append(user)
                elif user not in non_exist_users:
                    non_exist_users.append(user)

            db_dealerships_unique_value_list = db_dealerships.values_list("id", flat=True)
            exist_dealerships = []
            non_exist_dealerships = []
            for dealership in reversed(dealership_list):
                if dealership.id in db_dealerships_unique_value_list:
                    if dealership not in exist_dealerships:
                        exist_dealerships.append(dealership)
                elif dealership not in non_exist_dealerships:
                    non_exist_dealerships.append(dealership)


            db_user_profiles_unique_value_list = db_user_profiles.values_list(unique_user_field_for_user_profile_query,
                                                                              'dealership_id')
            exist_user_profiles = []
            non_exist_user_profiles = []
            for user_profile in reversed(user_profile_list):
                if (getattr(user_profile.user, unique_user_field_for_user_query), user_profile.dealership_id) in db_user_profiles_unique_value_list:
                    if user_profile not in exist_user_profiles:
                        exist_user_profiles.append(user_profile)
                elif user_profile not in non_exist_user_profiles:
                    non_exist_user_profiles.append(user_profile)

            if create_if_not_exist:
                # CREATE USERS
                if len(non_exist_users) != 0:
                    created_users, password_list_for_users = self.create_users(non_exist_users,
                                                                               unique_user_field_for_user_query)

                # CREATE DEALERSHIPS
                if len(non_exist_dealerships) != 0:
                    created_dealerships = self.create_dealerships(non_exist_dealerships)

            else:  # Send only exist users and dealerships
                for user_profile in non_exist_user_profiles:
                    if user_profile.user not in exist_users or user_profile.dealership not in exist_dealerships:
                        non_exist_user_profiles.pop(non_exist_user_profiles.index(user_profile))

            if len(non_exist_user_profiles) != 0:
                # To get the id fields of the created_users
                if scenario != 1:
                    user_list = User.objects.select_for_update().filter(
                        username__in=[user.username for user in user_list])
                    """
                    Alternatively, you can use:
                    for user in created_users:
                        user.refresh_from_db()
                    """
                    for user_profile in user_profile_list:
                        for user in user_list:
                            if user.username == user_profile.user.username:
                                user_profile.user.id = user.id

                created_user_profiles = self.create_user_profiles(non_exist_user_profiles)

            if len(exist_users) != 0:
                self.update_users(exist_users, csv_keys)

            if len(exist_dealerships) != 0:
                self.update_dealerships(exist_dealerships, csv_keys)

            if len(exist_user_profiles) != 0:
                query = reduce(operator.or_, (Q(user_id=u_id, dealership_id=d_id) for u_id, d_id in
                                              zip([userprofile.user.id for userprofile in exist_user_profiles],
                                                  [userprofile.dealership.id for userprofile in exist_user_profiles])))
                exist_user_profiles_with_old_values = UserProfile.objects.filter(query)

                for user_profile in exist_user_profiles:
                    for db_user_profile in exist_user_profiles_with_old_values:
                        if (user_profile.user.id, user_profile.dealership.id) == (
                                db_user_profile.user.id, db_user_profile.dealership.id):
                            user_profile.id = db_user_profile.id
                # Get User Profile values to update then UPDATE USER PROFILES
                self.update_user_profiles(exist_user_profiles, csv_keys)

            if created_users:
                created_users = zip(created_users, password_list_for_users)
            context = {"created_users": created_users,
                       "created_dealerships": created_dealerships,
                       "created_user_profiles": created_user_profiles,
                       "updated_users": exist_users,
                       "updated_dealerships": exist_dealerships,
                       "updated_user_profiles": exist_user_profiles,
                       "show_created_and_updated_objects": True,
                       }

            return render(request, "user/user_profile_add.html", context)

    def create_users(self, user_list_for_create, unique_field):
        created_users = None
        password_list_for_users = None
        try:
            field_list = [model_field[1].attname for model_field in enumerate(User._meta.fields)]

            password_list_for_users = [get_random_string(8, self.characters) for _ in range(len(user_list_for_create))]
            for index, user in enumerate(user_list_for_create):
                user.set_password(password_list_for_users[index])

            field_list.pop(field_list.index("id"))
            field_list.pop(field_list.index("username"))

            created_users = User.objects.bulk_create(user_list_for_create,
                                                     update_conflicts=True,
                                                     unique_fields=[unique_field],
                                                     update_fields=field_list)
        except Exception as e:
            print(f"{e} Happened When Creating User")

        return created_users, password_list_for_users

    @staticmethod
    def create_dealerships(dealership_list_for_create):
        created_dealerships = None
        try:
            field_list = [model_field[1].attname for model_field in enumerate(Dealership._meta.fields)]
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
    def create_user_profiles(user_profiles_list_for_create):
        created_user_profiles = None
        try:
            field_list = [model_field[1].attname for model_field in enumerate(UserProfile._meta.fields)]
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
    def update_users(updatable_users, dict_keys):
        try:
            updatable_fields = []
            user_fields_list = [model_field[1].attname for model_field in enumerate(User._meta.fields)]
            for key in dict_keys:
                if key.replace("user_", "") in user_fields_list and key != "user_id" and key != "is_active":
                    updatable_fields.append(key.replace("user_", ""))

            User.objects.bulk_update(updatable_users, updatable_fields)
        except Exception as e:
            print(f"{e} Happened When Updating User")
        return ""

    @staticmethod
    def update_dealerships(updatable_dealerships, dict_keys):
        try:
            updatable_fields = []
            dealership_fields_list = [model_field[1].attname for model_field in enumerate(Dealership._meta.fields)]
            for key in dict_keys:
                if key.replace("dealership_", "") in dealership_fields_list and key != "dealership_id":
                    updatable_fields.append(key.replace("dealership_", ""))

            Dealership.objects.bulk_update(updatable_dealerships, updatable_fields)
        except Exception as e:
            print(f"{e} Happened When Updating Dealership")
        return ""

    @staticmethod
    def update_user_profiles(updatable_user_profiles, dict_keys):
        try:
            updatable_fields = []
            user_profile_fields_list = [model_field[1].attname for model_field in enumerate(UserProfile._meta.fields)]
            for key in dict_keys:
                if key in user_profile_fields_list:
                    updatable_fields.append(key)

            UserProfile.objects.bulk_update(updatable_user_profiles, updatable_fields)
        except Exception as e:
            print(f"{e} Happened When Updating User Profile")
        return ""

    def abc(self, csv_string):
        user_list = []
        dealership_list = []
        user_profile_list = []
        csv_keys = []

        user_fields_list = [model_field[1].attname for model_field in enumerate(User._meta.fields)]
        dealership_fields_list = [model_field[1].attname for model_field in enumerate(Dealership._meta.fields)]
        user_profile_fields_list = [model_field[1].attname for model_field in enumerate(UserProfile._meta.fields)]

        # Use the StringIO class to create a file-like object from the CSV string
        f = StringIO(csv_string)
        # Create a DictReader object
        reader = csv.DictReader(f)

        # Read the CSV string into a list of dictionaries
        data = list(reader)

        csv_keys = data[0].keys()
        unique_user_field_for_dict, unique_user_field_for_user_query, unique_user_field_for_user_profile_query, \
        scenario = get_unique_field_name_for_query_and_dict(csv_keys)

        # Loop through the list of dictionaries
        for row in data:
            user = User()
            dealership = Dealership()
            user_profile = UserProfile()
            for key, value in row.items():
                if str(key).endswith("id"):
                    value = int(value)

                if key.replace("user_", "") in user_fields_list and key != "is_active":  # User
                    user.__setattr__(key.replace("user_", ""), value)
                elif key.replace("dealership_", "") in dealership_fields_list:  # Dealership
                    dealership.__setattr__(key.replace("dealership_", ""), value)
                elif key in user_profile_fields_list:  # User Profile
                    user_profile.__setattr__(key, value)

            # if username does not exist in the input
            if scenario != 2:
                user.username = user.first_name + user.last_name

            user_list.append(user)
            dealership_list.append(dealership)
            user_profile_list.append(user_profile)
            user_profile.user = user
            user_profile.dealership = dealership

        return user_list, dealership_list, user_profile_list, csv_keys


admin.site.register(UserProfile, UserProfileAdmin)
