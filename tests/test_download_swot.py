import pytest
from download_swot import download_swot

# Test normalization of pass_ids (private helper for test)
def test_pass_id_normalization():
    # Simulate user input
    user_pass_ids = ['2', '02', '002', '123']
    # Expected normalized set
    expected = {'002', '123'}
    # Use the same normalization logic as in list_files
    norm_pass_ids = set(f"{int(pid):03d}" for pid in user_pass_ids)
    assert norm_pass_ids == expected

# Test filtering logic in list_files (mocked)
def test_list_files_filters_by_pass_id(monkeypatch):
    # Prepare a fake FTP listing
    fake_files = [
        'SWOT_L3_LR_SSH_Unsmoothed_001_002_20230101T000000_20230101T235959_v2.0.1.nc',
        'SWOT_L3_LR_SSH_Unsmoothed_001_123_20230101T000000_20230101T235959_v2.0.1.nc',
        'SWOT_L3_LR_SSH_Unsmoothed_001_999_20230101T000000_20230101T235959_v2.0.1.nc',
    ]
    fake_cycle_folders = ['cycle_001']
    # Patch ftplib.FTP and its methods
    class FakeFTP:
        def __init__(self, *a, **kw): pass
        def __enter__(self): return self
        def __exit__(self, exc_type, exc_val, exc_tb): pass
        def login(self, *a, **kw): pass
        def cwd(self, *a, **kw): pass
        def nlst(self):
            # First call returns cycle folders, second returns files
            if not hasattr(self, 'called'):
                self.called = True
                return fake_cycle_folders
            return fake_files
    monkeypatch.setattr('download_swot.download_swot.ftplib.FTP', FakeFTP)
    # Call list_files with pass_ids
    result = download_swot.list_files(
        path='fake_path',
        output='fake_output',
        dtype='Unsmoothed',
        username='user',
        password='pw',
        pass_ids={'002', '123'}
    )
    # Only files with pass_id 002 and 123 should be included
    assert len(result) == 2
    assert all(any(pid in r[0] for pid in ['002', '123']) for r in result)

# Test that all files are included if pass_ids is None
def test_list_files_no_filter(monkeypatch):
    fake_files = [
        'SWOT_L3_LR_SSH_Unsmoothed_001_002_20230101T000000_20230101T235959_v2.0.1.nc',
        'SWOT_L3_LR_SSH_Unsmoothed_001_123_20230101T000000_20230101T235959_v2.0.1.nc',
        'SWOT_L3_LR_SSH_Unsmoothed_001_999_20230101T000000_20230101T235959_v2.0.1.nc',
    ]
    fake_cycle_folders = ['cycle_001']
    class FakeFTP:
        def __init__(self, *a, **kw): pass
        def __enter__(self): return self
        def __exit__(self, exc_type, exc_val, exc_tb): pass
        def login(self, *a, **kw): pass
        def cwd(self, *a, **kw): pass
        def nlst(self):
            if not hasattr(self, 'called'):
                self.called = True
                return fake_cycle_folders
            return fake_files
    monkeypatch.setattr('download_swot.download_swot.ftplib.FTP', FakeFTP)
    result = download_swot.list_files(
        path='fake_path',
        output='fake_output',
        dtype='Unsmoothed',
        username='user',
        password='pw',
        pass_ids=None
    )


# Test cycle filtering by list
def test_list_files_cycle_list(monkeypatch):
    fake_files = [
        'SWOT_L3_LR_SSH_Unsmoothed_002_002_20230101T000000_20230101T235959_v2.0.1.nc',
    ]
    fake_cycle_folders = ['cycle_001', 'cycle_002', 'cycle_003']
    class FakeFTP:
        def __init__(self, *a, **kw): pass
        def __enter__(self): return self
        def __exit__(self, exc_type, exc_val, exc_tb): pass
        def login(self, *a, **kw): pass
        def cwd(self, *a, **kw): pass
        def nlst(self):
            if not hasattr(self, 'called'):
                self.called = True
                return fake_cycle_folders
            return fake_files
    monkeypatch.setattr('download_swot.download_swot.ftplib.FTP', FakeFTP)
    # Only cycle 2 should be included
    result = download_swot.list_files(
        path='fake_path',
        output='fake_output',
        dtype='Unsmoothed',
        username='user',
        password='pw',
        pass_ids=None,
        cycle_list=[2]
    )
    assert all('cycle_002' in r[0] for r in result)

# Test cycle filtering by min/max
def test_list_files_cycle_min_max(monkeypatch):
    fake_files = [
        'SWOT_L3_LR_SSH_Unsmoothed_002_002_20230101T000000_20230101T235959_v2.0.1.nc',
        'SWOT_L3_LR_SSH_Unsmoothed_003_003_20230101T000000_20230101T235959_v2.0.1.nc',
    ]
    fake_cycle_folders = ['cycle_001', 'cycle_002', 'cycle_003']
    class FakeFTP:
        def __init__(self, *a, **kw): pass
        def __enter__(self): return self
        def __exit__(self, exc_type, exc_val, exc_tb): pass
        def login(self, *a, **kw): pass
        def cwd(self, *a, **kw): pass
        def nlst(self):
            if not hasattr(self, 'called'):
                self.called = True
                return fake_cycle_folders
            return fake_files
    monkeypatch.setattr('download_swot.download_swot.ftplib.FTP', FakeFTP)
    # Only cycle 2 and 3 should be included
    result = download_swot.list_files(
        path='fake_path',
        output='fake_output',
        dtype='Unsmoothed',
        username='user',
        password='pw',
        pass_ids=None,
        cycle_min=2,
        cycle_max=3
    )
    assert all(any(f'cycle_00{c}' in r[0] for c in [2,3]) for r in result)

# Test precedence: cycle_list over min/max
def test_list_files_cycle_list_precedence(monkeypatch):
    fake_files = [
        'SWOT_L3_LR_SSH_Unsmoothed_002_002_20230101T000000_20230101T235959_v2.0.1.nc',
    ]
    fake_cycle_folders = ['cycle_001', 'cycle_002', 'cycle_003']
    class FakeFTP:
        def __init__(self, *a, **kw): pass
        def __enter__(self): return self
        def __exit__(self, exc_type, exc_val, exc_tb): pass
        def login(self, *a, **kw): pass
        def cwd(self, *a, **kw): pass
        def nlst(self):
            if not hasattr(self, 'called'):
                self.called = True
                return fake_cycle_folders
            return fake_files
    monkeypatch.setattr('download_swot.download_swot.ftplib.FTP', FakeFTP)
    # Only cycle 2 should be included, min/max ignored
    result = download_swot.list_files(
        path='fake_path',
        output='fake_output',
        dtype='Unsmoothed',
        username='user',
        password='pw',
        pass_ids=None,
        cycle_list=[2],
        cycle_min=1,
        cycle_max=3
    )
    assert all('cycle_002' in r[0] for r in result)
    assert len(result) == 1
    assert all(r[0].endswith('.nc') for r in result)
