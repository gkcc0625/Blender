# ##### BEGIN GPL LICENSE BLOCK #####
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

import unittest

try:
    # Testing within Poliigon core venv.
    from poliigon_core import assets
except ModuleNotFoundError:
    # Testing within addon environment.
    import os
    import sys
    SCRIPT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    sys.path.append(os.path.dirname(SCRIPT_DIR))

    from poliigon_core import assets


class AssetsUnitTest(unittest.TestCase):
    """Create assets tests."""

    def test_create_unsupported(self):
        unsupported = assets.AssetData(
            name="RandomAssetName001",
            asset_id=0,
            asset_type=assets.AssetData.AssetType.UNSUPPORTED
        )

    def test_create_brush(self):
        brush = assets.AssetData(
            name="BrushRockCliff001",
            asset_id=0,
            asset_type=assets.AssetData.AssetType.BRUSH,
            brush=assets.Brush(
                alpha=assets.Texture(
                    maps=[
                        assets.TextureMap(
                            filename="BrushRockCliff001_ALPHA_1K.png",
                            map_type=assets.TextureMap.MapType.ALPHA,
                            size="1K"
                        )
                    ],
                    sizes=["1K"]
                )
            )
        )

    def test_create_hdri(self):
        hdri = assets.AssetData(
            name="HdrOutdoorBeachBlueHourClear001",
            asset_id=0,
            asset_type=assets.AssetData.AssetType.HDRI,
            hdri=assets.Hdri(
                bg=assets.Texture(
                    maps=[
                        assets.TextureMap(
                            filename="HdrOutdoorBeachBlueHourClear001_JPG_1K.jpg",
                            map_type=assets.TextureMap.MapType.ENV,
                            size="1K"
                        )
                    ],
                    sizes=["1K"]
                ),
                light=assets.Texture(
                    maps=[
                        assets.TextureMap(
                            filename="HdrOutdoorBeachBlueHourClear001_HDR_1K.exr",
                            map_type=assets.TextureMap.MapType.LIGHT,
                            size="1K"
                        )
                    ],
                    sizes=["1K"]
                )
            )
        )

    def test_create_model(self):
        model = assets.AssetData(
            name="Blender001",
            asset_id=0,
            asset_type=assets.AssetData.AssetType.MODEL,
            model=assets.Model(
                textures=[
                    assets.Texture(
                        maps=[
                            assets.TextureMap(
                                filename="Blender001_AO_1K_METALNESS.jpg",
                                map_type=assets.TextureMap.MapType.AO,
                                size="1K"
                            ),
                            assets.TextureMap(
                                filename="Blender001_COL_1K_METALNESS.jpg",
                                map_type=assets.TextureMap.MapType.COL,
                                size="1K"
                            ),
                            assets.TextureMap(
                                filename="Blender001_IDMAP_1K_METALNESS.png",
                                map_type=assets.TextureMap.MapType.IDMAP,
                                size="1K"
                            ),
                            assets.TextureMap(
                                filename="Blender001_METALNESS_1K_METALNESS.png",
                                map_type=assets.TextureMap.MapType.METALNESS,
                                size="1K"
                            ),
                            assets.TextureMap(
                                filename="Blender001_NRM_1K_METALNESS.tif",
                                map_type=assets.TextureMap.MapType.NRM,
                                size="1K"
                            ),
                            assets.TextureMap(
                                filename="Blender001_ROUGHNESS_1K_METALNESS.jpg",
                                map_type=assets.TextureMap.MapType.ROUGHNESS,
                                size="1K"
                            ),
                            assets.TextureMap(
                                filename="Blender001_TRANSMISSION_1K_METALNESS.png",
                                map_type=assets.TextureMap.MapType.TRANSMISSION,
                                size="1K"
                            )
                        ],
                        sizes=["1K"]
                    )
                ]
            )
        )

    def test_create_texture(self):
        texture = assets.AssetData(
            name="ConcreteBlocksPavingZigzagOffset005",
            asset_id=0,
            asset_type=assets.AssetData.AssetType.TEXTURE,
            texture=assets.Texture(
                maps=[
                    assets.TextureMap(
                        filename="ConcreteBlocksPavingZigzagOffset005_AO_8K.png",
                        map_type=assets.TextureMap.MapType.AO,
                        size="8K"
                    ),
                    assets.TextureMap(
                        filename="ConcreteBlocksPavingZigzagOffset005_BUMP_8K.png",
                        map_type=assets.TextureMap.MapType.BUMP,
                        size="8K"
                    ),
                    assets.TextureMap(
                        filename="ConcreteBlocksPavingZigzagOffset005_BUMP16_8K.png",
                        map_type=assets.TextureMap.MapType.BUMP16,
                        size="8K"
                    ),
                    assets.TextureMap(
                        filename="ConcreteBlocksPavingZigzagOffset005_COL_8K.png",
                        map_type=assets.TextureMap.MapType.COL,
                        size="8K"
                    ),
                    assets.TextureMap(
                        filename="ConcreteBlocksPavingZigzagOffset005_DISP_8K.png",
                        map_type=assets.TextureMap.MapType.DISP,
                        size="8K"
                    ),
                    assets.TextureMap(
                        filename="ConcreteBlocksPavingZigzagOffset005_DISP16_8K.png",
                        map_type=assets.TextureMap.MapType.DISP16,
                        size="8K"
                    ),
                    assets.TextureMap(
                        filename="ConcreteBlocksPavingZigzagOffset005_GLOSS_8K.png",
                        map_type=assets.TextureMap.MapType.GLOSS,
                        size="8K"
                    ),
                    assets.TextureMap(
                        filename="ConcreteBlocksPavingZigzagOffset005_IDMAP_8K.png",
                        map_type=assets.TextureMap.MapType.IDMAP,
                        size="8K"
                    ),
                    assets.TextureMap(
                        filename="ConcreteBlocksPavingZigzagOffset005_NRM_8K.png",
                        map_type=assets.TextureMap.MapType.NRM,
                        size="8K"
                    ),
                    assets.TextureMap(
                        filename="ConcreteBlocksPavingZigzagOffset005_REFL_8K.png",
                        map_type=assets.TextureMap.MapType.REFL,
                        size="8K"
                    )
                ],
                sizes=["8K"]
            )
        )


if __name__ == '__main__':
    unittest.main()
