"""
docs
"""

from dataclasses import dataclass
import pathlib

from . import utils

@dataclass
class Metadata:
    """
    A dataclass for accessing metadata used in other parts of the project.

    """
    columns_properties = utils.open_yaml("metadata/columns_properties.yaml")
    maps = utils.open_yaml("metadata/maps.yaml")
    house_hold_id = utils.open_yaml("metadata/house_hold_id.yaml")
    commodity_codes = utils.open_yaml("metadata/commodity_codes.yaml")
    standard_tables = utils.open_yaml("metadata/standard_tables.yaml")
    other = utils.open_yaml("metadata/other.yaml")


@dataclass
class Defaults:
    """
    This dataclass provides access to default values that are used in other
    parts of the project. It first attempts to load the settings from a local
    `settings.yaml` file. If the file is not found, it loads the settings from
    the sample file named `settings-sample.yaml`.

    """
    try:
        settings = utils.open_yaml(["settings.yaml"])
    except FileNotFoundError:
        settings = utils.open_yaml(["settings-sample.yaml"])

    # online directory
    online_dir = settings['online_directory']

    # local directories
    root_dir = pathlib.Path(__file__).parents[1]
    local_dir = root_dir.joinpath(settings['local_directory'])
    original_dir = local_dir.joinpath(settings['original_folder_name'])
    raw_dir = local_dir.joinpath(settings['raw_data_folder_name'])
    csv_dir = local_dir.joinpath(settings['csv_folder_name'])
    sqlite_dir = local_dir
    parquets_dir = local_dir.joinpath(settings['parquet_folder_name'])

    first_year = settings['first_year']
    last_year = settings['last_year']

    storage = settings['storage_technology']


def get_latest_version_year(metadata: dict, year: int) -> int | None:
    """
    Retrieve the most recent available version of metadata that matches or
    precedes the given year, provided that the metadata is versioned.

    :param metadata: A dictionary representing the metadata.
    :type metadata: dict

    :param year: The year to which the version of the metadata should match or
        precede.
    :type year: int

    :return: The version number of the most recent metadata version that
        matches or precedes the given year, or None if the metadata is not
        versioned.
    :rtype: int or None

    """
    if not isinstance(metadata, dict):
        return None
    version_list = list(metadata.keys())
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


def get_metadata_version(metadata: dict, year: int) -> dict:
    """
    Retrieve the metadata version that matches or precedes the given year,
    returning the complete metadata for that version.

    :param metadata: A dictionary representing the metadata.
    :type metadata: dict

    :param year: The year to which the version of the metadata should match or
        precede.
    :type year: int

    :return: A dictionary containing the complete metadata for the version that
        matches or precedes the given year. If the metadata is not versioned, the
        function returns the original metadata dictionary.
    :rtype: dict

    """
    selected_version = get_latest_version_year(metadata, year)

    if selected_version is None:
        return metadata
    return metadata[selected_version]
