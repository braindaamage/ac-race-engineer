"""Filename sanitization for AC Race Engineer.

Sanitizes car/track names for use in filenames. Python 3.3 compatible.
"""
import re


def sanitize_name(name):
    """Sanitize a name for use in filenames.

    Rules (per contracts/csv-output.md):
    1. Convert to lowercase
    2. Replace spaces with underscores
    3. Replace any character not in [a-z0-9_] with underscore
    4. Collapse multiple consecutive underscores to single underscore
    5. Strip leading and trailing underscores
    """
    if not name:
        return ""
    result = name.lower()
    result = result.replace(" ", "_")
    result = re.sub(r"[^a-z0-9_]", "_", result)
    result = re.sub(r"_+", "_", result)
    result = result.strip("_")
    return result
