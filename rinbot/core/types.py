import nextcord

from nextcord import TextChannel
from enum import Enum
from pydantic import BaseModel, Field
from dataclasses import dataclass
from typing import Optional

class VideoSearchViewMode(Enum):
    TRACK_MODE = 0
    PLAYLIST_MODE = 1

@dataclass
class Track:
    title: str
    url: Optional[str] = None
    duration: Optional[str] = None
    uploader: Optional[str] = None

@dataclass
class Playlist:
    title: str
    url: str
    count: int
    uploader: Optional[str] = None

@dataclass
class TTSClient:
    channel: TextChannel
    client: nextcord.VoiceClient
    language: str
    blame: int

class ResponseType(Enum):
    SEND_MESSAGE = 0
    FOLLOWUP     = 1
    CHANNEL      = 2

class StoreItem(BaseModel):
    id: int = Field(..., description='The store item ID')
    name: str = Field(..., description='The store item name')
    price: int = Field(..., description='The store item price')
    type: int = Field(..., description='The store item type')
    
    # These descriptions lmao

class StorePurchaseStatus(Enum):
    SUCCESS = 0
    ALREADY_HAS_ITEM = 1
    ROLE_DOESNT_EXIST = 2

class SystemSpecs(BaseModel):
    os: str = Field(..., description='Operating system and version')
    cpu: str = Field(..., description='CPU brand and max frequency')
    ram: str = Field(..., description='Total RAM in GB')
    gpu: Optional[str] = Field(None, description='GPU name and memory (if available)')

class TransferResult(BaseModel):
    result: bool = Field(..., description='Transaction success or failure')
    wallet: int = Field(..., description='The amount of oranges left in the user wallet')
