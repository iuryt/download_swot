from download_swot.utils.normalize import normalize_pass_ids
import requests
import xml.etree.ElementTree as ET
import ftplib
from urllib.parse import urlparse
from .utils.credentials import get_netrc_credentials
import warnings

TDS_HOST = "tds-odatis.aviso.altimetry.fr"
CATALOG_BASE = "https://tds-odatis.aviso.altimetry.fr/thredds/catalog/dataset-l3-swot-karin-nadir-validated/l3_lr_ssh"
FILESERVER_BASE = "https://tds-odatis.aviso.altimetry.fr/thredds/fileServer/dataset-l3-swot-karin-nadir-validated/l3_lr_ssh"
FTP_HOST = "ftp-access.aviso.altimetry.fr"
FTP_BASE = "/swot_products/l3_karin_nadir/l3_lr_ssh"



def list_https_files(version, dtype, auth, pass_ids=None, cycle_list=None, cycle_min=None, cycle_max=None):
    """
    List HTTPS file URLs with optional filtering by pass_ids, cycle_list, cycle_min, cycle_max.
    """
    catalog_url = f"{CATALOG_BASE}/{version}/{dtype}/catalog.xml"
    resp = requests.get(catalog_url, auth=auth)
    resp.raise_for_status()
    root = ET.fromstring(resp.content)
    ns = {'cat': 'http://www.unidata.ucar.edu/namespaces/thredds/InvCatalog/v1.0'}
    refs = [e.attrib['name'] for e in root.findall('.//cat:catalogRef', ns)]
    # v2 lists cycle_XXX directly under dtype; v3 adds a stream level
    # (forward/, reproc/) above them. Collect cycles as paths relative to dtype.
    cycles = [r for r in refs if r.startswith('cycle_')]
    for stream in (r for r in refs if not r.startswith('cycle_')):
        sresp = requests.get(f"{CATALOG_BASE}/{version}/{dtype}/{stream}/catalog.xml", auth=auth)
        sresp.raise_for_status()
        sroot = ET.fromstring(sresp.content)
        cycles += [f"{stream}/{e.attrib['name']}" for e in sroot.findall('.//cat:catalogRef', ns)
                   if e.attrib['name'].startswith('cycle_')]
    # Filtering cycles
    filtered_cycles = []
    for c in cycles:
        try:
            cycle_num = int(c.rsplit('cycle_', 1)[1])
            if cycle_list and cycle_num not in cycle_list:
                continue
            if cycle_min is not None and cycle_num < cycle_min:
                continue
            if cycle_max is not None and cycle_num > cycle_max:
                continue
            filtered_cycles.append(c)
        except Exception:
            continue
    all_urls = []
    for cycle in filtered_cycles:
        cycle_url = f"{CATALOG_BASE}/{version}/{dtype}/{cycle}/catalog.xml"
        resp = requests.get(cycle_url, auth=auth)
        resp.raise_for_status()
        root = ET.fromstring(resp.content)
        files = [e.attrib['name'] for e in root.findall('.//cat:dataset', ns) if e.attrib['name'].endswith('.nc')]
        for fname in files:
            # pass_id is always the 4th from the end, like in FTP
            try:
                pass_id = fname.split('_')[-4]
            except Exception:
                pass_id = None
            if pass_ids and pass_id not in pass_ids:
                continue
            all_urls.append(f"{FILESERVER_BASE}/{version}/{dtype}/{cycle}/{fname}")
    return all_urls

def list_ftp_files(version, dtype, username, password, pass_ids=None, cycle_list=None, cycle_min=None, cycle_max=None):
    base_path = f"{FTP_BASE}/{version}/{dtype}"
    all_files = []
    if pass_ids:
        pass_ids = normalize_pass_ids(pass_ids)
    with ftplib.FTP(FTP_HOST) as ftp:
        ftp.login(username, password)
        ftp.cwd(base_path)
        entries = ftp.nlst()
        # v2 lists cycle_XXX directly under dtype; v3 adds a stream level
        # (forward/, reproc/) above them. Keep (path relative to dtype, cycle name).
        cycles = [(e, e) for e in entries if e.startswith("cycle_")]
        for stream in (e for e in entries if not e.startswith("cycle_")):
            try:
                ftp.cwd(f"{base_path}/{stream}")
                cycles += [(f"{stream}/{c}", c) for c in ftp.nlst() if c.startswith("cycle_")]
                ftp.cwd(base_path)
            except Exception as e:
                warnings.warn(f"Skipping folder {stream}: {e}")
        for d, cname in cycles:
            try:
                cycle = int(cname.split("_")[1])
                if cycle_list and cycle not in cycle_list:
                    continue
                if cycle_min is not None and cycle < cycle_min:
                    continue
                if cycle_max is not None and cycle > cycle_max:
                    continue
                ftp.cwd(f"{base_path}/{d}")
                file_list = ftp.nlst()
                for fname in file_list:
                    pass_id = fname.split("_")[-4]
                    if pass_ids and pass_id not in pass_ids:
                        continue
                    all_files.append((f"{base_path}/{d}/{fname}", cname, fname))
                ftp.cwd(base_path)
            except Exception as e:
                warnings.warn(f"Skipping folder {d}: {e}")
    seen = set()
    for _, _, fname in all_files:
        if fname in seen:
            warnings.warn(f"{fname} is listed in more than one stream; the last copy wins locally")
        seen.add(fname)
    return all_files
