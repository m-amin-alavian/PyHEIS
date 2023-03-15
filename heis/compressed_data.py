from tqdm import tqdm

import subprocess
import platform
import pathlib
import patoolib

from .metadata import Defaults
from . import utils


def download_a_file(year:int, replace:bool=True):
    file_name = f"{year}.rar"
    file_url = f"{Defaults.online_dir}/original_files/{file_name}"
    Defaults.original_dir.mkdir(parents=True, exist_ok=True)
    local_path = Defaults.original_dir.joinpath(file_name)
    if (not pathlib.Path(local_path).exists()) or replace:
        utils.download_file(url=file_url, path=local_path, show_progress_bar=True)


def download_files(from_year:int|None=None, to_year:int|None=None, replace:bool=False):
    from_year, to_year = utils.build_year_interval(from_year, to_year)
    pathlib.Path(Defaults.original_dir).mkdir(exist_ok =True, parents=True)
    for year in range(from_year, to_year):
        download_a_file(year , replace=replace)


def extract_with_7zip(compressed_file_path, output_directory):
    if platform.system() == "Windows":
        seven_zip_file_path = pathlib.Path().joinpath("7-Zip", "7z.exe")
        if not seven_zip_file_path.exists():
            utils.download_7zip()
        subprocess.run([seven_zip_file_path, "e", compressed_file_path, f"-o{output_directory}", "-y"], shell=True)
    elif platform.system() == "Linux":
        seven_zip_file_path = Defaults.root_dir.joinpath("7-Zip", "7zz")
        subprocess.run([seven_zip_file_path, "e", compressed_file_path, f"-o{output_directory}", "-y"])

def extract_with_patool(compressed_file_path, output_directory):
    patoolib.extract_archive(str(compressed_file_path), 
                             outdir=str(output_directory), interactive=False)

def inplace_extract(directory):
    while True:
        extracted_zip_files = list(pathlib.Path(directory).rglob("*.rar"))
        extracted_zip_files.extend(list(pathlib.Path(directory).rglob("*.zip")))
        if len(extracted_zip_files) == 0:
            break
        for file in extracted_zip_files:
            extract_with_7zip(file, directory)
            pathlib.Path(file).unlink()


def delete_empty_directories(directory:pathlib.Path):
    for path in directory.iterdir():
        if path.is_dir():
            path.rmdir()


def extract_a_file(year):
    file_path = Defaults.original_dir.joinpath(f"{year}.rar")
    year_directory = Defaults.raw_dir.joinpath(str(year))
    year_directory.mkdir(parents=True, exist_ok=True)
    if Defaults.use_patool:
        extract_with_patool(file_path, year_directory)
    else:
        extract_with_7zip(file_path, year_directory)
    inplace_extract(year_directory)
    delete_empty_directories(year_directory)


def extract_all(from_year=None, to_year=None):
    from_year, to_year = utils.build_year_interval(from_year=from_year, to_year=to_year)
    for year in tqdm(range(from_year, to_year), desc="Unziping raw data", unit="file"):
        extract_a_file(year)
        
