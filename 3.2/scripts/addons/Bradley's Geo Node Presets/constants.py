from pathlib import Path, PurePath
import re

import bpy
import requests
from .Dtcls import BRD_Datas, __DYN__, Social
from .utils import connected_to_internet
import json

Folder = Path(Path(__file__).parents[0], "Data")

with open(PurePath(Folder, "settings.json"), "r") as f:
    stuff = json.loads(f.read())


repo = stuff["Github"]["Repository"]

version = float()

if connected_to_internet():

    r = requests.get(f"https://api.github.com/repos/{repo}/contents/").json()

    vers = [float(i["name"]) for i in r if re.match(r"^-?\d+(?:\.\d+)$", i["name"])]

    version = (
        str(bpy.app.version_string)[0:3]
        if float(str(bpy.app.version_string)[0:3]) in vers
        else str(
            min(
                vers,
                key=lambda x: abs(x - float(float(str(bpy.app.version_string)[0:3]))),
            )
        )
    )

else:
    version = "3.1"


Path(PurePath(Folder, version)).mkdir(parents=True, exist_ok=True)

BRD_CONST_DATA = BRD_Datas(
    __package__,
    [Social(**i) for i in stuff["Socials"]],
    stuff["Custom_Category"],
    f"https://api.github.com/repos/{repo}/contents/{version}",
    Folder,
    __DYN__(
        stuff["__DYN__"]["P_Version"],
        version,
        # Path(stuff["__DYN__"]["File_Location"]),
        stuff["__DYN__"]["New"],
        stuff["__DYN__"]["Debug"],
        stuff["__DYN__"]["sha"],
    ),
)
