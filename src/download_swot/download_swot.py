#%%
import os
import ftplib
from tqdm import tqdm
import os 
from concurrent.futures import ThreadPoolExecutor
import netrc
import xarray as xr

#%%
FTP_SERVER = "ftp-access.aviso.altimetry.fr"

# Retrieve credentials from .netrc
auth_data = netrc.netrc().authenticators(FTP_SERVER)
if auth_data:
    username, _, password = auth_data
else:
    raise ValueError(f"Credentials for {FTP_SERVER} not found in ~/.netrc")

#%%

ftp = ftplib.FTP(FTP_SERVER)
ftp.login(username, password)

version = "v2_0_1"
dtype = "Unsmoothed"

output = f"/mnt/bigcreek_nfs_share/swot/{version}/"

#%%

# Define the directories to create
directories = [
    os.path.join(output, dtype, "calval"),
    os.path.join(output, dtype, "science")
]

os.makedirs(os.path.join(output,dtype), exist_ok=True)

# Create the directories if they don't exist
for directory in directories:
    os.makedirs(directory, exist_ok=True)


path = f'/swot_products/l3_karin_nadir/l3_lr_ssh/{version}/{dtype}'
ftp.cwd(path)


# Step 1: Pre-scan to list all files
all_files = []
cycle_folders = ftp.nlst()

for d in tqdm(cycle_folders, desc="Listing files", unit="cycle"):
    cycle = int(d.split("_")[1])
    orbit = "calval" if cycle > 400 else "science"
    
    ftp.cwd(os.path.join(path, d))
    file_list = ftp.nlst()
    
    for fname in file_list:
        foutput = os.path.join(output, dtype, orbit, fname)
        all_files.append((os.path.join(path, d, fname), foutput))  # Store (remote_path, local_path)
    
    ftp.cwd(path)  # Go back to the parent directory for the next cycle
    


# Step 2: Multi-threaded FTP Download
def download_file(remote_path, local_path, username=username, password=password, server=FTP_SERVER):
    """Download a single file using a separate FTP connection."""
    if os.path.exists(local_path):
        try:
            xr.open_dataset(local_path)
            return # skip existing non-corrupted files
        except Exception as e:
            print(f"Error loading  {remote_path}: {e}. File is likely corrupted. Let's try to download it again.")

    try:
        with ftplib.FTP(server) as ftp:
            ftp.login(username, password)
            ftp.set_pasv(True)  # Ensure passive mode
            with open(local_path, 'wb') as f:
                ftp.retrbinary(f"RETR {remote_path}", f.write, 8192)  # Larger buffer for speed
    except Exception as e:
        print(f"Error downloading {remote_path}: {e}")

files_to_download = all_files

# Use a thread pool to download files in parallel
num_workers = 4  # Adjust based on server limits (8 is the max for this server)
with ThreadPoolExecutor(max_workers=num_workers) as executor:
    list(tqdm(executor.map(lambda x: download_file(*x), files_to_download), 
              total=len(files_to_download), desc="Downloading files", unit="file"))

print("Download complete.")
