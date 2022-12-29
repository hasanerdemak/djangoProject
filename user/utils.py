import base64
import csv
import gzip
import re
from collections import Counter
from io import StringIO

from django.db import models
from django.contrib.auth.models import User
from django.core.exceptions import FieldDoesNotExist

from dealership.models import Dealership
from user.models import UserProfile

# Define regular expressions to match different data types
REGEX_VALID_INT = r"^[0-9]+$"
REGEX_VALID_BOOL = r"^(1|0)$"
REGEX_VALID_NAME = r"^[a-zA-Z]+$"
REGEX_VALID_USERNAME = r"^[\w.@+-]+\Z"
REGEX_VALID_EMAIL = r'^(?P<email>[\w\.-]+@[\w\.-]+\.[\w]+)$'

# map of field types to Django model field classes
MODEL_FIELD_TYPES = {"int": (models.AutoField, models.BigAutoField,
                             models.IntegerField, models.BigIntegerField, models.SmallIntegerField,
                             models.PositiveIntegerField,
                             models.PositiveSmallIntegerField,
                             models.ForeignKey),
                     "bool": (models.BooleanField, models.NullBooleanField),
                     "name": [models.CharField],
                     "email": [models.EmailField]}


def read_csv_as_dict(text):
    f = StringIO(text)
    reader = csv.DictReader(f)

    keys = reader.fieldnames
    user_profile_dict = {key: [] for key in keys}

    for row in reader:
        for key in keys:
            try:
                user_profile_dict[key].append(row[key])
            except KeyError:
                user_profile_dict[key].append("")

    return user_profile_dict


def create_obj_lists_from_csv(csv_string):
    user_list = []
    dealership_list = []
    user_profile_list = []

    user_fields_list = set(field.attname for field in User._meta.fields if field.attname != "is_active")
    dealership_fields_list = set(field.attname for field in Dealership._meta.fields if field.attname != "is_active")
    user_profile_fields_list = set(field.attname for field in UserProfile._meta.fields)

    f = StringIO(csv_string)
    reader = csv.DictReader(f)

    # Read the CSV string into a list of dictionaries
    data = list(reader)

    csv_keys = reader.fieldnames
    scenario = check_which_scenario(csv_keys)

    # Loop through the list of dictionaries
    # Traverse the data in reverse to make sure the last entity of the objects is in the list
    for row in reversed(data):
        user = User()
        dealership = Dealership()
        user_profile = UserProfile()
        for key in row:
            value = row.get(key)
            if value is None:
                continue
            if "id" in key:
                value = int(value)

            if key.replace("user_", "") in user_fields_list:  # User
                setattr(user, key.replace("user_", ""), value)
            elif key.replace("dealership_", "") in dealership_fields_list:  # Dealership
                setattr(dealership, key.replace("dealership_", ""), value)
            elif key in user_profile_fields_list:  # User Profile
                setattr(user_profile, key, value)

        # if username does not exist in the input
        if scenario != 2:
            user.username = f"{user.first_name}{user.last_name}"

        # If the user already exists in the list, do not append it
        try:
            user_index = user_list.index(user)
            user_profile.user = user_list[user_index]
        except ValueError:
            user_list.append(user)
            user_profile.user = user

        # If the dealership already exists in the list, do not append it
        try:
            dealership_index = dealership_list.index(dealership)
            user_profile.dealership = dealership_list[dealership_index]
        except ValueError:
            dealership_list.append(dealership)
            user_profile.dealership = dealership

        user_profile_list.append(user_profile)

    return user_list, dealership_list, user_profile_list, csv_keys


def get_non_valid_field_indices(field_list):
    field_names = set([field.attname for field in UserProfile._meta.fields])
    field_names.update([field.attname for field in User._meta.fields])
    field_names.update([field.attname for field in Dealership._meta.fields])
    field_names.update(UserProfile().property_names())

    return [index for index, field_name in enumerate(field_list) if field_name not in field_names]


def get_missing_spaces_indices_and_messages(user_profile_dict):
    missing_spaces_rows = []
    missing_spaces_cols = []
    missing_spaces_messages = ""

    for col_index, (key, values) in enumerate(user_profile_dict.items()):
        missing_indices = [index for index, value in enumerate(values) if not value or value == ""]
        missing_spaces_rows.extend([j for j in missing_indices])
        missing_spaces_cols.extend([col_index for _ in missing_indices])
        if missing_indices:
            missing_spaces_messages += f'"{key}" field at row(s): {[i + 1 for i in missing_indices]} is/are required. \r\n'

    return missing_spaces_rows, missing_spaces_cols, missing_spaces_messages


def get_non_valid_spaces_indices_and_messages(user_profile_dict):
    non_valid_spaces_rows = []
    non_valid_spaces_cols = []
    non_valid_messages = ""

    # Iterate over the columns in the user_profile_dict
    for col_index, (key, values) in enumerate(user_profile_dict.items()):
        pattern = None
        col_type = get_col_type(key)
        if col_type in MODEL_FIELD_TYPES["int"]:
            pattern = REGEX_VALID_INT
        elif col_type in MODEL_FIELD_TYPES["bool"]:
            pattern = REGEX_VALID_BOOL
        elif col_type in MODEL_FIELD_TYPES["name"] and key != "dealership_name":
            if key == "username":
                pattern = REGEX_VALID_USERNAME
            else:
                pattern = REGEX_VALID_NAME
        elif col_type in MODEL_FIELD_TYPES["email"]:
            pattern = REGEX_VALID_EMAIL

        if pattern:
            non_valid_indices = [index for index, value in enumerate(values) if
                                 not re.match(pattern, value) and value != ""]
            non_valid_spaces_rows.extend([j for j in non_valid_indices])
            non_valid_spaces_cols.extend([col_index for _ in non_valid_indices])
            if non_valid_indices:
                non_valid_messages += f"{key} fields at row(s): {[i + 1 for i in non_valid_indices]} is/are not valid.\r\n"

    return non_valid_spaces_rows, non_valid_spaces_cols, non_valid_messages


def get_non_unique_spaces_indices_and_messages(user_profile_dict, scenario):
    if scenario not in (1, 2):
        return [], [], ""

    non_unique_rows = []
    non_unique_cols = []
    non_unique_messages = ""

    # Set the unique fields based on the scenario
    unique_fields = ["user_id", "dealership_id"] if scenario == 1 else ["username", "dealership_id"]

    # Get the unique values tuples
    values = merge_lists(*[user_profile_dict[field] for field in unique_fields])

    # Find the indices of non-unique values
    non_unique_indices = [index for index, value in enumerate(values) if values.count(value) > 1]

    if non_unique_indices:
        non_unique_rows = non_unique_indices * len(unique_fields)
        dict_keys = list(user_profile_dict.keys())
        non_unique_cols = [dict_keys.index(f) for f in unique_fields for _ in range(len(non_unique_indices))]
        non_unique_messages += f"{unique_fields} pairs at row(s): {[i + 1 for i in non_unique_indices]} must be unique.\r\n"

    return non_unique_rows, non_unique_cols, non_unique_messages


def get_col_type(col_name):
    if col_name.startswith("dealership_"):
        model = Dealership
        field_name = col_name.replace("dealership_", "")
    else:
        model = UserProfile
        field_name = col_name

    try:
        col_type = type(model._meta.get_field(field_name))
    except FieldDoesNotExist:
        model = User
        col_type = type(model._meta.get_field(field_name))
    return col_type


def get_existing_and_non_existing_users(user_list, unique_user_field_for_user_query, db_user_ids_and_usernames):
    db_users_unique_values_set = set(db_user_ids_and_usernames.values_list(unique_user_field_for_user_query, flat=True))

    existing_users = [user for user in user_list if
                      getattr(user, unique_user_field_for_user_query) in db_users_unique_values_set]
    non_existing_users = [user for user in user_list if
                          getattr(user, unique_user_field_for_user_query) not in db_users_unique_values_set]

    return existing_users, non_existing_users


def get_existing_and_non_existing_dealerships(dealership_list, db_dealership_ids_set):
    existing_dealerships = [dealership for dealership in dealership_list if
                            dealership.id in db_dealership_ids_set]
    non_existing_dealerships = [dealership for dealership in dealership_list if
                                dealership.id not in db_dealership_ids_set]

    return existing_dealerships, non_existing_dealerships


def get_existing_and_non_existing_user_profiles(user_profile_list, unique_user_field_for_user_query,
                                                db_user_profile_unique_values_set):
    existing_user_profiles = [user_profile for user_profile in user_profile_list if (
        getattr(user_profile.user, unique_user_field_for_user_query),
        user_profile.dealership_id) in db_user_profile_unique_values_set]
    non_existing_user_profiles = [user_profile for user_profile in user_profile_list if (
        getattr(user_profile.user, unique_user_field_for_user_query),
        user_profile.dealership_id) not in db_user_profile_unique_values_set]

    return existing_user_profiles, non_existing_user_profiles


def check_which_scenario(text_keys):
    if 'user_id' in text_keys:
        return 1
    elif 'username' in text_keys:
        return 2
    else:
        return 3


def set_required_fields_with_scenario(required_fields, scenario):
    if scenario == 1:
        required_fields.append('user_id')
    elif scenario == 2:
        required_fields.append('username')
    else:
        required_fields.extend(['first_name', 'last_name'])

    return required_fields


def update_same_usernames(user_list, db_usernames):
    input_usernames = [user.username for user in user_list]
    # Create an empty dictionary to store the frequencies
    frequencies = Counter()
    for input_username in input_usernames:
        count = sum(input_username.lower() in db_username.lower() for db_username in db_usernames)
        # Add the count for this string to the dictionary
        frequencies[input_username.lower()] = count

    for username, user in zip(input_usernames, user_list):
        frequency = frequencies.get(username.lower(), 0)
        if frequency > 0:
            frequencies[username.lower()] = frequency + 1
            user.username = f"{username}-{frequency + 1}"

    return ""


def merge_lists(*lists):
    merged_list = [tuple(lists[j][i] for j in range(len(lists))) for i in range(len(lists[0]))]
    return merged_list


def serialize_objects(objects):
    return [{"id": obj.id, "name": str(obj)} for obj in objects]


def compress_data(data):
    compressed_data = gzip.compress(data)
    # Encode the compressed data to a base64-encoded string
    return base64.b64encode(compressed_data).decode()


def decompress_data(data):
    # Decode the base64-encoded string to get the compressed data
    data = base64.b64decode(data)
    return gzip.decompress(data)
