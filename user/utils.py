import contextlib
import re
from collections import Counter

import pandas as pd

REGEX_VALID_EMAIL = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'


def is_NaN(num):
    """to type check float('NaN') while reading csv"""
    return num != num


def indices_of_non_int_values(value_list):
    output = []
    for index, value in enumerate(value_list):
        try:
            int(value)
        except ValueError:
            if not is_NaN(value):
                output.append(index)

    return output


def indices_of_non_valid_emails(value_list):
    output = []
    if len(value_list):
        for email in value_list:
            index = value_list.index(email)
            with contextlib.suppress(TypeError):
                if not re.fullmatch(REGEX_VALID_EMAIL, email):
                    output.append(index)
    return output


def indices_of_non_boolean_values(value_list):
    output = []
    for value in value_list:
        index = value_list.index(value)
        try:
            if int(value) != 0 and int(value) != 1:
                output.append(index)
        except ValueError:
            if not is_NaN(value):
                output.append(index)

    return output


def indices_of_non_valid_names(value_list):
    output = []
    for value in value_list:
        index = value_list.index(value)
        if not str(value).replace(" ", "").isalpha():
            output.append(index)

    return output


def indices_of_non_unique_cells(value_df):
    output = []
    if isinstance(value_df, pd.Series):
        value_list = value_df.tolist()
    else:
        value_list = list(value_df.itertuples(index=False, name=None))

    freq = Counter(value_list)
    for value in value_list:
        index = value_list.index(value)
        if freq[value] > 1:
            output.append(index)

    return output


def increase_list_values(value_list, increase_amount):
    return [value + increase_amount
            for value in value_list]


def reorder_list(updatable_list, model_id_list):
    return [model_id_list.values.tolist().index(value.id)
            for value in updatable_list]
