# Download SWOT Data

## Overview

`download_swot` is a Python tool for downloading SWOT (Surface Water and Ocean Topography) Level 3 data products from the AVISO FTP server. It automates authentication, scanning, and parallel downloading of large datasets, organizing them into a local directory structure for further analysis.

## Features

- Authenticates securely using `.netrc` credentials.
- Scans the remote FTP directory for available SWOT data files.
- Downloads files in parallel using a thread pool for efficiency (up to 8 threads).
- Verifies file integrity using `xarray`.
- Organizes downloaded data into `calval` and `science` subfolders.
- Flexible CLI for filtering by pass ID and cycle.

## Requirements

- Python 3.11+
- [pixi](https://prefix.dev/docs/pixi/) (for environment management)
- Packages: `xarray`, `tqdm`, `ipykernel`, `netcdf4`, `h5netcdf`, `pytest` (for tests)

## Installation

1. Clone the repository:
    ```bash
    git clone https://github.com/iuryt/download_swot.git
    cd download_swot
    ```

2. Set up the environment with pixi:
    ```bash
    pixi install
    ```

3. Ensure your `~/.netrc` file contains credentials for `ftp-access.aviso.altimetry.fr`:
    ```
    machine ftp-access.aviso.altimetry.fr
      login <your_username>
      password <your_password>
    ```

## Usage

To download SWOT data, run:

```bash
pixi run download_swot
```

### CLI Options

- `--pass-id`: Specify one or more pass IDs (PPP) to download (space separated).
- `--cycle`: Specify one or more cycles (CCC) to download (space separated).
- `--cycle-min` and `--cycle-max`: Specify a range of cycles to download.
- `--output`: Set a custom output directory (default: `./data/external`).
- `--num-workers`: Set the number of parallel downloads (default: 4, max: 8).
- `--log-level`: Set the logging level (default: INFO).

### Example

To download only files for pass IDs 214 and 533, and cycles 14 to 16:

```bash
pixi run download_swot --pass-id 214 533 --cycle-min 14 --cycle-max 16
```

Downloaded files will be organized under `./data/external/<dtype>/` by default.

### Python API Example

```python
from download_swot import list_files, download_file
# ... set up your arguments ...
files = list_files(path, output, dtype, username, password, pass_ids={"214", "533"}, cycle_min=14, cycle_max=16)
for remote, local in files:
    download_file(remote, local, username, password)
```

## Project Structure

```
download_swot/
    __init__.py
    download_swot.py
data/
    external/
    processed/
tests/
    test_download_swot.py
```

- `download_swot/download_swot.py`: Main script for downloading SWOT data.
- `data/`: Place for storing raw and processed data.
- `tests/`: Unit tests for the package.

## Contribution

Contributions are welcome! Please open issues or submit pull requests for improvements or bug fixes.

## License

This project is licensed under the MIT License.
