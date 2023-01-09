# PyHEIS

A package to obtain household data.

## Usage

:one: Clone the repository:

```sh
git clone https://github.com/m-amin-alavian/PyHEIS household
```

:two: Modify the `setttings.yaml` file to your liking.

:three: Create a script in the root folder, using the `heis` modules as needed:

```python
from heis import compressed_data, raw_data

compressed_data.download(1396, 1397)
compressed_data.extract(1396,1397)
raw_data.extract_raw_data_to_db(1396, 1397)
```
