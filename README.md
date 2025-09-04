# Download SWOT Data

## Overview

`download_swot` is a Python tool for downloading SWOT (Surface Water and Ocean Topography) Level 3 data products from the AVISO FTP server. It automates the process of authenticating, scanning, and downloading large datasets in parallel, organizing them into a local directory structure for further analysis.

## Features

- Authenticates securely using `.netrc` credentials.
- Scans the remote FTP directory for available SWOT data files.
- Downloads files in parallel using a thread pool for efficiency (max 6 threads, following AVISO guidelines).
- Verifies file integrity using `xarray`.
- Organizes downloaded data into `calval` and `science` subfolders.

## Requirements

- Python 3.11+
- [pixi](https://prefix.dev/docs/pixi/) (for environment management)
- Packages: `xarray`, `tqdm`, `ipykernel`

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
Downloaded files will be organized under `/mnt/bigcreek_nfs_share/swot/<version>/<dtype>/`.

Edit the script `src/download_swot/download_swot.py` to customize output directory or other parameters as needed.

## Project Structure

```
src/download_swot/
	 __init__.py
	 download_swot.py
data/
	 external/
	 processed/
```

- `src/download_swot/download_swot.py`: Main script for downloading SWOT data.
- `data/`: Place for storing raw and processed data (if needed).

## Contribution

Contributions are welcome! Please open issues or submit pull requests for improvements or bug fixes.

## License

This project is licensed under the MIT License.
