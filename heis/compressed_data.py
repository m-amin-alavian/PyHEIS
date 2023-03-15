"""
docs
"""

import shutil
import subprocess
import platform
import pathlib

from tqdm import tqdm

from .metadata import Defaults
from . import utils


def download_year_file(year: int, replace: bool = True) -> None:
    """
    Downloads a compressed household census file for a specified year from the online directory.

    :param year: The year for which to download the household census file.
    :type year: int
    :param replace: Whether to replace an existing file with the same name. Defaults to True.
    :type replace: bool, optional
    :return: None, as this function does not return anything.

    """
    file_name = f"{year}.rar"
    file_url = f"{Defaults.online_dir}/original_files/{file_name}"
    Defaults.original_dir.mkdir(parents=True, exist_ok=True)
    local_path = Defaults.original_dir.joinpath(file_name)
    if (not pathlib.Path(local_path).exists()) or replace:
        utils.download_file(url=file_url, path=local_path, show_progress_bar=True)


def download_year_files_in_range(
    from_year: int | None = None, to_year: int | None = None, replace: bool = False
) -> None:
    """
    Downloads compressed household census files for all years within a
    specified range from the online directory.

    :param from_year: The starting year of the range (inclusive). If not
    specified, defaults to the earliest year available.
    :type from_year: int, optional
    :param to_year: The ending year of the range (inclusive). If not specified,
    defaults to the latest year available.
    :type to_year: int, optional
    :param replace: Whether to replace existing files with the same names. Defaults to False.
    :type replace: bool, optional
    :return: None, as this function does not return anything.

    """
    from_year, to_year = utils.build_year_interval(from_year, to_year)
    pathlib.Path(Defaults.original_dir).mkdir(exist_ok=True, parents=True)
    for year in range(from_year, to_year):
        download_year_file(year, replace=replace)


def extract_archive_with_7zip(compressed_file_path: str, output_directory: str) -> None:
    """
    Extracts the contents of a compressed file using the 7-Zip tool.

    :param compressed_file_path: The path to the compressed file to be extracted.
    :type compressed_file_path: str
    :param output_directory: The path to the directory where the extracted files will be stored.
    :type output_directory: str
    :return: None, as this function does not return anything.

    """
    if platform.system() == "Windows":
        seven_zip_file_path = pathlib.Path().joinpath("7-Zip", "7z.exe")
        if not seven_zip_file_path.exists():
            utils.download_7zip()
        subprocess.run(
            [
                seven_zip_file_path,
                "e",
                compressed_file_path,
                f"-o{output_directory}",
                "-y",
            ],
            check=False,
            shell=True,
        )
    elif platform.system() == "Linux":
        seven_zip_file_path = Defaults.root_dir.joinpath("7-Zip", "7zz")
        subprocess.run(
            [
                seven_zip_file_path,
                "e",
                compressed_file_path,
                f"-o{output_directory}",
                "-y",
            ],
            check=False,
        )


def extract_archives_recursive(directory):
    """
    Extract all archives with the extensions ".zip" and ".rar" found
    recursively in the given directory and its subdirectories using 7zip.

    :param directory: The directory path to search for archives.
    :type directory: str
    :return: None

    """
    while True:
        all_files = list(pathlib.Path(directory).iterdir())
        archive_files = [file for file in all_files if file.suffix in (".zip", ".rar")]
        if len(archive_files) == 0:
            break
        for file in archive_files:
            extract_archive_with_7zip(file, directory)
            pathlib.Path(file).unlink()



def extract_yearly_data_archives(from_year=None, to_year=None):
    """
    Extracts all the yearly data archives from a starting year to an ending year.

    :param from_year: The starting year (inclusive) to extract the data from.
        If None, the default is the first year available.
    :type from_year: int or None

    :param to_year: The ending year (inclusive) to extract the data up to. If
        None, the default is the last year.
    :type to_year: int or None

    :returns: None

    This function extracts all the yearly data archives from the specified
    starting year (inclusive) to the specified ending year (exclusive). If
    no starting year is specified, it starts from the first available year.
    If no ending year is specified, it extracts up to the last year. The yearly
    data archives are extracted into newly created directories under the
    'original_files' directory. Each archive file is named '`year`.rar' where
    `year` is the year for which the archive was created. If any of the
    directories already exist, the function will overwrite any existing files
    with the same name. Any nested archive files within the extracted
    directories will also be extracted recursively.

    """
    from_year, to_year = utils.build_year_interval(from_year=from_year, to_year=to_year)
    for year in tqdm(range(from_year, to_year), desc="Unziping raw data", unit="file"):
        _extract_yearly_data_archive(year)


def _extract_yearly_data_archive(year):
    """
    Extracts data archive for the given year.
    """
    file_path = Defaults.original_dir.joinpath(f"{year}.rar")
    year_directory = Defaults.raw_dir.joinpath(str(year))
    if year_directory.exists():
        shutil.rmtree(year_directory)
    year_directory.mkdir(parents=True)
    extract_archive_with_7zip(file_path, year_directory)
    extract_archives_recursive(year_directory)
    _remove_created_directories(year_directory)


def _remove_created_directories(directory: pathlib.Path):
    for path in directory.iterdir():
        if path.is_dir():
            shutil.rmtree(path)
