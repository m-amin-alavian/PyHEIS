import pyodbc
import pandas as pd
import numpy as np
from tqdm import tqdm

from pathlib import Path
import json
import requests
import os

print(os.path.abspath("."))
DEFULT_DIRECTORY = ""
main_directory = DEFULT_DIRECTORY


def check_folder(folder_name, directory=main_directory):
    if not os.path.exists(os.path.join(directory, folder_name)):
        os.mkdir(os.path.join(directory, folder_name))

        
def download_from_server(url, local_path):
    response = requests.get(url, stream=True)
    file_size = int(response.headers.get('content-length'))
    download_bar = tqdm(desc=f"downloading {file_name}", total=file_size, unit="B", unit_scale=True)
    with open(os.path.join(local_path), mode="wb") as f:
        for chunk in response.iter_content(chunk_size=4096):
            download_bar.update(len(chunk))
            f.write(chunk)
    download_bar.close()

    
def download_compressed_file(year, to_year=None, directory=main_directory):
    from_year = year
    if to_year is None:
        to_year = year + 1
    else:
        if to_year <= year:
            to_year = year + 1
        else:
            to_year = to_year + 1
    Path.mkdir("compressed_file", parents=True, exist_ok =True)
    for year in range(from_year, to_year):
        file_name = f"HEIS{year}.rar"
        url = f"https://s3.ir-thr-at1.arvanstorage.com/gsmedb/HEIS/{file_name}"
        local_path = os.path.join(directory, "zip_files", file_name)
        download_from_server(year, directory)


def extract_rar_to_directory():
    pass
