import tqdm

import requests

from .general import Defults


def download_file(url, path, show_progress_bar=False):
    response = requests.get(url, stream=True)
    file_size = int(response.headers.get('content-length'))
    download_bar = tqdm(desc=f"downloading {path.name}", total=file_size, unit="B", unit_scale=True, disable=not show_progress_bar)
    with open(path, mode="wb") as f:
        for chunk in response.iter_content(chunk_size=4096):
            download_bar.update(len(chunk))
            f.write(chunk)
    download_bar.close()


def build_year_interval(from_year, to_year):
    if (from_year is None) and (to_year is None):
        return (Defults.first_year, Defults.last_year+1)
    elif to_year is None:
        return (from_year, from_year+1)
    elif to_year <= from_year:
        return (from_year, from_year+1)
    else:
        return (from_year, to_year+1)