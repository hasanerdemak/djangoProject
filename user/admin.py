import operator
import string
from functools import reduce

from django.contrib import admin
from django.db.models import Q
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

    def error_check(self, request):
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
            non_existing_required_fields_list = [field for field in required_fields if field not in user_profile_dict]
            # If there is no non-existing required field then check other errors
            if not non_existing_required_fields_list:
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

            else:  # If there is non-existing required field
                non_valid_field_indices = []
                show_table = "false"
                error = f"{non_existing_required_fields_list} Field(s) Must Be Exist"
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
            created_users = []
            created_dealerships = []
            created_user_profiles = []
            password_list_for_users = []

            create_if_not_exist = True if (request.POST.get("form-check-box-1") is not None) else False
            # Get the text in the "form-text-area" and remove any trailing new line characters
            text = request.POST.get("form-text-area").rstrip("\r\n")

            user_list, dealership_list, user_profile_list, csv_keys = create_obj_lists_from_csv(text)

            """
                Scenario 1: user_id exists
                Scenario 2: user_id not exists, but username exists
                Scenario 3: user_id not exists, username not exists, but first_name and last_name exist 
            """
            scenario = check_which_scenario(csv_keys)
            unique_user_field_for_user_query = "id" if scenario == 1 else "username"

            db_user_ids_and_usernames = None
            db_dealership_ids_set = None
            db_user_profile_unique_values_set = None
            try:
                db_user_ids_and_usernames = User.objects.only("id", "username").values_list("id", "username")
                db_dealership_ids_set = set(Dealership.objects.only("id").filter(
                    id__in=[dealership.id for dealership in dealership_list]).values_list("id", flat=True))
                # Determine the fields to retrieve
                fields = ("user_id", "dealership_id") if scenario == 1 else ("user__username", "dealership_id")
                # Use .only() or .defer() to select only the necessary fields
                db_user_profile_unique_values_set = set(UserProfile.objects.only(*fields).values_list(*fields))
            except Exception as e:
                print(f"{e} Happened When Fetching Objects From DB")

            # If scenario is 3, then update same usernames
            if scenario == 3:
                # Get the list of existing usernames from the database and update the same usernames in the list
                updated_usernames = update_same_usernames([user.username for user in user_list],
                                                          db_user_ids_and_usernames.values_list("username", flat=True))
                [setattr(user_list[i], 'username', updated_usernames[i]) for i in range(len(user_list))]

            # Get existing and non-existing users to update or create them
            db_users_unique_values_set = set(
                db_user_ids_and_usernames.values_list(unique_user_field_for_user_query, flat=True))
            existing_users = [user for user in user_list if
                              getattr(user, unique_user_field_for_user_query) in db_users_unique_values_set]
            non_existing_users = [user for user in user_list if
                                  getattr(user, unique_user_field_for_user_query) not in db_users_unique_values_set]

            # Get existing and non-existing dealerships to update or create them
            existing_dealerships = [dealership for dealership in dealership_list if
                                    dealership.id in db_dealership_ids_set]
            non_existing_dealerships = [dealership for dealership in dealership_list if
                                        dealership.id not in db_dealership_ids_set]

            # Get existing and non-existing user_profiles to update or create them
            existing_user_profiles = [user_profile for user_profile in user_profile_list if (
                getattr(user_profile.user, unique_user_field_for_user_query),
                user_profile.dealership_id) in db_user_profile_unique_values_set]
            non_existing_user_profiles = [user_profile for user_profile in user_profile_list if (
                getattr(user_profile.user, unique_user_field_for_user_query),
                user_profile.dealership_id) not in db_user_profile_unique_values_set]

            if create_if_not_exist:
                # Create non-existing Users
                created_users, password_list_for_users = self.create_users(non_existing_users,
                                                                           unique_user_field_for_user_query)
                # Create non-existing Dealerships
                created_dealerships = self.create_dealerships(non_existing_dealerships)

            else:
                # If non-existing users and dealerships was not created,
                # then send only user profiles that have existing users and dealerships
                for i in range(len(non_existing_user_profiles)):
                    if non_existing_user_profiles[i].user not in existing_users or \
                            non_existing_user_profiles[i].dealership not in existing_dealerships:
                        non_existing_user_profiles.pop(i)

            # If the scenario is not 1, then we must have the ids of the Users that connected to User Profiles
            if scenario != 1:
                user_profiles_users = User.objects.select_for_update().filter(
                    username__in=[user_profile.user.username for user_profile in user_profile_list])

                # Create a dictionary that maps username to user ID
                username_to_id = {user.username: user.id for user in user_profiles_users}
                # Use the dictionary to look up the user ID for each user profile
                for user_profile in user_profile_list:
                    user_id = username_to_id.get(user_profile.user.username)
                    if user_id is not None:
                        user_profile.user.id = user_id

            if len(non_existing_user_profiles) != 0:
                created_user_profiles = self.create_user_profiles(non_existing_user_profiles)

            # We need to have ids of the User Profiles to update them.
            # To do that get user profiles values with user_id and dealership_id
            query = reduce(operator.or_, (Q(user__id=user_profile.user.id) & Q(dealership_id=user_profile.dealership_id)
                                          for user_profile in existing_user_profiles))
            db_user_profiles = UserProfile.objects.filter(query)

            db_user_profiles_dict = {(db_user_profile.user.id, db_user_profile.dealership.id): db_user_profile for
                                     db_user_profile in db_user_profiles}
            for user_profile in user_profile_list:
                key = (user_profile.user.id, user_profile.dealership.id)
                if key in db_user_profiles_dict:
                    user_profile.id = db_user_profiles_dict[key].id

            # Update existing objects
            self.update_users(existing_users, csv_keys)
            self.update_dealerships(existing_dealerships, csv_keys)
            self.update_user_profiles(existing_user_profiles, csv_keys)

            created_user_profiles = [user_profile for user_profile in user_profile_list if
                                     user_profile.is_active == "1" and user_profile in created_user_profiles]
            existing_user_profiles = [user_profile for user_profile in user_profile_list if
                                      user_profile.is_active == "1" and user_profile in existing_user_profiles]
            deleted_user_profiles = [user_profile for user_profile in user_profile_list if
                                     user_profile.is_active == "0"]

            if len(created_users) != 0:
                created_users = zip(created_users, password_list_for_users)
            context = {"created_users": created_users,
                       "created_dealerships": created_dealerships,
                       "created_user_profiles": created_user_profiles,
                       "updated_users": existing_users,
                       "updated_dealerships": existing_dealerships,
                       "updated_user_profiles": existing_user_profiles,
                       "deleted_user_profiles": deleted_user_profiles,
                       "show_created_and_updated_objects": True,
                       }

            return render(request, "user/user_profile_add.html", context)

    def create_users(self, user_list_for_create, unique_field):
        created_users = []
        password_list_for_users = []
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

    def create_dealerships(self, dealership_list_for_create):
        created_dealerships = []
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

    def create_user_profiles(self, user_profiles_list_for_create):
        created_user_profiles = []
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

    def update_users(self, updatable_users, dict_keys):
        try:
            updatable_fields = ["username"]
            user_fields_list = [model_field[1].attname for model_field in enumerate(User._meta.fields)]
            for key in dict_keys:
                if key.replace("user_", "") in user_fields_list and key != "user_id" and key != "is_active":
                    updatable_fields.append(key.replace("user_", ""))

            User.objects.bulk_update(updatable_users, updatable_fields)
        except Exception as e:
            print(f"{e} Happened When Updating User")
        return ""

    def update_dealerships(self, updatable_dealerships, dict_keys):
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

    def update_user_profiles(self, updatable_user_profiles, dict_keys):
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


admin.site.register(UserProfile, UserProfileAdmin)
