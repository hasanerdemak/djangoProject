import json
import operator
from concurrent.futures import ThreadPoolExecutor
from functools import reduce

from django.conf import settings
from django.contrib import admin
from django.db.models import Q
from django.http import HttpResponseRedirect
from django.shortcuts import render, redirect
from django.template.response import TemplateResponse
from django.urls import re_path, reverse
from django.utils.crypto import get_random_string
from django.core.signing import TimestampSigner, BadSignature, SignatureExpired

from user.utils import *
from .models import UserProfile


class UserProfileAdmin(admin.ModelAdmin):
    change_list_template = "user/my_user_profile_change_list.html"
    list_display = ["user", "dealership", "is_active"]
    readonly_fields = ["username", "dealership_name", "first_name", "last_name", "email"]
    fieldsets = [
        (None, {'fields': ["user", "dealership", "is_active"]}),
        ('User Information', {'fields': ["username", "first_name", "last_name", "email"]}),
        ('Dealership Information', {'fields': ["dealership_name"]}),
    ]
    search_fields = ["user__username", "user__first_name", "user__last_name", "user__email", "dealership__name"]

    class Meta:
        model = UserProfile

    def get_urls(self):
        # Get the default URLs for the UserProfileAdmin view
        urls = super().get_urls()
        # Add a custom URL for the add_user_profile and show_info views
        my_urls = [
            re_path(r'^add-user-profile$', self.admin_site.admin_view(self.check_buttons), name='add-user-profile'),
            re_path(r'^show-info$', self.admin_site.admin_view(self.show_info), name='show-info'),
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
        scenario = check_which_scenario(user_profile_dict.keys())
        required_fields = ["dealership_id", "dealership_name"]
        required_fields = set_required_fields_with_scenario(required_fields, scenario)

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
                   }
        return render(request, "user/user_profile_add.html", context)

    def add_user_profile(self, request):
        if request.method == "GET":
            return redirect("/admin/user/userprofile")
        else:  # POST
            password_list_for_users = []

            create_if_not_exist = True if (request.POST.get("form-check-box-1") is not None) else False
            # Get the text in the "form-text-area" and remove any trailing new line characters
            text = request.POST.get("form-text-area").rstrip("\r\n")

            # Create lists of object instances from the text to process on them.
            user_list, dealership_list, user_profile_list, csv_keys = create_obj_lists_from_csv(text)

            """
            Check the scenario based on the fields given in the user input. There can be 3 different scenarios:
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
                db_user_profile_unique_values_set = set(UserProfile.objects.only(*fields).values_list(*fields))
            except Exception as e:
                print(f"{e} Happened When Fetching Objects From DB")

            # If scenario is 3, then update same usernames
            if scenario == 3:
                # Get the list of existing usernames from the database and update the same usernames in the list
                update_same_usernames(user_list, db_user_ids_and_usernames.values_list("username", flat=True))

            # Get existing and non-existing users to update or create them
            existing_users, non_existing_users = get_existing_and_non_existing_users(user_list,
                                                                                     unique_user_field_for_user_query,
                                                                                     db_user_ids_and_usernames)
            # Get existing and non-existing dealerships to update or create them
            existing_dealerships, non_existing_dealerships = get_existing_and_non_existing_dealerships(dealership_list,
                                                                                                       db_dealership_ids_set)
            # Get existing and non-existing user_profiles to update or create them
            existing_user_profiles, non_existing_user_profiles = get_existing_and_non_existing_user_profiles(
                user_profile_list, unique_user_field_for_user_query, db_user_profile_unique_values_set)

            if create_if_not_exist:
                # Create non-existing Users
                password_list_for_users = self.create_users(non_existing_users)
                # Create non-existing Dealerships
                self.create_dealerships(non_existing_dealerships)
            else:
                # Since these objects are not created, empty the lists to not show them in the template.
                non_existing_users, non_existing_dealerships = [], []
                # If non-existing users and dealerships was not created,
                # then send only user profiles that have existing users and dealerships
                non_existing_user_profiles = [user_profile for user_profile in non_existing_user_profiles if
                                              user_profile.user in existing_users and
                                              user_profile.dealership in existing_dealerships]

            # If the scenario is not 1, then we must have the ids of the Users that connected to User Profiles
            if scenario != 1 and (len(existing_user_profiles) != 0 or len(non_existing_user_profiles) != 0):
                user_profiles_users = User.objects.filter(
                    username__in=[user_profile.username for user_profile in user_profile_list])

                username_to_id = {user.username: user.id for user in user_profiles_users}
                # Use the dictionary to look up the user ID for each user profile
                for user_profile in user_profile_list:
                    user_id = username_to_id.get(user_profile.user.username)
                    if user_id is not None:
                        user_profile.user.id = user_id
                        user_profile.user = user_profile.user

            self.create_user_profiles(non_existing_user_profiles)

            # We need to have ids of the User Profiles to update them and add link to all of them in template.
            # To do that get user profiles values by user_id and dealership_id
            query = reduce(operator.or_, (Q(user__id=user_profile.user_id) & Q(dealership_id=user_profile.dealership_id)
                                          for user_profile in user_profile_list))
            db_user_profiles = UserProfile.objects.filter(query)

            # Create dict to assign ids in O(n) time
            db_user_profiles_dict = {(db_user_profile.user_id, db_user_profile.dealership_id): db_user_profile for
                                     db_user_profile in db_user_profiles}
            for user_profile in user_profile_list:
                key = (user_profile.user_id, user_profile.dealership_id)
                if key in db_user_profiles_dict:
                    user_profile.id = db_user_profiles_dict[key].id

            # Update existing objects
            self.update_users(existing_users, csv_keys)
            self.update_dealerships(existing_dealerships, csv_keys)
            self.update_user_profiles(existing_user_profiles, csv_keys)

            # Separate the User Profile lists by the is active field indicating whether User Profile has been deleted.
            non_existing_user_profiles = list(filter(lambda x: x.is_active == "1", non_existing_user_profiles))
            existing_user_profiles = list(filter(lambda x: x.is_active == "1", existing_user_profiles))
            deleted_user_profiles = list(filter(lambda x: x.is_active == "0", user_profile_list))
            # Create context by serializing lists
            context = {
                "created_users": serialize_objects(non_existing_users),
                "created_dealerships": serialize_objects(non_existing_dealerships),
                "created_user_profiles": serialize_objects(non_existing_user_profiles),
                "updated_users": serialize_objects(existing_users),
                "updated_dealerships": serialize_objects(existing_dealerships),
                "updated_user_profiles": serialize_objects(existing_user_profiles),
                "deleted_user_profiles": serialize_objects(deleted_user_profiles),
                "password_list_for_users": password_list_for_users,
            }

            # First compress the context to reduce the length of the url, then sign and encrypt it for security
            compressed_context = compress_data(json.dumps(context).encode())
            signer = TimestampSigner(settings.SECRET_KEY)
            signed_data = signer.sign_object(compressed_context)

            # Add signed data to the new url and redirect to this url
            return HttpResponseRedirect(f"{reverse('admin:show-info')}?data={signed_data}")

    def create_users(self, user_list_to_create):
        password_list_for_users = [get_random_string(8) for _ in range(len(user_list_to_create))]
        # Use multi threading to speed up the set_password process of the users
        with ThreadPoolExecutor() as executor:
            executor.map(User.set_password, user_list_to_create, password_list_for_users)

        try:
            User.objects.bulk_create(user_list_to_create)
        except Exception as e:
            print(f"{e} Happened When Creating User")

        return password_list_for_users

    def create_dealerships(self, dealership_list_to_create):
        try:
            Dealership.objects.bulk_create(dealership_list_to_create)
        except Exception as e:
            print(f"{e} Happened When Creating Dealership")

        return ""

    def create_user_profiles(self, user_profiles_list_to_create):
        try:
            UserProfile.objects.bulk_create(user_profiles_list_to_create)
        except Exception as e:
            print(f"{e} Happened When Creating User Profile")

        return ""

    def update_users(self, updatable_users, dict_keys):
        try:
            updatable_fields = ["username"]
            user_fields_set = {field.attname for field in User._meta.fields}
            for key in dict_keys:
                if key.replace("user_", "") in user_fields_set and key != "user_id" and key != "is_active":
                    updatable_fields.append(key.replace("user_", ""))

            User.objects.bulk_update(updatable_users, updatable_fields)
        except Exception as e:
            print(f"{e} Happened When Updating User")
        return ""

    def update_dealerships(self, updatable_dealerships, dict_keys):
        try:
            updatable_fields = []
            dealership_fields_set = {field.attname for field in Dealership._meta.fields}
            for key in dict_keys:
                if key.replace("dealership_", "") in dealership_fields_set \
                        and key != "dealership_id" and key != "is_active":
                    updatable_fields.append(key.replace("dealership_", ""))

            Dealership.objects.bulk_update(updatable_dealerships, updatable_fields)
        except Exception as e:
            print(f"{e} Happened When Updating Dealership")
        return ""

    def update_user_profiles(self, updatable_user_profiles, dict_keys):
        try:
            updatable_fields = []
            user_profile_fields_set = {field.attname for field in UserProfile._meta.fields}
            for key in dict_keys:
                if key in user_profile_fields_set:
                    updatable_fields.append(key)

            UserProfile.objects.bulk_update(updatable_user_profiles, updatable_fields)
        except Exception as e:
            print(f"{e} Happened When Updating User Profile")
        return ""

    def show_info(self, request):
        encrypted_data = request.GET['data']
        # Create a TimestampSigner object with the same secret key
        signer = TimestampSigner(settings.SECRET_KEY)
        try:
            # Decrypt, verify, and decompress the data
            decrypted_compressed_data = signer.unsign_object(encrypted_data, max_age=3600)
            context = json.loads(decompress_data(decrypted_compressed_data))
        except (BadSignature, SignatureExpired, gzip.BadGzipFile, json.JSONDecodeError) as e:
            print(f"{e} Happened When Decrypting, Verifying, and Decompressing The Data")
            return render(request, 'user/user_profile_creation_info.html')

        # If there is a user created, zip the user and password lists to print the username and passwords in a single loop in html
        if context["created_users"]:
            context["created_users"] = zip(context["created_users"], context.pop("password_list_for_users"))

        return render(request, "user/user_profile_creation_info.html", context)


admin.site.register(UserProfile, UserProfileAdmin)
