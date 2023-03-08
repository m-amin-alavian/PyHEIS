from tqdm import tqdm
import requests

import logging
import pathlib
import platform
from zipfile import ZipFile

from .metadata import Defults


logging.basicConfig(filename="ihbs.log")


def download_file(url:str, path:str|pathlib.Path|None=None, show_progress_bar:bool=False):
    if type(path) is str:
        path = pathlib.Path(path)
        file_name = path.name
    elif path is None:
        temp_folder = pathlib.Path(__file__).absolute().parents[1].joinpath("temp")
        temp_folder.mkdir(exist_ok=True)
        file_name = url.split("/")[-1]
        path = temp_folder.joinpath(file_name)
    else:
        file_name = path.name

    logging.info(url)
    response = requests.get(url, stream=True)
    file_size = int(response.headers.get('content-length'))
    download_bar = tqdm(desc=f"downloading {file_name}", total=file_size, unit="B", unit_scale=True, disable=not show_progress_bar)
    with open(path, mode="wb") as f:
        for chunk in response.iter_content(chunk_size=4096):
            download_bar.update(len(chunk))
            f.write(chunk)
    download_bar.close()


def download_7zip():
    print(f"Downloading 7-Zip for {platform.system()} with {platform.architecture()[0]} architecture")
    file_name = f"{platform.system()}-{platform.architecture()[0]}.zip"
    file_path = pathlib.Path().joinpath("temp", file_name)
    download_file(f"https://s3.ir-tbz-sh1.arvanstorage.ir/sdac/ihbs/7-Zip/{file_name}", show_progress_bar=True)
    with ZipFile(file_path) as zip_file:
        zip_file.extractall(pathlib.Path())
    file_path.unlink()


def build_year_interval(from_year, to_year):
    if (from_year is None) and (to_year is None):
        return (Defults.first_year, Defults.last_year+1)
    elif to_year is None:
        return (from_year, from_year+1)
    elif to_year <= from_year:
        return (from_year, from_year+1)
    else:
        return (from_year, to_year+1)


def select_version(dictionary, year:int) -> int|None:
    if type(dictionary) is not dict:
        return None
    pattern_list = list(dictionary.keys())
    for element in pattern_list:
        if type(element) is not int:
            return None
        elif (element < 1300) or (element > 1500):
            return None

    selected_pattern = None
    for pattern in pattern_list:
        if pattern <= year:
            if (selected_pattern is None) or (selected_pattern <= pattern):
                selected_pattern = pattern
    return selected_pattern


def get_version(dictionary, year:int) -> dict:
    selected_year = select_version(dictionary, year)
    if selected_year is None:
        selected_version = dictionary
    else:
        selected_version = dictionary[selected_year]
    return selected_version