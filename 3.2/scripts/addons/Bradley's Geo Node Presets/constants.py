from pathlib import Path, PurePath

import bpy
from .Dtcls import BRD_Datas, __DYN__, Social
import json

Folder = Path(Path(__file__).parents[0], "Data")

with open(PurePath(Folder, "settings.json"), "r") as f:
    stuff = json.loads(f.read())

version = "3.1" if not 3.1 > float(str(bpy.app.version_string)[0:3]) else "3.0"
repo = stuff["Github"]["Repository"]

Path(PurePath(Folder, version)).mkdir(parents=True, exist_ok=True)

BRD_CONST_DATA = BRD_Datas(
    [Social(**i) for i in stuff["Socials"]],
    stuff["Custom_Category"],
    f"https://api.github.com/repos/{repo}/contents/{version}",
    Folder,
    __DYN__(
        stuff["__DYN__"]["P_Version"],
        version,
        Path(stuff["__DYN__"]["File_Location"]),
        stuff["__DYN__"]["New"],
        stuff["__DYN__"]["Debug"],
        stuff["__DYN__"]["sha"],
    ),
)
