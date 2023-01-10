import yaml

import pathlib

settings_path = pathlib.PurePath().joinpath("settings.yaml")
with open(settings_path, mode="r", encoding="utf8") as yaml_file:
    settings = yaml.load(yaml_file, Loader=yaml.CLoader)

other_metadata_path = pathlib.PurePath().joinpath("metadata", "other.yaml")
with open(other_metadata_path, mode="r", encoding="utf8") as yaml_file:
    other_metadata = yaml.load(yaml_file, Loader=yaml.CLoader)

columns_properties_path = pathlib.PurePath().joinpath("metadata", "columns_properties.yaml")
with open(columns_properties_path, mode="r", encoding="utf8") as yaml_file:
    columns_properties = yaml.load(yaml_file, Loader=yaml.CLoader)

class Defults:
    local_directory = pathlib.PurePath(settings['local_directory'])
    online_directory = settings['online_directory']
    compressed_dir = local_directory.joinpath('1_compressed_files')
    raw_dir = local_directory.joinpath('2_raw_data')
    csv_dir = local_directory.joinpath('3_csv_files')
    parquets_dir = local_directory.joinpath('4_parquets')

    first_year = settings['defult_first_year']
    last_year = settings['defult_last_year']

    storage = settings['storage_technology']
