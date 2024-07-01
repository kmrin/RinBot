"""
RinBot v6 'Aurora' codebase
"""

from .command_checks import is_owner, is_admin, is_guild, not_blacklisted
from .client import RinBot
from .db import DBTable, DBManager
from .interface import Paginator, SetWelcomeConfirmation, StoreCreateRoleModal, HeadsOrTails, RockPaperScissorsView, MediaControls, VideoSearchView, QueueEditViewMode, QueueEditView, FavouritesEditView, FavouritesPlayView, Valorant2FAView, get_timeout_embed
from .errors import RinBotInteractionError, UserNotOwner, UserNotAdmin, UserNotInGuild, UserBlacklisted, InteractionTimedOut
from .helpers import get_localized_string, get_interaction_locale, remove_nl_from_string_iterable, ms_to_str, is_url, get_expiration_time
from .helpers import translate, get_specs, is_hex_colour, hex_to_colour, hex_to_int
from .json_manager import read, write, get_locale, get_conf
from .loggers import Loggers, log_exception
from .paths import Path, get_os_path
from .responder import respond
from .types import ResponseType, SystemSpecs, StoreItem, TransferResult, StorePurchaseStatus, TTSClient, VideoSearchViewMode, Track, Playlist
