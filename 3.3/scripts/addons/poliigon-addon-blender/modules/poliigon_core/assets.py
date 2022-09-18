# #### BEGIN GPL LICENSE BLOCK #####
#
#  This program is free software; you can redistribute it and/or
#  modify it under the terms of the GNU General Public License
#  as published by the Free Software Foundation; either version 2
#  of the License, or (at your option) any later version.
#
#  This program is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#  GNU General Public License for more details.
#
#  You should have received a copy of the GNU General Public License
#  along with this program; if not, write to the Free Software Foundation,
#  Inc., 51 Franklin Street, Fifth Floor, Boston, MA 02110-1301, USA.
#
# ##### END GPL LICENSE BLOCK #####

from dataclasses import dataclass
from enum import Enum
from typing import Optional, Sequence


@dataclass
class TextureMap:
    """Container object for a texture map."""
    class MapType(Enum):
        ALPHA = 1  # Usually associated with a brush
        ALPHAMASKED = 2
        AO = 3
        BUMP = 4
        BUMP16 = 5
        COL = 6
        DIFF = 7
        DISP = 8
        DISP16 = 9
        EMISSIVE = 10
        ENV = 11  # Environment for an HDRI, typically a .jpg file
        FUZZ = 12
        GLOSS = 13
        IDMAP = 14
        LIGHT = 15  # Lighting for an HDRI, typically a .exr file
        MASK = 16
        METALNESS = 17
        NRM = 18
        NRM16 = 19
        OVERLAY = 20
        REFL = 21
        ROUGHNESS = 22
        SSS = 23
        TRANSLUCENCY = 24
        TRANSMISSION = 25

    filename: str
    map_type: MapType
    size: str  # Short string, e.g., "1K"
    variants: Optional[Sequence[str]] = None  # List of filenames


@dataclass
class Texture:
    """Container object for a texture."""
    maps: Sequence[TextureMap]
    sizes: Sequence[str]  # List of sizes, e.g., ["1K", "2K"]


@dataclass
class Model:
    """Container object for a model."""
    lods: Optional[Sequence[str]] = None  # List of lods, e.g., ["SOURCE", "LOD0"]
    textures: Optional[Sequence[Texture]] = None


@dataclass
class Hdri:
    """Container object for a hdri."""
    bg: Texture  # Background texture with single map of type JPG
    light: Texture  # Light texture with single map of type HDR


@dataclass
class Brush:
    """Container object for a brush."""
    alpha: Texture  # Texture with single map of type ALPHA


@dataclass
class AssetData:
    """Container object for an asset."""
    class AssetType(Enum):
        UNSUPPORTED = 1
        BRUSH = 2
        HDRI = 3
        MODEL = 4
        TEXTURE = 5

    name: str
    asset_id: int
    asset_type: AssetType
    categories: Optional[Sequence[str]] = None
    url: Optional[str] = None
    slug: Optional[str] = None
    credits: Optional[int] = None
    preview: Optional[str] = None
    thumbnails: Optional[Sequence[str]] = None
    is_local: Optional[bool] = None  # None until proven true or false.
    is_purchased: Optional[bool] = None  # None until proven true or false.

    # Treat below as a "oneof" where only set if the given asset type is assigned.
    # BRUSH
    brush: Optional[Brush] = None
    # HDRI
    hdri: Optional[Hdri] = None
    # MODEL
    model: Optional[Model] = None
    # TEXTURE
    texture: Optional[Texture] = None
