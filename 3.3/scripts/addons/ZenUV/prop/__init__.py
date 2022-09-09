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

""" Zen UV Addon Preferences Init """

import bpy
from bpy.props import PointerProperty
from bpy.utils import register_class, unregister_class
from ZenUV.prop.zuv_preferences import ZUV_AddonPreferences
# from ZenUV.ui.labels import ZuvLabels
from ZenUV.prop.properties import ZUV_Properties
from ZenUV.sticky_uv_editor.uv_editor_settings import UVEditorSettings


def register():
    register_class(UVEditorSettings)
    register_class(ZUV_AddonPreferences)
    register_class(ZUV_Properties)

    bpy.types.Scene.zen_uv = PointerProperty(type=ZUV_Properties)
    bpy.types.Scene.uv_editor_settings = PointerProperty(type=UVEditorSettings)


def unregister():
    unregister_class(UVEditorSettings)
    unregister_class(ZUV_AddonPreferences)
    unregister_class(ZUV_Properties)

    del bpy.types.Scene.zen_uv
    del bpy.types.Scene.uv_editor_settings

if __name__ == "__main__":
    pass
