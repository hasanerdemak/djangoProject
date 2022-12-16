import re
from collections import Counter

from django.db import models
from django.contrib.auth.models import User
from django.core.exceptions import FieldDoesNotExist

from dealership.models import Dealership
from user.models import UserProfile

REGEX_VALID_EMAIL = re.compile(r'^(?P<email>[\w\.-]+@[\w\.-]+\.[\w]+)$')
REGEX_VALID_USERNAME = r"^[\w.@+-]+\Z"

# map of field types to Django model field classes
MODEL_FIELD_TYPES = {"int": (models.AutoField, models.BigAutoField,
                             models.IntegerField, models.BigIntegerField, models.SmallIntegerField,
                             models.PositiveIntegerField, models.PositiveBigIntegerField,
                             models.PositiveSmallIntegerField,
                             models.ForeignKey),
                     "bool": (models.BooleanField, models.NullBooleanField),
                     "name": [models.CharField],
                     "email": [models.EmailField]}


def is_NaN(num):
    """to type check float('NaN') while reading csv"""
    return num != num


def indices_of_non_int_values(value_list):
    output = []
    for index in range(len(value_list)):
        try:
            int(value_list[index])
        except ValueError:
            if not is_NaN(value_list[index]) and value_list[index] != "":
                output.append(index)

    return output


def indices_of_non_valid_emails(value_list):
    return [index for index in range(len(value_list)) if (value_list[index] and
                                                          not REGEX_VALID_EMAIL.match(value_list[index]))]


def indices_of_non_boolean_values(value_list):
    output = []
    for index in range(len(value_list)):
        try:
            if int(value_list[index]) != 0 and int(value_list[index]) != 1:
                output.append(index)
        except ValueError:
            if not is_NaN(value_list[index]) and value_list[index] != "":
                output.append(index)

    return output


def indices_of_non_valid_names(value_list):
    return [index for index in range(len(value_list)) if (value_list[index] != "" and
                                                          not str(value_list[index]).replace(" ", "").isalpha())]


def indices_of_non_valid_usernames(value_list):
    return [index for index in range(len(value_list)) if (value_list[index] and
                                                          not re.fullmatch(REGEX_VALID_USERNAME, value_list[index]))]


def indices_of_non_unique_cells(value_list):
    freq = Counter(value_list)
    return [index for index in range(len(value_list)) if freq[value_list[index]] > 1]


def increase_list_values(value_list, increase_amount):
    return [value + increase_amount
            for value in value_list]


def reorder_list(updatable_list_ids, model_id_list):
    return [model_id_list.index(obj_id)
            for obj_id in updatable_list_ids]


def merge_lists(*lists):
    merged_list = [tuple(lists[j][i] for j in range(len(lists))) for i in range(len(lists[0]))]
    return merged_list


def read_csv_as_dict(text):
    lines = text.split("\r\n")

    keys = lines[0].split(",")

    user_profile_dict = {key: [] for key in keys}
    for i in range(1, len(lines)):
        values = lines[i].split(",")
        j = 0
        for key in user_profile_dict.keys():
            try:
                user_profile_dict[key].append(values[j])
            except IndexError:
                user_profile_dict[key].append("")
            j += 1

    return user_profile_dict


def get_non_valid_field_indices(field_list):
    field_names = [model_field[1].attname for model_field in enumerate(UserProfile._meta.fields)]
    field_names += UserProfile().property_names()

    return [index for index, field_name in enumerate(field_list) if field_name not in field_names]


def get_col_type(col_name):
    try:
        col_type = type(UserProfile._meta.get_field(col_name))
    except FieldDoesNotExist:
        try:
            col_type = type(User._meta.get_field(col_name))
        except FieldDoesNotExist:
            col_type = type(Dealership._meta.get_field(str(col_name).replace("dealership_", "")))
    return col_type


def get_missing_spaces_indices_and_messages(user_profile_dict):
    missing_spaces_rows = []
    missing_spaces_cols = []
    missing_spaces_messages = ""

    col_index = 0
    for key in user_profile_dict:
        index_list = [index for index, value in enumerate(user_profile_dict[key]) if
                      not value or value == ""]

        for j in index_list:
            missing_spaces_rows.append(j)
            missing_spaces_cols.append(col_index)
        if len(index_list) != 0:
            list_str = str(increase_list_values(index_list, 1))
            missing_spaces_messages += f'"{key}" field at row(s): {list_str} is/are required. \r\n'
        col_index += 1

    return missing_spaces_rows, missing_spaces_cols, missing_spaces_messages


def get_non_valid_spaces_indices_and_messages(user_profile_dict):
    non_valid_spaces_rows = []
    non_valid_spaces_cols = []
    non_valid_messages = ""

    col_index = 0
    for key in user_profile_dict:
        index_list = []
        col_type = get_col_type(key)
        if col_type in MODEL_FIELD_TYPES["int"]:
            index_list = indices_of_non_int_values(user_profile_dict[key])
        elif col_type in MODEL_FIELD_TYPES["bool"]:
            index_list = indices_of_non_boolean_values(user_profile_dict[key])
        elif col_type in MODEL_FIELD_TYPES["name"] and key != "dealership_name":
            if key == "username":
                index_list = indices_of_non_valid_usernames(user_profile_dict[key])
            else:
                index_list = indices_of_non_valid_names(user_profile_dict[key])
        elif col_type in MODEL_FIELD_TYPES["email"]:
            index_list = indices_of_non_valid_emails(user_profile_dict[key])

        for j in index_list:
            non_valid_spaces_rows.append(j)
            non_valid_spaces_cols.append(col_index)
        if len(index_list) != 0:
            non_valid_messages += '"' + key + '" fields at row(s): ' + str(
                increase_list_values(index_list, 1)) + ' is/are not valid. \r\n'
        col_index += 1

    return non_valid_spaces_rows, non_valid_spaces_cols, non_valid_messages


def get_non_unique_spaces_indices_and_messages(user_profile_dict, scenario):
    if scenario == 1:
        unique_fields = ["user_id", "dealership_id"]
    elif scenario == 2:
        unique_fields = ["username", "dealership_id"]
    else:
        return [], [], ""

    non_unique_rows = []
    non_unique_cols = []
    non_unique_messages = ""

    list_to_give = merge_lists(*[user_profile_dict[unique_fields[i]] for i in range(len(unique_fields))])

    index_list = indices_of_non_unique_cells(list_to_give)

    if len(index_list) != 0:
        for field in unique_fields:
            for j in index_list:
                non_unique_rows.append(j)
                non_unique_cols.append(list(user_profile_dict.keys()).index(field))

        non_unique_messages += str(unique_fields) + ' at row(s): '
        for index in index_list:
            non_unique_messages += str(index + 1) + ', '

        non_unique_messages = non_unique_messages[:len(non_unique_messages) - 2]
        non_unique_messages += ' must be unique. \r\n'

    return non_unique_rows, non_unique_cols, non_unique_messages


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


def check_which_scenario(text_keys):
    if 'user_id' in text_keys:
        return 1
    elif 'username' in text_keys:
        return 2
    else:
        return 3


def set_required_fields_with_scenario(required_fields, text_keys):
    scenario = check_which_scenario(text_keys)

    if scenario == 1:
        required_fields.append('user_id')
    elif scenario == 2:
        required_fields.append('username')
    elif scenario == 3:
        required_fields.append('first_name')
        required_fields.append('last_name')

    return required_fields, scenario


def get_unique_field_name_for_query_and_dict(user_profile_dict):
    scenario = check_which_scenario(user_profile_dict.keys())

    if scenario == 1:
        unique_user_field_for_dict = 'user_id'
        unique_user_field_for_user_query = 'id'
        unique_user_field_for_user_profile_query = 'user_id'

    elif scenario == 2 or scenario == 3:
        unique_user_field_for_dict = 'username'
        unique_user_field_for_user_query = 'username'
        unique_user_field_for_user_profile_query = 'user__username'
        if scenario == 3:
            user_profile_dict['username'] = list(
                map(str.__add__, user_profile_dict['first_name'], user_profile_dict['last_name']))
    else:
        unique_user_field_for_dict = None
        unique_user_field_for_user_query = None
        unique_user_field_for_user_profile_query = None

    return unique_user_field_for_dict, unique_user_field_for_user_query, unique_user_field_for_user_profile_query, scenario


def update_same_usernames(list1, list2):
    # Create an empty dictionary to store the frequencies
    frequencies = {}
    # Loop over the strings in list1
    for username1 in list1:
        # Initialize the count for this string to 0
        count = 0
        # Loop over the strings in list2
        for username2 in list2:
            # Check if the string in list1 is a substring of the string in list2 (ignoring the characters after the hyphen and after "ls")
            if username1.lower() in username2.lower():
                count += 1
        # Add the count for this string to the dictionary
        frequencies[username1.lower()] = count

    for index, username in enumerate(list1):
        if frequencies[username.lower()] > 0:
            frequencies[username.lower()] += 1
            list1[index] += f"-{str(frequencies[username.lower()])}"

    return list1
