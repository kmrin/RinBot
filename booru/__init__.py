__version__ = "5.0.0.dev1"
__license__ = "MIT"
__source_url__ = "https://github.com/LuqueDaniel/pybooru"
__author__ = "Daniel Luque <danielluque14[at]gmail[dot]com>"

# pybooru imports
from .moebooru import Moebooru
from .danbooru import Danbooru
from .exceptions import (PybooruError, PybooruAPIError, PybooruHTTPError)