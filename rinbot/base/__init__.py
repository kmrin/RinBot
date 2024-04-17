"""
RinBot 5 'Aurora' code base
"""

from .client import RinBot
from .colours import Colour
from .command_checks import is_admin, is_owner, not_blacklisted
from .db import DBTable, DBManager
from .errors import Exceptions as E
from .events import EventHandler
from .exception_handler import log_exception
from .extension_loader import load_extensions
from .get_os_path import get_os_path
from .helpers import get_specs, get_expiration_time, remove_nl, is_hex, hex_to_int, meg_to_gig, translate, ms_to_str, is_url
from .intents import gen_intents
from .interface import Paginator, ButtonChoice, RockPaperScissorsView, Valorant2FAView, VideoSearchView, MediaControls
from .json_loader import get_conf, get_lang
from .launch_checks import check_cache, check_java
from .logger import logger
from .paths import Path
from .program_handler import ProgramHandler
from .responder import respond
from .tasks import TaskHandler

conf = get_conf()
text = get_lang()
