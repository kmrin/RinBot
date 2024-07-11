import os

from typing import List

def get_os_path(p: str) -> str:
    """
    Returns the realpath of the given path starting at rinbot/

    Args:
        p (str): The path starting at rinbot/

    Returns:
        str: Real os path to be used without errors (hopefuly)
    """
    
    return os.path.realpath(os.path.join(os.path.dirname(__file__), '..', p))

class Path:
    # Paths
    assets = get_os_path('assets/')
    config = get_os_path('config/client/rin.json')
    database = get_os_path('../instance/database/sqlite.db')
    extensions = get_os_path('extensions')
    instance = get_os_path('../instance')
    kobold_cogs = get_os_path('kobold/cogs')
    locale = get_os_path('config/localization')
    programs = get_os_path('programs')
    schema = get_os_path('config/database/schema.sql')
    tracebacks = get_os_path('../instance/logs/tracebacks')
    valorant = get_os_path('../instance/cache/valorant')
    
    @classmethod
    def list(cls) -> List[str]:
        """
        Returns a list with all available paths

        Returns:
            List[str]: The path list
        """
        
        path_list = [
            getattr(cls, attr) for attr in dir(cls)
            if not attr.startswith('__') and not callable(getattr(cls, attr))
        ]
        
        return path_list
