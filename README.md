# PyHEIS

A package to obtain household expenditure and income survey data.

## Usage

:one: Clone the repository:

```sh
git clone https://github.com/m-amin-alavian/PyHEIS household
```

:two: Create the `settings.yaml` file based on the `settings-sample.yaml`.

:three: Create a script in the root folder, using the `heis` modules as needed:

```python
from heis import archive_handler, raw_data, process
 
archive_handler.download_year_files_in_range(1396, 1397)
archive_handler.extract_data_from_access_files(1396,1397)

raw_data.make_parquet([1396, 1397], 'food')

process.get_commodity_data("flour_and_noodle", 1397)
process.get_commodity_data("meat", 1397)
```
