"""
General function to return a realpath string of any path starting on rinbot/
"""

import os

def get_os_path(path: str) -> str:
    """
    Returns the realpath of the given path starting at rinbot/

    Args:
        path (str): The path starting on rinbot/

    Returns:
        str: Real os path to be used without errors
    """
    
    return os.path.realpath(os.path.join(os.path.dirname(__file__), '..', path))

# TEST
if __name__ == '__main__':
    print(get_os_path('base'))
    print(get_os_path('base/logger.py'))
    print(get_os_path('../instance'))
