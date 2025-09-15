import pytest
from download_swot.listing import list_https_files, list_ftp_files, TDS_HOST, FTP_HOST
from download_swot.utils.credentials import get_netrc_credentials
import os

@pytest.mark.skipif(os.environ.get('CI') == 'true', reason='No network in CI')
def test_https_listing_filtered():
    creds = get_netrc_credentials(TDS_HOST)
    assert creds is not None, "No HTTPS or FTP credentials found in .netrc"
    # Use a small cycle range and a specific pass_id to limit the result
    urls = list_https_files('v2_0_1', 'Unsmoothed', creds, pass_ids={'001'}, cycle_min=2, cycle_max=2)
    assert isinstance(urls, list)
    # If there are no files, that's OK, but if there are, they must match the filter
    for url in urls:
        assert url.endswith('.nc')
        assert '_001_' in url
        assert '/cycle_002/' in url

@pytest.mark.skipif(os.environ.get('CI') == 'true', reason='No network in CI')
def test_ftp_listing_filtered():
    creds = get_netrc_credentials(FTP_HOST)
    assert creds is not None, "No FTP credentials found in .netrc"
    files = list_ftp_files('v2_0_1', 'Unsmoothed', creds[0], creds[1], pass_ids={'001'}, cycle_min=2, cycle_max=2)
    assert isinstance(files, list)
    for _, cycle, fname in files:
        assert fname.endswith('.nc')
        assert '_001_' in fname
        assert 'cycle_002' in cycle
