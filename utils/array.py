"""
Array utils
"""


def get_item(items, i, default=None):
    """
    "Return the i-th item of items, or default if i is out of range."
    """
    try:
        return items[i]
    except IndexError:
        return default
