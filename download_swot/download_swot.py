# CLI entry point for unified download_swot
import argparse
from download_swot.listing import list_https_files, list_ftp_files, TDS_HOST, FTP_HOST
from download_swot.downloader import download_https_file, download_ftp_file
from download_swot.utils.credentials import get_netrc_credentials, ensure_directories
from download_swot.utils.orbit import get_orbit_subfolder
import sys
import os
from concurrent.futures import ThreadPoolExecutor


def main():
    parser = argparse.ArgumentParser(description="Download SWOT products from FTP or HTTPS.")
    parser.add_argument('--protocol', choices=['ftp', 'https'], default='ftp', help='Download protocol (ftp or https)')
    parser.add_argument('--version', type=str, default="v2_0_1", help='SWOT data version (default: v2_0_1)')
    parser.add_argument('--dtype', type=str, default="Basic", help='Data type (default: Basic)')
    parser.add_argument('--output', type=str, default=None, help='Output directory (default: ../data/external)')
    parser.add_argument('--num-workers', type=int, default=4, help='Number of parallel downloads (default: 4, max: 8)')
    parser.add_argument('--pass-id', type=str, nargs='*', default=None, help='Specific pass_id(s) to download (space separated or repeatable)')
    parser.add_argument('--cycle', type=int, nargs='*', default=None, help='Specific cycle(s) to download (space separated or repeatable)')
    parser.add_argument('--cycle-min', type=int, default=None, help='Minimum cycle number to download')
    parser.add_argument('--cycle-max', type=int, default=None, help='Maximum cycle number to download')
    parser.add_argument('--overwrite', action='store_true', help='Overwrite files even if they exist and are valid')
    args = parser.parse_args()

    version = args.version
    dtype = args.dtype

    protocol = args.protocol
    if protocol not in ('ftp', 'https'):
        raise ValueError(f"Invalid protocol: {protocol}. Must be 'ftp' or 'https'.")

    if args.output:
        output = os.path.join(args.output, version, dtype)
    else:
        output = os.path.abspath(os.path.join(os.path.dirname(__file__), '../data/external', version, dtype))
    num_workers = min(max(1, args.num_workers), 8)
    pass_ids = set(args.pass_id) if args.pass_id else None
    cycle_list = args.cycle if args.cycle else None
    cycle_min = args.cycle_min
    cycle_max = args.cycle_max


    # Ensure science and calval subfolders exist
    science_dir = os.path.join(output, "science")
    calval_dir = os.path.join(output, "calval")
    os.makedirs(science_dir, exist_ok=True)
    os.makedirs(calval_dir, exist_ok=True)

    if protocol == 'ftp':
        creds = get_netrc_credentials(FTP_HOST)
        if not creds:
            print("No FTP credentials found in .netrc", file=sys.stderr)
            sys.exit(1)
        username, password = creds
        files = list_ftp_files(version, dtype, username, password, pass_ids=pass_ids, cycle_list=cycle_list, cycle_min=cycle_min, cycle_max=cycle_max)
        if not files:
            print("No files to download.")
            return
        print(f"Total files to download: {len(files)}")
        total_files = len(files)
        def ftp_task(args_with_idx):
            idx, (remote_path, cycle, fname) = args_with_idx
            # Ensure cycle is int for get_orbit_subfolder
            if isinstance(cycle, str):
                cycle_int = int(cycle.split('_')[-1]) if '_' in cycle else int(cycle)
            else:
                cycle_int = int(cycle)
            subfolder = get_orbit_subfolder(cycle_int)
            local_path = os.path.join(output, subfolder, fname)
            prefix = f"[{idx+1}/{total_files}]"
            download_ftp_file(FTP_HOST, remote_path, local_path, username, password, desc_prefix=prefix, overwrite=args.overwrite if hasattr(args, 'overwrite') else False)
        with ThreadPoolExecutor(max_workers=num_workers) as executor:
            list(executor.map(ftp_task, enumerate(files)))
    elif protocol == 'https':
        creds = get_netrc_credentials(TDS_HOST, fallback_host=FTP_HOST)
        if not creds:
            print("No HTTPS/FTP credentials found in .netrc", file=sys.stderr)
            sys.exit(1)
        urls = list_https_files(version, dtype, creds, pass_ids=pass_ids, cycle_list=cycle_list, cycle_min=cycle_min, cycle_max=cycle_max)
        if not urls:
            print("No files to download.")
            return
        print(f"Total files to download: {len(urls)}")
        total_files = len(urls)
        def https_task(args_with_idx):
            idx, url = args_with_idx
            fname = os.path.basename(url)
            # Try to extract cycle from URL: .../cycle_XXX/filename
            try:
                parts = url.split('/')
                idx_cycle = parts.index('l3_lr_ssh')
                cycle = parts[idx_cycle+3].split('_')[-1]
            except Exception:
                cycle = 'unknown'
            # Ensure cycle is int for get_orbit_subfolder
            cycle_int = int(cycle)
            subfolder = get_orbit_subfolder(cycle_int)
            local_path = os.path.join(output, subfolder, fname)
            prefix = f"[{idx+1}/{total_files}]"
            download_https_file(url, local_path, creds, desc_prefix=prefix, overwrite=args.overwrite if hasattr(args, 'overwrite') else False)
        with ThreadPoolExecutor(max_workers=num_workers) as executor:
            list(executor.map(https_task, enumerate(urls)))
    print("Download complete.")

if __name__ == "__main__":
    main()

