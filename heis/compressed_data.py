from tqdm import tqdm

import subprocess
import sys
import pathlib

from .metadata import Defults
from .utils import build_year_interval, download_file


def download_a_file(year:int, replace:bool=True, compressed_files_directory=Defults.compressed_dir):
    file_name = f"HEIS{year}.rar"
    file_url = f"{Defults.online_dir}/{file_name}"
    local_path = compressed_files_directory.joinpath(file_name)
    if (not pathlib.Path(local_path).exists()) or replace:
        download_file(file_url, local_path, show_progress_bar=True)


def download(from_year:int, to_year:int|None=None, replace:bool=False, compressed_files_directory=Defults.compressed_dir):
    from_year, to_year = build_year_interval(from_year=from_year, to_year=to_year)
    pathlib.Path(compressed_files_directory).mkdir(exist_ok =True)
    for year in range(from_year, to_year):
        download(year , replace=replace, compressed_files_directory=compressed_files_directory)

def extract_with_7zip(compressed_file_path, output_directory):
    if not exe_file_path.exists():
        raise FileNotFoundError("7-ZIP folder not found")
    if sys.platform == "win32":
        exe_file_path = pathlib.Path(pathlib.PurePath().joinpath("7-ZIP", "windows", "7z.exe"))
        subprocess.run([exe_file_path, "e", compressed_file_path, f"-o{output_directory}", "-y"], shell=True)
    else:
        exe_file_path = pathlib.Path(pathlib.PurePath().joinpath("7-ZIP", "linux", "7zz"))
        subprocess.run([exe_file_path, "e", compressed_file_path, f"-o{output_directory}", "-y"])


def inplace_extract(compressed_file_directory):
    while True:
        extracted_zip_files = list(pathlib.Path(compressed_file_directory).rglob("*.rar"))
        extracted_zip_files.extend(list(pathlib.Path(compressed_file_directory).rglob("*.zip")))
        if len(extracted_zip_files) == 0:
            break
        for file in extracted_zip_files:
            extract_with_7zip(file, compressed_file_directory)
            pathlib.Path(file).unlink()


def extract_a_file(compressed_file_path, raw_data_directory=None):
    year_directory = raw_data_directory.joinpath(compressed_file_path.stem)
    pathlib.Path(year_directory).mkdir(parents=True, exist_ok=True)
    extract_with_7zip(compressed_file_path, year_directory)
    inplace_extract(year_directory)


def extract(from_year=None, to_year=None, compressed_files_directory=Defults.compressed_dir, raw_data_directory=Defults.raw_dir):
    from_year, to_year = build_year_interval(from_year=from_year, to_year=to_year)
    for year in tqdm(range(from_year, to_year), desc="Unziping raw data", unit="file"):
        file_path = compressed_files_directory.joinpath(f"HEIS{year}.rar")
        extract_a_file(file_path, raw_data_directory)
        