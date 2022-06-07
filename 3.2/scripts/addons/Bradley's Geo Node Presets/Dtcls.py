from dataclasses import dataclass
from pathlib import Path
from typing import List


@dataclass
class Social:
    Name: str
    Url: str
    Icon: str


@dataclass
class __DYN__:
    P_Version: str
    B_Version: str
    File_Location: Path
    New: bool
    Debug: bool
    sha: str


@dataclass
class BRD_Datas:
    Socials: List[Social]
    Custom_Category: dict
    Repository: str
    Folder: Path
    __DYN__: __DYN__
