"""
Paths to important files used throughout the codebase
"""

from typing import List

from .get_os_path import get_os_path

class Path:
    # Paths
    config = get_os_path('config/config.json')
    database = get_os_path('../instance/database/sqlite.db')
    extensions = get_os_path('extensions')
    instance = get_os_path('../instance')
    schema = get_os_path('config/database/schema.sql')
    tracebacks = get_os_path('../instance/logs/tracebacks')
    verbose = get_os_path('config/localization/{lang}.json')

    @classmethod
    def list(cls) -> List[str]:
        """
        List all paths

        Returns:
            List[str]: A list containing all paths as a string
        """
        
        paths = [
            getattr(cls, attr) for attr in dir(cls)
            if not attr.startswith('__') and not callable(getattr(cls, attr))
        ]
        
        return paths

# TEST
if __name__ == "__main__":
    paths = Path.list()
    
    for path in paths:
        print(path)
