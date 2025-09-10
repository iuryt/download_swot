import os
import ftplib
from tqdm import tqdm
from concurrent.futures import ThreadPoolExecutor
import netrc
import xarray as xr
import logging
import argparse

FTP_SERVER = "ftp-access.aviso.altimetry.fr"

def get_credentials(server):
    """Retrieve FTP credentials from .netrc."""
    auth_data = netrc.netrc().authenticators(server)
    if auth_data:
        username, _, password = auth_data
        return username, password
    else:
        raise ValueError(f"Credentials for {server} not found in ~/.netrc")

def ensure_directories(base_output, dtype):
    """Create output directories if they don't exist."""
    directories = [
        os.path.join(base_output, dtype, "calval"),
        os.path.join(base_output, dtype, "science")
    ]
    os.makedirs(os.path.join(base_output, dtype), exist_ok=True)
    for directory in directories:
        os.makedirs(directory, exist_ok=True)

def list_files(path, output, dtype, username, password, pass_ids=None, cycle_list=None, cycle_min=None, cycle_max=None, server=FTP_SERVER):
    """List all files to download from the FTP server. Handles its own connection."""
    all_files = []
    # Normalize pass_ids to zero-padded 3-digit strings if provided
    norm_pass_ids = None
    if pass_ids is not None:
        norm_pass_ids = set(f"{int(pid):03d}" for pid in pass_ids)
    norm_cycle_list = set(int(c) for c in cycle_list) if cycle_list else None
    try:
        with ftplib.FTP(server) as ftp:
            ftp.login(username, password)
            ftp.cwd(path)
            cycle_folders = ftp.nlst()

            for d in tqdm(cycle_folders, desc="Listing files", unit="cycle"):
                try:
                    cycle = int(d.split("_")[1])
                    # Filter by cycle list or min/max
                    if norm_cycle_list and cycle not in norm_cycle_list:
                        continue
                    if cycle_min is not None and cycle < cycle_min:
                        continue
                    if cycle_max is not None and cycle > cycle_max:
                        continue
                    orbit = "calval" if cycle > 400 else "science"
                    ftp.cwd(os.path.join(path, d))
                    file_list = ftp.nlst()
                    for fname in file_list:
                        pass_id = fname.split("_")[-4]
                        if norm_pass_ids is not None and pass_id not in norm_pass_ids:
                            continue
                        foutput = os.path.join(output, dtype, orbit, fname)
                        all_files.append((os.path.join(path, d, fname), foutput))
                    ftp.cwd(path)
                except Exception as e:
                    logging.warning(f"Skipping folder {d}: {e}")
    except Exception as e:
        logging.error(f"Failed to list folders in {path}: {e}")
        return []
    return all_files

def download_file(remote_path, local_path, username, password, server=FTP_SERVER):
    """Download a single file using a separate FTP connection."""
    if os.path.exists(local_path):
        try:
            xr.open_dataset(local_path)
            return  # skip existing non-corrupted files
        except Exception as e:
            logging.warning(f"Corrupted file detected at {local_path}: {e}. Re-downloading.")

    try:
        with ftplib.FTP(server) as ftp:
            ftp.login(username, password)
            ftp.set_pasv(True)
            with open(local_path, 'wb') as f:
                ftp.retrbinary(f"RETR {remote_path}", f.write, 8192)
    except Exception as e:
        logging.error(f"Error downloading {remote_path}: {e}")

def main():
    """Main function to orchestrate the download process."""
    parser = argparse.ArgumentParser(description="Download SWOT products from FTP server.")
    parser.add_argument('--version', type=str, default="v2_0_1", help='SWOT data version (default: v2_0_1)')
    parser.add_argument('--dtype', type=str, default="Unsmoothed", help='Data type (default: Unsmoothed)')
    parser.add_argument('--output', type=str, default=None, help='Output directory (default: /mnt/bigcreek_nfs_share/swot/<version>/)')
    parser.add_argument('--num-workers', type=int, default=4, help='Number of parallel downloads (default: 4, max: 8)')
    parser.add_argument('--log-level', type=str, default="INFO", help='Logging level (default: INFO)')
    parser.add_argument('--pass-id', type=str, nargs='*', default=None, help='Specific pass_id(s) to download (space separated or repeatable)')
    parser.add_argument('--cycle', type=int, nargs='*', default=None, help='Specific cycle(s) to download (space separated or repeatable)')
    parser.add_argument('--cycle-min', type=int, default=None, help='Minimum cycle number to download')
    parser.add_argument('--cycle-max', type=int, default=None, help='Maximum cycle number to download')
    args = parser.parse_args()

    version = args.version
    dtype = args.dtype
    output = args.output or os.path.abspath(os.path.join(os.path.dirname(__file__), '../data/external'))
    num_workers = min(max(1, args.num_workers), 8)  # Ensure between 1 and 8
    log_level = getattr(logging, args.log_level.upper(), logging.INFO)

    logging.basicConfig(level=log_level, format="%(asctime)s [%(levelname)s] %(message)s")

    username, password = get_credentials(FTP_SERVER)
    ensure_directories(output, dtype)
    path = f'/swot_products/l3_karin_nadir/l3_lr_ssh/{version}/{dtype}'

    pass_ids = set(args.pass_id) if args.pass_id else None
    cycle_list = args.cycle if args.cycle else None
    cycle_min = args.cycle_min
    cycle_max = args.cycle_max

    # Warn and ignore min/max if cycle_list is provided
    if cycle_list and (cycle_min is not None or cycle_max is not None):
        logging.warning("Both --cycle and --cycle-min/--cycle-max were provided. Only --cycle will be used.")
        cycle_min = None
        cycle_max = None

    all_files = list_files(
        path, output, dtype, username, password,
        pass_ids=pass_ids,
        cycle_list=cycle_list,
        cycle_min=cycle_min,
        cycle_max=cycle_max
    )

    if not all_files:
        logging.info("No files to download.")
        return

    logging.info(f"Total files to download: {len(all_files)}")
    with ThreadPoolExecutor(max_workers=num_workers) as executor:
        list(tqdm(
            executor.map(lambda x: download_file(x[0], x[1], username, password), all_files),
            total=len(all_files), desc="Downloading files", unit="file"
        ))
    logging.info("Download complete.")

if __name__ == "__main__":
    main()
