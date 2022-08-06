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

# (c) 2021 Jakub Uhlik

from . import debug
from . import config
from . import manager
from . import ops
from . import brushes
# from . import gizmos

import bpy

# classes = config.classes + ops.classes + brushes.classes + gizmos.classes
classes = config.classes + ops.classes + brushes.classes


def register():
    for cls in classes:
        bpy.utils.register_class(cls)
    
    manager.init()


def unregister():
    manager.deinit()
    
    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)


# NOTE $ pycodestyle --ignore=W293,E501,E741,E402 .
