import pandas as pd

from . import utils
from .general import house_hold_id

def _get_part_position(part_name:str, year:int):
    id_length = utils.get_version(dictionary=house_hold_id['ID_Length'], year=year)
    position = utils.get_version(dictionary=house_hold_id[part_name]['position'], year=year)
    right = id_length - position['end']
    left = position['end'] - position['start']
    return right, left


def _extract_part_code(id_column:pd.Series, part_name:str, year:int):
    right, left = _get_part_position(part_name=part_name, year=year)
    new_column = (id_column // pow(10, right) % pow(10, left)).copy()
    return new_column


def get_part_names(id_column:pd.Series, part_name:str, year:int):
    part_codes = _extract_part_code(id_column=id_column, part_name=part_name, year=year)
    names_mapping = utils.get_version(dictionary=house_hold_id[part_name]['names'], year=year)
    part_codes = part_codes.astype("category")
    part_names = part_codes.cat.rename_categories(names_mapping)
    return part_names
