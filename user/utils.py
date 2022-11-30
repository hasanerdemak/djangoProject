import re
from collections import Counter

from django.contrib.auth.models import User
from django.core.exceptions import FieldDoesNotExist

from dealership.models import Dealership
from user.models import UserProfile

REGEX_VALID_EMAIL = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'


def is_NaN(num) -> bool:
    """to type check float('NaN') while reading csv"""
    return num != num


def indices_of_non_int_values(value_list: list) -> list:
    output = []
    for index in range(len(value_list)):
        try:
            int(value_list[index])
        except ValueError:
            if not is_NaN(value_list[index]):
                output.append(index)

    return output


def indices_of_non_valid_emails(value_list: list) -> list:
    return [index for index in range(len(value_list)) if (value_list[index] and
                                                          not re.fullmatch(REGEX_VALID_EMAIL, value_list[index]))]


def indices_of_non_boolean_values(value_list: list) -> list:
    output = []
    for index in range(len(value_list)):
        try:
            if int(value_list[index]) != 0 and int(value_list[index]) != 1:
                output.append(index)
        except ValueError:
            if not is_NaN(value_list[index]):
                output.append(index)

    return output


def indices_of_non_valid_names(value_list: list) -> list:
    return [index for index in range(len(value_list)) if (value_list[index] != "" and
                                                          not str(value_list[index]).replace(" ", "").isalpha())]


def indices_of_non_unique_cells(value_list: list) -> list:
    freq = Counter(value_list)
    return [index for index in range(len(value_list)) if freq[value_list[index]] > 1]


def increase_list_values(value_list: list, increase_amount: int) -> list:
    return [value + increase_amount
            for value in value_list]


def reorder_list(updatable_list_ids: list, model_id_list: list) -> list:
    return [model_id_list.index(obj_id)
            for obj_id in updatable_list_ids]


def merge_lists(*lists: list) -> list:
    merged_list = [tuple(lists[j][i] for j in range(len(lists))) for i in range(len(lists[0]))]
    return merged_list


def read_csv_as_dict(text: str) -> dict:
    lines = text.split("\r\n")

    user_profile_dict = {key: [] for key in lines[0].split(",")}
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


def non_valid_field_indices(field_list) -> list:
    field_names = [model_field[1].attname for model_field in enumerate(UserProfile._meta.fields)]
    field_names += UserProfile._meta._property_names

    return [index for index, field_name in enumerate(field_list) if field_name not in field_names]


def get_col_type(col_name: str) -> type:
    try:
        col_type = type(UserProfile._meta.get_field(col_name))
    except FieldDoesNotExist:
        try:
            col_type = type(User._meta.get_field(col_name))
        except FieldDoesNotExist:
            col_type = type(Dealership._meta.get_field(str(col_name).replace("dealership_", "")))
    return col_type
