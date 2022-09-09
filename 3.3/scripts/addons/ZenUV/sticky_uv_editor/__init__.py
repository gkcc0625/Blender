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

# <pep8 compliant>

# Sticky UV Editor
# Developed by Oleg Stepanov (DotBow)
# https://github.com/DotBow/Blender-Sticky-UV-Editor-Add-on

from ZenUV.sticky_uv_editor.controls import StickyUVEditor, StickyUVEditor_UI_Button, StickyUVEditorSplit
from bpy.utils import register_class, unregister_class

classes = (
    StickyUVEditor,
    StickyUVEditor_UI_Button,
    StickyUVEditorSplit
)


def register():
    for cls in classes:
        register_class(cls)


def unregister():
    for cls in classes:
        unregister_class(cls)


if __name__ == "__main__":
    pass
