import yaml
import pathlib


def open_yaml(path):
    if type(path) is list:
        relative_path = pathlib.Path(__file__).parents[1]
        for element in path:
            relative_path = relative_path.joinpath(element)
        path = relative_path
    with open(path, mode="r", encoding="utf8") as yaml_file:
        yaml_content = yaml.load(yaml_file, Loader=yaml.CLoader)
    return yaml_content


class Metadata:
    columns_properties = open_yaml(["metadata", "columns_properties.yaml"])
    maps = open_yaml(["metadata", "maps.yaml"])
    house_hold_id = open_yaml(["metadata", "house_hold_id.yaml"])
    commodity_codes = open_yaml(["metadata", "commodity_codes.yaml"])
    standard_tables = open_yaml(["metadata", "standard_tables.yaml"])
    other = open_yaml(["metadata", "other.yaml"])


class Defults:
    try:
        settings = open_yaml(["settings.yaml"])
    except FileNotFoundError:
        settings = open_yaml(["settings-sample.yaml"])
        
    local_dir = pathlib.Path(settings['local_directory'])
    online_dir = settings['online_directory']
    compressed_dir = local_dir.joinpath(settings['compressed_folder_name'])
    raw_dir = local_dir.joinpath(settings['raw_data_folder_name'])
    csv_dir = local_dir.joinpath(settings['csv_folder_name'])
    parquets_dir = local_dir.joinpath(settings['parquet_folder_name'])

    first_year = settings['defult_first_year']
    last_year = settings['defult_last_year']

    storage = settings['storage_technology']

defaults = Defults()
