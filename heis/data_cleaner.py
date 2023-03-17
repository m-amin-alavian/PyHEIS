"""
docstring

"""

from pathlib import Path

import pandas as pd

from . import metadata


defaults = metadata.Defaults()
metadata_obj = metadata.Metadata()


def get_latest_version_year(metadata_dict: dict, year: int) -> int | None:
    """
    Retrieve the most recent available version of metadata that matches or
    precedes the given year, provided that the metadata is versioned.

    :param metadata_dict: A dictionary representing the metadata.
    :type metadata_dict: dict

    :param year: The year to which the version of the metadata should match or
        precede.
    :type year: int

    :return: The version number of the most recent metadata version that
        matches or precedes the given year, or None if the metadata is not
        versioned.
    :rtype: int or None

    """
    if not isinstance(metadata_dict, dict):
        return None
    version_list = list(metadata_dict.keys())
    for element in version_list:
        if not isinstance(element, int):
            return None
        if (element < 1300) or (element > 1500):
            return None

    selected_version = 0
    for version in version_list:
        if version <= year:
            selected_version = max(selected_version, version)
    return selected_version


def get_metadata_version(metadata_dict: dict, year: int) -> dict:
    """
    Retrieve the metadata version that matches or precedes the given year,
    returning the complete metadata for that version.

    :param metadata_dict: A dictionary representing the metadata.
    :type metadata_dict: dict

    :param year: The year to which the version of the metadata should match or
        precede.
    :type year: int

    :return: A dictionary containing the complete metadata for the version that
        matches or precedes the given year. If the metadata is not versioned, the
        function returns the original metadata dictionary.
    :rtype: dict

    """
    selected_version = get_latest_version_year(metadata_dict, year)

    if selected_version is None:
        return metadata_dict
    return metadata_dict[selected_version]


def load_table_data(table_name: str, year: int, urban: bool|None = None) -> pd.DataFrame:
    """
    Reads CSV file(s) containing data for a given table, year, and urban/rural category,
    and returns the data as a pandas DataFrame.

    :param table_name: The name of the table to be read.
    :type table_name: str
    :param year: The year of the data to be read.
    :type year: int
    :param urban: A boolean indicating whether to read data for urban areas only (`True`),
        rural areas only (`False`), or both (`None`, default). If `None`, data for both
        urban and rural areas will be read.
    :type urban: bool|None
    :return: A DataFrame containing the concatenated data from the CSV file(s).
    :rtype: pd.DataFrame
    :raises FileNotFoundError: If the CSV file(s) cannot be found at the expected file path(s).
    :raises ValueError: If the table name or year are invalid, or if the table metadata file is
        corrupt.
    :raises pd.errors.EmptyDataError: If the CSV file(s) are empty.

    :example:
    
    >>> load_table_data("food", 1393, urban=True)
    """

    if urban is None:
        urban_stats = [True, False]
    else:
        urban_stats = [urban]

    tables = []
    for urban_stat in urban_stats:
        file_path = _build_file_path(table_name=table_name, year=year, urban=urban_stat)
        tables.append(
            pd.read_csv(file_path, low_memory=False)
            )
    table = pd.concat(tables, axis="index", ignore_index=True)
    return table


def _build_file_path(table_name: str, year: int, urban: bool):
    urban_rural = "U" if urban else "R"
    year_string = year % 100 if year < 1400 else year
    table_metadata = _get_table_metadata(table_name, year, urban)
    file_code = get_metadata_version(table_metadata["file_code"], year)
    file_name = f"{urban_rural}{year_string}{file_code}.csv"
    file_path = Path(defaults.extracted_data).joinpath(str(year)).joinpath(file_name)
    return file_path


def _get_table_metadata(table_name, year, urban=None):
    table_metadata = metadata_obj.columns_properties[table_name]
    table_metadata = get_metadata_version(table_metadata, year)

    if urban is True:
        table_metadata = table_metadata["urban"] if "urban" in table_metadata else table_metadata
    if urban is False:
        table_metadata = table_metadata["rural"] if "rural" in table_metadata else table_metadata

    return table_metadata


def _get_column_metadata():
    pass
