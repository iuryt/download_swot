import os
import requests
import ftplib
from tqdm import tqdm
from .utils.credentials import ensure_directories


def download_https_file(url, local_path, auth, chunk_size=8192, desc_prefix=None, overwrite=False):
    os.makedirs(os.path.dirname(local_path), exist_ok=True)
    # Check if file exists and is valid
    if os.path.exists(local_path) and not overwrite:
        # Check file size against remote
        with requests.head(url, auth=auth) as r_head:
            r_head.raise_for_status()
            remote_size = int(r_head.headers.get('content-length', 0))
        local_size = os.path.getsize(local_path)
        if remote_size == local_size and remote_size > 0:
            if desc_prefix:
                print(f"{desc_prefix} {os.path.basename(local_path)}: already downloaded and valid.")
            else:
                print(f"{os.path.basename(local_path)}: already downloaded and valid.")
            return  # File exists and is not corrupted
        # else: fall through to re-download
    with requests.get(url, stream=True, auth=auth) as r:
        r.raise_for_status()
        total = int(r.headers.get('content-length', 0))
        desc = os.path.basename(local_path)
        if desc_prefix:
            desc = f"{desc_prefix} {desc}"
        with open(local_path, 'wb') as f, tqdm(total=total, unit='B', unit_scale=True, desc=desc, leave=True) as pbar:
            for chunk in r.iter_content(chunk_size=chunk_size):
                if chunk:
                    f.write(chunk)
                    pbar.update(len(chunk))

def download_ftp_file(ftp_host, remote_path, local_path, username, password, chunk_size=8192, desc_prefix=None, overwrite=False):
    os.makedirs(os.path.dirname(local_path), exist_ok=True)
    with ftplib.FTP(ftp_host) as ftp:
        ftp.login(username, password)
        # Sempre muda para modo binário antes de SIZE
        try:
            ftp.sendcmd('TYPE I')
        except Exception:
            pass
        total = None
        try:
            total = ftp.size(remote_path)
        except Exception:
            pass
        # Check if file exists and is valid
        if os.path.exists(local_path) and not overwrite and total:
            local_size = os.path.getsize(local_path)
            if local_size == total and total > 0:
                if desc_prefix:
                    print(f"{desc_prefix} {os.path.basename(local_path)}: already downloaded and valid.")
                else:
                    print(f"{os.path.basename(local_path)}: already downloaded and valid.")
                return  # File exists and is not corrupted
        desc = os.path.basename(local_path)
        if desc_prefix:
            desc = f"{desc_prefix} {desc}"
        with open(local_path, 'wb') as f:
            with tqdm(total=total, unit='B', unit_scale=True, desc=desc, leave=True) as pbar:
                def callback(data):
                    f.write(data)
                    pbar.update(len(data))
                ftp.retrbinary(f"RETR {remote_path}", callback, blocksize=chunk_size)
