import os
import netrc
import warnings

def get_netrc_credentials(host, fallback_host=None):
    try:
        auth_data = netrc.netrc().authenticators(host)
    except Exception:
        auth_data = None
    if auth_data:
        username, _, password = auth_data
    elif fallback_host:
        try:
            fallback_auth = netrc.netrc().authenticators(fallback_host)
        except Exception:
            fallback_auth = None
        if fallback_auth:
            username, _, password = fallback_auth
            warnings.warn(f"No credentials for {host}, using credentials for {fallback_host}.")
        else:
            return None
    else:
        return None
    return (username, password)

def ensure_directories(base_output, dtype=None):
    """
    Create output directories if they don't exist. base_output should be <output>/<version>/<dtype>
    """
    directories = [
        os.path.join(base_output, "calval"),
        os.path.join(base_output, "science")
    ]
    os.makedirs(base_output, exist_ok=True)
    for directory in directories:
        os.makedirs(directory, exist_ok=True)
