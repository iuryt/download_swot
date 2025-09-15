def get_orbit_subfolder(cycle: int) -> str:
    """
    Returns 'calval' if cycle >= 400, else 'science'.
    Assumes cycle is an int.
    """
    assert isinstance(cycle, int), "cycle must be an integer"
    return "calval" if cycle >= 400 else "science"
