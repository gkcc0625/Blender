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

import numpy as np

import bpy
from mathutils import Vector, Matrix, Quaternion, Euler
from bpy.types import GizmoGroup

from .debug import log
from . import manager

from ..resources.translate import translate


class SC5GizmoManager():
    _target = None
    _point = None
    
    @classmethod
    def init(cls, ):
        cls._target = None
        cls._point = None
    
    @classmethod
    def deinit(cls, ):
        cls._target = None
        cls._point = None
    
    @classmethod
    def get(cls,):
        return cls._target, cls._point
    
    @classmethod
    def set(cls, t, p, ):
        cls._target = t
        cls._point = p


class SCATTER5_GGT_move(GizmoGroup, ):
    bl_idname = "SCATTER5_GGT_move"
    bl_label = "Move"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'WINDOW'
    bl_options = {'3D', 'PERSISTENT', }
    
    @classmethod
    def poll(cls, context, ):
        t, p = SC5GizmoManager.get()
        if(t is not None and p is not None):
            return True
        
        return False
    
    @staticmethod
    def get_vertex():
        t, p = SC5GizmoManager.get()
        o = bpy.data.objects.get(t)
        return o.data.vertices[p]
    
    def setup(self, context, ):
        arrow_x = self.gizmos.new("GIZMO_GT_arrow_3d")
        
        def move_get_x():
            v = SCATTER5_GGT_move.get_vertex()
            return v.co.x
        
        def move_set_x(value, ):
            v = SCATTER5_GGT_move.get_vertex()
            v.co.x = value
        
        arrow_x.target_set_handler("offset", get=move_get_x, set=move_set_x, )
        
        v = SCATTER5_GGT_move.get_vertex()
        mb = Matrix()
        mb.translation = v.co
        arrow_x.matrix_basis = mb
        
        self.x_gizmo = arrow_x
    
    def refresh(self, context, ):
        v = SCATTER5_GGT_move.get_vertex()
        mb = Matrix()
        mb.translation = v.co
        self.x_gizmo.matrix_basis = mb


classes = (
    SCATTER5_GGT_move,
)
