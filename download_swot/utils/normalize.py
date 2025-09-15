def normalize_pass_ids(pass_ids):
    """Normalize pass_ids to 3-digit strings and remove duplicates."""
    if not pass_ids:
        return set()
    return set(f"{int(pid):03d}" for pid in pass_ids)
