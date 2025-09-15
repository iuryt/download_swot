
import os
import time
import requests
import ftplib
from urllib.parse import urlparse
import netrc
import argparse
import sys
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from download_swot.listing import list_https_files, list_ftp_files, TDS_HOST, FTP_HOST
from download_swot.utils.credentials import get_netrc_credentials

DEFAULT_VERSION = "v2_0_1"
DEFAULT_DTYPE = "Unsmoothed"
DEFAULT_OUTPUT_DIR = "../data/external/benchmark_downloads"
os.makedirs(DEFAULT_OUTPUT_DIR, exist_ok=True)

def download_https(url, out_path, username=None, password=None):
    print(f"Downloading via HTTPS: {url}")
    start = time.time()
    auth = (username, password) if username and password else None
    with requests.get(url, stream=True, auth=auth) as r:
        r.raise_for_status()
        with open(out_path, 'wb') as f:
            for chunk in r.iter_content(chunk_size=8192):
                if chunk:
                    f.write(chunk)
    elapsed = time.time() - start
    print(f"HTTPS download finished in {elapsed:.2f} seconds\n")
    return elapsed

def download_ftp(url, out_path, username=None, password=None):
    print(f"Downloading via FTP: {url}")
    parsed = urlparse(url)
    ftp_host = parsed.hostname
    ftp_path = parsed.path
    start = time.time()
    with ftplib.FTP(ftp_host) as ftp:
        ftp.login(username, password)
        with open(out_path, 'wb') as f:
            ftp.retrbinary(f"RETR {ftp_path}", f.write, 8192)
    elapsed = time.time() - start
    print(f"FTP download finished in {elapsed:.2f} seconds\n")
    return elapsed


def get_first_file(version, dtype, pass_id, cycle):
    # Use list_https_files and list_ftp_files to get the first file for the given filters
    creds = get_netrc_credentials(TDS_HOST, fallback_host=FTP_HOST)
    https_files = list_https_files(version, dtype, creds, pass_ids={pass_id}, cycle_list=[int(cycle)])
    ftp_creds = get_netrc_credentials(FTP_HOST)
    ftp_files = list_ftp_files(version, dtype, ftp_creds[0], ftp_creds[1], pass_ids={pass_id}, cycle_list=[int(cycle)])
    https_url = https_files[0] if https_files else None
    ftp_tuple = ftp_files[0] if ftp_files else None
    ftp_url = None
    if ftp_tuple:
        # ftp_tuple = (remote_path, cycle, fname)
        ftp_url = f"ftp://{FTP_HOST}{ftp_tuple[0]}"
    fname = os.path.basename(https_url) if https_url else (ftp_tuple[2] if ftp_tuple else None)
    return https_url, ftp_url, fname

def main():
    parser = argparse.ArgumentParser(description="Benchmark FTP vs HTTPS download speed for a single SWOT file using package listing functions.")
    parser.add_argument('--protocol', choices=['ftp', 'https', 'both'], default='both', help='Which protocol(s) to benchmark')
    parser.add_argument('--version', type=str, default=DEFAULT_VERSION)
    parser.add_argument('--dtype', type=str, default=DEFAULT_DTYPE)
    parser.add_argument('--cycle', type=str, required=True)
    parser.add_argument('--pass-id', type=str, required=True)
    parser.add_argument('--output-dir', type=str, default=DEFAULT_OUTPUT_DIR)
    args = parser.parse_args()

    https_url, ftp_url, filename = get_first_file(args.version, args.dtype, args.pass_id, args.cycle)
    if not (https_url or ftp_url):
        print("No file found for the given filters.")
        return
    os.makedirs(args.output_dir, exist_ok=True)
    https_path = os.path.join(args.output_dir, f"https_{filename}") if https_url else None
    ftp_path = os.path.join(args.output_dir, f"ftp_{filename}") if ftp_url else None

    creds = get_netrc_credentials(TDS_HOST, fallback_host=FTP_HOST)
    ftp_creds = get_netrc_credentials(FTP_HOST)
    username, password = creds if creds else (None, None)
    ftp_username, ftp_password = ftp_creds if ftp_creds else (None, None)

    times = {}
    if args.protocol in ('https', 'both') and https_url:
        times['https'] = download_https(https_url, https_path, username, password)
    if args.protocol in ('ftp', 'both') and ftp_url:
        times['ftp'] = download_ftp(ftp_url, ftp_path, ftp_username, ftp_password)

    print("Summary:")
    for proto, t in times.items():
        print(f"  {proto.upper()}: {t:.2f} s")

if __name__ == "__main__":
    main()
