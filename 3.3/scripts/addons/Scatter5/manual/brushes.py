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

import uuid
import math
import random
import traceback
import numpy as np

import bpy
import bmesh
from bpy.types import Operator
from bpy_extras import view3d_utils
import mathutils
from mathutils import Vector, Matrix, Quaternion, Euler
from mathutils.bvhtree import BVHTree

from . import debug
from .debug import log, profile, verbose, stopwatch, profile
from . import config
from .manager import SC5Cursor, SC5ViewportTheme, SC5Toolbox, SC5Stats, SC5Overlay, SC5UISwapper, SC5SessionCache, SC5ToolTip, SC5GestureCursor, SC5Cursor2D, SC5GestureCursor2D

from .. resources.translate import translate
from ..ui import ui_manual


# ---------------------------- main ----------------------------
# TODO: convert operator, try to recalculate attributes that can't be determined
# TODO: fix 3d direction in base brush (and back port 2d from 2d base) (and convert direction driven brushes to it so i don't have two systems, old one works fine, but it is scattered all over)
# TODO: gizmo brush.. "select tool (something like current gizmo brush) > select point > cancel select tool and let autorun gizmo with linked another oprator that executes changes > repeat (meanwhile do not exit brush ui mode)" - this might work, more testing is required.
# TODO: brush vertex group masking, if it can be reasonably fast.. vertex groups are listed in spreadsheet with values for all vertices. does that mean that api changed? or only internally and python can still only access that with weight(index) function (slow and with error when vertex is not in group etc.)? on the other hand because i don't allow anything to happen to surface while brushing, it could be processed at brush mode start..
# TODO: and relax brush, at least 2.5D (along global Z axis) (or projected by surface averaged normal and brush location and influence)

# ---------------------------- less important ----------------------------
# TODO: there is slight inconsistency in _generate() and _select_points() return values between brushes. while it is working, would be nice to have retun values same in all brushes
# FIXME: if falloff = 1.0, weights are all set to 1.0 because they are calculated bigget than 1.0, then they are inverted 1.0 - ws, so they are all zero, then normalizing ws = ws / np.sum(ws) result in zero division and array full of nan. so when falloff is default 0.0 should never happen.. never say never, so fix this in the fullness of time..


class SCATTER5_OT_manual_base_brush(Operator, ):
    bl_idname = "scatter5.manual_base_brush"
    bl_label = translate("Base Brush")
    bl_description = translate("Base Brush")
    
    attribute_map = {
        # public for nodes
        'normal': ['FLOAT_VECTOR', 'POINT', ],
        'rotation': ['FLOAT_VECTOR', 'POINT', ],
        'scale': ['FLOAT_VECTOR', 'POINT', ],
        'index': ['INT', 'POINT', ],
        # 'id': ['FLOAT', 'POINT', ],
        'id': ['INT', 'POINT', ],
        'align_z': ['FLOAT_VECTOR', 'POINT', ],
        'align_y': ['FLOAT_VECTOR', 'POINT', ],
        
        # # brush location and surface normal at the time of point is generated
        # 'private_loc': ['FLOAT_VECTOR', 'POINT', ],
        # 'private_nor': ['FLOAT_VECTOR', 'POINT', ],
        
        # rotation intermediates v2 / starting points
        # TODO: call this 'private_r_align_z'? or something like that..
        # 'SURFACE_NORMAL' = 0, 'LOCAL_Z_AXIS' = 1, 'GLOBAL_Z_AXIS' = 2, custom vector = 3
        'private_r_align': ['INT', 'POINT', ],
        'private_r_align_vector': ['FLOAT_VECTOR', 'POINT', ],
        # TODO: call this 'private_r_align_y'? or something like that..
        # 'GLOBAL_Y_AXIS' = 0, 'LOCAL_Y_AXIS' = 1, custom vector = 2
        'private_r_up': ['INT', 'POINT', ],
        'private_r_up_vector': ['FLOAT_VECTOR', 'POINT', ],
        # rotation_base value
        'private_r_base': ['FLOAT_VECTOR', 'POINT', ],
        # rotation_random value
        'private_r_random': ['FLOAT_VECTOR', 'POINT', ],
        # 3 random number used for random euler calculation
        'private_r_random_random': ['FLOAT_VECTOR', 'POINT', ],
        
        # scale intermediates v2 / starting points
        'private_s_base': ['FLOAT_VECTOR', 'POINT', ],
        'private_s_random': ['FLOAT_VECTOR', 'POINT', ],
        'private_s_random_random': ['FLOAT_VECTOR', 'POINT', ],
        # 'UNIFORM' = 0, 'VECTORIAL' = 1
        'private_s_random_type': ['INT', 'POINT', ],
        'private_s_change': ['FLOAT_VECTOR', 'POINT', ],
        # 0: direction (1 or -1) - currently unused because there is no point using it, 1: scale increment factor 0.0-1.0, 2: unused
        # NOTE: only single value is used now, but might become handy later.. also it is set at creation time, only set rotation brush regenerates it
        'private_s_change_random': ['FLOAT_VECTOR', 'POINT', ],
        
        'private_z_original': ['FLOAT_VECTOR', 'POINT', ],
        # 0: start, 1: current, 2: lerp factor
        'private_z_random': ['FLOAT_VECTOR', 'POINT', ],
    }
    attribute_prefix = 'manual_'
    
    modal_adjust = False
    modal_adjust_map = [
        # {
        #     'enabled': True,
        #     'key': 'F',
        #     'oskey': False,
        #     'shift': False,
        #     'property': 'radius',
        #     'type': 'float',
        #     'change': 1 / 100,
        #     'text': 'Radius: {:.3f}',
        # },
        # {
        #     'enabled': True,
        #     'key': 'F',
        #     'oskey': True,
        #     'shift': True,
        #     'property': 'num_dots',
        #     'type': 'int',
        #     'change': 1,
        #     'text': 'Points Per Interval: {}',
        # },
        # {
        #     'enabled': False,
        #     'key': 'S',
        #     'oskey': False,
        #     'shift': False,
        #     'property': 'scale',
        #     'type': 'vector',
        #     'change': (0.1, 0.1, 0.1, ),
        #     'text': 'Scale: {}',
        # },
    ]
    modal_adjust_current = None
    modal_adjust_property_init = None
    modal_adjust_property_modified = None
    modal_adjust_mouse_init = None
    modal_adjust_abort = False
    modal_adjust_cursor = None
    modal_adjust_cursor_2d = None
    
    help_message_extra = ""
    
    @classmethod
    def poll(cls, context, ):
        if(context.space_data.type == 'VIEW_3D'):
            emitter = bpy.context.scene.scatter5.emitter
            if(emitter is None):
                return False
            target = None

            psy_active = emitter.scatter5.get_psy_active()
            if(psy_active is None):
                return False

            target = psy_active.scatter_obj
            if(target is None):
                return False
            
            if(emitter is not None and target is not None):
                if(emitter.mode == 'OBJECT' and target.mode == 'OBJECT'):
                    if(psy_active.s_distribution_method != 'manual_all'):
                        return False
                    return True
        return False
    
    def _tag_redraw(self, ):
        for window in bpy.context.window_manager.windows:
            for area in window.screen.areas:
                if(area.type == 'VIEW_3D'):
                    area.tag_redraw()
    
    def _cursor_update(self, enable=True, loc=None, nor=None, radius=None, color=None, z_scale=1.0, ):
        # NOTE: so i can override that in subclasses..
        SC5Cursor.update(self.surface.name, enable=enable, loc=loc, nor=nor, radius=radius, color=color, z_scale=z_scale, )
        # SC5Cursor2D.update(self.surface.name, enable=enable, coords=self._path_2d_region[1], radius=100, color=color, )
    
    def _project(self, context, event, ):
        if(context is None):
            region = self.region
            rv3d = self.rv3d
        else:
            region = context.region
            rv3d = context.region_data
        if(event is None):
            coord = (self.mouse_region_x, self.mouse_region_y, )
        else:
            coord = (event.mouse_region_x, event.mouse_region_y, )
        
        direction = view3d_utils.region_2d_to_vector_3d(region, rv3d, coord)
        origin = view3d_utils.region_2d_to_origin_3d(region, rv3d, coord)
        loc, nor, idx, dst = self.bvh.ray_cast(origin, direction, )
        
        nor = self._interpolate_smooth_face_normal(loc, nor, idx, )
        
        return loc, nor, idx, dst
    
    def _barycentric_weights(self, p, a, b, c, ):
        v0 = b - a
        v1 = c - a
        v2 = p - a
        d00 = v0.dot(v0)
        d01 = v0.dot(v1)
        d11 = v1.dot(v1)
        d20 = v2.dot(v0)
        d21 = v2.dot(v1)
        denom = d00 * d11 - d01 * d01
        v = (d11 * d20 - d01 * d21) / denom
        w = (d00 * d21 - d01 * d20) / denom
        u = 1.0 - v - w
        return u, v, w
    
    def _interpolate_smooth_face_normal(self, loc, nor, idx, ):
        if(loc is None):
            return nor
        if(self.bm is None):
            return nor
        if(not self.bm.is_valid):
            return nor
        
        f = self.bm.faces[idx]
        if(not f.smooth):
            return nor
        
        # smooth surface, iterpolate normal..
        vs = f.verts
        ws = self._barycentric_weights(loc, *[v.co.copy() for v in vs])
        ns = [v.normal.copy() for v in vs]
        n = Vector()
        for i, ni in enumerate(ns):
            # we want... a shrubbery! ni! ni! ni!
            n += ni * ws[i]
        n.normalize()
        return n
    
    def _rotation_to(self, a, b):
        # http://stackoverflow.com/questions/1171849/finding-quaternion-representing-the-rotation-from-one-vector-to-another
        # https://github.com/toji/gl-matrix/blob/f0583ef53e94bc7e78b78c8a24f09ed5e2f7a20c/src/gl-matrix/quat.js#L54
        
        a = a.normalized()
        b = b.normalized()
        q = Quaternion()
        
        tmpvec3 = Vector()
        xUnitVec3 = Vector((1, 0, 0))
        yUnitVec3 = Vector((0, 1, 0))
        
        dot = a.dot(b)
        if(dot < -0.999999):
            tmpvec3 = xUnitVec3.cross(a)
            if(tmpvec3.length < 0.000001):
                tmpvec3 = yUnitVec3.cross(a)
            tmpvec3.normalize()
            q = Quaternion(tmpvec3, math.pi)
        elif(dot > 0.999999):
            q.x = 0
            q.y = 0
            q.z = 0
            q.w = 1
        else:
            tmpvec3 = a.cross(b)
            q.x = tmpvec3[0]
            q.y = tmpvec3[1]
            q.z = tmpvec3[2]
            q.w = 1 + dot
            q.normalize()
        return q
    
    def _direction_to_rotation_with_m3x3(self, direction, up=Vector((0.0, 1.0, 0.0, )), ):
        x = up.cross(direction)
        x.normalize()
        y = direction.cross(x)
        y.normalize()
        
        m = Matrix()
        m[0][0] = x.x
        m[0][1] = y.x
        m[0][2] = direction.x
        m[1][0] = x.y
        m[1][1] = y.y
        m[1][2] = direction.y
        m[2][0] = x.z
        m[2][1] = y.z
        m[2][2] = direction.z
        
        return m.to_quaternion()
    
    def _point_at(self, loc, target, roll=0.0, ):
        # https://blender.stackexchange.com/questions/5210/pointing-the-camera-in-a-particular-direction-programmatically
        # direction = target - loc
        direction = target
        # direction.negate()
        # q = direction.to_track_quat('-Z', 'Y')
        q = direction.to_track_quat('Z', 'Y')
        q = q.to_matrix().to_4x4()
        if(roll != 0.0):
            rm = Matrix.Rotation(roll, 4, 'Z')
            m = q @ rm
            _, q, _ = m.decompose()
        return q
    
    def _apply_matrix(self, m, loc, nor=None, ):
        if(type(loc) is Vector):
            loc = m @ loc
            if(nor is not None):
                l, r, s = m.decompose()
                mr = r.to_matrix().to_4x4()
                nor = mr @ nor
        else:
            def apply_matrix(m, vs, ns=None, ):
                vs.shape = (-1, 3)
                vs = np.c_[vs, np.ones(vs.shape[0])]
                vs = np.dot(m, vs.T)[0:3].T.reshape((-1))
                vs.shape = (-1, 3)
                if(ns is not None):
                    _, rot, _ = m.decompose()
                    rmat = rot.to_matrix().to_4x4()
                    ns.shape = (-1, 3)
                    ns = np.c_[ns, np.ones(ns.shape[0])]
                    ns = np.dot(rmat, ns.T)[0:3].T.reshape((-1))
                    ns.shape = (-1, 3)
                vs = vs.astype(np.float32)
                if(ns is not None):
                    ns = ns.astype(np.float32)
                return vs, ns
            
            loc, nor = apply_matrix(m, loc, nor, )
        
        return loc, nor
    
    def _distance_range(self, vertices, point, radius, ):
        # mask out points in cube around point of side 2x radius
        mask = np.array((point[0] - radius <= vertices[:, 0]) & (vertices[:, 0] <= point[0] + radius) & (point[1] - radius <= vertices[:, 1]) & (vertices[:, 1] <= point[1] + radius) & (point[2] - radius <= vertices[:, 2]) & (vertices[:, 2] <= point[2] + radius), dtype=np.bool, )
        indices = np.arange(len(vertices))
        indices = indices[mask]
        vs = vertices[mask]
        # distance from point for all vertices
        d = ((vs[:, 0] - point[0]) ** 2 + (vs[:, 1] - point[1]) ** 2 + (vs[:, 2] - point[2]) ** 2) ** 0.5
        # remove all with distance > radius
        i = np.arange(len(vs))
        i = i[(d <= radius)]
        return vs[i], d[i], indices[i]
    
    def _distance_ranges(self, vertices, points, radius, ):
        # duplicate vertices points length times
        vs = np.full((len(points), ) + vertices.shape, vertices, )
        # calculate distances per point
        d = ((vs[:, :, 0] - points[:, 0].reshape(-1, 1)) ** 2 + (vs[:, :, 1] - points[:, 1].reshape(-1, 1)) ** 2 + (vs[:, :, 2] - points[:, 2].reshape(-1, 1)) ** 2) ** 0.5
        # select points
        rvs = []
        rd = []
        ri = []
        # indices
        a = np.arange(len(vertices))
        for i in range(len(points)):
            # select indices within radius
            ai = a[(d[i] <= radius)]
            # select data
            rvs.append(vs[i][ai])
            rd.append(d[i][ai])
            ri.append(ai)
        return rvs, rd, ri
    
    def _distance_vectors_2d(self, a, b, ):
        return ((a.x - b.x) ** 2 + (a.y - b.y) ** 2) ** 0.5
    
    def _distance_vectors_3d(self, a, b, ):
        return ((a.x - b.x) ** 2 + (a.y - b.y) ** 2 + (a.z - b.z) ** 2) ** 0.5
    
    def _global_to_target_space(self, loc, nor=None, ):
        # # no conversions with GLOBAL space
        # if(self.space == 'GLOBAL'):
        #     return loc, nor
        
        m = self.target.matrix_world.inverted()
        return self._apply_matrix(m, loc, nor, )
    
    def _target_to_global_space(self, loc, nor=None, ):
        # # no conversions with GLOBAL space
        # if(self.space == 'GLOBAL'):
        #     return loc, nor
        
        m = self.target.matrix_world
        return self._apply_matrix(m, loc, nor, )
    
    def _global_to_surface_space(self, loc, nor=None, ):
        # # no conversions with GLOBAL space
        # if(self.space == 'GLOBAL'):
        #     return loc, nor
        
        m = self.surface.matrix_world.inverted()
        return self._apply_matrix(m, loc, nor, )
    
    def _surface_to_global_space(self, loc, nor=None, ):
        # # no conversions with GLOBAL space
        # if(self.space == 'GLOBAL'):
        #     return loc, nor
        
        m = self.surface.matrix_world
        return self._apply_matrix(m, loc, nor, )
    
    def _global_length_to_surface_space(self, l, ):
        # # no conversions with GLOBAL space
        # if(self.space == 'GLOBAL'):
        #     return l
        
        m = self.surface.matrix_world.inverted()
        _, _, s = m.decompose()
        ms = Matrix(((s[0], 0.0, 0.0, 0.0), (0.0, s[1], 0.0, 0.0), (0.0, 0.0, s[2], 0.0), (0.0, 0.0, 0.0, 1.0)))
        v = Vector((0.0, 0.0, l))
        v = ms @ v
        return v.length
    
    def _ensure_attributes(self, ):
        me = self.target.data
        for n, t in self.attribute_map.items():
            nm = '{}{}'.format(self.attribute_prefix, n)
            a = me.attributes.get(nm)
            if(a is None):
                me.attributes.new(nm, t[0], t[1])
    
    def _store(self, loc, nor, _loc, _nor, ):
        # MAYBE FIXED, WE WILL SEE..: when all drawing is undoed, target has no vertices, at new draw, _store will throw exception, because attributes are not created yet, so add some check/create-if-missing before calling _store
        pass
    
    def _generate(self, loc, nor, idx, dst, ):
        return loc, nor
    
    def _drawing(self, context, event, ):
        loc, nor, idx, dst = self._project(context, event, )
        if(loc is not None):
            # for each draw event, those two should be the same for all generated points, so i can keep this on class.. might get easier in future to access that
            self._loc = loc.copy()
            self._nor = nor.copy()
            
            r = self._generate(loc, nor, idx, dst, )
            if(r is not None):
                loc, nor = r
                self._store(loc, nor, )
            
            self.target.data.update()
    
    def _is_viewport(self, context, event, ):
        # for a in context.screen.areas:
        #     if(a.type == 'VIEW_3D'):
        #         for r in a.regions:
        #             if(r.type == 'WINDOW'):
        #                 x = r.x
        #                 y = r.y
        #                 w = r.width
        #                 h = r.height
        #                 mx = event.mouse_x
        #                 my = event.mouse_y
        #                 if(mx > x and mx < x + w):
        #                     if(my > y and my < y + h):
        #                         return True
        # return False
        
        def in_region(r):
            x = r.x
            y = r.y
            w = r.width
            h = r.height
            if(mx > x and mx < x + w):
                if(my > y and my < y + h):
                    return True
            return False
        
        for a in context.screen.areas:
            if(a.type == 'VIEW_3D'):
                mx = event.mouse_x
                my = event.mouse_y
                
                for r in a.regions:
                    if(r.type in ('TOOL_HEADER', 'HEADER', 'TOOLS', 'UI', 'HUD', )):
                        if(in_region(r)):
                            # 3d view but not in viewport
                            return True, False
                    elif(r.type == 'WINDOW'):
                        if(in_region(r)):
                            # 3d view AND in viewport
                            return True, True
        # outside
        return False, False
    
    def _on_lmb_event(self, context, event, ):
        self.region = context.region
        self.rv3d = context.region_data
        self.mouse_region_x = event.mouse_region_x
        self.mouse_region_y = event.mouse_region_y
        
        self.pressure = 1.0
        if(event.is_tablet):
            if(self.lmb):
                self.pressure = event.pressure
                if(self.pressure <= 0.001):
                    # prevent zero pressure when mouse button is still reported as down
                    self.pressure = 0.001
    
    def _on_lmb_press(self, context, event, ):
        self._on_lmb_event(context, event, )
        # SC5Cursor.update(self.surface.name, color=SC5ViewportTheme.BRUSH_DOWN, )
        self._cursor_update(color=SC5ViewportTheme.BRUSH_DOWN, )
        if(self.is_timer):
            if(self.brush.draw_on in ('TIMER', 'BOTH', )):
                bpy.app.timers.register(self._on_timer, first_interval=self.brush.interval, )
    
    def _on_lmb_move(self, context, event, ):
        self._on_lmb_event(context, event, )
    
    def _on_lmb_release(self, context, event, ):
        self._on_lmb_event(context, event, )
        # SC5Cursor.update(self.surface.name, color=SC5ViewportTheme.BRUSH_UP, )
        self._cursor_update(color=SC5ViewportTheme.BRUSH_UP, )
    
    def _on_timer(self, ):
        # NOTE: this might need same check if SC5Toolbox contents is the same or not, like in _modal() for hot swapping brushes. but the things is, timer is active when brush is drawing, you can't switch while you drawing right? but keep the note here, maybe someone will report some strange behavior and that might be timer running when brush should be already gone..
        
        try:
            if(not self.lmb):
                return
        except ReferenceError:
            # operator has been remove meanwhile.. nothing to do here
            return
        
        self._drawing(None, None, )
        
        bpy.app.timers.register(self._on_timer, first_interval=self.brush.interval, )
        
        self._tag_redraw()
    
    def _on_start(self, context, event, ):
        # user starts drawing..
        self._tag_redraw()
    
    def _on_cancel(self, context, event, ):
        # cancel drawn points..
        self._tag_redraw()
    
    def _on_commit(self, context, event, ):
        # accept drawn points..
        self._tag_redraw()
    
    def _modal(self, context, event, ):
        # if(SC5Toolbox.get() is not self):
        #     # NOTE: kill operator if SC5Toolbox is set to some different or to None from outside..
        #     return {'CANCELLED'}
        
        # # -- SWITCHER v2 --
        if(SC5Toolbox.get() is not self):
            # # NOTE: kill operator if SC5Toolbox is set to some different or to None from outside..
            # return {'CANCELLED'}
            
            if(self._abort):
                if(event.type == 'TIMER'):
                    # print('abort..')
                    # these are the only things left to cleanup. stats are handled elsewhere, cursor is already taken by new brush..
                    context.window_manager.event_timer_remove(self._abort_timer)
                    # NOTE: brush bmesh should be freed only when whole mode stops..
                    # self.bm.free()
                    return {'CANCELLED'}
                else:
                    # not a timer event, allow to pass to new brush..
                    return {'PASS_THROUGH'}
            else:
                # old behavior, tool has been changed on toolbar
                return {'CANCELLED'}
        # # -- SWITCHER v2 --
        
        # new viewport check, now it differentiate between 3d viewport and 3d view header, tools, etc
        is_3dview, is_viewport = self._is_viewport(context, event, )
        
        # ignore anything from outside of 3d view
        if(not is_3dview):
            if(self.lmb):
                if(event.type == 'LEFTMOUSE' and event.value == 'RELEASE'):
                    # user released outside of drawing area.. fixe that
                    self.lmb = False
                    self._on_lmb_release(context, event, )
                    self._on_commit(context, event, )
                    context.window.cursor_modal_restore()
                    return {'RUNNING_MODAL'}
        
        # main ending
        if(event.type == 'ESC'):
            self._on_cancel(context, event, )
            context.window.cursor_modal_restore()
            self._cleanup()
            
            # NOTE: should be called upon any type of brush exit, escape, brush switch, error, anything, so it put here, and if does not restore interface, it is a bug.
            self._integration_on_finish(context, event, )
            
            return {'CANCELLED'}
        
        # tool switching
        active_tool_type = context.workspace.tools.from_space_view3d_mode(context.mode).idname
        if(active_tool_type not in all_brush_types()):
            raise Exception(f"How did user get access to '{active_tool_type}'? This should not happend")
        elif(self.brush_type != active_tool_type):
            # # NOTE: there are several ways to end brush, depending on what is needed. decide which one fits here..
            # self._on_cancel(context, event, )
            # context.window.cursor_modal_restore()
            # self._cleanup()
            
            # Calling new tool dynamically depending on future brush_type using ugly exec
            future_brush = get_brush_class_by_brush_type(active_tool_type)
            # NOTE: there should be something to do it without exec..
            # exec(f"bpy.ops.{future_brush.bl_idname}(('INVOKE_DEFAULT'))")
            # NOTE: there is, but it looks like a lot of work.. make some utility for it
            op_name = future_brush.bl_idname.split('.', 1)
            op = getattr(getattr(bpy.ops, op_name[0]), op_name[1])
            if(op.poll()):
                self._on_cancel(context, event, )
                context.window.cursor_modal_restore()
                self._cleanup()
                
                op('INVOKE_DEFAULT', )
                return {'CANCELLED'}
        
        # shortcut tool switch
        if(event.value == 'PRESS' and event.ascii != ""):
            try:
                shortcuts = config.switch_shortcuts()
            except Exception as e:
                log('ERROR: {}\n{}'.format(e, traceback.format_exc()))
                shortcuts = {}
            # event_char = event.ascii.upper()
            # if(event.type.startswith('NUMPAD_')):
            #     # NOTE: skip all numpad events, these are for navigation..
            #     event_char = 'skip this..'
            # if(event_char in shortcuts.values()):
            if(event.type in shortcuts.values()):
                for nb in shortcuts.keys():
                    if(shortcuts[nb] == event.type):
                        break
                if(self.brush_type != nb):
                    # self._cleanup()
                    nb = get_brush_class_by_brush_type(nb)
                    op_name = nb.bl_idname.split('.', 1)
                    op = getattr(getattr(bpy.ops, op_name[0]), op_name[1])
                    if(op.poll()):
                        self._cleanup()
                        op('INVOKE_DEFAULT', )
                        return {'CANCELLED'}
        
        # decide if event is from viewport so user can draw, or from buttons in 3d view
        if(not is_3dview):
            # throw away events outside of viewport
            context.window.cursor_modal_restore()
            # no interaction with anything outside viewport
            return {'RUNNING_MODAL'}
        elif(not is_viewport):
            # allow 3d view ui interaction.. toolbar, header..
            return {'PASS_THROUGH'}
        else:
            # i am in active viewport area, change cursor, and continue to allow drawing.
            context.window.cursor_modal_set('PAINT_CROSS')
        
        # modifier keys
        if(event.oskey or event.ctrl):
            self.ctrl = True
        else:
            self.ctrl = False
        if(event.shift):
            self.shift = True
        else:
            self.shift = False
        if(event.alt):
            self.alt = True
        else:
            self.alt = False
        
        # modal adjust keys
        modal_adjust_enabled = [k['enabled'] for k in self.modal_adjust_map]
        modal_adjust_keys = [k['key'] for k in self.modal_adjust_map]
        modal_adjust_oskey = [k['oskey'] for k in self.modal_adjust_map]
        modal_adjust_shift = [k['shift'] for k in self.modal_adjust_map]
        
        numpad_nav = ('NUMPAD_0', 'NUMPAD_1', 'NUMPAD_2', 'NUMPAD_3', 'NUMPAD_4', 'NUMPAD_5', 'NUMPAD_6', 'NUMPAD_7', 'NUMPAD_8', 'NUMPAD_9', 'NUMPAD_MINUS', 'NUMPAD_PLUS', 'NUMPAD_PERIOD', )
        
        # viewport events handling
        if(event.type in {'MIDDLEMOUSE', 'WHEELUPMOUSE', 'WHEELDOWNMOUSE'}):
            if(self.modal_adjust):
                # NOTE: kill operator processing here, so other operator functions are not called when no drawing is happening
                return {'RUNNING_MODAL'}
            
            # allow navigation..
            context.window.cursor_modal_restore()
            return {'PASS_THROUGH'}
        elif(event.type in numpad_nav):
            if(self.modal_adjust):
                # NOTE: kill operator processing here, so other operator functions are not called when no drawing is happening
                return {'RUNNING_MODAL'}
            
            # allow navigation..
            context.window.cursor_modal_restore()
            return {'PASS_THROUGH'}
        elif(event.type == 'MOUSEMOVE' and self.lmb):
            if(self.modal_adjust):
                # NOTE: kill operator processing here, so other operator functions are not called when no drawing is happening
                return {'RUNNING_MODAL'}
            
            # drawing with mouse pressed
            self._on_lmb_move(context, event, )
        elif(event.type == 'LEFTMOUSE' and not self.modal_adjust):
            if(self.modal_adjust):
                # NOTE: kill operator processing here, so other operator functions are not called when no drawing is happening
                return {'RUNNING_MODAL'}
            
            if(event.value == 'PRESS'):
                # user pressed lmb
                self._on_start(context, event, )
                self.lmb = True
                self._on_lmb_press(context, event, )
            else:
                # user released lmb
                self.lmb = False
                self._on_lmb_release(context, event, )
                self._on_commit(context, event, )
                context.window.cursor_modal_restore()
        elif(event.type in {'Z', } and (event.oskey or event.ctrl)):
            # pass through undo
            return {'PASS_THROUGH'}
        elif(event.type in ('RIGHT_BRACKET', 'LEFT_BRACKET', ) and event.value == 'PRESS'):
            if(event.type in ('RIGHT_BRACKET', )):
                self.brush.radius += self.brush.radius_increment
            if(event.type in ('LEFT_BRACKET', )):
                self.brush.radius -= self.brush.radius_increment
        elif(event.type in modal_adjust_keys and event.value == 'PRESS' and not self.modal_adjust_abort):
            if(not self.modal_adjust):
                # find matching key combination in map
                ok = False
                for i, k in enumerate(modal_adjust_keys):
                    if(k == event.type):
                        if(modal_adjust_oskey[i] == (event.oskey or event.ctrl)):
                            if(modal_adjust_shift[i] == event.shift):
                                if(modal_adjust_enabled[i]):
                                    # ok, i got index of correct event from map
                                    ok = True
                                    break
                if(ok):
                    if(self.lmb):
                        # don't allow gestures while drawing..
                        return {'RUNNING_MODAL'}
                    
                    # found it, cool, now go for it
                    self.modal_adjust = True
                    self.modal_adjust_current = self.modal_adjust_map[i]
                    if(self.modal_adjust_current['type'] == 'float'):
                        v = float(getattr(self.brush, self.modal_adjust_current['property'], ))
                        vm = v
                    elif(self.modal_adjust_current['type'] == 'int'):
                        v = int(getattr(self.brush, self.modal_adjust_current['property'], ))
                        vm = v
                    elif(self.modal_adjust_current['type'] == 'vector'):
                        v = Vector(getattr(self.brush, self.modal_adjust_current['property'], ))
                        vm = Vector(v)
                    self.modal_adjust_property_init = v
                    self.modal_adjust_property_modified = vm
                    self.modal_adjust_mouse_init = event.mouse_region_x
                    
                    SC5GestureCursor.add(self.surface.name, self.modal_adjust_current['cursor'], )
                    
                    return {'MODAL_PROPERTY_ADJUST'}
            else:
                # pass other press events (depend on keyboard repeat)
                return {'MODAL_PROPERTY_ADJUST'}
        elif(event.type == 'MOUSEMOVE' and self.modal_adjust):
            # just pass event..
            return {'MODAL_PROPERTY_ADJUST'}
        elif(event.type == 'LEFTMOUSE' and self.modal_adjust):
            # kill adjust on left mouse and set adjusted value
            setattr(self.brush, self.modal_adjust_current['property'], self.modal_adjust_property_modified, )
            self.modal_adjust = False
            self.modal_adjust_current = None
            self.modal_adjust_property_init = None
            self.modal_adjust_property_modified = None
            self.modal_adjust_mouse_init = None
            self.modal_adjust_abort = True
            if(self.__class__.__name__ in SC5ToolTip._cache.keys()):
                del SC5ToolTip._cache[self.__class__.__name__]
            SC5GestureCursor.remove(self.surface.name, )
        elif(event.type == 'RIGHTMOUSE' and self.modal_adjust):
            # kill adjust on right mouse and set initial value
            setattr(self.brush, self.modal_adjust_current['property'], self.modal_adjust_property_init, )
            self.modal_adjust = False
            self.modal_adjust_current = None
            self.modal_adjust_property_init = None
            self.modal_adjust_property_modified = None
            self.modal_adjust_mouse_init = None
            self.modal_adjust_abort = True
            if(self.__class__.__name__ in SC5ToolTip._cache.keys()):
                del SC5ToolTip._cache[self.__class__.__name__]
            SC5GestureCursor.remove(self.surface.name, )
        elif(self.modal_adjust_current is not None and self.modal_adjust_current['key'] == event.type and event.value == 'RELEASE'):
            # kill adjust on release of main key and set adjusted value
            setattr(self.brush, self.modal_adjust_current['property'], self.modal_adjust_property_modified, )
            self.modal_adjust = False
            self.modal_adjust_current = None
            self.modal_adjust_property_init = None
            self.modal_adjust_property_modified = None
            self.modal_adjust_mouse_init = None
            self.modal_adjust_abort = False
            if(self.__class__.__name__ in SC5ToolTip._cache.keys()):
                del SC5ToolTip._cache[self.__class__.__name__]
            SC5GestureCursor.remove(self.surface.name, )
        elif(event.type in modal_adjust_keys and event.value == 'RELEASE' and self.modal_adjust_abort):
            # allow running it again after
            self.modal_adjust_abort = False
        
        # if i am here, good job mate, lets continue..
        return {'RUNNING_MODAL'}
    
    def _self_brush_modal_update(self, context, ):
        # NOTE: with undo/redo, `self.brush` reference to properties is invalid, all brushes must get new reference to properties here. and it have to be called in modal() at first place!
        pass
    
    def _ensure_surface_and_target_visibility(self, ):
        if(self.surface.hide_viewport):
            self.surface.hide_viewport = False
        if(self.target.hide_viewport):
            self.target.hide_viewport = False
    
    def modal(self, context, event, ):
        # NOTE: call this first! always!
        self._self_brush_modal_update(context, )
        
        try:
            # run modal
            r = self._modal(context, event, )
        except Exception as e:
            # abort if some error there..
            self._cleanup()
            traceback.print_exc()
            self.report({'ERROR'}, traceback.format_exc(), )
            
            # NOTE: should be called upon any type of brush exit, escape, brush switch, error, anything, so it put here, and it does not restore interface, it is a bug.
            self._integration_on_finish(context, event, )
            
            return {'CANCELLED'}
        
        if(event.type == 'MOUSEMOVE'):
            mouse = Vector((event.mouse_x, event.mouse_y, ))
            if(self._mouse_2d_prev.to_tuple() != mouse.to_tuple()):
                self._mouse_2d_prev = self._mouse_2d
                self._mouse_2d = mouse
                
                prev = None
                for i in reversed(range(len(self._mouse_2d_path))):
                    d = self._distance_vectors_2d(self._mouse_2d_path[i], mouse)
                    if(d >= self._mouse_2d_direction_minimal_distance):
                        prev = self._mouse_2d_path[i]
                        break
                
                if(prev is not None):
                    self._mouse_2d_prev = prev
                    
                    n = self._mouse_2d - self._mouse_2d_prev
                    n.normalize()
                    self._mouse_2d_direction = n
                
                self._mouse_2d_path.append(mouse)
            
            self._mouse_2d_region_prev = self._mouse_2d_region
            self._mouse_2d_region = Vector((event.mouse_region_x, event.mouse_region_y, ))
            rdiff = self._mouse_2d - self._mouse_2d_region
            self._mouse_2d_region_prev = self._mouse_2d_prev - rdiff
        
        # lock cursor while in gesture
        loc, nor, idx, dst = self._project(context, event, )
        
        _loc = None
        if(loc is not None):
            # copy for 3d path and direction so i don't need to ray_cast again..
            _loc = loc.copy()
        
        if(self.modal_adjust and self.modal_adjust_cursor is None):
            self.modal_adjust_cursor = (loc, nor, )
            self.modal_adjust_cursor_2d = (event.mouse_region_x, event.mouse_region_y, )
        if(not self.modal_adjust and self.modal_adjust_cursor is not None):
            self.modal_adjust_cursor = None
            self.modal_adjust_cursor_2d = None
        if(self.modal_adjust):
            loc, nor = self.modal_adjust_cursor
        
        if(event.type == 'MOUSEMOVE'):
            if(_loc is not None):
                if(self._mouse_3d is None):
                    self._mouse_3d = _loc
                if(_loc != self._mouse_3d):
                    d = self._distance_vectors_3d(_loc, self._mouse_3d)
                    if(d > self._mouse_3d_direction_minimal_distance):
                        self._path_3d.append(_loc)
                        self._path_direction_3d.append(self._mouse_3d_direction)
                        
                        self._mouse_3d_prev = self._mouse_3d
                        self._mouse_3d = _loc
                        if(self._mouse_3d is not None and self._mouse_3d_prev is not None):
                            n = self._mouse_3d - self._mouse_3d_prev
                            n.normalize()
                            self._mouse_3d_direction = n
                        else:
                            self._mouse_3d_direction = None
                    else:
                        pass
                else:
                    pass
            else:
                self._mouse_3d_prev = self._mouse_3d
                self._mouse_3d = None
                self._mouse_3d_direction = None
        
        # if(self._mouse_3d is not None and self._mouse_3d_direction is not None):
        #     from space_view3d_point_cloud_visualizer.mechanist import PCVMechanist
        #     k = self.target.name
        #     if(k in PCVMechanist.cache.keys()):
        #         c = PCVMechanist.cache[k]
        #         vs = c['vs']
        #         ns = c['ns']
        #         cs = c['cs']
        #         vs = np.append(vs, np.array(self._mouse_3d, dtype=np.float32, ).reshape(-1, 3), axis=0, )
        #         ns = np.append(ns, np.array(self._mouse_3d_direction, dtype=np.float32, ).reshape(-1, 3), axis=0, )
        #         cs = np.append(cs, np.array((1,1,1,1), dtype=np.float32, ).reshape(-1, 4), axis=0, )
        #         c['vs'] = vs
        #         c['ns'] = ns
        #         c['cs'] = cs
        #         PCVMechanist.force_update(k)
        #     else:
        #         vs = np.array(self._mouse_3d, dtype=np.float32, ).reshape(-1, 3)
        #         ns = np.array(self._mouse_3d_direction, dtype=np.float32, ).reshape(-1, 3)
        #         cs = np.array((1,1,1,1), dtype=np.float32, ).reshape(-1, 4)
        #         debug.points(self.target, vs, ns, cs, )
        
        if(r == {'MODAL_PROPERTY_ADJUST'}):
            d = ((event.mouse_region_x - self.modal_adjust_mouse_init) / self.modal_adjust_current['change_pixels']) * self.modal_adjust_current['change']
            if(self.modal_adjust_current['type'] in ('vector', )):
                vv = Vector(self.modal_adjust_property_init)
                vv.x += d
                vv.y += d
                vv.z += d
                # set value, let it sanitize
                setattr(self.brush, self.modal_adjust_current['property'], vv, )
                # Vector have to be copied.. this returns just reference..
                vv = Vector(getattr(self.brush, self.modal_adjust_current['property']))
                # and set it back to initial
                setattr(self.brush, self.modal_adjust_current['property'], self.modal_adjust_property_init, )
                self.modal_adjust_property_modified = vv
                SC5ToolTip._cache[self.__class__.__name__] = (self.modal_adjust_current['text'].format(vv.x, vv.y, vv.z),
                                                              self.modal_adjust_cursor_2d[0] + 20,
                                                              self.modal_adjust_cursor_2d[1] - 20, )
            else:
                v = self.modal_adjust_property_init + d
                # set value, let it sanitize
                setattr(self.brush, self.modal_adjust_current['property'], v, )
                v = getattr(self.brush, self.modal_adjust_current['property'])
                # and set it back to initial
                setattr(self.brush, self.modal_adjust_current['property'], self.modal_adjust_property_init, )
                self.modal_adjust_property_modified = v
                SC5ToolTip._cache[self.__class__.__name__] = (self.modal_adjust_current['text'].format(v),
                                                              self.modal_adjust_cursor_2d[0] + 20,
                                                              self.modal_adjust_cursor_2d[1] - 20, )
            
            v = self.modal_adjust_property_modified
            if(self.modal_adjust_current['cursor'] in (SC5GestureCursor.STRENGTH, )):
                r = getattr(self.brush, 'radius', )
                v = v * r
            extra = 1.0
            if(self.modal_adjust_current['cursor'] in (SC5GestureCursor.COUNT, )):
                extra = getattr(self.brush, 'radius', )
            
            SC5GestureCursor.update(self.surface.name, enable=True, value=v, color=SC5ViewportTheme.BRUSH_UP, extra=extra, )
            
            r = {'RUNNING_MODAL'}
        
        if(r != {'RUNNING_MODAL'}):
            # NOTE: skip following when sidebar props are adjusted. it slows down buttons, it was ray casting in background when it is not needed.
            return r
        
        try:
            self.surface.name
            self.target.name
        except ReferenceError:
            # NOTE: this is only quick hack to fix. i got so far with undo, that objects set in invoke are no longer valid. so do following:
            # FIXME: get rid of direct references to objects, always use name..
            
            # NOTE: whole modal is handled, lets handle all exceptions in following as well
            # TODO: try to disable using other tools while drawing.. somehow. or at least remove them from mouse pointer access, most keys are already disabled except navigation and undo/redo, i think bet would be allow access only to viewport and sidebar, other areas events send to void..
            
            self.surface = bpy.data.objects.get(self.surface_name)
            self.target = bpy.data.objects.get(self.target_name)
        except AttributeError:
            # object has been removed, abort all
            self._on_cancel(context, event, )
            context.window.cursor_modal_restore()
            self._cleanup()
            
            # NOTE: should be called upon any type of brush exit, escape, brush switch, error, anything, so it put here, and it does not restore interface, it is a bug.
            self._integration_on_finish(context, event, )
            
            return {'CANCELLED'}
        
        # and this as well.. undoing too far can change that as well.. do it here so refewrences are correct without new try-except, ray casting is done at bvh, so i don't really need surface visible..
        self._ensure_surface_and_target_visibility()
        
        # and update cursor..
        if(loc is not None):
            radius = getattr(self.brush, 'radius', 0.0, )
            if(hasattr(self.brush, 'radius')):
                radius = self.brush.radius
            
            # Variable gizmo size for tablet user if use radius pressure
            # if(event.is_tablet) and (hasattr(self.brush, 'radius_pressure')) and (self.brush.radius_pressure) and (event.value == 'PRESS'):
            if(event.is_tablet) and (hasattr(self.brush, 'radius_pressure')) and (self.brush.radius_pressure) and self.lmb:
                p = event.pressure
                if(p == 0.0):
                    # prevent zero pressure
                    p = 0.001
                radius *= p
            # # SC5Cursor.update(self.surface.name, enable=True, loc=loc, nor=nor, radius=radius, )
            # self._cursor_update(enable=True, loc=loc, nor=nor, radius=radius, )
            
            enable = True
            if(self.modal_adjust):
                if(self.modal_adjust_current['cursor'] not in (SC5GestureCursor.RADIUS, SC5GestureCursor.STRENGTH, )):
                    enable = False
            
            self._cursor_update(enable=enable, loc=loc, nor=nor, radius=radius, )
        else:
            # SC5Cursor.update(self.surface.name, enable=False, )
            self._cursor_update(enable=False, )
        self._tag_redraw()
        
        # # debug 3d mouse props
        # # on mousemove and successful projection it should be already calculated from above..
        # if(event.type == 'MOUSEMOVE' and _loc is not None):
        #     # for direction i need second point, so skip it now..
        #     if(self._mouse_3d_direction is not None):
        #         vs = []
        #         ns = []
        #         cs = []
        #         vs.append(self._mouse_3d.to_tuple())
        #         ns.append(self._mouse_3d_direction.to_tuple())
        #         cs.append((1.0, 1.0, 0.0, 1.0, ))
        #         # vs.append(self._mouse_3d_prev.to_tuple())
        #         # ns.append((0.0, 0.0, 0.1))
        #         # cs.append((1.0, 0.0, 0.0, 1.0, ))
        #         for i, p in enumerate(self._path_3d[:-1]):
        #             vs.append(p.to_tuple())
        #             n = self._path_direction_3d[i]
        #             if(n is not None):
        #                 n.length = 0.1
        #                 ns.append(n.to_tuple())
        #             else:
        #                 ns.append((0.0, 0.0, 0.1, ))
        #             cs.append((0.5, 0.0, 0.0, 1.0, ))
        #         debug.points(self.surface, vs, ns, cs)
        
        return r
    
    def _prepare(self, context, ):
        # NOTE: this is obsolete now.., but leave it here for reference..
        
        o = self.surface
        m = o.matrix_world
        
        # # v1
        # depsgraph = context.evaluated_depsgraph_get()
        # eo = o.evaluated_get(depsgraph)
        # bm = bmesh.new()
        # bm.from_object(eo, depsgraph, cage=False, face_normals=True, )
        # bm.transform(m)
        # if(self.triangulate):
        #     bmesh.ops.triangulate(bm, faces=bm.faces, )
        #     # bm.normal_update()
        #     # bmesh.ops.recalc_face_normals(bm, faces=bm.faces, )
        #
        #     # me = bpy.data.meshes.new(name='tmp-{}'.format(uuid.uuid1()), )
        #     # bm.to_mesh(me)
        #     # me.calc_normals()
        #     # bm.free()
        #     # bm = bmesh.new()
        #     # bm.from_mesh(me, face_normals=True, use_shape_key=False, shape_key_index=0, )
        #     # bpy.data.meshes.remove(me)
        #
        # bvh = BVHTree.FromBMesh(bm, epsilon=self.epsilon, )
        
        # # v2
        # depsgraph = context.evaluated_depsgraph_get()
        # eo = o.evaluated_get(depsgraph)
        # bm = bmesh.new()
        # bm.from_object(eo, depsgraph, cage=False, face_normals=True, )
        # me = bpy.data.meshes.new(name='tmp-{}'.format(uuid.uuid1()), )
        # bm.to_mesh(me)
        # bm.free()
        # me.transform(m)
        # me.update()
        # me.calc_loop_triangles()
        #
        # # get vertices
        # vs = np.zeros((len(me.vertices) * 3), dtype=np.float, )
        # me.vertices.foreach_get('co', vs, )
        # vs.shape = (-1, 3, )
        # # get triangles
        # tris = np.zeros((len(me.loop_triangles) * 3), dtype=np.int, )
        # me.loop_triangles.foreach_get('vertices', tris, )
        # tris.shape = (-1, 3, )
        # # # get loop triangles to use later in random point generation
        # # loop_triangles = np.array(me.loop_triangles, dtype=MeshLoopTriangle, )
        #
        # bm = bmesh.new()
        # bm.from_mesh(me, face_normals=True, use_shape_key=False, shape_key_index=0, )
        # bpy.data.meshes.remove(me)
        #
        # bvh = BVHTree.FromPolygons(vs.tolist(), tris.tolist(), all_triangles=True, epsilon=self.epsilon, )
        
        # v3
        depsgraph = context.evaluated_depsgraph_get()
        eo = o.evaluated_get(depsgraph)
        bm = bmesh.new()
        bm.from_object(eo, depsgraph, cage=False, face_normals=True, )
        bm.transform(m)
        if(self.triangulate):
            bmesh.ops.triangulate(bm, faces=bm.faces, )
        bm.verts.ensure_lookup_table()
        bm.faces.ensure_lookup_table()
        
        bvh = BVHTree.FromBMesh(bm, epsilon=self.epsilon, )
        
        # TODO: surface matrix, might be better to be more descriptive
        self.m = m
        self.bm = bm
        self.bvh = bvh
        
        # # now create on target attributes i need to store points (in case they are not already there)
        # me = self.target.data
        # nm = '{}normal'.format(self.attribute_prefix)
        # normal = me.attributes.get(nm)
        # if(normal is None):
        #     me.attributes.new(nm, 'FLOAT_VECTOR', 'POINT')
        #
        # nm = '{}rotation'.format(self.attribute_prefix)
        # rotation = me.attributes.get(nm)
        # if(rotation is None):
        #     me.attributes.new(nm, 'FLOAT_VECTOR', 'POINT')
        #
        # nm = '{}scale'.format(self.attribute_prefix)
        # scale = me.attributes.get(nm)
        # if(scale is None):
        #     me.attributes.new(nm, 'FLOAT_VECTOR', 'POINT')
        
        me = self.target.data
        for n, t in self.attribute_map.items():
            nm = '{}{}'.format(self.attribute_prefix, n)
            a = me.attributes.get(nm)
            if(a is None):
                me.attributes.new(nm, t[0], t[1])
    
    def _prepare_cached(self, context, ):
        m, bm, bvh = SC5SessionCache.get(context, )
        self.m = m
        self.bm = bm
        self.bvh = bvh
        
        # initialize attributes on target
        me = self.target.data
        for n, t in self.attribute_map.items():
            nm = '{}{}'.format(self.attribute_prefix, n)
            a = me.attributes.get(nm)
            if(a is None):
                me.attributes.new(nm, t[0], t[1])
    
    def _collect(self, context, ):
        pass
    
    def _cleanup(self, ):
        # back with cursor
        SC5Cursor.remove(self.surface.name, )
        # SC5Cursor2D.remove(self.surface.name, )
        SC5Stats.remove(self.target.name, )
        bpy.context.window.cursor_modal_restore()
        # clean up data, bvhtree should be garbage collected
        # NOTE: brush bmesh should be freed only when whole mode stops..
        # self.bm.free()
        # and remove reference to operator
        SC5Toolbox.set(None, )
    
    '''
    def __init__(self, ):
        print("init: {}".format(str(self).split(' ')[-1][:-1]))
    
    def __del__(self, ):
        print("del: {}".format(str(self).split(' ')[-1][:-1]))
    '''
    
    def invoke(self, context, event, ):
        # some defaults (triangulate should be true anyway..)
        self.epsilon = 0.001
        self.triangulate = True
        
        # to detect if user moving with cursor while pressing left button
        self.lmb = False
        
        # define modifier keys attributes
        self.ctrl = False
        self.shift = False
        self.alt = False
        
        # reconfigure modal key map from config..
        try:
            self.modal_adjust_map = config.gesture_reconfigure(self.modal_adjust_map)
        except Exception as e:
            log('ERROR: {}\n{}'.format(e, traceback.format_exc()))
            self.modal_adjust_map = []
        
        self._mouse_2d = Vector((event.mouse_x, event.mouse_y, ))
        self._mouse_2d_prev = Vector((event.mouse_x, event.mouse_y, ))
        self._mouse_2d_direction = Vector()
        self._mouse_2d_region = Vector((event.mouse_region_x, event.mouse_region_y, ))
        self._mouse_2d_region_prev = Vector((event.mouse_region_x, event.mouse_region_y, ))
        self._mouse_2d_direction_minimal_distance = 10
        self._mouse_2d_path = [Vector((event.mouse_region_x, event.mouse_region_y, )), ]
        
        self._mouse_3d = None
        self._mouse_3d_prev = None
        self._mouse_3d_direction = None
        # self._mouse_3d_direction_minimal_distance = 0.01
        self._mouse_3d_direction_minimal_distance = 0.05
        self._path_3d = []
        self._path_direction_3d = []
        
        # main props..
        self.props = context.scene.scatter5.manual
        self.surface = bpy.context.scene.scatter5.emitter
        self.target = self.surface.scatter5.get_psy_active().scatter_obj
        # self.space = self.surface.scatter5.get_psy_active().s_distribution_space.upper()
        # NOTE: keep also names for fallback after undo/redo
        self.surface_name = self.surface.name
        self.target_name = self.target.name
        
        # brush props..
        if(not hasattr(self, 'brush')):
            # brushes have to set its own set of properties before calling super().invoke()
            self.brush = self.props.default_brush
        
        if(not hasattr(self, 'is_timer')):
            # if it is timer enabled brush, set this befor calling super().invoke()
            self.is_timer = False
        
        # process surface mesh to bmesh and bvhtree, at first click, user can expect some processing..
        # self._prepare(context, )
        self._prepare_cached(context, )
        
        # for brushes working with existing data, note, some brushes need to call this and each mouse press
        self._collect(context, )
        
        # init cursor drawing (if isn't already)
        SC5Cursor.init()
        # SC5Cursor2D.init()
        # set cursor from brush props..
        SC5Cursor.add(self.surface.name, self.brush.cursor, )
        # SC5Cursor2D.add(self.surface.name, self.brush.cursor, )
        # store active tool, so i can detect if some brush modal is already running
        SC5Toolbox.set(self)
        # init text drawing (if isn't already)
        SC5Stats.init()
        SC5Stats.add(self.target.name, )
        # init cursor gesture drawing (if isn't already)
        SC5GestureCursor.init()
        
        # # -- SWITCHER v2 --
        # abort brush on timer
        self._abort = False
        self._abort_timer = context.window_manager.event_timer_add(0.1, window=context.window, )
        # # -- SWITCHER v2 --
        
        # finally!
        context.window_manager.modal_handler_add(self)
        
        # i guess this is better place for it.. call it once all is set.. i.e. SC5Toolbox is no longer None, it points to `self`
        self._integration_on_invoke(context, event, )
        
        # at one redraw so cursor is ready..
        self._tag_redraw()
        return {'RUNNING_MODAL'}
    
    def _gen_rotation(self, n, vs, ns, ):
        vs, ns = self._surface_to_global_space(vs, ns, )
        bsb = self.brush
        
        l = len(vs)
        if(bsb.rotation_align == 'GLOBAL_Z_AXIS'):
            nors = [Vector((0.0, 0.0, 1.0, )) for i in range(l)]
        elif(bsb.rotation_align == 'LOCAL_Z_AXIS'):
            _, nor = self._surface_to_global_space(Vector((0.0, 0.0, 0.0, )), Vector((0.0, 0.0, 1.0, )), )
            nors = [nor.copy() for i in range(l)]
        elif(bsb.rotation_align == 'SURFACE_NORMAL'):
            nors = [Vector(e) for e in ns]
        
        def direction_to_rotation_with_m3x3(direction, up=Vector((0.0, 1.0, 0.0, )), ):
            x = up.cross(direction)
            x.normalize()
            y = direction.cross(x)
            y.normalize()
            
            m = Matrix()
            m[0][0] = x.x
            m[0][1] = y.x
            m[0][2] = direction.x
            m[1][0] = x.y
            m[1][1] = y.y
            m[1][2] = direction.y
            m[2][0] = x.z
            m[2][1] = y.z
            m[2][2] = direction.z
            
            return m.to_quaternion()
        
        # _align_z = np.zeros((l, 3), dtype=np.float, )
        # _align_y = np.zeros((l, 3), dtype=np.float, )
        
        if(bsb.rotation_up == 'LOCAL_Y_AXIS'):
            locy = Vector((0.0, 1.0, 0.0, ))
            mwi = self.surface.matrix_world.copy()
            _, cr, _ = mwi.decompose()
            locy.rotate(cr)
            
            qs = []
            for i in range(l):
                # _align_z[i] = nors[i]
                # _align_y[i] = locy
                
                q = direction_to_rotation_with_m3x3(nors[i], locy, )
                qs.append(q)
        elif(bsb.rotation_up == 'GLOBAL_Y_AXIS'):
            qs = []
            for i in range(l):
                # _align_z[i] = nors[i]
                # _align_y[i] = (0.0, 1.0, 0.0, )
                
                q = direction_to_rotation_with_m3x3(nors[i], )
                qs.append(q)
        
        rng = np.random.default_rng()
        _random_numbers = rng.random((l, 3, ), )
        
        eb = bsb.rotation_base
        er = bsb.rotation_random
        err = []
        for i in range(l):
            # err.append(Euler((er.x * random.random(), er.y * random.random(), er.z * random.random(), ), ))
            err.append(Euler((er.x * _random_numbers[i][0], er.y * _random_numbers[i][1], er.z * _random_numbers[i][2], ), ))
        
        mwi = self.surface.matrix_world.inverted()
        _, cr, _ = mwi.decompose()
        
        fq = []
        for i in range(l):
            q = Quaternion()
            q.rotate(eb)
            q.rotate(err[i])
            q.rotate(qs[i])
            q.rotate(cr)
            fq.append(q)
        
        # rotation intermediates v2 ---------------------------------------------------
        _private_r_align = np.zeros(l, dtype=np.int, )
        if(bsb.rotation_align == 'GLOBAL_Z_AXIS'):
            _private_r_align = _private_r_align + 2
        elif(bsb.rotation_align == 'LOCAL_Z_AXIS'):
            _private_r_align = _private_r_align + 1
        elif(bsb.rotation_align == 'SURFACE_NORMAL'):
            pass
        
        _private_r_up = np.zeros(l, dtype=np.int, )
        if(bsb.rotation_up == 'LOCAL_Y_AXIS'):
            _private_r_up = _private_r_up + 1
        elif(bsb.rotation_up == 'GLOBAL_Y_AXIS'):
            pass
        
        _private_r_base = np.full((l, 3), bsb.rotation_base, dtype=np.float, )
        _private_r_random = np.full((l, 3), bsb.rotation_random, dtype=np.float, )
        # _private_r_change_override = np.zeros(l, dtype=np.float, )
        # _private_r_change = np.zeros((l, 3), dtype=np.float, )
        
        self._private_r_align = _private_r_align
        self._private_r_up = _private_r_up
        self._private_r_base = _private_r_base
        self._private_r_random = _private_r_random
        self._private_r_random_random = _random_numbers
        # self._private_r_change_override = _private_r_change_override
        # self._private_r_change = _private_r_change
        
        # self._align_z = _align_z
        # self._align_y = _align_y
        
        # rotation intermediates v2 ---------------------------------------------------
        
        return fq
    
    def _regenerate_rotation_from_attributes(self, indices, ):
        # this will load all attributes for rotation (set by create brushes), calculate again and set back final rotations for indices
        # if some attribute has bee changed before running, it will change resulting rotation, and brush doing it can just change attribute and call function.. in theory..
        
        # get attributes for ALL points
        me = self.target.data
        l = len(me.vertices)
        
        _vs = np.zeros(l * 3, dtype=np.float, )
        me.vertices.foreach_get('co', _vs, )
        _vs.shape = (-1, 3, )
        
        _ns = np.zeros(l * 3, dtype=np.float, )
        me.attributes['{}normal'.format(self.attribute_prefix)].data.foreach_get('vector', _ns, )
        _ns.shape = (-1, 3)
        
        _rotation = np.zeros(l * 3, dtype=np.float, )
        me.attributes['{}rotation'.format(self.attribute_prefix)].data.foreach_get('vector', _rotation, )
        _rotation.shape = (-1, 3)
        
        _private_r_align = np.zeros(l, dtype=np.int, )
        me.attributes['{}private_r_align'.format(self.attribute_prefix)].data.foreach_get('value', _private_r_align, )
        
        _private_r_align_vector = np.zeros(l * 3, dtype=np.float, )
        me.attributes['{}private_r_align_vector'.format(self.attribute_prefix)].data.foreach_get('vector', _private_r_align_vector, )
        _private_r_align_vector.shape = (-1, 3)
        
        _private_r_up = np.zeros(l, dtype=np.int, )
        me.attributes['{}private_r_up'.format(self.attribute_prefix)].data.foreach_get('value', _private_r_up, )
        
        _private_r_up_vector = np.zeros(l * 3, dtype=np.float, )
        me.attributes['{}private_r_up_vector'.format(self.attribute_prefix)].data.foreach_get('vector', _private_r_up_vector, )
        _private_r_up_vector.shape = (-1, 3)
        
        _private_r_base = np.zeros(l * 3, dtype=np.float, )
        me.attributes['{}private_r_base'.format(self.attribute_prefix)].data.foreach_get('vector', _private_r_base, )
        _private_r_base.shape = (-1, 3)
        
        _private_r_random = np.zeros(l * 3, dtype=np.float, )
        me.attributes['{}private_r_random'.format(self.attribute_prefix)].data.foreach_get('vector', _private_r_random, )
        _private_r_random.shape = (-1, 3)
        
        _private_r_random_random = np.zeros(l * 3, dtype=np.float, )
        me.attributes['{}private_r_random_random'.format(self.attribute_prefix)].data.foreach_get('vector', _private_r_random_random, )
        _private_r_random_random.shape = (-1, 3)
        
        _align_z = np.zeros((l * 3), dtype=np.float, )
        me.attributes['{}align_z'.format(self.attribute_prefix)].data.foreach_get('vector', _align_z, )
        _align_z.shape = (-1, 3)
        
        _align_y = np.zeros((l * 3), dtype=np.float, )
        me.attributes['{}align_y'.format(self.attribute_prefix)].data.foreach_get('vector', _align_y, )
        _align_y.shape = (-1, 3)
        
        # _private_r_change_override = np.zeros(l, dtype=np.int, )
        # me.attributes['{}private_r_change_override'.format(self.attribute_prefix)].data.foreach_get('value', _private_r_change_override, )
        #
        # _private_r_change = np.zeros(l * 3, dtype=np.float, )
        # me.attributes['{}private_r_change'.format(self.attribute_prefix)].data.foreach_get('vector', _private_r_change, )
        # _private_r_change.shape = (-1, 3)
        
        # select points to modify by indices
        vs = _vs[indices]
        ns = _ns[indices]
        rotation = _rotation[indices]
        private_r_align = _private_r_align[indices]
        private_r_align_vector = _private_r_align_vector[indices]
        private_r_up = _private_r_up[indices]
        private_r_up_vector = _private_r_up_vector[indices]
        private_r_base = _private_r_base[indices]
        private_r_random = _private_r_random[indices]
        private_r_random_random = _private_r_random_random[indices]
        # private_r_change_override = _private_r_change_override[indices]
        # private_r_change = _private_r_change[indices]
        align_z = _align_z[indices]
        align_y = _align_y[indices]
        
        # calculate it..
        l = len(indices)
        vs, ns = self._surface_to_global_space(vs, ns, )
        
        nors = []
        _, nor_1 = self._surface_to_global_space(Vector((0.0, 0.0, 0.0, )), Vector((0.0, 0.0, 1.0, )), )
        for i, a in enumerate(private_r_align):
            if(a == 0):
                # normal
                nors.append(Vector(ns[i]))
            elif(a == 1):
                # local
                nors.append(nor_1.copy())
            elif(a == 2):
                # global
                nors.append(Vector((0.0, 0.0, 1.0, )))
            elif(a == 3):
                # custom
                nors.append(Vector(private_r_align_vector[i]))
        
        def direction_to_rotation_with_m3x3(direction, up=Vector((0.0, 1.0, 0.0, )), ):
            x = up.cross(direction)
            x.normalize()
            y = direction.cross(x)
            y.normalize()
            
            m = Matrix()
            m[0][0] = x.x
            m[0][1] = y.x
            m[0][2] = direction.x
            m[1][0] = x.y
            m[1][1] = y.y
            m[1][2] = direction.y
            m[2][0] = x.z
            m[2][1] = y.z
            m[2][2] = direction.z
            
            return m.to_quaternion()
        
        qs = []
        
        locy_1 = Vector((0.0, 1.0, 0.0, ))
        mwi_1 = self.surface.matrix_world.copy()
        _, cr_1, _ = mwi_1.decompose()
        locy_1.rotate(cr_1)
        
        for i, u in enumerate(private_r_up):
            if(u == 0):
                # align_z[i] = nors[i]
                # align_y[i] = (0.0, 1.0, 0.0, )
                # global
                q = direction_to_rotation_with_m3x3(nors[i], )
                qs.append(q)
            elif(u == 1):
                # align_z[i] = nors[i]
                # align_y[i] = locy_1
                # local
                q = direction_to_rotation_with_m3x3(nors[i], locy_1, )
                qs.append(q)
            elif(u == 2):
                # align_z[i] = nors[i]
                # align_y[i] = private_r_up_vector[i]
                # custom
                q = direction_to_rotation_with_m3x3(nors[i], Vector(private_r_up_vector[i]), )
                qs.append(q)
        
        err = []
        for i in range(l):
            err.append(Euler(private_r_random[i] * private_r_random_random[i]))
        
        mwi = self.surface.matrix_world.inverted()
        _, cr, _ = mwi.decompose()
        
        fq = []
        for i in range(l):
            q = Quaternion()
            # if(private_r_change_override[i]):
            #     q.rotate(Euler(private_r_change[i]))
            #     q.rotate(cr)
            # else:
            #     q.rotate(Euler(private_r_base[i]))
            #     q.rotate(err[i])
            #     q.rotate(qs[i])
            #     q.rotate(cr)
            q.rotate(Euler(private_r_base[i]))
            q.rotate(err[i])
            q.rotate(qs[i])
            q.rotate(cr)
            
            fq.append(q)
        
        for i, q in enumerate(fq):
            e = q.to_euler('XYZ')
            rotation[i] = (e.x, e.y, e.z, )
        
        # and set back to attribute..
        _rotation[indices] = rotation
        me.attributes['{}rotation'.format(self.attribute_prefix)].data.foreach_set('vector', _rotation.flatten(), )
        
        # align_z and align_y attributes
        
        # align_z = np.zeros((len(indices), 3), dtype=np.float, )
        # X = rotation[:, 0]
        # Y = rotation[:, 1]
        # Z = rotation[:, 2]
        # x = -np.cos(Z) * np.sin(Y) * np.sin(X) - np.sin(Z) * np.cos(X)
        # y = -np.sin(Z) * np.sin(Y) * np.sin(X) + np.cos(Z) * np.cos(X)
        # z = np.cos(Y) * np.sin(X)
        # align_z[:, 0] = x
        # align_z[:, 1] = y
        # align_z[:, 2] = z
        #
        # align_y = np.zeros((len(indices), 3), dtype=np.float, )
        # rotation_x90 = rotation.copy()
        # x90 = Euler((math.radians(90.0), 0.0, 0.0))
        # for i, r in enumerate(rotation):
        #     ey = Euler(r)
        #     ey.rotate(x90)
        #     rotation_x90[i] = (ey.x, ey.y, ey.y, )
        # X = rotation_x90[:, 0]
        # Y = rotation_x90[:, 1]
        # Z = rotation_x90[:, 2]
        # x = -np.cos(Z) * np.sin(Y) * np.sin(X) - np.sin(Z) * np.cos(X)
        # y = -np.sin(Z) * np.sin(Y) * np.sin(X) + np.cos(Z) * np.cos(X)
        # z = np.cos(Y) * np.sin(X)
        # align_y[:, 0] = x
        # align_y[:, 1] = y
        # align_y[:, 2] = z
        
        align_z = np.zeros((len(indices), 3), dtype=np.float, )
        align_y = np.zeros((len(indices), 3), dtype=np.float, )
        for i in range(len(indices)):
            v = Vector((0.0, 0.0, 1.0))
            v.rotate(Euler(rotation[i]))
            align_z[i] = v.to_tuple()
            
            v = Vector((0.0, 1.0, 0.0))
            v.rotate(Euler(rotation[i]))
            # x90 = Euler((math.radians(90.0), 0.0, 0.0))
            # v.rotate(x90)
            align_y[i] = v.to_tuple()
        
        # write those as well, so i don't have to store them specially after regeneration..
        _align_z[indices] = align_z
        me.attributes['{}align_z'.format(self.attribute_prefix)].data.foreach_set('vector', _align_z.flatten(), )
        _align_y[indices] = align_y
        me.attributes['{}align_y'.format(self.attribute_prefix)].data.foreach_set('vector', _align_y.flatten(), )
    
    def _gen_scale(self, n, ):
        d = np.array(self.brush.scale_default, dtype=np.float, )
        r = np.array(self.brush.scale_random_factor, dtype=np.float, )
        t = 0
        rr = np.random.rand(n, 3)
        if self.brush.scale_default_use_pressure:
            d = d * self.pressure
        if(self.brush.scale_random_type == 'UNIFORM'):
            # f = rr[:, 1]
            f = rr[:, 0]
            f.shape = (-1, 1)
            fn = 1.0 - f
            dr = d * r
            s = (d * fn) + (dr * f)
        elif(self.brush.scale_random_type == 'VECTORIAL'):
            t = 1
            f = r + (1.0 - r) * rr
            s = d * f
        # else:
        #     s = np.ones((n, 3, ), dtype=np.float, )
        
        self._private_s_base = np.full((n, 3), d, dtype=np.float, )
        self._private_s_random = np.full((n, 3), r, dtype=np.float, )
        self._private_s_random_random = rr
        self._private_s_random_type = np.full(n, t, dtype=np.int, )
        self._private_s_change = np.zeros((n, 3), dtype=np.float, )
        
        self._private_s_change_random = np.random.rand(n, 3)
        
        s.shape = (-1, 3, )
        
        return s
    
    def _regenerate_scale_from_attributes(self, indices, ):
        me = self.target.data
        l = len(me.vertices)
        
        # get all..
        _scale = np.zeros(l * 3, dtype=np.float, )
        me.attributes['{}scale'.format(self.attribute_prefix)].data.foreach_get('vector', _scale, )
        _scale.shape = (-1, 3)
        
        _private_s_base = np.zeros(l * 3, dtype=np.float, )
        me.attributes['{}private_s_base'.format(self.attribute_prefix)].data.foreach_get('vector', _private_s_base, )
        _private_s_base.shape = (-1, 3)
        
        _private_s_random = np.zeros(l * 3, dtype=np.float, )
        me.attributes['{}private_s_random'.format(self.attribute_prefix)].data.foreach_get('vector', _private_s_random, )
        _private_s_random.shape = (-1, 3)
        
        _private_s_random_random = np.zeros(l * 3, dtype=np.float, )
        me.attributes['{}private_s_random_random'.format(self.attribute_prefix)].data.foreach_get('vector', _private_s_random_random, )
        _private_s_random_random.shape = (-1, 3)
        
        _private_s_random_type = np.zeros(l, dtype=np.int, )
        me.attributes['{}private_s_random_type'.format(self.attribute_prefix)].data.foreach_get('value', _private_s_random_type, )
        
        _private_s_change = np.zeros(l * 3, dtype=np.float, )
        me.attributes['{}private_s_change'.format(self.attribute_prefix)].data.foreach_get('vector', _private_s_change, )
        _private_s_change.shape = (-1, 3)
        
        # slice by indices..
        scale = _scale[indices]
        private_s_base = _private_s_base[indices]
        private_s_random = _private_s_random[indices]
        private_s_random_random = _private_s_random_random[indices]
        private_s_random_type = _private_s_random_type[indices]
        private_s_change = _private_s_change[indices]
        
        # calculate..
        l = len(indices)
        for i in range(l):
            d = private_s_base[i]
            r = private_s_random[i]
            rr = private_s_random_random[i]
            
            if(private_s_random_type[i] == 0):
                # 'UNIFORM'
                f = rr[0]
                fn = 1.0 - f
                dr = d * r
                s = (d * fn) + (dr * f)
            elif(private_s_random_type[i] == 1):
                # 'VECTORIAL'
                f = r + (1.0 - r) * rr
                s = d * f
            
            s = s + private_s_change[i]
            
            scale[i] = s
        
        # and set back to attribute..
        _scale[indices] = scale
        me.attributes['{}scale'.format(self.attribute_prefix)].data.foreach_set('vector', _scale.flatten(), )
    
    def _gen_id(self, n, ):
        if(not hasattr(self, '_max_id')):
            # NOTE: do this only when create brush is run for the first time..
            me = self.target.data
            l = len(me.vertices)
            if(l == 0):
                self._max_id = 0
            else:
                ids = np.zeros(len(me.vertices), dtype=np.int, )
                me.attributes['{}id'.format(self.attribute_prefix)].data.foreach_get('value', ids)
                v = np.max(ids) + 1
                self._max_id = v
        
        a = np.arange(n)
        r = a + self._max_id
        self._max_id += n
        return r
    
    def _cursor_align(self, loc, nor, ):
        # align viewport cursor the same way resulting instance will be aligned without random (used only with CROSS and RETICLE types)
        bsb = self.brush
        if(bsb.rotation_align == 'GLOBAL_Z_AXIS'):
            nor = Vector((0.0, 0.0, 1.0, ))
        elif(bsb.rotation_align == 'LOCAL_Z_AXIS'):
            _, nor = self._surface_to_global_space(Vector((0.0, 0.0, 0.0, )), Vector((0.0, 0.0, 1.0, )), )
        elif(bsb.rotation_align == 'SURFACE_NORMAL'):
            nor = Vector(nor)
        
        def direction_to_rotation_with_m3x3(direction, up=Vector((0.0, 1.0, 0.0, )), ):
            x = up.cross(direction)
            x.normalize()
            y = direction.cross(x)
            y.normalize()
            
            m = Matrix()
            m[0][0] = x.x
            m[0][1] = y.x
            m[0][2] = direction.x
            m[1][0] = x.y
            m[1][1] = y.y
            m[1][2] = direction.y
            m[2][0] = x.z
            m[2][1] = y.z
            m[2][2] = direction.z
            
            return m.to_quaternion()
        
        if(bsb.rotation_up == 'LOCAL_Y_AXIS'):
            locy = Vector((0.0, 1.0, 0.0, ))
            mwi = self.surface.matrix_world.copy()
            _, cr, _ = mwi.decompose()
            locy.rotate(cr)
            aq = direction_to_rotation_with_m3x3(nor, locy, )
        elif(bsb.rotation_up == 'GLOBAL_Y_AXIS'):
            aq = direction_to_rotation_with_m3x3(nor, )
        
        eb = bsb.rotation_base
        
        q = Quaternion()
        q.rotate(eb)
        q.rotate(aq)
        
        return q
    
    def _switch_help_text(self, ):
        nums = {'ONE': '1', 'TWO': '2', 'THREE': '3', 'FOUR': '4', 'FIVE': '5', 'SIX': '6', 'SEVEN': '7', 'EIGHT': '8', 'NINE': '9', 'ZERO': '0', }
        bcs = all_brush_classes()
        ls = []
        for k, v in config.switch_shortcuts().items():
            for c in bcs:
                if(c.brush_type == k):
                    if(v in nums.keys()):
                        v = nums[v]
                    ls.append("'{}': {}".format(v, c.bl_label))
        t = ", ".join(ls)
        return t
    
    def _integration_on_invoke(self, context, event, ):
        # swap ui
        SC5UISwapper.show(context, )
        # and overlay inactive ui areas
        SC5Overlay.show()
        # tooltips..
        SC5ToolTip.init()
        # set active tool to our newly hijacked registered interface
        bpy.ops.wm.tool_set_by_id(name=self.brush_type)
        # statusbar text
        try:
            t = self._switch_help_text()
        except Exception as e:
            log('ERROR: {}\n{}'.format(e, traceback.format_exc()))
            t = ""
        bpy.context.workspace.status_text_set(text=t, )
        
        # store user active/selected
        self.user_select = [o.name for o in bpy.context.selected_objects]
        self.user_active = None
        if(bpy.context.view_layer.objects.active is not None):
            self.user_active = bpy.context.view_layer.objects.active.name
            
        # deselect all
        for i in bpy.context.scene.objects:
            i.select_set(False)
        # make target active/unselected object
        self.target.select_set(True)
        bpy.context.view_layer.objects.active = self.target
        self.target.select_set(False)
    
    def _integration_on_finish(self, context, event, ):
        # restore original
        SC5UISwapper.hide(context, )
        # hide overlay
        SC5Overlay.hide()
        # free session cahce
        SC5SessionCache.free()
        # tooltips..
        SC5ToolTip.deinit()
        # statusbar text
        bpy.context.workspace.status_text_set(text=None, )
        
        # restore user selection..
        for n in self.user_select:
            o = bpy.data.objects.get(n)
            if(o is not None):
                o.select_set(True)
        if(self.user_active is not None):
            o = bpy.data.objects.get(self.user_active)
            bpy.context.view_layer.objects.active = o


class SCATTER5_OT_manual_dot_brush(SCATTER5_OT_manual_base_brush, ):
    bl_idname = "scatter5.manual_dot_brush"
    bl_label = translate("Dot Brush")
    bl_description = translate("Dot Brush")
    
    brush_type = "dot_brush"
    icon = "W_CLICK"
    dat_icon = "SCATTER5_CLICK"
    
    modal_adjust_map = []
    
    def _cursor_update(self, enable=True, loc=None, nor=None, radius=None, color=None, z_scale=1.0, ):
        s = self.brush.scale_default.length
        s = s / 3
        s = s / 2
        SC5Cursor.update(self.surface.name, enable=enable, loc=loc, nor=nor, radius=s, color=color, z_scale=z_scale, )
    
    def invoke(self, context, event, ):
        # set brush props here so subclass can inject its own collection..
        self.brush = context.scene.scatter5.manual.dot_brush
        return super().invoke(context, event, )
    
    def _self_brush_modal_update(self, context, ):
        self.brush = context.scene.scatter5.manual.dot_brush
    
    def _on_lmb_press(self, context, event, ):
        # NOTE: very important, if there was some drawing done, then undo without dropping tool, this is pointing somewhere invalid, each brush MUST set this again on each use AND before super()
        self.brush = context.scene.scatter5.manual.dot_brush
        super()._on_lmb_press(context, event, )
        self._drawing(context, event, )
        
        # push to history..
        bpy.ops.ed.undo_push(message=self.bl_label, )
    
    def _store(self, loc, nor, ):
        self._ensure_attributes()
        
        loc, nor = self._global_to_surface_space(loc, nor, )
        me = self.target.data
        me.vertices.add(1)
        i = len(me.vertices) - 1
        me.vertices[i].co = loc
        
        me.attributes['{}index'.format(self.attribute_prefix)].data[i].value = self.brush.instance_index
        
        nm = '{}normal'.format(self.attribute_prefix)
        me.attributes[nm].data[i].vector = nor
        
        r = self._gen_rotation(1, np.array(loc, dtype=np.float, ).reshape(-1, 3), np.array(nor, dtype=np.float, ).reshape(-1, 3), )[0]
        e = r.to_euler('XYZ')
        nm = '{}rotation'.format(self.attribute_prefix)
        me.attributes[nm].data[i].vector = e
        
        # align_z and align_y attributes
        
        # X = e.x
        # Y = e.y
        # Z = e.z
        # x = -np.cos(Z) * np.sin(Y) * np.sin(X) - np.sin(Z) * np.cos(X)
        # y = -np.sin(Z) * np.sin(Y) * np.sin(X) + np.cos(Z) * np.cos(X)
        # z = np.cos(Y) * np.sin(X)
        # nm = '{}align_z'.format(self.attribute_prefix)
        # me.attributes[nm].data[i].vector = (x, y, z, )
        
        v = Vector((0.0, 0.0, 1.0))
        v.rotate(e)
        nm = '{}align_z'.format(self.attribute_prefix)
        me.attributes[nm].data[i].vector = v
        
        # vs = np.array([loc, loc, ])
        # ns = [v.to_tuple(), ]
        
        # x90 = Euler((math.radians(90.0), 0.0, 0.0))
        # ey = Euler(e)
        # ey.rotate(x90)
        # X = ey.x
        # Y = ey.y
        # Z = ey.z
        # x = -np.cos(Z) * np.sin(Y) * np.sin(X) - np.sin(Z) * np.cos(X)
        # y = -np.sin(Z) * np.sin(Y) * np.sin(X) + np.cos(Z) * np.cos(X)
        # z = np.cos(Y) * np.sin(X)
        # nm = '{}align_y'.format(self.attribute_prefix)
        # me.attributes[nm].data[i].vector = (x, y, z, )
        
        v = Vector((0.0, 1.0, 0.0))
        v.rotate(e)
        # x90 = Euler((math.radians(90.0), 0.0, 0.0))
        # v.rotate(x90)
        nm = '{}align_y'.format(self.attribute_prefix)
        me.attributes[nm].data[i].vector = v
        
        # ns.append(v.to_tuple())
        # ns = np.array(ns)
        # debug.points(self.target, vs, ns, )
        
        s = self._gen_scale(1, )
        
        nm = '{}scale'.format(self.attribute_prefix)
        me.attributes[nm].data[i].vector = s[0]
        
        anm = '{}private_s_base'.format(self.attribute_prefix)
        att = me.attributes[anm].data
        att[i].vector = self._private_s_base[0]
        
        anm = '{}private_s_random'.format(self.attribute_prefix)
        att = me.attributes[anm].data
        att[i].vector = self._private_s_random[0]
        
        anm = '{}private_s_random_random'.format(self.attribute_prefix)
        att = me.attributes[anm].data
        att[i].vector = self._private_s_random_random[0]
        
        anm = '{}private_s_random_type'.format(self.attribute_prefix)
        att = me.attributes[anm].data
        att[i].value = self._private_s_random_type[0]
        
        anm = '{}private_s_change'.format(self.attribute_prefix)
        att = me.attributes[anm].data
        att[i].vector = self._private_s_change[0]
        
        anm = '{}private_s_change_random'.format(self.attribute_prefix)
        att = me.attributes[anm].data
        att[i].vector = self._private_s_change_random[0]
        
        # private attributes..
        me = self.target.data
        
        # id
        ids = self._gen_id(1, )
        nm = '{}id'.format(self.attribute_prefix)
        me.attributes[nm].data[i].value = ids[0]
        
        # rotation intermediates v2 ---------------------------------------------------
        anm = '{}private_r_align'.format(self.attribute_prefix)
        att = me.attributes[anm].data
        att[i].value = self._private_r_align[0]
        
        anm = '{}private_r_up'.format(self.attribute_prefix)
        att = me.attributes[anm].data
        att[i].value = self._private_r_up[0]
        
        anm = '{}private_r_base'.format(self.attribute_prefix)
        att = me.attributes[anm].data
        att[i].vector = self._private_r_base[0]
        
        anm = '{}private_r_random'.format(self.attribute_prefix)
        att = me.attributes[anm].data
        att[i].vector = self._private_r_random[0]
        
        anm = '{}private_r_random_random'.format(self.attribute_prefix)
        att = me.attributes[anm].data
        att[i].vector = self._private_r_random_random[0]
        
        # rotation intermediates v2 ---------------------------------------------------
        
        # anm = '{}align_z'.format(self.attribute_prefix)
        # att = me.attributes[anm].data
        # att[i].vector = self._align_z[0]
        #
        # anm = '{}align_y'.format(self.attribute_prefix)
        # att = me.attributes[anm].data
        # att[i].vector = self._align_y[0]


class SCATTER5_OT_manual_spatter_brush(SCATTER5_OT_manual_base_brush, ):
    bl_idname = "scatter5.manual_spatter_brush"
    bl_label = translate("Spatter Brush")
    bl_description = translate("Spatter Brush")
    
    brush_type = "spatter_brush"
    icon = "W_SPATTER"
    dat_icon = "SCATTER5_SPATTER"
    
    modal_adjust_map = [
        {
            'enabled': True,
            'key': 'F',
            'oskey': False,
            'shift': False,
            'property': 'random_location',
            'type': 'float',
            'change': 1 / 100,
            'change_pixels': 1,
            'text': 'Random Location: {:.3f}',
            'cursor': 'LENGTH',
        },
    ]
    
    def _cursor_update(self, enable=True, loc=None, nor=None, radius=None, color=None, z_scale=1.0, ):
        s = self.brush.scale_default.length
        s = s / 3
        s = s / 2
        SC5Cursor.update(self.surface.name, enable=enable, loc=loc, nor=nor, radius=s, color=color, z_scale=z_scale, )
    
    def invoke(self, context, event, ):
        # set brush props here so subclass can inject its own collection..
        self.brush = context.scene.scatter5.manual.spatter_brush
        self.is_timer = True
        self.path = []
        self.direction = []
        return super().invoke(context, event, )
    
    def _self_brush_modal_update(self, context, ):
        self.brush = context.scene.scatter5.manual.spatter_brush
    
    def _on_lmb_press(self, context, event, ):
        # NOTE: very important, if there was some drawing done, then undo without dropping tool, this is pointing somewhere invalid, each brush MUST set this again on each use AND before super()
        self.brush = context.scene.scatter5.manual.spatter_brush
        
        super()._on_lmb_press(context, event, )
        self._drawing(context, event, )
    
    def _on_lmb_move(self, context, event, ):
        super()._on_lmb_move(context, event, )
        # self._drawing(context, event, )
        
        if(self.brush.draw_on in ('MOUSEMOVE', 'BOTH', )):
            self._drawing(context, event, )
    
    def _on_lmb_release(self, context, event, ):
        super()._on_lmb_release(context, event, )
        self.path = []
        self.direction = []
        # push to history..
        bpy.ops.ed.undo_push(message=self.bl_label, )
    
    def _drawing(self, context, event, ):
        # if(len(self.path)):
        #     debug.points(self.target, self.path, self.direction, )
        
        loc, nor, idx, dst = self._project(context, event, )
        if(loc is not None):
            # for each draw event, those two should be the same for all generated points, so i can keep this on class.. might get easier in future to access that
            self._loc = loc.copy()
            self._nor = nor.copy()
            
            if(len(self.path) == 0):
                self.path.append(loc)
                self.direction.append(Vector((0.0, 0.0, 0.0, )))
            else:
                a = self.path[-1]
                b = loc
                n = b - a
                n.normalize()
                self.direction.append(n)
                self.path.append(loc)
            
            r = self._generate(loc, nor, idx, dst, )
            if(r is not None):
                loc, nor = r
                self._store(loc, nor, )
            
            self.target.data.update()
    
    def _generate(self, loc, nor, idx, dst, ):
        d = self.brush.random_location
        if(d > 0.0):
            if(self.brush.random_location_pressure):
                d = d * self.pressure
            r = d * random.random()
            a = (2 * math.pi) * random.random()
            x = r * math.cos(a)
            y = r * math.sin(a)
            z = 0.0
            v = Vector((x, y, z, ))
            z = Vector((0.0, 0.0, 1.0, ))
            q = self._rotation_to(z, nor, )
            v.rotate(q)
            c = loc + v
            loc, nor, idx, dst = self.bvh.find_nearest(c)
            nor = self._interpolate_smooth_face_normal(loc, nor, idx, )
        
        return loc, nor
    
    def _store(self, loc, nor, ):
        self._ensure_attributes()
        
        if(self.brush.align):
            # if align is enabled, but mouse did not moved yet, skip until it moves so i have direction to use.. this is preventing having the first instance oriented in wrong direction..
            if(self.direction[-1].length == 0.0):
                return
        
        loc, nor = self._global_to_surface_space(loc, nor, )
        me = self.target.data
        me.vertices.add(1)
        i = len(me.vertices) - 1
        me.vertices[i].co = loc
        
        me.attributes['{}index'.format(self.attribute_prefix)].data[i].value = self.brush.instance_index
        
        nm = '{}normal'.format(self.attribute_prefix)
        me.attributes[nm].data[i].vector = nor
        
        r = self._gen_rotation(1, np.array(loc, dtype=np.float, ).reshape(-1, 3), np.array(nor, dtype=np.float, ).reshape(-1, 3), )[0]
        e = r.to_euler('XYZ')
        nm = '{}rotation'.format(self.attribute_prefix)
        me.attributes[nm].data[i].vector = e
        
        # align_z and align_y attributes
        v = Vector((0.0, 0.0, 1.0))
        v.rotate(e)
        nm = '{}align_z'.format(self.attribute_prefix)
        me.attributes[nm].data[i].vector = v
        v = Vector((0.0, 1.0, 0.0))
        v.rotate(e)
        nm = '{}align_y'.format(self.attribute_prefix)
        me.attributes[nm].data[i].vector = v
        
        s = self._gen_scale(1, )
        
        nm = '{}scale'.format(self.attribute_prefix)
        me.attributes[nm].data[i].vector = s[0]
        
        anm = '{}private_s_base'.format(self.attribute_prefix)
        att = me.attributes[anm].data
        att[i].vector = self._private_s_base[0]
        
        anm = '{}private_s_random'.format(self.attribute_prefix)
        att = me.attributes[anm].data
        att[i].vector = self._private_s_random[0]
        
        anm = '{}private_s_random_random'.format(self.attribute_prefix)
        att = me.attributes[anm].data
        att[i].vector = self._private_s_random_random[0]
        
        anm = '{}private_s_random_type'.format(self.attribute_prefix)
        att = me.attributes[anm].data
        att[i].value = self._private_s_random_type[0]
        
        anm = '{}private_s_change'.format(self.attribute_prefix)
        att = me.attributes[anm].data
        att[i].vector = self._private_s_change[0]
        
        anm = '{}private_s_change_random'.format(self.attribute_prefix)
        att = me.attributes[anm].data
        att[i].vector = self._private_s_change_random[0]
        
        # private attributes..
        me = self.target.data
        
        # id
        ids = self._gen_id(1, )
        nm = '{}id'.format(self.attribute_prefix)
        me.attributes[nm].data[i].value = ids[0]
        
        # rotation intermediates v2 ---------------------------------------------------
        anm = '{}private_r_align'.format(self.attribute_prefix)
        att = me.attributes[anm].data
        att[i].value = self._private_r_align[0]
        
        anm = '{}private_r_up'.format(self.attribute_prefix)
        att = me.attributes[anm].data
        att[i].value = self._private_r_up[0]
        
        anm = '{}private_r_base'.format(self.attribute_prefix)
        att = me.attributes[anm].data
        att[i].vector = self._private_r_base[0]
        
        anm = '{}private_r_random'.format(self.attribute_prefix)
        att = me.attributes[anm].data
        att[i].vector = self._private_r_random[0]
        
        anm = '{}private_r_random_random'.format(self.attribute_prefix)
        att = me.attributes[anm].data
        att[i].vector = self._private_r_random_random[0]
        
        # rotation intermediates v2 ---------------------------------------------------
        
        # anm = '{}align_z'.format(self.attribute_prefix)
        # att = me.attributes[anm].data
        # att[i].vector = self._align_z[0]
        #
        # anm = '{}align_y'.format(self.attribute_prefix)
        # att = me.attributes[anm].data
        # att[i].vector = self._align_y[0]
        
        if(self.brush.align):
            # d = np.array(self._mouse_3d_direction, dtype=np.float, )
            d = self.direction[-1]
            
            me.attributes['{}private_r_up'.format(self.attribute_prefix)].data[i].value = 2
            me.attributes['{}private_r_up_vector'.format(self.attribute_prefix)].data[i].vector = d
            
            indices = np.array([i, ], dtype=np.int, )
            self._regenerate_rotation_from_attributes(indices, )


class SCATTER5_OT_manual_pose_brush(SCATTER5_OT_manual_base_brush, ):
    bl_idname = "scatter5.manual_pose_brush"
    bl_label = translate("Pose Brush")
    bl_description = translate("Pose Brush")
    
    brush_type = "pose_brush"
    icon = "W_SCALE_GROW"
    dat_icon = "SCATTER5_POSE"
    
    def _cursor_update_2d(self, coords=None, enable=True, radius=None, color=None, ):
        # NOTE: so i can override that in subclasses..
        # coords = (self.mouse_region_x, self.mouse_region_y, )
        if(coords is None):
            # coords = Vector(self._path_2d_region[1])
            coords = Vector(self._mouse_2d_region)
        
        # SC5Cursor2D.update(self.surface.name, enable=enable, coords=coords, radius=radius, color=color, )
        SC5Cursor2D.update(self.surface.name, enable=enable, coords=coords, radius=radius, color=color, angle=self._angle, length=self._distance, )
    
    def _cursor_update(self, enable=True, loc=None, nor=None, radius=None, color=None, z_scale=1.0, angle=0.0, ):
        if(radius):
            radius = radius / 2
        SC5Cursor.update(self.surface.name, enable=enable, loc=loc, nor=nor, radius=radius, color=color, z_scale=z_scale, angle=angle, )
        # SC5Cursor.update(self.surface.name, enable=enable, loc=loc, nor=nor, radius=radius, color=color, z_scale=z_scale, angle=self._angle, )
    
    def invoke(self, context, event, ):
        # set brush props here so subclass can inject its own collection..
        # this is where instance will be located
        self._origin = None
        # this is instance up (z)
        self._normal = None
        # and store this for 2d calculations
        self._origin_2d = None
        self._angle = 0.0
        self._distance = 0.0
        
        self.brush = context.scene.scatter5.manual.pose_brush
        
        r = super().invoke(context, event, )
        
        SC5Cursor2D.init()
        SC5Cursor2D.add(self.surface.name, self.brush.cursor_2d, )
        SC5Cursor2D.update(self.surface.name, angle=self._angle, length=self._distance, )
        
        return r
    
    def _self_brush_modal_update(self, context, ):
        self.brush = context.scene.scatter5.manual.pose_brush
    
    def _on_lmb_press(self, context, event, ):
        # NOTE: very important, if there was some drawing done, then undo without dropping tool, this is pointing somewhere invalid, each brush MUST set this again on each use AND before super()
        self.brush = context.scene.scatter5.manual.pose_brush
        super()._on_lmb_press(context, event, )
        
        self._cursor_update_2d(color=SC5ViewportTheme.BRUSH_DOWN, )
        
        loc, nor, idx, dst = self._project(context, event, )
        if(loc is not None):
            self._loc = loc.copy()
            self._nor = nor.copy()
            
            # start drawing only when surface is clicked..
            self._origin = loc.copy()
            self._normal = nor.copy()
            self._origin_2d = Vector((event.mouse_region_x, event.mouse_region_y, ))
            
            self._store(loc, nor, )
            self.target.data.update()
    
    def _on_lmb_move(self, context, event, ):
        a = self._origin_2d
        b = Vector((event.mouse_region_x, event.mouse_region_y, ))
        c = b - a
        self._distance = c.length / self.brush.radius_2d
        self._angle = c.angle_signed(Vector((0.0, 1.0, )), 0.0, )
        
        super()._on_lmb_move(context, event, )
        
        self._update_last(context, event, )
        self.target.data.update()
    
    def _on_lmb_release(self, context, event, ):
        self._angle = 0.0
        self._distance = 0.0
        
        super()._on_lmb_release(context, event, )
        
        self._cursor_update_2d(color=SC5ViewportTheme.BRUSH_UP, )
        
        # push to history..
        bpy.ops.ed.undo_push(message=self.bl_label, )
    
    def modal(self, context, event, ):
        r = super().modal(context, event, )
        if(self.lmb):
            self._cursor_update(enable=False, )
            
            radius = getattr(self.brush, 'radius', 0.0, )
            if(hasattr(self.brush, 'radius')):
                radius = self.brush.radius_2d
            if(event.is_tablet) and (hasattr(self.brush, 'radius_pressure')) and (self.brush.radius_pressure) and self.lmb:
                p = event.pressure
                if(p == 0.0):
                    p = 0.001
                radius *= p
            enable = True
            if(self.modal_adjust):
                if(self.modal_adjust_current['cursor'] not in (SC5GestureCursor2D.RADIUS, SC5GestureCursor2D.STRENGTH, )):
                    enable = False
            else:
                # update coords..
                self._coords = (event.mouse_region_x, event.mouse_region_y, )
            is_3dview, is_viewport = self._is_viewport(context, event, )
            if(not is_viewport):
                enable = False
            self._cursor_update_2d(enable=enable, coords=self._coords, radius=radius, )
        else:
            self._cursor_update_2d(enable=False, )
        
        return r
    
    def _cleanup(self, ):
        SC5Cursor2D.remove(self.surface.name, )
        super()._cleanup()
    
    def _update_last(self, context, event, ):
        me = self.target.data
        i = len(me.vertices) - 1
        
        # scale
        d = Vector(self._mouse_2d_region - self._origin_2d).length * self.brush.scale_multiplier
        # leave initial scale unchanged when mouse distance is zero
        # l = 1.0 + d
        # s = Vector((l, l, l, ))
        v = self.brush.scale_default
        x = v.x + (v.x * d)
        y = v.y + (v.y * d)
        z = v.z + (v.z * d)
        s = Vector((x, y, z, ))
        
        me.attributes['{}scale'.format(self.attribute_prefix)].data[i].vector = s
        me.attributes['{}private_s_base'.format(self.attribute_prefix)].data[i].vector = s
        
        # rotation
        region = context.region
        rv3d = context.region_data
        coord = (event.mouse_region_x, event.mouse_region_y, )
        # get mouse location in 3d at origin depth
        loc = view3d_utils.region_2d_to_location_3d(region, rv3d, coord, self._origin, )
        me.attributes['{}private_r_align'.format(self.attribute_prefix)].data[i].value = 3
        
        if(self.brush.rotation_align == 'GLOBAL_Z_AXIS'):
            av = Vector((0.0, 0.0, 1.0, ))
        elif(self.brush.rotation_align == 'LOCAL_Z_AXIS'):
            _, av = self._surface_to_global_space(Vector((0.0, 0.0, 0.0, )), Vector((0.0, 0.0, 1.0, )), )
        elif(self.brush.rotation_align == 'SURFACE_NORMAL'):
            av = self._normal
        # me.attributes['{}private_r_align_vector'.format(self.attribute_prefix)].data[i].vector = self._normal
        me.attributes['{}private_r_align_vector'.format(self.attribute_prefix)].data[i].vector = av
        me.attributes['{}private_r_up'.format(self.attribute_prefix)].data[i].value = 2
        # use that as before in 3d
        d = self._origin - loc
        q = self._rotation_to(Vector((0.0, 0.0, 1.0, )), d)
        u = Vector((0.0, 0.0, 1.0, ))
        u.rotate(q)
        u.normalize()
        u.negate()
        me.attributes['{}private_r_up_vector'.format(self.attribute_prefix)].data[i].vector = u
        self._regenerate_rotation_from_attributes(np.array([i, ], dtype=np.int, ), )
    
    def _store(self, loc, nor, ):
        # taken from dot brush.. unchanged..
        self._ensure_attributes()
        
        loc, nor = self._global_to_surface_space(loc, nor, )
        me = self.target.data
        me.vertices.add(1)
        i = len(me.vertices) - 1
        me.vertices[i].co = loc
        
        me.attributes['{}index'.format(self.attribute_prefix)].data[i].value = self.brush.instance_index
        
        nm = '{}normal'.format(self.attribute_prefix)
        me.attributes[nm].data[i].vector = nor
        
        r = self._gen_rotation(1, np.array(loc, dtype=np.float, ).reshape(-1, 3), np.array(nor, dtype=np.float, ).reshape(-1, 3), )[0]
        e = r.to_euler('XYZ')
        nm = '{}rotation'.format(self.attribute_prefix)
        me.attributes[nm].data[i].vector = e
        
        # align_z and align_y attributes
        v = Vector((0.0, 0.0, 1.0))
        v.rotate(e)
        nm = '{}align_z'.format(self.attribute_prefix)
        me.attributes[nm].data[i].vector = v
        v = Vector((0.0, 1.0, 0.0))
        v.rotate(e)
        nm = '{}align_y'.format(self.attribute_prefix)
        me.attributes[nm].data[i].vector = v
        
        s = self._gen_scale(1, )
        
        nm = '{}scale'.format(self.attribute_prefix)
        me.attributes[nm].data[i].vector = s[0]
        
        anm = '{}private_s_base'.format(self.attribute_prefix)
        att = me.attributes[anm].data
        att[i].vector = self._private_s_base[0]
        
        anm = '{}private_s_random'.format(self.attribute_prefix)
        att = me.attributes[anm].data
        att[i].vector = self._private_s_random[0]
        
        anm = '{}private_s_random_random'.format(self.attribute_prefix)
        att = me.attributes[anm].data
        att[i].vector = self._private_s_random_random[0]
        
        anm = '{}private_s_random_type'.format(self.attribute_prefix)
        att = me.attributes[anm].data
        att[i].value = self._private_s_random_type[0]
        
        anm = '{}private_s_change'.format(self.attribute_prefix)
        att = me.attributes[anm].data
        att[i].vector = self._private_s_change[0]
        
        anm = '{}private_s_change_random'.format(self.attribute_prefix)
        att = me.attributes[anm].data
        att[i].vector = self._private_s_change_random[0]
        
        # private attributes..
        me = self.target.data
        
        # id
        ids = self._gen_id(1, )
        nm = '{}id'.format(self.attribute_prefix)
        me.attributes[nm].data[i].value = ids[0]
        
        # rotation intermediates v2 ---------------------------------------------------
        anm = '{}private_r_align'.format(self.attribute_prefix)
        att = me.attributes[anm].data
        att[i].value = self._private_r_align[0]
        
        anm = '{}private_r_up'.format(self.attribute_prefix)
        att = me.attributes[anm].data
        att[i].value = self._private_r_up[0]
        
        anm = '{}private_r_base'.format(self.attribute_prefix)
        att = me.attributes[anm].data
        att[i].vector = self._private_r_base[0]
        
        anm = '{}private_r_random'.format(self.attribute_prefix)
        att = me.attributes[anm].data
        att[i].vector = self._private_r_random[0]
        
        anm = '{}private_r_random_random'.format(self.attribute_prefix)
        att = me.attributes[anm].data
        att[i].vector = self._private_r_random_random[0]
        
        # rotation intermediates v2 ---------------------------------------------------
        
        # anm = '{}align_z'.format(self.attribute_prefix)
        # att = me.attributes[anm].data
        # att[i].vector = self._align_z[0]
        #
        # anm = '{}align_y'.format(self.attribute_prefix)
        # att = me.attributes[anm].data
        # att[i].vector = self._align_y[0]


class SCATTER5_OT_manual_path_brush(SCATTER5_OT_manual_base_brush, ):
    bl_idname = "scatter5.manual_path_brush"
    bl_label = translate("Path Brush")
    bl_description = translate("Path Brush")

    brush_type = "path_brush"
    icon = "W_PENCIL"
    dat_icon = "SCATTER5_PENCIL"
    
    modal_adjust_map = [
        # {
        #     'enabled': True,
        #     'key': 'F',
        #     'oskey': False,
        #     'shift': False,
        #     'property': 'radius',
        #     'type': 'float',
        #     'change': 1 / 100,
        #     'text': 'Radius: {:.3f}',
        #     'cursor': 'RADIUS',
        # },
        {
            'enabled': True,
            'key': 'F',
            'oskey': False,
            'shift': False,
            'property': 'path_distance',
            'type': 'float',
            'change': 1 / 100,
            'change_pixels': 1,
            'text': 'Dot Distance: {:.3f}',
            'cursor': 'LENGTH',
        },
        {
            'enabled': True,
            'key': 'F',
            'oskey': True,
            'shift': False,
            'property': 'divergence_distance',
            'type': 'float',
            'change': 1 / 100,
            'change_pixels': 1,
            'text': 'Divergence Distance: {:.3f}',
            'cursor': 'LENGTH',
        },
    ]
    
    def _cursor_update(self, enable=True, loc=None, nor=None, radius=None, color=None, z_scale=1.0, ):
        s = self.brush.scale_default.length
        s = s / 3
        s = s / 2
        SC5Cursor.update(self.surface.name, enable=enable, loc=loc, nor=nor, radius=s, color=color, z_scale=z_scale, )
    
    def invoke(self, context, event, ):
        self.path = []
        self.direction = []
        
        self.brush = context.scene.scatter5.manual.path_brush
        return super().invoke(context, event, )
    
    def _self_brush_modal_update(self, context, ):
        self.brush = context.scene.scatter5.manual.path_brush
    
    def _on_lmb_press(self, context, event, ):
        # NOTE: very important, if there was some drawing done, then undo without dropping tool, this is pointing somewhere invalid, each brush MUST set this again on each use AND before super()
        self.brush = context.scene.scatter5.manual.path_brush
        super()._on_lmb_press(context, event, )
        self._drawing(context, event, )
    
    def _on_lmb_move(self, context, event, ):
        super()._on_lmb_move(context, event, )
        self._drawing(context, event, )
    
    def _on_lmb_release(self, context, event, ):
        super()._on_lmb_release(context, event, )
        self.path = []
        self.direction = []
        
        # push to history..
        bpy.ops.ed.undo_push(message=self.bl_label, )
    
    def _distance_vectors(self, a, b, ):
        return ((a.x - b.x) ** 2 + (a.y - b.y) ** 2 + (a.z - b.z) ** 2) ** 0.5
    
    def _store(self, loc, nor, ):
        self._ensure_attributes()
        
        loc, nor = self._global_to_surface_space(loc, nor, )
        
        # ok, now i can store some points in target
        me = self.target.data
        me.vertices.add(1)
        i = len(me.vertices) - 1
        me.vertices[i].co = loc
        
        me.attributes['{}index'.format(self.attribute_prefix)].data[i].value = self.brush.instance_index
        
        nm = '{}normal'.format(self.attribute_prefix)
        me.attributes[nm].data[i].vector = nor
        
        r = self._gen_rotation(1, np.array(loc, dtype=np.float, ).reshape(-1, 3), np.array(nor, dtype=np.float, ).reshape(-1, 3), )[0]
        e = r.to_euler('XYZ')
        nm = '{}rotation'.format(self.attribute_prefix)
        me.attributes[nm].data[i].vector = e
        
        # align_z and align_y attributes
        v = Vector((0.0, 0.0, 1.0))
        v.rotate(e)
        nm = '{}align_z'.format(self.attribute_prefix)
        me.attributes[nm].data[i].vector = v
        v = Vector((0.0, 1.0, 0.0))
        v.rotate(e)
        nm = '{}align_y'.format(self.attribute_prefix)
        me.attributes[nm].data[i].vector = v
        
        s = self._gen_scale(1, )
        
        nm = '{}scale'.format(self.attribute_prefix)
        me.attributes[nm].data[i].vector = s[0]
        
        anm = '{}private_s_base'.format(self.attribute_prefix)
        att = me.attributes[anm].data
        att[i].vector = self._private_s_base[0]
        
        anm = '{}private_s_random'.format(self.attribute_prefix)
        att = me.attributes[anm].data
        att[i].vector = self._private_s_random[0]
        
        anm = '{}private_s_random_random'.format(self.attribute_prefix)
        att = me.attributes[anm].data
        att[i].vector = self._private_s_random_random[0]
        
        anm = '{}private_s_random_type'.format(self.attribute_prefix)
        att = me.attributes[anm].data
        att[i].value = self._private_s_random_type[0]
        
        anm = '{}private_s_change'.format(self.attribute_prefix)
        att = me.attributes[anm].data
        att[i].vector = self._private_s_change[0]
        
        anm = '{}private_s_change_random'.format(self.attribute_prefix)
        att = me.attributes[anm].data
        att[i].vector = self._private_s_change_random[0]
        
        # private attributes..
        me = self.target.data
        
        # id
        ids = self._gen_id(1, )
        nm = '{}id'.format(self.attribute_prefix)
        me.attributes[nm].data[i].value = ids[0]
        
        # rotation intermediates v2 ---------------------------------------------------
        anm = '{}private_r_align'.format(self.attribute_prefix)
        att = me.attributes[anm].data
        att[i].value = self._private_r_align[0]
        
        anm = '{}private_r_up'.format(self.attribute_prefix)
        att = me.attributes[anm].data
        att[i].value = self._private_r_up[0]
        
        anm = '{}private_r_base'.format(self.attribute_prefix)
        att = me.attributes[anm].data
        att[i].vector = self._private_r_base[0]
        
        anm = '{}private_r_random'.format(self.attribute_prefix)
        att = me.attributes[anm].data
        att[i].vector = self._private_r_random[0]
        
        anm = '{}private_r_random_random'.format(self.attribute_prefix)
        att = me.attributes[anm].data
        att[i].vector = self._private_r_random_random[0]
        
        # rotation intermediates v2 ---------------------------------------------------
        
        # anm = '{}align_z'.format(self.attribute_prefix)
        # att = me.attributes[anm].data
        # att[i].vector = self._align_z[0]
        #
        # anm = '{}align_y'.format(self.attribute_prefix)
        # att = me.attributes[anm].data
        # att[i].vector = self._align_y[0]
        
        if(self.brush.align):
            d = self.direction[-1]
            
            me.attributes['{}private_r_up'.format(self.attribute_prefix)].data[i].value = 2
            me.attributes['{}private_r_up_vector'.format(self.attribute_prefix)].data[i].vector = d
            
            indices = [i, ]
            
            if(self.brush.chain):
                if(len(self.path) >= 3):
                    a = self.path[-2]
                    b = self.path[-1]
                    n = b - a
                    n.normalize()
                    
                    me.attributes['{}private_r_up'.format(self.attribute_prefix)].data[i - 1].value = 2
                    me.attributes['{}private_r_up_vector'.format(self.attribute_prefix)].data[i - 1].vector = n
                    indices.append(i - 1)
            
            # self._regenerate_rotation_from_attributes(np.array((i, ), dtype=np.int, ), )
            self._regenerate_rotation_from_attributes(np.array(indices, dtype=np.int, ), )
    
    def _drawing(self, context, event, ):
        loc, nor, idx, dst = self._project(context, event, )
        if(loc is not None):
            self._loc = loc.copy()
            self._nor = nor.copy()
            
            if(len(self.path) == 0):
                self.path.append(loc)
                self.direction.append(Vector((0.0, 0.0, 0.0, )))
                
                # self._store(loc, nor, )
            else:
                a = self.path[-1]
                b = loc
                d = self._distance_vectors(a, b)
                fd = self.brush.path_distance
                if(self.brush.path_distance_pressure):
                    fd = fd * self.pressure
                if(fd <= d):
                    # NOTE: why it is getting slower with more point when i use just last point from path with new one?
                    n = b - a
                    n.normalize()
                    
                    self.direction.append(n)
                    
                    # if(self.brush.path_distance_random):
                    #     fd = fd * random.random()
                    
                    c = Vector((a.x + fd * n.x, a.y + fd * n.y, a.z + fd * n.z, ))
                    
                    if(self.brush.divergence_distance > 0.0):
                        d = self.brush.divergence_distance
                        
                        # if(self.brush.path_distance_random):
                        #     # NOTE: distance / 2 because it is left + right, and i want it to match with regular random distance if enabled
                        #     d  = d / 2
                        
                        if(self.brush.divergence_distance_pressure):
                            d = d * self.pressure
                        
                        v = self.direction[-1].cross(nor)
                        if(random.random() < 0.5):
                            v.negate()
                        
                        d = d * random.random()
                        c = c + (v.normalized() * d)
                        
                        lp = self.path[-1]
                        cc = c - lp
                        cc.normalize()
                        cc.length = fd
                        c = lp + cc
                    
                    # find it again, because target polygon and normal can change while coorecting distance
                    loc, nor, idx, dst = self.bvh.find_nearest(c)
                    nor = self._interpolate_smooth_face_normal(loc, nor, idx, )
                    self.path.append(loc)
                    self._store(loc, nor, )


class SCATTER5_OT_manual_spray_brush(SCATTER5_OT_manual_base_brush, ):
    bl_idname = "scatter5.manual_spray_brush"
    bl_label = translate("Spray Brush")
    bl_description = translate("Spray Brush")

    brush_type = "spray_brush"
    icon = "W_SPRAY"
    dat_icon = "SCATTER5_SPRAY"
    
    modal_adjust_map = [
        {
            'enabled': True,
            'key': 'F',
            'oskey': False,
            'shift': False,
            'property': 'radius',
            'type': 'float',
            'change': 1 / 100,
            'change_pixels': 1,
            'text': 'Radius: {:.3f}',
            'cursor': 'RADIUS',
        },
        {
            'enabled': True,
            'key': 'F',
            'oskey': True,
            'shift': False,
            'property': 'num_dots',
            'type': 'int',
            'change': 1,
            'change_pixels': 5,
            'text': 'Points Per Interval: {}',
            'cursor': 'COUNT',
        },
    ]
    
    def invoke(self, context, event, ):
        self.brush = context.scene.scatter5.manual.spray_brush
        self.is_timer = True
        return super().invoke(context, event, )
    
    def _cursor_update(self, enable=True, loc=None, nor=None, radius=None, color=None, z_scale=1.0, ):
        if(radius is not None):
            SC5Cursor.update(self.surface.name, enable=enable, loc=loc, nor=nor, radius=radius, color=color, z_scale=self.brush.jet * radius, )
        else:
            SC5Cursor.update(self.surface.name, enable=enable, loc=loc, nor=nor, radius=radius, color=color, z_scale=self.brush.jet, )
    
    def _self_brush_modal_update(self, context, ):
        self.brush = context.scene.scatter5.manual.spray_brush
    
    def _on_lmb_press(self, context, event, ):
        # NOTE: very important, if there was some drawing done, then undo without dropping tool, this is pointing somewhere invalid, each brush MUST set this again on each use AND before super()
        self.brush = context.scene.scatter5.manual.spray_brush
        super()._on_lmb_press(context, event, )
        self._drawing(context, event, )
    
    def _on_lmb_release(self, context, event, ):
        super()._on_lmb_release(context, event, )
        
        # push to history..
        bpy.ops.ed.undo_push(message=self.bl_label, )
    
    def _generate(self, loc, nor, idx, dst, ):
        brush_radius = self.brush.radius
        if(self.brush.radius_pressure):
            brush_radius = brush_radius * self.pressure
        
        num_dots = self.brush.num_dots
        if(self.brush.num_dots_pressure):
            num_dots = int(self.brush.num_dots * self.pressure)
            if(num_dots == 0):
                # draw at least one..
                num_dots = 1
        else:
            num_dots = self.brush.num_dots
        
        rnd = random.Random()
        
        # radius in radians from 0.0 to math.pi to be somewhat useable
        def rnd_in_cone(radius, ):
            # http://answers.unity.com/comments/1324674/view.html
            z = rnd.uniform(math.cos(radius), 1)
            t = rnd.uniform(0, math.pi * 2)
            v = Vector((math.sqrt(1 - z * z) * math.cos(t), math.sqrt(1 - z * z) * math.sin(t), z))
            return v
        
        # d = brush_radius * 2
        d = self.brush.jet * self.brush.radius
        max_d = d + self.brush.reach
        # NOTE: epsilon of the same value as bvh epsilon result in around half of points being discarded
        epsilon_d = self.epsilon * 2
        
        def distance_vectors(a, b, ):
            return ((a.x - b.x) ** 2 + (a.y - b.y) ** 2 + (a.z - b.z) ** 2) ** 0.5
        
        origin = loc + (nor * d)
        
        _os = np.zeros((num_dots, 3, ), dtype=np.float, )
        _ds = np.zeros((num_dots, 3, ), dtype=np.float, )
        
        vs = np.zeros((num_dots, 3, ), dtype=np.float, )
        ns = np.zeros((num_dots, 3, ), dtype=np.float, )
        status = np.zeros(num_dots, dtype=np.bool, )
        
        # cone slice = right angle triangle so:
        angle = math.atan(brush_radius / d)
        angle = angle * 2
        
        for i in range(num_dots):
            axis = Vector((np.random.rand(3) - 0.5) * 2)
            axis.normalize()
            
            r = np.random.rand(1)
            
            a = (r - 0.5) * angle
            q = Quaternion(axis, a)
            
            direction = nor * (-1.0)
            direction.rotate(q)
            
            _os[i] = origin
            _ds[i] = direction
            
            _loc, _nor, _idx, _dst = self.bvh.ray_cast(origin, direction, )
            if(_loc is not None):
                if(distance_vectors(origin, _loc) > max_d):
                    continue
                
                co, _, _, _ = self.bvh.find_nearest(_loc, epsilon_d, )
                if(co is None):
                    continue
                
                vs[i] = _loc
                # make it smooth if needed..
                _nor = self._interpolate_smooth_face_normal(_loc, _nor, _idx, )
                ns[i] = _nor
                status[i] = True
        
        vs = vs[status]
        ns = ns[status]
        
        # from space_view3d_point_cloud_visualizer.mechanist import PCVOverseer
        # pcv = PCVOverseer(self.target)
        # # pcv.load(vs, ns, None, True)
        # pcv.load(_os, _ds, None, True)
        
        if(self.brush.use_minimal_distance):
            minimal_distance = self.brush.minimal_distance
            if(self.brush.minimal_distance_pressure):
                minimal_distance = minimal_distance * self.pressure
            
            if(len(vs) > 0):
                # filter new points with each other
                indices = []
                for i, v in enumerate(vs):
                    if(len(indices) > 0):
                        fvs, fds, fii = self._distance_range(vs[indices], v, minimal_distance, )
                        if(len(fii) > 0):
                            continue
                    indices.append(i)
                vs = vs[indices]
                ns = ns[indices]
            
            locations = np.zeros(len(self.target.data.vertices) * 3, dtype=np.float, )
            self.target.data.vertices.foreach_get('co', locations)
            locations.shape = (-1, 3)
            locations, _ = self._surface_to_global_space(locations, None, )
            
            if(len(vs) > 0 and len(locations) > 0):
                # filter new points with existing points
                indices = []
                for i, v in enumerate(vs):
                    fvs, fds, fii = self._distance_range(locations, v, minimal_distance, )
                    if(len(fii) == 0):
                        indices.append(i)
                vs = vs[indices]
                ns = ns[indices]
        
        return vs, ns
    
    def _store(self, vs, ns, ):
        self._ensure_attributes()
        
        if(self.brush.align):
            if(self._mouse_3d_direction is None):
                # skip event if user just went out of surface and now it is returning back, to have 3d direction i need to wait to another event to calculate direction..
                return
        
        me = self.target.data
        
        s = self._gen_scale(len(vs), )
        
        r = self._gen_rotation(len(vs), vs, ns, )
        
        # id
        ids = self._gen_id(len(vs), )
        
        _l = len(me.vertices)
        
        for i in range(len(vs)):
            me.vertices.add(1)
            ii = len(me.vertices) - 1
            me.vertices[ii].co = vs[i]
            
            me.attributes['{}index'.format(self.attribute_prefix)].data[ii].value = self.brush.instance_index
            
            nm = '{}normal'.format(self.attribute_prefix)
            me.attributes[nm].data[ii].vector = ns[i]
            
            e = r[i].to_euler('XYZ')
            nm = '{}rotation'.format(self.attribute_prefix)
            me.attributes[nm].data[ii].vector = e
            
            # align_z and align_y attributes
            v = Vector((0.0, 0.0, 1.0))
            v.rotate(e)
            nm = '{}align_z'.format(self.attribute_prefix)
            me.attributes[nm].data[ii].vector = v
            v = Vector((0.0, 1.0, 0.0))
            v.rotate(e)
            nm = '{}align_y'.format(self.attribute_prefix)
            me.attributes[nm].data[ii].vector = v
            
            nm = '{}scale'.format(self.attribute_prefix)
            me.attributes[nm].data[ii].vector = s[i]
            
            anm = '{}private_s_base'.format(self.attribute_prefix)
            att = me.attributes[anm].data
            att[ii].vector = self._private_s_base[i]
            
            anm = '{}private_s_random'.format(self.attribute_prefix)
            att = me.attributes[anm].data
            att[ii].vector = self._private_s_random[i]
            
            anm = '{}private_s_random_random'.format(self.attribute_prefix)
            att = me.attributes[anm].data
            att[ii].vector = self._private_s_random_random[i]
            
            anm = '{}private_s_random_type'.format(self.attribute_prefix)
            att = me.attributes[anm].data
            att[ii].value = self._private_s_random_type[i]
            
            anm = '{}private_s_change'.format(self.attribute_prefix)
            att = me.attributes[anm].data
            att[ii].vector = self._private_s_change[i]
            
            anm = '{}private_s_change_random'.format(self.attribute_prefix)
            att = me.attributes[anm].data
            att[ii].vector = self._private_s_change_random[i]
            
            # private attributes..
            me = self.target.data
            
            nm = '{}id'.format(self.attribute_prefix)
            me.attributes[nm].data[ii].value = ids[i]
            
            # rotation intermediates v2 ---------------------------------------------------
            anm = '{}private_r_align'.format(self.attribute_prefix)
            att = me.attributes[anm].data
            att[ii].value = self._private_r_align[i]
            
            anm = '{}private_r_up'.format(self.attribute_prefix)
            att = me.attributes[anm].data
            att[ii].value = self._private_r_up[i]
            
            anm = '{}private_r_base'.format(self.attribute_prefix)
            att = me.attributes[anm].data
            att[ii].vector = self._private_r_base[i]
            
            anm = '{}private_r_random'.format(self.attribute_prefix)
            att = me.attributes[anm].data
            att[ii].vector = self._private_r_random[i]
            
            anm = '{}private_r_random_random'.format(self.attribute_prefix)
            att = me.attributes[anm].data
            att[ii].vector = self._private_r_random_random[i]
            
            # rotation intermediates v2 ---------------------------------------------------
            
            # anm = '{}align_z'.format(self.attribute_prefix)
            # att = me.attributes[anm].data
            # att[ii].vector = self._align_z[i]
            #
            # anm = '{}align_y'.format(self.attribute_prefix)
            # att = me.attributes[anm].data
            # att[ii].vector = self._align_y[i]
        
        if(self.brush.align):
            indices = np.arange(len(vs), dtype=np.int, )
            indices = indices + _l
            
            d = np.array(self._mouse_3d_direction, dtype=np.float, )
            
            for i, ii in enumerate(indices):
                me.attributes['{}private_r_up'.format(self.attribute_prefix)].data[ii].value = 2
                me.attributes['{}private_r_up_vector'.format(self.attribute_prefix)].data[ii].vector = d
            
            self._regenerate_rotation_from_attributes(indices, )
    
    def _drawing(self, context, event, ):
        loc, nor, idx, dst = self._project(context, event, )
        if(loc is not None):
            self._loc = loc.copy()
            self._nor = nor.copy()
            
            r = self._generate(loc, nor, idx, dst, )
            if(r is not None):
                vs, ns = r
                vs, ns = self._global_to_surface_space(vs, ns, )
                self._store(vs, ns, )
                
                self.target.data.update()


class SCATTER5_OT_manual_eraser_brush(SCATTER5_OT_manual_base_brush, ):
    bl_idname = "scatter5.manual_eraser_brush"
    bl_label = translate("Eraser Brush")
    bl_description = translate("Eraser Brush")
    
    brush_type = "eraser_brush"
    icon = "W_ERASER"
    dat_icon = "SCATTER5_ERASER"
    
    modal_adjust_map = [
        {
            'enabled': True,
            'key': 'F',
            'oskey': False,
            'shift': False,
            'property': 'radius',
            'type': 'float',
            'change': 1 / 100,
            'change_pixels': 1,
            'text': 'Radius: {:.3f}',
            'cursor': 'RADIUS',
        },
        {
            'enabled': True,
            'key': 'F',
            'oskey': True,
            'shift': False,
            'property': 'affect_portion',
            'type': 'float',
            'change': 1 / 100,
            'change_pixels': 1,
            'text': 'Probability: {:.3f}',
            'cursor': 'STRENGTH',
        },
    ]
    
    def invoke(self, context, event, ):
        self.brush = context.scene.scatter5.manual.eraser_brush
        self.is_timer = True
        return super().invoke(context, event, )
    
    def _self_brush_modal_update(self, context, ):
        self.brush = context.scene.scatter5.manual.eraser_brush
    
    def _on_lmb_press(self, context, event, ):
        # NOTE: very important, if there was some drawing done, then undo without dropping tool, this is pointing somewhere invalid, each brush MUST set this again on each use AND before super()
        self.brush = context.scene.scatter5.manual.eraser_brush
        super()._on_lmb_press(context, event, )
        self._drawing(context, event, )
    
    def _on_lmb_move(self, context, event, ):
        super()._on_lmb_move(context, event, )
        
        if(self.brush.draw_on in ('MOUSEMOVE', 'BOTH', )):
            self._drawing(context, event, )
    
    def _on_lmb_release(self, context, event, ):
        super()._on_lmb_release(context, event, )
        
        # push to history..
        bpy.ops.ed.undo_push(message=self.bl_label, )
    
    def _generate(self, loc, nor, idx, dst, ):
        brush_radius = self.brush.radius
        if(self.brush.radius_pressure):
            brush_radius = brush_radius * self.pressure
        
        if(self.brush.falloff_distance >= brush_radius):
            self.brush.falloff_distance = self.brush.falloff_distance - self.epsilon
        
        me = self.target.data
        l = len(me.vertices)
        locations = np.zeros(l * 3, dtype=np.float, )
        me.vertices.foreach_get('co', locations)
        locations.shape = (-1, 3)
        vs = locations
        
        # vs, _ = self._to_global_space(vs, None, )
        loc, nor = self._global_to_surface_space(loc, nor, )
        
        radius = brush_radius
        radius = self._global_length_to_surface_space(radius)
        # print(radius)
        falloff_distance = self.brush.falloff_distance
        falloff_distance = self._global_length_to_surface_space(falloff_distance)
        # print(falloff_distance)
        
        if(len(vs) == 0):
            fvs = []
            fds = []
            fii = []
        else:
            # fvs, fds, fii = self._distance_range(vs, loc, brush_radius, )
            fvs, fds, fii = self._distance_range(vs, loc, radius, )
        
        if(len(fii) == 0):
            # FIXMENOT: this might cause exception later on
            return None
        
        indices = []
        ws = []
        for i, ii in enumerate(fii):
            indices.append(ii)
            
            d = fds[i]
            w = d / (radius - falloff_distance)
            if(w > 1.0):
                w = 1.0
            ws.append(w)
        
        ws = np.array(ws, dtype=np.float, )
        ws = 1.0 - ws
        
        # def easeInCubic(t, b, c, d, ):
        #     t /= d
        #     return c * t * t * t + b
        #
        # ws = easeInCubic(ws, 0.0, np.max(ws), np.max(ws))
        ws = ws / np.sum(ws)
        
        indices = np.array(indices, dtype=np.int, )
        # select only portion of points by weights..
        
        affect_portion = self.brush.affect_portion
        if(self.brush.affect_portion_pressure):
            affect_portion = self.pressure
        
        s = int(len(indices) * affect_portion)
        if(s == 0 and len(indices) > 0):
            s = 1
        try:
            # FIXME: fix bug, remove in production..
            choice = np.random.choice(indices, size=s, replace=False, p=ws, )
        except ValueError as e:
            self.report({'ERROR'}, "Eraser brush numpy.random.choice exception!")
            print('*' * 100)
            print('indices: ', indices)
            print('s: ', s)
            print('ws: ', ws)
            print('affect_portion: ', affect_portion)
            print('pressure: ', self.pressure)
            print('radius: ', brush_radius)
            print('falloff_distance: ', falloff_distance)
            print('fvs: ', fvs)
            print('fds: ', fds)
            print('fii: ', fii)
            print('*' * 100)
            choice = []
        
        self.mask = np.zeros(len(me.vertices), np.bool, )
        self.mask[choice] = True
        
        bm = bmesh.new()
        bm.from_mesh(me)
        rm = []
        bm.verts.ensure_lookup_table()
        for i, v in enumerate(bm.verts):
            if(self.mask[i]):
                rm.append(v)
        for v in rm:
            bm.verts.remove(v)
        bm.to_mesh(me)
        bm.free()


class SCATTER5_OT_manual_dilute_brush(SCATTER5_OT_manual_base_brush, ):
    bl_idname = "scatter5.manual_dilute_brush"
    bl_label = translate("Dilute Brush")
    bl_description = translate("Dilute Brush")
    
    brush_type = "dilute_brush"
    icon = "MATFLUID"
    dat_icon = "SCATTER5_DILLUTE"
    
    modal_adjust_map = [
        {
            'enabled': True,
            'key': 'F',
            'oskey': False,
            'shift': False,
            'property': 'radius',
            'type': 'float',
            'change': 1 / 100,
            'change_pixels': 1,
            'text': 'Radius: {:.3f}',
            'cursor': 'RADIUS',
        },
        {
            'enabled': True,
            'key': 'F',
            'oskey': True,
            'shift': False,
            'property': 'minimal_distance',
            'type': 'float',
            'change': 1 / 100,
            'change_pixels': 1,
            'text': 'Points Minimal Distance: {:.3f}',
            'cursor': 'LENGTH',
        },
    ]
    
    def invoke(self, context, event, ):
        self.brush = context.scene.scatter5.manual.dilute_brush
        self.is_timer = True
        return super().invoke(context, event, )
    
    def _self_brush_modal_update(self, context, ):
        self.brush = context.scene.scatter5.manual.dilute_brush
    
    def _on_lmb_press(self, context, event, ):
        # NOTE: very important, if there was some drawing done, then undo without dropping tool, this is pointing somewhere invalid, each brush MUST set this again on each use AND before super()
        self.brush = context.scene.scatter5.manual.dilute_brush
        super()._on_lmb_press(context, event, )
        self._drawing(context, event, )
    
    def _on_lmb_move(self, context, event, ):
        super()._on_lmb_move(context, event, )
        
        if(self.brush.draw_on in ('MOUSEMOVE', 'BOTH', )):
            self._drawing(context, event, )
    
    def _on_lmb_release(self, context, event, ):
        super()._on_lmb_release(context, event, )
        
        # push to history..
        bpy.ops.ed.undo_push(message=self.bl_label, )
    
    def _select_points(self, loc, nor, idx, dst, ):
        brush_radius = self.brush.radius
        if(self.brush.radius_pressure):
            brush_radius = brush_radius * self.pressure
        
        if(self.brush.falloff_distance >= brush_radius):
            self.brush.falloff_distance = self.brush.falloff_distance - self.epsilon
        
        me = self.target.data
        l = len(me.vertices)
        locations = np.zeros(l * 3, dtype=np.float, )
        me.vertices.foreach_get('co', locations)
        locations.shape = (-1, 3)
        vs = locations.copy()
        
        # vs, _ = self._to_global_space(vs, None, )
        loc, nor = self._global_to_surface_space(loc, nor, )
        
        radius = brush_radius
        radius = self._global_length_to_surface_space(radius)
        # print(radius)
        falloff_distance = self.brush.falloff_distance
        falloff_distance = self._global_length_to_surface_space(falloff_distance)
        # print(falloff_distance)
        
        if(len(vs) == 0):
            fvs = []
            fds = []
            fii = []
        else:
            # fvs, fds, fii = self._distance_range(vs, loc, brush_radius, )
            fvs, fds, fii = self._distance_range(vs, loc, radius, )
        
        if(len(fii) == 0):
            return locations, []
        
        indices = []
        ws = []
        for i, ii in enumerate(fii):
            indices.append(ii)
            
            d = fds[i]
            w = d / (radius - falloff_distance)
            if(w > 1.0):
                w = 1.0
            ws.append(w)
        
        ws = np.array(ws, dtype=np.float, )
        ws = 1.0 - ws
        ws = ws / np.sum(ws)
        
        indices = np.array(indices, dtype=np.int, )
        
        # select only portion of points by weights..
        
        affect_portion = self.brush.affect_portion
        if(self.brush.affect_portion_pressure):
            affect_portion = self.pressure
        
        s = int(len(indices) * affect_portion)
        if(s == 0 and len(indices) > 0):
            s = 1
        choice = np.random.choice(indices, size=s, replace=False, p=ws, )
        
        return locations, choice
    
    def _generate(self, loc, nor, idx, dst, ):
        brush_radius = self.brush.radius
        if(self.brush.radius_pressure):
            brush_radius = brush_radius * self.pressure
        
        me = self.target.data
        l = len(me.vertices)
        
        indices = []
        locations, choice = self._select_points(loc, nor, idx, dst, )
        imask = np.ones(l, dtype=np.bool, )
        
        choice_sorted = []
        if(len(choice) > 0 and len(locations) > 0):
            _loc, _nor = self._global_to_surface_space(loc, nor, )
            _radius = self._global_length_to_surface_space(brush_radius)
            fvs, fds, fii = self._distance_range(locations[choice], _loc, _radius, )
            asort = np.argsort(fds)
            choice_sorted = choice[asort]
            choice_sorted = choice_sorted[::-1]
        
        minimal_distance = self._global_length_to_surface_space(self.brush.minimal_distance)
        
        if(len(choice_sorted) > 0 and len(locations) > 0):
            for i, ii in enumerate(choice_sorted):
                fvs, fds, fii = self._distance_range(locations[imask], locations[ii], minimal_distance, )
                if(len(fii) > 1):
                    indices.append(ii)
                    imask[ii] = False
        
        mask = np.zeros(l, np.bool, )
        mask[indices] = True
        
        bm = bmesh.new()
        bm.from_mesh(me)
        rm = []
        bm.verts.ensure_lookup_table()
        for i, v in enumerate(bm.verts):
            if(mask[i]):
                rm.append(v)
        for v in rm:
            bm.verts.remove(v)
        bm.to_mesh(me)
        bm.free()


class SCATTER5_OT_manual_move_brush(SCATTER5_OT_manual_base_brush, ):
    bl_idname = "scatter5.manual_move_brush"
    bl_label = translate("Move Brush")
    bl_description = translate("Move Brush")
    
    brush_type = "move_brush"
    icon = "W_MOVE"
    dat_icon = "SCATTER5_MOVE"
    
    modal_adjust_map = [
        {
            'enabled': True,
            'key': 'F',
            'oskey': False,
            'shift': False,
            'property': 'radius',
            'type': 'float',
            'change': 1 / 100,
            'change_pixels': 1,
            'text': 'Radius: {:.3f}',
            'cursor': 'RADIUS',
        },
        {
            'enabled': True,
            'key': 'F',
            'oskey': True,
            'shift': False,
            'property': 'affect_portion',
            'type': 'float',
            'change': 1 / 100,
            'change_pixels': 1,
            'text': 'Probability: {:.3f}',
            'cursor': 'STRENGTH',
        },
    ]
    
    def invoke(self, context, event, ):
        self.brush = context.scene.scatter5.manual.move_brush
        r = super().invoke(context, event, )
        
        me = self.target.data
        l = len(me.vertices)
        
        vs = np.zeros(l * 3, dtype=np.float, )
        me.vertices.foreach_get('co', vs)
        vs.shape = (-1, 3)
        
        ns = np.zeros(l * 3, dtype=np.float, )
        me.attributes['{}normal'.format(self.attribute_prefix)].data.foreach_get('vector', ns)
        ns.shape = (-1, 3)
        
        # vs, ns = self._to_global_space(vs, ns, )
        vs, ns = self._surface_to_global_space(vs, ns, )
        self.locations = vs
        self.normals = ns
        
        self.mask = np.zeros(l, dtype=np.bool, )
        self.selected = np.zeros(l, dtype=np.bool, )
        self.is_selected = False
        
        return r
    
    def _self_brush_modal_update(self, context, ):
        self.brush = context.scene.scatter5.manual.move_brush
    
    def _on_lmb_press(self, context, event, ):
        # NOTE: very important, if there was some drawing done, then undo without dropping tool, this is pointing somewhere invalid, each brush MUST set this again on each use AND before super()
        self.brush = context.scene.scatter5.manual.move_brush
        super()._on_lmb_press(context, event, )
        self._drawing(context, event, )
    
    def _on_lmb_move(self, context, event, ):
        super()._on_lmb_move(context, event, )
        self._drawing(context, event, )
    
    def _on_lmb_release(self, context, event, ):
        super()._on_lmb_release(context, event, )
        # self.is_selected = False
        
        # reset..
        me = self.target.data
        l = len(me.vertices)
        self.mask = np.zeros(l, dtype=np.bool, )
        self.selected = np.zeros(l, dtype=np.bool, )
        self.is_selected = False
        
        # from space_view3d_point_cloud_visualizer.mechanist import PCVOverseer
        # pcv = PCVOverseer(self.target)
        # pcv.load(self.locations, self.normals, None, True)
        
        # push to history..
        bpy.ops.ed.undo_push(message=self.bl_label, )
    
    def _select_points(self, loc, nor, idx, dst, ):
        brush_radius = self.brush.radius
        if(self.brush.radius_pressure):
            brush_radius = brush_radius * self.pressure
        
        self.selected = np.zeros(len(self.locations), np.bool, )
        
        if(self.brush.falloff_distance >= brush_radius):
            self.brush.falloff_distance = self.brush.falloff_distance - self.epsilon
        
        vs = self.locations
        ns = self.normals
        
        if(len(vs) == 0):
            fvs = []
            fds = []
            fii = []
        else:
            fvs, fds, fii = self._distance_range(vs, loc, brush_radius, )
        
        if(len(fii) == 0):
            # FIXME: this might cause exception later on
            return False
        
        indices = []
        ws = []
        for i, ii in enumerate(fii):
            indices.append(ii)
            
            d = fds[i]
            w = d / (brush_radius - self.brush.falloff_distance)
            if(w > 1.0):
                w = 1.0
            ws.append(w)
        
        ws = np.array(ws, dtype=np.float, )
        ws = 1.0 - ws
        ws = ws / np.sum(ws)
        
        indices = np.array(indices, dtype=np.int, )
        # select only portion of points by weights..
        
        affect_portion = self.brush.affect_portion
        if(self.brush.affect_portion_pressure):
            affect_portion = self.pressure
        
        s = int(len(indices) * affect_portion)
        if(s == 0 and len(indices) > 0):
            s = 1
        
        # ok, now i have selected some points to move
        choice = np.random.choice(indices, size=s, replace=False, p=ws, )
        self.mask[choice] = True
        self.selected[choice] = True
        self.is_selected = True
        
        return True
    
    def _pick_up_points(self, loc, nor, idx, dst, ):
        vs = self.locations[self.selected]
        ns = self.normals[self.selected]
        
        # put on brush plane..
        l = len(vs)
        ds = np.zeros(l, dtype=np.float, )
        for i, v in enumerate(vs):
            d = mathutils.geometry.distance_point_to_plane(v, loc, nor, )
            ds[i] = d
        ds = ds * -1
        ds.shape = (-1, 1)
        vs2d = vs + (ns * ds)
        vs2d_local = vs2d - loc
        
        self.vs2d = vs2d
        self.vs2d_local = vs2d_local
        self.vs2d_depth = ds * -1
        self.vs2d_normal = nor
        self.ns2d = ns
    
    def _drop_points(self, loc, nor, idx, dst, ):
        vs = self.vs2d
        ns = self.ns2d
        
        # stick back to surface
        l = len(vs)
        ds = np.zeros(l, dtype=np.float, )
        for i, v in enumerate(vs):
            d = mathutils.geometry.distance_point_to_plane(v, loc, nor, )
            ds[i] = d
        ds = ds * -1
        ds.shape = (-1, 1)
        vs2d = vs + (ns * ds)
        
        # FIXME: on mesh edges it behaves really strange..
        
        # stick back to surface even more
        for i, v in enumerate(vs2d):
            l, n, ii, d = self.bvh.ray_cast(v, ns[i])
            l2, n2, ii2, d2 = self.bvh.ray_cast(v, ns[i] * -1)
            if(l is not None and l2 is not None):
                if(d > d2):
                    vs2d[i] = l2
                else:
                    vs2d[i] = l
            elif(l is not None and l2 is None):
                vs2d[i] = l
            elif(l is None and l2 is not None):
                vs2d[i] = l2
            else:
                # do not change because i did not hit anything..
                pass
                
                # # stick to closest point on mesh
                # l3, n3, ii3, d3 = self.bvh.find_nearest(v)
                # vs2d[i] = l3
        
        vs2d_local = vs2d - loc
        
        self.vs2d = vs2d
        self.vs2d_local = vs2d_local
    
    def _generate(self, loc, nor, idx, dst, ):
        ok = False
        if(not self.is_selected):
            ok = self._select_points(loc, nor, idx, dst, )
            if(not ok):
                return None
            self._pick_up_points(loc, nor, idx, dst, )
        
        # ok, now i've selected points, picked them up, now it's time to make them follow cursor..
        vs2d_local = self.vs2d_local.copy()
        self.vs2d = vs2d_local + loc
        
        # if(self.bs_props.use_align_surface):
        #     # FIXME: does not work at all.. number of hours spent so far: 2.5
        #     self.align_points(loc, nor, idx, dst, )
        
        # from space_view3d_point_cloud_visualizer.mechanist import PCVOverseer
        # pcv = PCVOverseer(self.target)
        # pcv.load(self.vs2d, None, None, True)
        
        self._drop_points(loc, nor, idx, dst, )
        self._store()
    
    def _store(self, ):
        self._ensure_attributes()
        
        me = self.target.data
        vs = self.vs2d
        # gvs, _ = self._global_to_surface_space(vs, None, )
        
        indices = np.arange(len(me.vertices), dtype=np.int, )
        indices = indices[self.selected]
        
        for i, ii in enumerate(indices):
            # me.vertices[ii].co = gvs[i]
            # self.locations[ii] = vs[i]
            
            # snap to surface even more...
            # TODO: to much snapping to surface.. shouldn't it be all on one spot?
            v = Vector(vs[i])
            loc, nor, idx, dst = self.bvh.find_nearest(v, )
            # iterpolate normal if on smooth surface
            nor = self._interpolate_smooth_face_normal(loc, nor, idx, )
            
            self.locations[ii] = loc
            
            loc, nor = self._global_to_surface_space(loc, nor, )
            
            me.vertices[ii].co = loc
            
            if(self.brush.use_align_surface):
                old_normal = Vector(me.attributes['{}normal'.format(self.attribute_prefix)].data[ii].vector)
                
                me.attributes['{}normal'.format(self.attribute_prefix)].data[ii].vector = nor
                
                q = self._rotation_to(old_normal, nor, )
                if(me.attributes['{}private_r_align'.format(self.attribute_prefix)].data[ii].value == 3):
                    a = Vector(me.attributes['{}private_r_align_vector'.format(self.attribute_prefix)].data[ii].vector)
                    a.rotate(q)
                    me.attributes['{}private_r_align_vector'.format(self.attribute_prefix)].data[ii].vector = a
                if(me.attributes['{}private_r_up'.format(self.attribute_prefix)].data[ii].value == 2):
                    a = Vector(me.attributes['{}private_r_up_vector'.format(self.attribute_prefix)].data[ii].vector)
                    a.rotate(q)
                    me.attributes['{}private_r_up_vector'.format(self.attribute_prefix)].data[ii].vector = a
        
        # from space_view3d_point_cloud_visualizer.mechanist import PCVOverseer
        # # o = self.target
        # o = self.surface
        # pcv = PCVOverseer(o)
        #
        # l = len(me.vertices)
        # _vs = np.zeros(l * 3, dtype=np.float, )
        # me.vertices.foreach_get('co', _vs, )
        # _vs.shape = (-1, 3, )
        # _ns = np.zeros(l * 3, dtype=np.float, )
        # me.attributes['{}normal'.format(self.attribute_prefix)].data.foreach_get('vector', _ns, )
        # _ns.shape = (-1, 3)
        #
        # pcv.load(_vs, _ns, None, True)
        # o.point_cloud_visualizer.display.vertex_normals = True
        # o.point_cloud_visualizer.display.vertex_normals_size = 1.0
        # o.point_cloud_visualizer.display.point_size = 6
        
        if(self.brush.use_align_surface):
            # # TODO: try to support overriden rotation
            # # reset override
            # for i, ii in enumerate(indices):
            #     me.attributes['{}private_r_change_override'.format(self.attribute_prefix)].data[ii].value = 0
            #     me.attributes['{}private_r_change'.format(self.attribute_prefix)].data[ii].vector = (0.0, 0.0, 0.0, )
            
            self._regenerate_rotation_from_attributes(indices, )


class SCATTER5_OT_manual_rotation_base_brush(SCATTER5_OT_manual_base_brush, ):
    bl_idname = "scatter5.manual_rotation_base_brush"
    bl_label = translate("Rotate Base Brush")
    bl_description = translate("Rotate Base Brush")
    
    # brush_type = "rotation_set_brush"
    # icon = "ORIENTATION_GIMBAL"
    # dat_icon = "SCATTER5_ROTATION_SET"

    def invoke(self, context, event, ):
        # self.brush = context.scene.scatter5.manual.rotation_set_brush
        # self.is_timer = True
        r = super().invoke(context, event, )
        return r
    
    def _self_brush_modal_update(self, context, ):
        # self.brush = context.scene.scatter5.manual.rotation_set_brush
        pass
    
    def _on_lmb_press(self, context, event, ):
        # NOTE: very important, if there was some drawing done, then undo without dropping tool, this is pointing somewhere invalid, each brush MUST set this again on each use AND before super()
        # self.brush = context.scene.scatter5.manual.rotation_set_brush
        super()._on_lmb_press(context, event, )
        self._drawing(context, event, )
    
    def _on_lmb_move(self, context, event, ):
        super()._on_lmb_move(context, event, )
        if(self.brush.draw_on in ('MOUSEMOVE', 'BOTH', )):
            self._drawing(context, event, )
    
    def _on_lmb_release(self, context, event, ):
        super()._on_lmb_release(context, event, )
        
        # push to history..
        bpy.ops.ed.undo_push(message=self.bl_label, )
    
    def _select_points(self, loc, nor, idx, dst, ):
        brush_radius = self.brush.radius
        if(self.brush.radius_pressure):
            brush_radius = brush_radius * self.pressure
        
        self.selected = np.zeros(len(self.locations), np.bool, )
        
        if(self.brush.falloff_distance >= brush_radius):
            self.brush.falloff_distance = self.brush.falloff_distance - self.epsilon
        
        vs = self.locations
        ns = self.normals
        
        if(len(vs) == 0):
            fvs = []
            fds = []
            fii = []
        else:
            fvs, fds, fii = self._distance_range(vs, loc, brush_radius, )
        
        if(len(fii) == 0):
            # FIXME: this might cause exception later on
            return False
        
        indices = []
        ws = []
        for i, ii in enumerate(fii):
            indices.append(ii)
            
            d = fds[i]
            w = d / (brush_radius - self.brush.falloff_distance)
            if(w > 1.0):
                w = 1.0
            ws.append(w)
        
        ws = np.array(ws, dtype=np.float, )
        ws = 1.0 - ws
        ws = ws / np.sum(ws)
        
        indices = np.array(indices, dtype=np.int, )
        # select only portion of points by weights..
        
        affect_portion = self.brush.affect_portion
        if(self.brush.affect_portion_pressure):
            affect_portion = self.pressure
        
        s = int(len(indices) * affect_portion)
        if(s == 0 and len(indices) > 0):
            s = 1
        
        # ok, now i have selected some points to move
        choice = np.random.choice(indices, size=s, replace=False, p=ws, )
        self.selected[choice] = True
        
        return True
    
    def _generate(self, loc, nor, idx, dst, ):
        self._select_points(loc, nor, idx, dst, )
        # self._rotate()
        # self._store()
        self._execute()
    
    def _execute(self, ):
        # wrap in another function to be able to call brush from operator, just set selected points, and run..
        self._ensure_attributes()
        indices = np.arange(len(self.target.data.vertices), dtype=np.int, )
        indices = indices[self.selected]
        if(len(indices)):
            self._modify(indices, )
            self._regenerate_rotation_from_attributes(indices, )
    
    def _modify(self, indices, ):
        # override in subclasses..
        pass
    
    def _collect(self, context, ):
        me = self.target.data
        l = len(me.vertices)
        
        vs = np.zeros(l * 3, dtype=np.float, )
        me.vertices.foreach_get('co', vs)
        vs.shape = (-1, 3)
        
        ns = np.zeros(l * 3, dtype=np.float, )
        me.attributes['{}normal'.format(self.attribute_prefix)].data.foreach_get('vector', ns)
        ns.shape = (-1, 3)
        
        vs, ns = self._surface_to_global_space(vs, ns, )
        self.locations = vs
        self.normals = ns
        
        rs = np.zeros(l * 3, dtype=np.float, )
        me.attributes['{}rotation'.format(self.attribute_prefix)].data.foreach_get('vector', rs)
        rs.shape = (-1, 3)
        self.rotations = rs
        
        # p_locs = np.zeros(l * 3, dtype=np.float, )
        # me.attributes['{}private_loc'.format(self.attribute_prefix)].data.foreach_get('vector', p_locs)
        # p_locs.shape = (-1, 3)
        # self.p_locs = p_locs
        
        # p_nors = np.zeros(l * 3, dtype=np.float, )
        # me.attributes['{}private_nor'.format(self.attribute_prefix)].data.foreach_get('vector', p_nors)
        # p_nors.shape = (-1, 3)
        # self.p_nors = p_nors
        
        # m = self.surface.matrix_world
        # _, _, s = m.decompose()
        # a = np.array(s.to_tuple(), dtype=np.float, )
        # self.scales = self.scales * a
        
        self.selected = np.zeros(l, dtype=np.bool, )


class SCATTER5_OT_manual_rotation_brush(SCATTER5_OT_manual_rotation_base_brush, ):
    bl_idname = "scatter5.manual_rotation_brush"
    bl_label = translate("Rotation Settings Brush")
    bl_description = translate("Rotation Settings Brush")
    
    brush_type = "rotation_brush"
    icon = "PREFERENCES"
    dat_icon = "SCATTER5_ROTATION_SETTINGS"
    
    modal_adjust_map = [
        {
            'enabled': True,
            'key': 'F',
            'oskey': False,
            'shift': False,
            'property': 'radius',
            'type': 'float',
            'change': 1 / 100,
            'change_pixels': 1,
            'text': 'Radius: {:.3f}',
            'cursor': 'RADIUS',
        },
    ]
    
    def invoke(self, context, event, ):
        self.brush = context.scene.scatter5.manual.rotation_brush
        self.is_timer = True
        r = super().invoke(context, event, )
        return r
    
    def _self_brush_modal_update(self, context, ):
        self.brush = context.scene.scatter5.manual.rotation_brush
    
    def _on_lmb_press(self, context, event, ):
        # NOTE: very important, if there was some drawing done, then undo without dropping tool, this is pointing somewhere invalid, each brush MUST set this again on each use AND before super()
        self.brush = context.scene.scatter5.manual.rotation_brush
        super()._on_lmb_press(context, event, )
        # self._drawing(context, event, )
    
    def _modify(self, indices, ):
        me = self.target.data
        for i in indices:
            if(self.brush.use_rotation_align):
                a = 0
                if(self.brush.rotation_align == 'LOCAL_Z_AXIS'):
                    a = 1
                elif(self.brush.rotation_align == 'GLOBAL_Z_AXIS'):
                    a = 2
                me.attributes['{}private_r_align'.format(self.attribute_prefix)].data[i].value = a
                u = 0
                if(self.brush.rotation_up == 'GLOBAL_Y_AXIS'):
                    u = 1
                me.attributes['{}private_r_up'.format(self.attribute_prefix)].data[i].value = u
                
                # reset custom vectors as well so brushes using that start from scratch..
                me.attributes['{}private_r_align_vector'.format(self.attribute_prefix)].data[i].vector = (0.0, 0.0, 0.0, )
                me.attributes['{}private_r_up_vector'.format(self.attribute_prefix)].data[i].vector = (0.0, 0.0, 0.0, )
                me.attributes['{}private_z_original'.format(self.attribute_prefix)].data[i].vector = (0.0, 0.0, 0.0, )
                # and random numbers as well.. they will (read: if i don't forget, they will) be regenerated at first brush run..
                me.attributes['{}private_z_random'.format(self.attribute_prefix)].data[i].vector = (0.0, 0.0, 0.0, )
            
            if(self.brush.use_rotation_base):
                me.attributes['{}private_r_base'.format(self.attribute_prefix)].data[i].vector = self.brush.rotation_base
            
            if(self.brush.use_rotation_random):
                me.attributes['{}private_r_random'.format(self.attribute_prefix)].data[i].vector = self.brush.rotation_random
                me.attributes['{}private_r_random_random'.format(self.attribute_prefix)].data[i].vector = (random.random(), random.random(), random.random(), )


class SCATTER5_OT_manual_comb_brush(SCATTER5_OT_manual_rotation_base_brush, ):
    bl_idname = "scatter5.manual_comb_brush"
    bl_label = translate("Tangent Alignment Brush")
    bl_description = translate("Tangent Alignment Brush")
    
    brush_type = "comb_brush"
    icon = "W_ARROW_TANGENT"
    dat_icon = "SCATTER5_ROTATION_ALIGN"
    
    modal_adjust_map = [
        {
            'enabled': True,
            'key': 'F',
            'oskey': False,
            'shift': False,
            'property': 'radius',
            'type': 'float',
            'change': 1 / 100,
            'change_pixels': 1,
            'text': 'Radius: {:.3f}',
            'cursor': 'RADIUS',
        },
        {
            'enabled': True,
            'key': 'F',
            'oskey': True,
            'shift': False,
            'property': 'strength',
            'type': 'float',
            'change': 1 / 100,
            'change_pixels': 1,
            'text': 'Srength: {:.3f}',
            'cursor': 'STRENGTH',
        },
    ]
    
    def invoke(self, context, event, ):
        self.brush = context.scene.scatter5.manual.comb_brush
        self.is_timer = True
        
        self.path = []
        self.direction = []
        
        r = super().invoke(context, event, )
        return r
    
    def _self_brush_modal_update(self, context, ):
        self.brush = context.scene.scatter5.manual.comb_brush
    
    def _on_lmb_press(self, context, event, ):
        # NOTE: very important, if there was some drawing done, then undo without dropping tool, this is pointing somewhere invalid, each brush MUST set this again on each use AND before super()
        self.brush = context.scene.scatter5.manual.comb_brush
        super()._on_lmb_press(context, event, )
        # self._drawing(context, event, )
    
    def _on_lmb_release(self, context, event, ):
        super()._on_lmb_release(context, event, )
        
        # NOTE: history is handled in rotation base brush
        # # push to history..
        # bpy.ops.ed.undo_push(message=self.bl_label, )
        
        self.path = []
        self.direction = []
    
    def _modify(self, indices, ):
        if(self.brush.mode == 'COMB'):
            self._modify_comb(indices, )
        elif(self.brush.mode == 'SPIN'):
            self._modify_spin(indices, )
    
    def _get_axis(self, i, ):
        me = self.target.data
        axis = Vector()
        if(self.brush.axis == 'SURFACE_NORMAL'):
            _, axis, _, _ = self.bvh.find_nearest(self.locations[i])
        elif(self.brush.axis == 'LOCAL_Z_AXIS'):
            _, axis = self._surface_to_global_space(Vector((0.0, 0.0, 0.0, )), Vector((0.0, 0.0, 1.0, )), )
        elif(self.brush.axis == 'GLOBAL_Z_AXIS'):
            axis = Vector((0.0, 0.0, 1.0, ))
        elif(self.brush.axis == 'PARTICLE_Z'):
            axis = Vector((0.0, 0.0, 1.0, ))
            e = Euler(me.attributes['{}rotation'.format(self.attribute_prefix)].data[i].vector)
            axis.rotate(e)
            # if(self.space == 'GLOBAL'):
            #     pass
            # else:
            #     # m = self.surface.matrix_world
            #     # axis = m @ axis
            #
            #     # NOTE: only rotate axis, no need for anything else..
            #     _, r, _ = self.surface.matrix_world.decompose()
            #     axis.rotate(r)
            
            # NOTE: only rotate axis, no need for anything else..
            _, r, _ = self.surface.matrix_world.decompose()
            axis.rotate(r)
        
        return axis
    
    def _calc_rotation_components_from_attributes(self, i, ):
        me = self.target.data
        # rotation = np.array(me.attributes['{}rotation'.format(self.attribute_prefix)].data[i].vector, dtype=np.float, )
        
        vec, nor = self._surface_to_global_space(me.vertices[i].co, me.attributes['{}normal'.format(self.attribute_prefix)].data[i].vector, )
        _, nor_1 = self._surface_to_global_space(Vector((0.0, 0.0, 0.0, )), Vector((0.0, 0.0, 1.0, )), )
        
        private_r_align = me.attributes['{}private_r_align'.format(self.attribute_prefix)].data[i].value
        if(private_r_align == 0):
            nor = Vector(nor)
        elif(private_r_align == 1):
            nor = nor_1.copy()
        elif(private_r_align == 2):
            nor = Vector((0.0, 0.0, 1.0, ))
        elif(private_r_align == 3):
            nor = Vector(me.attributes['{}private_r_align_vector'.format(self.attribute_prefix)].data[i].vector)
        
        locy_1 = Vector((0.0, 1.0, 0.0, ))
        mwi_1 = self.surface.matrix_world.copy()
        _, cr_1, _ = mwi_1.decompose()
        locy_1.rotate(cr_1)
        
        private_r_up = me.attributes['{}private_r_up'.format(self.attribute_prefix)].data[i].value
        if(private_r_up == 0):
            aq = self._direction_to_rotation_with_m3x3(nor, )
        elif(private_r_up == 1):
            aq = self._direction_to_rotation_with_m3x3(nor, locy_1, )
        elif(private_r_up == 2):
            aq = self._direction_to_rotation_with_m3x3(nor, Vector(me.attributes['{}private_r_up_vector'.format(self.attribute_prefix)].data[i].vector), )
        
        private_r_random = np.array(me.attributes['{}private_r_random'.format(self.attribute_prefix)].data[i].vector, dtype=np.float, )
        private_r_random_random = np.array(me.attributes['{}private_r_random_random'.format(self.attribute_prefix)].data[i].vector, dtype=np.float, )
        err = Euler(private_r_random * private_r_random_random)
        
        mwi = self.surface.matrix_world.inverted()
        _, cr, _ = mwi.decompose()
        
        eb = Euler(me.attributes['{}private_r_base'.format(self.attribute_prefix)].data[i].vector)
        
        # q = Quaternion()
        # q.rotate(eb)
        # q.rotate(err)
        # q.rotate(aq)
        # q.rotate(cr)
        #
        # e = q.to_euler('XYZ')
        # return eb, err, aq, cr, e
        return eb, err, aq, cr
    
    def _modify_comb(self, indices, ):
        # # DEBUG
        # _vs = []
        # _ns = []
        # # DEBUG
        
        me = self.target.data
        
        if(self.brush.direction_smoothing_steps > 0):
            ns = []
            for n in self.direction:
                ns.append(n.to_tuple())
            a = np.array(ns, dtype=np.float, )
            l = self.brush.direction_smoothing_steps
            if(len(a) > l):
                a = a[-l:]
            # # weighted. does not look that well i thought..
            # w = np.arange(len(a))
            # w = (w - np.min(w)) / (np.max(w) - np.min(w))
            # w = w / np.sum(w)
            # dx = np.average(a[:, 0], weights=w, )
            # dy = np.average(a[:, 1], weights=w, )
            # dz = np.average(a[:, 2], weights=w, )
            dx = np.average(a[:, 0], )
            dy = np.average(a[:, 1], )
            dz = np.average(a[:, 2], )
            d = Vector((dx, dy, dz))
            d.normalize()
        else:
            d = Vector(self.direction[-1]).copy()
        
        for i in indices:
            axis = self._get_axis(i, )
            
            py = Vector((0.0, 1.0, 0.0, ))
            e = Euler(me.attributes['{}rotation'.format(self.attribute_prefix)].data[i].vector)
            py.rotate(e)
            # to world space
            
            # # DEBUG
            # _vs.append(self.locations[i])
            # _ns.append(py.to_tuple())
            # # DEBUG
            
            # # NOTE: what was that? why i put it here?
            # py = self.surface.matrix_world @ py
            
            # # DEBUG
            # _vs.append(self.locations[i])
            # _ns.append(py.to_tuple())
            # # DEBUG
            
            def project_on_plane(p, n, q, ):
                return q - Vector(q - p).dot(n) * n
            
            pyp = project_on_plane(Vector((0.0, 0.0, 0.0, )), axis, py, )
            dp = project_on_plane(Vector((0.0, 0.0, 0.0, )), axis, d, )
            
            angle = Vector((dp.x, dp.y, )).angle_signed(Vector((pyp.x, pyp.y, )), 0.0, )
            angle = angle * self.brush.strength
            
            if(self.brush.strength_random):
                r = np.random.rand(1, )
                rr = self.brush.strength_random_range
                r = rr[0] + (rr[1] - rr[0]) * r
                angle = angle * r
            
            if(self.brush.strength_pressure):
                angle = angle * self.pressure
            
            _eb, _er, _qa, _cr = self._calc_rotation_components_from_attributes(i, )
            _q = Quaternion()
            _q.rotate(_qa)
            _q.rotate(_cr)
            _m = _q.to_matrix().to_4x4()
            e = _m
            e = self.surface.matrix_world @ e
            
            q = Quaternion(axis, angle, ).to_matrix().to_4x4()
            m = q @ e
            
            # # DEBUG
            # _vs.append(self.locations[i])
            # _ns.append(axis)
            # # DEBUG
            
            _, v, _ = m.decompose()
            v = v.to_euler('XYZ')
            
            z = Vector((0.0, 0.0, 1.0, ))
            z.rotate(v)
            y = Vector((0.0, 1.0, 0.0, ))
            y.rotate(v)
            me.attributes['{}private_r_align'.format(self.attribute_prefix)].data[i].value = 3
            me.attributes['{}private_r_align_vector'.format(self.attribute_prefix)].data[i].vector = z
            me.attributes['{}private_r_up'.format(self.attribute_prefix)].data[i].value = 2
            me.attributes['{}private_r_up_vector'.format(self.attribute_prefix)].data[i].vector = y
        
        # # DEBUG
        # debug.points(self.target, _vs, _ns, )
        # # DEBUG
    
    def _modify_spin(self, indices, ):
        # # # DEBUG
        # _vs = []
        # _ns = []
        # # # DEBUG
        
        me = self.target.data
        d = Vector(self.direction[-1]).copy()
        
        # NOTE: this is not for strictly unique number per particle, but having seed per particles really slow it down.. so this result in stable rotation increment per instance at current state, if some are removed, than it changes, but while in brush it will get the same random number per instance..
        if(self.brush.speed_random):
            rng = np.random.default_rng(seed=0, )
            l = len(me.vertices)
            rns = rng.random((l, 1))
            rr = self.brush.speed_random_range
            rns = rr[0] + (rr[1] - rr[0]) * rns
        
        for i in indices:
            axis = self._get_axis(i, )
            
            # # DEBUG
            # _vs.append(self.locations[i])
            # # _ns.append(m @ Vector((0,0,1)))
            # _ns.append(axis)
            # # _ns.append(py)
            # # DEBUG
            
            angle = self.brush.speed
            if(self.brush.speed_random):
                u = me.attributes['{}id'.format(self.attribute_prefix)].data[i].value
                angle = angle * rns[i]
            
            if(self.brush.speed_pressure):
                angle = angle * self.pressure
            
            _eb, _er, _qa, _cr = self._calc_rotation_components_from_attributes(i, )
            _q = Quaternion()
            _q.rotate(_qa)
            _q.rotate(_cr)
            _m = _q.to_matrix().to_4x4()
            e = _m
            
            e = self.surface.matrix_world @ e
            
            q = Quaternion(axis, angle, ).to_matrix().to_4x4()
            m = q @ e
            _, v, _ = m.decompose()
            
            z = Vector((0.0, 0.0, 1.0, ))
            z = v @ z
            y = Vector((0.0, 1.0, 0.0, ))
            y = v @ y
            me.attributes['{}private_r_align'.format(self.attribute_prefix)].data[i].value = 3
            me.attributes['{}private_r_align_vector'.format(self.attribute_prefix)].data[i].vector = z
            me.attributes['{}private_r_up'.format(self.attribute_prefix)].data[i].value = 2
            me.attributes['{}private_r_up_vector'.format(self.attribute_prefix)].data[i].vector = y
            
            # # DEBUG
            # _vs.append(self.locations[i])
            # _vs.append(self.locations[i])
            # _vs.append(self.locations[i])
            # _ns.append(axis)
            # _ns.append(z)
            # _ns.append(y)
            # # DEBUG
        
        # # # DEBUG
        # debug.points(self.target, _vs, _ns, )
        # # # DEBUG
    
    def _drawing(self, context, event, ):
        loc, nor, idx, dst = self._project(context, event, )
        if(loc is not None):
            
            # store brush path and direction
            self.path.append(loc.copy())
            if(len(self.direction) == 0):
                self.direction.append(Vector((0.0, 0.0, 0.0, )))
            else:
                # get previous location
                a = self.path[-2]
                b = loc
                # and get direction
                n = b - a
                n.normalize()
                self.direction.append(n)
            
            # for each draw event, those two should be the same for all generated points, so i can keep this on class.. might get easier in future to access that
            self._loc = loc.copy()
            self._nor = nor.copy()
            
            if(len(self.path) > 1):
                # if it is first point of path, skip the rest of brush, because i can't estimate direction
                r = self._generate(loc, nor, idx, dst, )
            
            self.target.data.update()
    
    # # DEBUG
    '''
    def modal(self, context, event, ):
        r = super().modal(context, event, )
        
        if(event.type == 'MOUSEMOVE' and len(self.path)):
            vs = [p.to_tuple() for p in self.path]
            ns = []
            for n in self.direction:
                n.length = 0.1
                ns.append(n.to_tuple())
            
            a = np.array(ns, dtype=np.float, )
            l = 10
            if(len(a) > l):
                a = a[-l:]
            
            # w = np.arange(len(a))
            # w = (w - np.min(w)) / (np.max(w) - np.min(w))
            # w = w / np.sum(w)
            # dx = np.average(a[:, 0], weights=w, )
            # dy = np.average(a[:, 1], weights=w, )
            # dz = np.average(a[:, 2], weights=w, )
            dx = np.average(a[:, 0], )
            dy = np.average(a[:, 1], )
            dz = np.average(a[:, 2], )
            
            d = Vector((dx, dy, dz))
            d.normalize()
            
            cs = [(1.0, 0.0, 0.0, 1.0) for i in range(len(vs))]
            
            vs.append(self.path[-1].to_tuple())
            ns.append(d.to_tuple())
            cs.append((1.0, 1.0, 0.0, 1.0))
            
            debug.points(self.surface, vs, ns, cs)
        
        return r
    '''
    # # DEBUG


class SCATTER5_OT_manual_scale_base_brush(SCATTER5_OT_manual_base_brush, ):
    bl_idname = "scatter5.manual_scale_base_brush"
    bl_label = translate("Scale Brush")
    bl_description = translate("Scale Brush")
    
    # brush_type = "scale_set_brush"
    # icon = "OBJECT_ORIGIN"
    # dat_icon = "SCATTER5_SCALE_SET"
    
    def invoke(self, context, event, ):
        # self.brush = context.scene.scatter5.manual.scale_base_brush
        # self.is_timer = True
        r = super().invoke(context, event, )
        return r
    
    def _self_brush_modal_update(self, context, ):
        # self.brush = context.scene.scatter5.manual.scale_base_brush
        pass
    
    def _on_lmb_press(self, context, event, ):
        # # NOTE: very important, if there was some drawing done, then undo without dropping tool, this is pointing somewhere invalid, each brush MUST set this again on each use AND before super()
        # self.brush = context.scene.scatter5.manual.scale_base_brush
        super()._on_lmb_press(context, event, )
        self._drawing(context, event, )
    
    def _on_lmb_move(self, context, event, ):
        super()._on_lmb_move(context, event, )
        if(self.brush.draw_on in ('MOUSEMOVE', 'BOTH', )):
            self._drawing(context, event, )
    
    def _on_lmb_release(self, context, event, ):
        super()._on_lmb_release(context, event, )
        
        # push to history..
        bpy.ops.ed.undo_push(message=self.bl_label, )
    
    def _select_points(self, loc, nor, idx, dst, ):
        brush_radius = self.brush.radius
        if(self.brush.radius_pressure):
            brush_radius = brush_radius * self.pressure
        
        self.selected = np.zeros(len(self.locations), np.bool, )
        
        if(self.brush.falloff_distance >= brush_radius):
            self.brush.falloff_distance = self.brush.falloff_distance - self.epsilon
        
        vs = self.locations
        ns = self.normals
        
        if(len(vs) == 0):
            fvs = []
            fds = []
            fii = []
        else:
            fvs, fds, fii = self._distance_range(vs, loc, brush_radius, )
        
        if(len(fii) == 0):
            # FIXME: this might cause exception later on
            return False
        
        indices = []
        ws = []
        for i, ii in enumerate(fii):
            indices.append(ii)
            
            d = fds[i]
            w = d / (brush_radius - self.brush.falloff_distance)
            if(w > 1.0):
                w = 1.0
            ws.append(w)
        
        ws = np.array(ws, dtype=np.float, )
        ws = 1.0 - ws
        ws = ws / np.sum(ws)
        
        indices = np.array(indices, dtype=np.int, )
        # select only portion of points by weights..
        
        affect_portion = self.brush.affect_portion
        if(self.brush.affect_portion_pressure):
            affect_portion = self.pressure
        
        s = int(len(indices) * affect_portion)
        if(s == 0 and len(indices) > 0):
            s = 1
        
        # ok, now i have selected some points to move
        choice = np.random.choice(indices, size=s, replace=False, p=ws, )
        self.selected[choice] = True
        
        return True
    
    def _collect(self, context, ):
        me = self.target.data
        l = len(me.vertices)
        
        vs = np.zeros(l * 3, dtype=np.float, )
        me.vertices.foreach_get('co', vs)
        vs.shape = (-1, 3)
        
        ns = np.zeros(l * 3, dtype=np.float, )
        me.attributes['{}normal'.format(self.attribute_prefix)].data.foreach_get('vector', ns)
        ns.shape = (-1, 3)
        
        vs, ns = self._surface_to_global_space(vs, ns, )
        self.locations = vs
        self.normals = ns
        
        rs = np.zeros(l * 3, dtype=np.float, )
        me.attributes['{}scale'.format(self.attribute_prefix)].data.foreach_get('vector', rs)
        rs.shape = (-1, 3)
        self.scales = rs
        
        m = self.surface.matrix_world
        _, _, s = m.decompose()
        a = np.array(s.to_tuple(), dtype=np.float, )
        self.scales = self.scales * a
        
        self.selected = np.zeros(l, dtype=np.bool, )
    
    def _generate(self, loc, nor, idx, dst, ):
        self._select_points(loc, nor, idx, dst, )
        self._execute()
    
    def _execute(self, ):
        # wrap in another function to be able to call brush from operator, just set selected points, and run..
        self._ensure_attributes()
        indices = np.arange(len(self.target.data.vertices), dtype=np.int, )
        indices = indices[self.selected]
        if(len(indices)):
            self._modify(indices, )
            self._regenerate_scale_from_attributes(indices, )
    
    def _modify(self, indices, ):
        # override in subclasses..
        pass


class SCATTER5_OT_manual_scale_brush(SCATTER5_OT_manual_scale_base_brush, ):
    bl_idname = "scatter5.manual_scale_brush"
    bl_label = translate("Scale Settings Brush")
    bl_description = translate("Scale Settings Brush")
    
    brush_type = "scale_brush"
    icon = "PREFERENCES"
    dat_icon = "SCATTER5_SCALE_SETTINGS"
    
    modal_adjust_map = [
        {
            'enabled': True,
            'key': 'F',
            'oskey': False,
            'shift': False,
            'property': 'radius',
            'type': 'float',
            'change': 1 / 100,
            'change_pixels': 1,
            'text': 'Radius: {:.3f}',
            'cursor': 'RADIUS',
        },
        {
            'enabled': True,
            'key': 'F',
            'oskey': True,
            'shift': False,
            'property': 'scale_default',
            'type': 'vector',
            'change': 1 / 1000,
            'change_pixels': 1,
            'text': 'Default Scale: ({:.3f}, {:.3f}, {:.3f})',
            'cursor': 'NONE',
        },
    ]
    
    def invoke(self, context, event, ):
        self.brush = context.scene.scatter5.manual.scale_brush
        self.is_timer = True
        r = super().invoke(context, event, )
        return r
    
    def _self_brush_modal_update(self, context, ):
        self.brush = context.scene.scatter5.manual.scale_brush
    
    def _on_lmb_press(self, context, event, ):
        # NOTE: very important, if there was some drawing done, then undo without dropping tool, this is pointing somewhere invalid, each brush MUST set this again on each use AND before super()
        self.brush = context.scene.scatter5.manual.scale_brush
        super()._on_lmb_press(context, event, )
        # self._drawing(context, event, )
    
    def _modify(self, indices, ):
        me = self.target.data
        
        r = np.array(self.brush.scale_random_factor, dtype=np.float, )
        if(self.brush.scale_random_type == 'UNIFORM'):
            t = 0
        elif(self.brush.scale_random_type == 'VECTORIAL'):
            t = 1
        
        for i in indices:
            if(self.brush.use_scale_default):
                me.attributes['{}private_s_base'.format(self.attribute_prefix)].data[i].vector = self.brush.scale_default
                me.attributes['{}private_s_change'.format(self.attribute_prefix)].data[i].vector = (0.0, 0.0, 0.0, )
                
                # regenerate also random numbers..
                me.attributes['{}private_s_change_random'.format(self.attribute_prefix)].data[i].vector = np.random.rand(3)
                
            if(self.brush.use_scale_random_factor):
                rr = np.random.rand(3)
                me.attributes['{}private_s_random'.format(self.attribute_prefix)].data[i].vector = r
                me.attributes['{}private_s_random_random'.format(self.attribute_prefix)].data[i].vector = rr
                me.attributes['{}private_s_random_type'.format(self.attribute_prefix)].data[i].value = t


class SCATTER5_OT_manual_scale_grow_shrink_brush(SCATTER5_OT_manual_scale_base_brush, ):
    bl_idname = "scatter5.manual_scale_grow_shrink_brush"
    bl_label = translate("Scale Grow/Shrink Brush")
    bl_description = translate("Scale Grow/Shrink Brush")
    
    brush_type = "scale_grow_shrink_brush"
    icon = "W_SCALE_GROW"
    dat_icon = "SCATTER5_SCALE_GROW"
    
    modal_adjust_map = [
        {
            'enabled': True,
            'key': 'F',
            'oskey': False,
            'shift': False,
            'property': 'radius',
            'type': 'float',
            'change': 1 / 100,
            'change_pixels': 1,
            'text': 'Radius: {:.3f}',
            'cursor': 'RADIUS',
        },
        {
            'enabled': True,
            'key': 'F',
            'oskey': True,
            'shift': False,
            'property': 'change',
            'type': 'vector',
            'change': 1 / 1000,
            'change_pixels': 1,
            'text': 'Value: ({:.3f}, {:.3f}, {:.3f})',
            'cursor': 'NONE',
        },
    ]
    
    help_message_extra = "Invert: CTRL+LMB"
    
    def invoke(self, context, event, ):
        self.brush = context.scene.scatter5.manual.scale_grow_shrink_brush
        self.is_timer = True
        r = super().invoke(context, event, )
        return r
    
    def _self_brush_modal_update(self, context, ):
        self.brush = context.scene.scatter5.manual.scale_grow_shrink_brush
    
    def _on_lmb_press(self, context, event, ):
        # NOTE: very important, if there was some drawing done, then undo without dropping tool, this is pointing somewhere invalid, each brush MUST set this again on each use AND before super()
        self.brush = context.scene.scatter5.manual.scale_grow_shrink_brush
        super()._on_lmb_press(context, event, )
        # self._drawing(context, event, )
    
    def _modify(self, indices, ):
        me = self.target.data
        
        # change = np.array(self.brush.change, dtype=np.float, )
        #
        # if(self.brush.change_pressure):
        #     change = change * self.pressure
        # if(self.brush.change_mode == 'SUBTRACT'):
        #     change = -change
        #
        # if(self.ctrl):
        #     # if CTRL is pressed, invert mode
        #     change = -change
        
        for i in indices:
            change = np.array(self.brush.change, dtype=np.float, )
        
            if(self.brush.change_pressure):
                change = change * self.pressure
            if(self.brush.change_mode == 'SUBTRACT'):
                change = -change
        
            if(self.ctrl):
                # if CTRL is pressed, invert mode
                change = -change
            
            if(self.brush.use_change_random):
                rnd = np.array(me.attributes['{}private_s_change_random'.format(self.attribute_prefix)].data[i].vector, dtype=np.float, )
                rr = self.brush.change_random_range
                rv = rr[0] + (rr[1] - rr[0]) * rnd[1]
                change = change * rv
            
            if(self.brush.use_limits):
                s = np.array(me.attributes['{}private_s_base'.format(self.attribute_prefix)].data[i].vector, dtype=np.float, )
                ch = np.array(me.attributes['{}private_s_change'.format(self.attribute_prefix)].data[i].vector, dtype=np.float, )
                r = change.copy()
                minv, maxv = self.brush.limits
                
                x = s[0] + ch[0] + r[0]
                if(x >= maxv):
                    r[0] = maxv - s[0]
                elif(x <= minv):
                    r[0] = -(s[0] - minv)
                else:
                    r[0] = ch[0] + r[0]
                
                y = s[1] + ch[1] + r[1]
                if(y >= maxv):
                    r[1] = maxv - s[1]
                elif(y <= minv):
                    r[1] = -(s[1] - minv)
                else:
                    r[1] = ch[1] + r[1]
                
                z = s[2] + ch[2] + r[2]
                if(z >= maxv):
                    r[2] = maxv - s[2]
                elif(z <= minv):
                    r[2] = -(s[2] - minv)
                else:
                    r[2] = ch[2] + r[2]
            else:
                ch = np.array(me.attributes['{}private_s_change'.format(self.attribute_prefix)].data[i].vector, dtype=np.float, )
                r = ch + change
            
            me.attributes['{}private_s_change'.format(self.attribute_prefix)].data[i].vector = r


class SCATTER5_OT_manual_object_brush(SCATTER5_OT_manual_base_brush, ):
    bl_idname = "scatter5.manual_object_brush"
    bl_label = translate("Instance Index Brush")
    bl_description = translate("Paint the Instance Index 'instance_idx' attribute")
    
    brush_type = "object_brush"
    icon = "W_INSTANCE"
    dat_icon = "SCATTER5_INSTANCE"
    
    modal_adjust_map = [
        {
            'enabled': True,
            'key': 'F',
            'oskey': False,
            'shift': False,
            'property': 'radius',
            'type': 'float',
            'change': 1 / 100,
            'change_pixels': 1,
            'text': 'Radius: {:.3f}',
            'cursor': 'RADIUS',
        },
        {
            'enabled': True,
            'key': 'F',
            'oskey': True,
            'shift': False,
            'property': 'index',
            'type': 'int',
            'change': 1,
            'change_pixels': 20,
            'text': 'Object Index: {}',
            'cursor': 'COUNT',
        },
    ]
    
    @classmethod
    def poll(cls, context, ):
        r = super().poll(context, )
        if(r):
            emitter = bpy.context.scene.scatter5.emitter
            psys = emitter.scatter5.particle_systems
            psy_active = emitter.scatter5.get_psy_active()
            if(psy_active.s_instances_method=="ins_collection" and psy_active.s_instances_pick_method=="pick_idx"):
                return True
        return False
    
    def invoke(self, context, event, ):
        self.brush = context.scene.scatter5.manual.object_brush
        self.is_timer = True
        r = super().invoke(context, event, )
        return r
    
    def _self_brush_modal_update(self, context, ):
        self.brush = context.scene.scatter5.manual.object_brush
    
    def _on_lmb_press(self, context, event, ):
        # NOTE: very important, if there was some drawing done, then undo without dropping tool, this is pointing somewhere invalid, each brush MUST set this again on each use AND before super()
        self.brush = context.scene.scatter5.manual.object_brush
        super()._on_lmb_press(context, event, )
        self._drawing(context, event, )
    
    def _on_lmb_move(self, context, event, ):
        super()._on_lmb_move(context, event, )
        if(self.brush.draw_on in ('MOUSEMOVE', 'BOTH', )):
            self._drawing(context, event, )
    
    def _on_lmb_release(self, context, event, ):
        super()._on_lmb_release(context, event, )
        
        # push to history..
        bpy.ops.ed.undo_push(message=self.bl_label, )
    
    def _select_points(self, loc, nor, idx, dst, ):
        brush_radius = self.brush.radius
        if(self.brush.radius_pressure):
            brush_radius = brush_radius * self.pressure
        
        self.selected = np.zeros(len(self.locations), np.bool, )
        
        if(self.brush.falloff_distance >= brush_radius):
            self.brush.falloff_distance = self.brush.falloff_distance - self.epsilon
        
        vs = self.locations
        ns = self.normals
        
        if(len(vs) == 0):
            fvs = []
            fds = []
            fii = []
        else:
            fvs, fds, fii = self._distance_range(vs, loc, brush_radius, )
        
        if(len(fii) == 0):
            # FIXME: this might cause exception later on
            return False
        
        indices = []
        ws = []
        for i, ii in enumerate(fii):
            indices.append(ii)
            
            d = fds[i]
            w = d / (brush_radius - self.brush.falloff_distance)
            if(w > 1.0):
                w = 1.0
            ws.append(w)
        
        ws = np.array(ws, dtype=np.float, )
        ws = 1.0 - ws
        ws = ws / np.sum(ws)
        
        indices = np.array(indices, dtype=np.int, )
        # select only portion of points by weights..
        
        affect_portion = self.brush.affect_portion
        if(self.brush.affect_portion_pressure):
            affect_portion = self.pressure
        
        s = int(len(indices) * affect_portion)
        if(s == 0 and len(indices) > 0):
            s = 1
        
        # ok, now i have selected some points to move
        choice = np.random.choice(indices, size=s, replace=False, p=ws, )
        self.selected[choice] = True
        
        return True
    
    def _generate(self, loc, nor, idx, dst, ):
        self._select_points(loc, nor, idx, dst, )
        self._object()
        self._store()
    
    def _collect(self, context, ):
        me = self.target.data
        l = len(me.vertices)
        
        vs = np.zeros(l * 3, dtype=np.float, )
        me.vertices.foreach_get('co', vs)
        vs.shape = (-1, 3)
        
        ns = np.zeros(l * 3, dtype=np.float, )
        me.attributes['{}normal'.format(self.attribute_prefix)].data.foreach_get('vector', ns)
        ns.shape = (-1, 3)
        
        vs, ns = self._surface_to_global_space(vs, ns, )
        self.locations = vs
        self.normals = ns
        
        rs = np.zeros(l * 3, dtype=np.float, )
        me.attributes['{}scale'.format(self.attribute_prefix)].data.foreach_get('vector', rs)
        rs.shape = (-1, 3)
        self.scales = rs
        
        m = self.surface.matrix_world
        _, _, s = m.decompose()
        a = np.array(s.to_tuple(), dtype=np.float, )
        self.scales = self.scales * a
        
        self.selected = np.zeros(l, dtype=np.bool, )
    
    def _object(self, ):
        indices = np.arange(len(self.locations))
        indices = indices[self.selected]
        
        me = self.target.data
        l = len(me.vertices)
        objects = np.zeros(l, dtype=np.int, )
        me.attributes['{}index'.format(self.attribute_prefix)].data.foreach_get('value', objects)
        
        # do something..
        objects[indices] = self.brush.index
        
        self.objects = objects
    
    def _store(self, ):
        self._ensure_attributes()
        
        me = self.target.data
        me.attributes['{}index'.format(self.attribute_prefix)].data.foreach_set('value', self.objects.flatten())


class SCATTER5_OT_manual_random_rotation_brush(SCATTER5_OT_manual_rotation_base_brush, ):
    bl_idname = "scatter5.manual_random_rotation_brush"
    bl_label = translate("Random Rotation Brush")
    bl_description = translate("Random Rotation Brush")
    
    brush_type = "random_rotation_brush"
    icon = "W_DICE"
    dat_icon = "SCATTER5_ROTATION_RANDOM"
    
    modal_adjust_map = [
        {
            'enabled': True,
            'key': 'F',
            'oskey': False,
            'shift': False,
            'property': 'radius',
            'type': 'float',
            'change': 1 / 100,
            'change_pixels': 1,
            'text': 'Radius: {:.3f}',
            'cursor': 'RADIUS',
        },
    ]
    
    def invoke(self, context, event, ):
        self.brush = context.scene.scatter5.manual.random_rotation_brush
        self.is_timer = True
        r = super().invoke(context, event, )
        return r
    
    def _self_brush_modal_update(self, context, ):
        self.brush = context.scene.scatter5.manual.random_rotation_brush
    
    def _on_lmb_press(self, context, event, ):
        # NOTE: very important, if there was some drawing done, then undo without dropping tool, this is pointing somewhere invalid, each brush MUST set this again on each use AND before super()
        self.brush = context.scene.scatter5.manual.random_rotation_brush
        super()._on_lmb_press(context, event, )
        # self._drawing(context, event, )
    
    def _modify(self, indices, ):
        me = self.target.data
        
        # _vs = []
        # _ns = []
        
        for i in indices:
            original = Vector()
            
            align = me.attributes['{}private_r_align'.format(self.attribute_prefix)].data[i].value
            if(align == 0):
                original = me.attributes['{}normal'.format(self.attribute_prefix)].data[i].vector
            elif(align == 1):
                _, original_1 = self._surface_to_global_space(Vector((0.0, 0.0, 0.0, )), Vector((0.0, 0.0, 1.0, )), )
                original = original_1.copy()
            elif(align == 2):
                original = Vector((0.0, 0.0, 1.0, ))
            elif(align == 3):
                original = me.attributes['{}private_z_original'.format(self.attribute_prefix)].data[i].vector
                if(original.length == 0.0):
                    original = me.attributes['{}private_r_align_vector'.format(self.attribute_prefix)].data[i].vector
                    me.attributes['{}private_z_original'.format(self.attribute_prefix)].data[i].vector = original
            
            if(align < 3):
                me.attributes['{}private_z_original'.format(self.attribute_prefix)].data[i].vector = original
            
            rns = me.attributes['{}private_z_random'.format(self.attribute_prefix)].data[i].vector
            if(np.sum(rns) == 0.0):
                rns = np.random.rand(3)
                rns[2] = 1.0
            
            pi2 = 2 * np.pi
            start = pi2 * rns[0]
            current = pi2 * rns[1]
            step = self.brush.speed
            if(self.brush.speed_pressure):
                step = step * self.pressure
            
            conform = rns[2]
            conform = conform - step
            if(conform <= 0.0):
                conform = 0.0
            rns[2] = conform
            
            alpha = self.brush.angle / 2
            # +
            # |   \
            # a       c
            # |            \
            # +-----1.0-----alpha
            _c = 1.0 / math.cos(alpha)
            _a = (_c ** 2 - 1.0 ** 2) ** 0.5
            A = _a
            B = _a
            
            # Lissajous curve
            # https://en.wikipedia.org/wiki/Lissajous_curve
            # 5 by 4
            
            t = (current + step) % pi2
            # A = 0.5
            a = 5
            f = np.pi / 4
            C = 0
            # B = 0.5
            b = 4
            D = 0
            x = A * np.sin((a * t) + f) + C
            y = B * np.sin(b * t) + D
            
            # TODO: somehow let user to set max variance in degrees? or something like that, or (pi)*0-1? something to control it..
            z = 1.0
            d = Vector((x, y, z, ))
            d.normalize()
            
            q = self._rotation_to(Vector((0.0, 0.0, 1.0, )), original, )
            d.rotate(q)
            
            d = d.lerp(original, conform, )
            
            # _vs.append(self.locations[i])
            # _vs.append(self.locations[i])
            # _ns.append(d)
            # _ns.append(original)
            
            current = t / pi2
            rns[1] = current
            me.attributes['{}private_z_random'.format(self.attribute_prefix)].data[i].vector = rns
            
            me.attributes['{}private_r_align'.format(self.attribute_prefix)].data[i].value = 3
            me.attributes['{}private_r_align_vector'.format(self.attribute_prefix)].data[i].vector = d
        
        # debug.points(self.target, _vs, _ns, )


class SCATTER5_OT_manual_base_brush_2d(SCATTER5_OT_manual_base_brush, ):
    bl_idname = "scatter5.manual_base_brush_2d"
    bl_label = translate("Base Brush 2D")
    bl_description = translate("Base Brush 2D")
    
    def _cursor_update_2d(self, coords=None, enable=True, radius=None, color=None, ):
        # NOTE: so i can override that in subclasses..
        # coords = (self.mouse_region_x, self.mouse_region_y, )
        if(coords is None):
            # coords = Vector(self._path_2d_region[1])
            coords = Vector(self._mouse_2d_region)
        
        SC5Cursor2D.update(self.surface.name, enable=enable, coords=coords, radius=radius, color=color, )
    
    def _generate(self, loc, nor, idx, dst, ):
        return loc, nor
    
    def _drawing(self, context, event, ):
        loc, nor, idx, dst = self._project(context, event, )
        if(loc is not None):
            # for each draw event, those two should be the same for all generated points, so i can keep this on class.. might get easier in future to access that
            self._loc = loc.copy()
            self._nor = nor.copy()
        
        # FIXED?: does not work in ortho projection!
        
        # 2d ------------------
        vs, indices, distances, vs_2d = self._project_2d(context, event, )
        
        # debug.points(self.target, vs / 100, ns=None, cs=None, )
        
        view_direction = self.rv3d.view_rotation.to_matrix() @ Vector((0.0, 0.0, -1.0, ))
        up_direction = self.rv3d.view_rotation.to_matrix() @ Vector((0.0, 1.0, 0.0, ))
        view_location = self.rv3d.view_matrix.inverted().translation
        # view_location = view3d_utils.region_2d_to_origin_3d(self.region, self.rv3d, (self.region.width / 2, self.region.height / 2), )
        view_target = self.rv3d.view_location
        
        # _vs = [view_target.to_tuple(), view_target.to_tuple(), view_target.to_tuple(), view_location.to_tuple(), ]
        # _ns = [view_direction.to_tuple(), up_direction.to_tuple(), Vector().to_tuple(), Vector().to_tuple()]
        # _cs = [(1,0,0,1), (1,0,0,1), (1,1,0,1), (1,1,1,1)]
        # debug.points(self.target, _vs, _ns, _cs, )
    
    def _points_3d_to_region_2d(self, region, rv3d, ):
        me = self.target.data
        l = len(me.vertices)
        if(l == 0):
            return None, None
        
        vs = np.zeros(l * 3, dtype=np.float, )
        me.vertices.foreach_get('co', vs)
        vs.shape = (-1, 3)
        
        ns = np.zeros(l * 3, dtype=np.float, )
        me.attributes['{}normal'.format(self.attribute_prefix)].data.foreach_get('vector', ns)
        ns.shape = (-1, 3)
        
        m = self.surface.matrix_world
        vs, ns = self._apply_matrix(m, vs, ns, )
        vs = np.c_[vs[:, 0], vs[:, 1], vs[:, 2], np.ones(l, dtype=np.float, )]
        
        m = rv3d.perspective_matrix
        wh = region.width / 2.0
        hh = region.height / 2.0
        
        r = []
        if(not rv3d.is_perspective):
            # >> ORTHO <<
            for i, v in enumerate(vs):
                p = m @ Vector(vs[i])
                r.append((wh + wh * (p.x / p.w), hh + hh * (p.y / p.w), 0.0, ))
        else:
            # >> PERSPECTIVE <<
            for i, v in enumerate(vs):
                p = m @ Vector(vs[i])
                if(p.w > 1.0):
                    # NOTE: why this? it is used here: view3d_utils.py > location_3d_to_region_2d(), but it does nothing in ortho..
                    r.append((wh + wh * (p.x / p.w), hh + hh * (p.y / p.w), 0.0, ))
        
        return np.array(r), np.arange(l, dtype=np.int, )
    
    def _project_2d(self, context, event, ):
        if(context is None):
            region = self.region
            rv3d = self.rv3d
        else:
            region = context.region
            rv3d = context.region_data
        if(event is None):
            coord = (self.mouse_region_x, self.mouse_region_y, )
        else:
            coord = (event.mouse_region_x, event.mouse_region_y, )
        
        vs, indices = self._points_3d_to_region_2d(region, rv3d, )
        vs_2d = vs.copy()
        
        affect_portion = self.brush.affect_portion
        if(self.brush.affect_portion_pressure):
            affect_portion = self.pressure
        
        radius = self.brush.radius / 2
        if(self.brush.radius_pressure):
            radius = radius * self.pressure
        
        if(vs is not None and len(vs)):
            sel_vs, sel_d, sel_i = self._distance_range(vs, np.array((coord[0], coord[1], 0.0, )), radius, )
            
            # _vs = vs.copy()
            # _vs = _vs.astype(np.float32, )
            # _cs = np.ones((len(vs), 4), dtype=np.float32, )
            # _cs[:, 2] = 0.0
            # _cs[sel_i] = (1.0, 0.0, 0.0, 1.0)
            # debug.points_2d(self.target.name, _vs, _cs, )
            
            if(len(sel_vs) > 0):
                if(affect_portion < 1.0):
                    s = int(len(sel_i) * affect_portion)
                    if(s == 0):
                        s = 1
                    choice = np.random.choice(sel_i, size=s, replace=False, )
                    
                    ds = np.zeros(len(vs), dtype=np.float, )
                    for i, j in enumerate(sel_i):
                        ds[j] = sel_d[i]
                    distances = ds[choice]
                    
                    # modify original vertices and indices to keep real indices, so later i can select correct points..
                    vs = vs[choice]
                    indices = indices[choice]
                    vs_2d = vs_2d[choice]
                else:
                    # modify original vertices and indices to keep real indices, so later i can select correct points..
                    vs = vs[sel_i]
                    indices = indices[sel_i]
                    distances = sel_d
                    vs_2d = vs_2d[sel_i]
            else:
                vs = np.array([], dtype=np.float, )
                vs_2d = np.array([], dtype=np.float, )
                indices = np.array([], dtype=np.int, )
                distances = np.array([], dtype=np.float, )
            
            return vs, indices, distances, vs_2d
        else:
            vs = np.array([], dtype=np.float, )
            vs_2d = np.array([], dtype=np.float, )
            indices = np.array([], dtype=np.int, )
            distances = np.array([], dtype=np.float, )
            return vs, indices, distances, vs_2d
    
    def _on_lmb_press(self, context, event, ):
        self._on_lmb_event(context, event, )
        # SC5Cursor.update(self.surface.name, color=SC5ViewportTheme.BRUSH_DOWN, )
        # self._cursor_update(color=SC5ViewportTheme.BRUSH_DOWN, )
        self._cursor_update_2d(color=SC5ViewportTheme.BRUSH_DOWN, )
        if(self.is_timer):
            if(self.brush.draw_on in ('TIMER', 'BOTH', )):
                bpy.app.timers.register(self._on_timer, first_interval=self.brush.interval, )
    
    def _on_lmb_release(self, context, event, ):
        self._on_lmb_event(context, event, )
        # SC5Cursor.update(self.surface.name, color=SC5ViewportTheme.BRUSH_UP, )
        # self._cursor_update(color=SC5ViewportTheme.BRUSH_UP, )
        self._cursor_update_2d(color=SC5ViewportTheme.BRUSH_UP, )
    
    def _on_timer(self, ):
        # NOTE: this might need same check if SC5Toolbox contents is the same or not, like in _modal() for hot swapping brushes. but the things is, timer is active when brush is drawing, you can't switch while you drawing right? but keep the note here, maybe someone will report some strange behavior and that might be timer running when brush should be already gone..
        
        try:
            if(not self.lmb):
                return
        except ReferenceError:
            # operator has been remove meanwhile.. nothing to do here
            return
        
        self._drawing(None, None, )
        
        bpy.app.timers.register(self._on_timer, first_interval=self.brush.interval, )
        
        self._tag_redraw()
    
    def _modal(self, context, event, ):
        # if(SC5Toolbox.get() is not self):
        #     # NOTE: kill operator if SC5Toolbox is set to some different or to None from outside..
        #     return {'CANCELLED'}
        
        # # -- SWITCHER v2 --
        if(SC5Toolbox.get() is not self):
            # # NOTE: kill operator if SC5Toolbox is set to some different or to None from outside..
            # return {'CANCELLED'}
            
            if(self._abort):
                if(event.type == 'TIMER'):
                    # print('abort..')
                    # these are the only things left to cleanup. stats are handled elsewhere, cursor is already taken by new brush..
                    context.window_manager.event_timer_remove(self._abort_timer)
                    # NOTE: brush bmesh should be freed only when whole mode stops..
                    # self.bm.free()
                    return {'CANCELLED'}
                else:
                    # not a timer event, allow to pass to new brush..
                    return {'PASS_THROUGH'}
            else:
                # old behavior, tool has been changed on toolbar
                return {'CANCELLED'}
        # # -- SWITCHER v2 --
        
        # new viewport check, now it differentiate between 3d viewport and 3d view header, tools, etc
        is_3dview, is_viewport = self._is_viewport(context, event, )
        
        # ignore anything from outside of 3d view
        if(not is_3dview):
            if(self.lmb):
                if(event.type == 'LEFTMOUSE' and event.value == 'RELEASE'):
                    # user released outside of drawing area.. fixe that
                    self.lmb = False
                    self._on_lmb_release(context, event, )
                    self._on_commit(context, event, )
                    context.window.cursor_modal_restore()
                    return {'RUNNING_MODAL'}
        
        # main ending
        if(event.type == 'ESC'):
            self._on_cancel(context, event, )
            context.window.cursor_modal_restore()
            self._cleanup()
            
            # NOTE: should be called upon any type of brush exit, escape, brush switch, error, anything, so it put here, and it does not restore interface, it is a bug.
            self._integration_on_finish(context, event, )
            
            return {'CANCELLED'}
        
        # tool switching
        active_tool_type = context.workspace.tools.from_space_view3d_mode(context.mode).idname
        if(active_tool_type not in all_brush_types()):
            raise Exception(f"How did user get access to '{active_tool_type}'? This should not happend")
        elif(self.brush_type != active_tool_type):
            # # NOTE: there are several ways to end brush, depending on what is needed. decide which one fits here..
            # self._on_cancel(context, event, )
            # context.window.cursor_modal_restore()
            # self._cleanup()
            
            # Calling new tool dynamically depending on future brush_type using ugly exec
            future_brush = get_brush_class_by_brush_type(active_tool_type)
            # NOTE: there should be something to do it without exec..
            # exec(f"bpy.ops.{future_brush.bl_idname}(('INVOKE_DEFAULT'))")
            # NOTE: there is, but it looks like a lot of work.. make some utility for it
            op_name = future_brush.bl_idname.split('.', 1)
            op = getattr(getattr(bpy.ops, op_name[0]), op_name[1])
            if(op.poll()):
                self._on_cancel(context, event, )
                context.window.cursor_modal_restore()
                self._cleanup()
                
                op('INVOKE_DEFAULT', )
                return {'CANCELLED'}
        
        # shortcut tool switch
        if(event.value == 'PRESS' and event.ascii != ""):
            try:
                shortcuts = config.switch_shortcuts()
            except Exception as e:
                log('ERROR: {}\n{}'.format(e, traceback.format_exc()))
                shortcuts = {}
            # event_char = event.ascii.upper()
            # if(event.type.startswith('NUMPAD_')):
            #     # NOTE: skip all numpad events, these are for navigation..
            #     event_char = 'skip this..'
            # if(event_char in shortcuts.values()):
            if(event.type in shortcuts.values()):
                for nb in shortcuts.keys():
                    if(shortcuts[nb] == event.type):
                        break
                if(self.brush_type != nb):
                    # self._cleanup()
                    nb = get_brush_class_by_brush_type(nb)
                    op_name = nb.bl_idname.split('.', 1)
                    op = getattr(getattr(bpy.ops, op_name[0]), op_name[1])
                    if(op.poll()):
                        self._cleanup()
                        op('INVOKE_DEFAULT', )
                        return {'CANCELLED'}
        
        # decide if event is from viewport so user can draw, or from buttons in 3d view
        if(not is_3dview):
            # throw away events outside of viewport
            context.window.cursor_modal_restore()
            # no interaction with anything outside viewport
            return {'RUNNING_MODAL'}
        elif(not is_viewport):
            # allow 3d view ui interaction.. toolbar, header..
            return {'PASS_THROUGH'}
        else:
            # i am in active viewport area, change cursor, and continue to allow drawing.
            context.window.cursor_modal_set('PAINT_CROSS')
        
        # modifier keys
        if(event.oskey or event.ctrl):
            self.ctrl = True
        else:
            self.ctrl = False
        if(event.shift):
            self.shift = True
        else:
            self.shift = False
        if(event.alt):
            self.alt = True
        else:
            self.alt = False
        
        # modal adjust keys
        modal_adjust_enabled = [k['enabled'] for k in self.modal_adjust_map]
        modal_adjust_keys = [k['key'] for k in self.modal_adjust_map]
        modal_adjust_oskey = [k['oskey'] for k in self.modal_adjust_map]
        modal_adjust_shift = [k['shift'] for k in self.modal_adjust_map]
        
        numpad_nav = ('NUMPAD_0', 'NUMPAD_1', 'NUMPAD_2', 'NUMPAD_3', 'NUMPAD_4', 'NUMPAD_5', 'NUMPAD_6', 'NUMPAD_7', 'NUMPAD_8', 'NUMPAD_9', 'NUMPAD_MINUS', 'NUMPAD_PLUS', 'NUMPAD_PERIOD', )
        
        # viewport events handling
        if(event.type in {'MIDDLEMOUSE', 'WHEELUPMOUSE', 'WHEELDOWNMOUSE'}):
            if(self.modal_adjust):
                # NOTE: kill operator processing here, so other operator functions are not called when no drawing is happening
                return {'RUNNING_MODAL'}
            
            # allow navigation..
            context.window.cursor_modal_restore()
            return {'PASS_THROUGH'}
        elif(event.type in numpad_nav):
            if(self.modal_adjust):
                # NOTE: kill operator processing here, so other operator functions are not called when no drawing is happening
                return {'RUNNING_MODAL'}
            
            # allow navigation..
            context.window.cursor_modal_restore()
            return {'PASS_THROUGH'}
        elif(event.type == 'MOUSEMOVE' and self.lmb):
            if(self.modal_adjust):
                # NOTE: kill operator processing here, so other operator functions are not called when no drawing is happening
                return {'RUNNING_MODAL'}
            
            # drawing with mouse pressed
            self._on_lmb_move(context, event, )
        elif(event.type == 'LEFTMOUSE' and not self.modal_adjust):
            if(self.modal_adjust):
                # NOTE: kill operator processing here, so other operator functions are not called when no drawing is happening
                return {'RUNNING_MODAL'}
            
            if(event.value == 'PRESS'):
                # user pressed lmb
                self._on_start(context, event, )
                self.lmb = True
                self._on_lmb_press(context, event, )
            else:
                # user released lmb
                self.lmb = False
                self._on_lmb_release(context, event, )
                self._on_commit(context, event, )
                context.window.cursor_modal_restore()
        elif(event.type in {'Z', } and (event.oskey or event.ctrl)):
            # pass through undo
            return {'PASS_THROUGH'}
        elif(event.type in ('RIGHT_BRACKET', 'LEFT_BRACKET', ) and event.value == 'PRESS'):
            if(event.type in ('RIGHT_BRACKET', )):
                self.brush.radius += self.brush.radius_increment
            if(event.type in ('LEFT_BRACKET', )):
                self.brush.radius -= self.brush.radius_increment
        elif(event.type in modal_adjust_keys and event.value == 'PRESS' and not self.modal_adjust_abort):
            if(not self.modal_adjust):
                # find matching key combination in map
                ok = False
                for i, k in enumerate(modal_adjust_keys):
                    if(k == event.type):
                        if(modal_adjust_oskey[i] == (event.oskey or event.ctrl)):
                            if(modal_adjust_shift[i] == event.shift):
                                if(modal_adjust_enabled[i]):
                                    # ok, i got index of correct event from map
                                    ok = True
                                    break
                if(ok):
                    if(self.lmb):
                        # don't allow gestures while drawing..
                        return {'RUNNING_MODAL'}
                    
                    # found it, cool, now go for it
                    self.modal_adjust = True
                    self.modal_adjust_current = self.modal_adjust_map[i]
                    if(self.modal_adjust_current['type'] == 'float'):
                        v = float(getattr(self.brush, self.modal_adjust_current['property'], ))
                        vm = v
                    elif(self.modal_adjust_current['type'] == 'int'):
                        v = int(getattr(self.brush, self.modal_adjust_current['property'], ))
                        vm = v
                    elif(self.modal_adjust_current['type'] == 'vector'):
                        v = Vector(getattr(self.brush, self.modal_adjust_current['property'], ))
                        vm = Vector(v)
                    self.modal_adjust_property_init = v
                    self.modal_adjust_property_modified = vm
                    self.modal_adjust_mouse_init = event.mouse_region_x
                    
                    SC5GestureCursor2D.add(self.surface.name, self.modal_adjust_current['cursor'], )
                    
                    return {'MODAL_PROPERTY_ADJUST'}
            else:
                # pass other press events (depend on keyboard repeat)
                return {'MODAL_PROPERTY_ADJUST'}
        elif(event.type == 'MOUSEMOVE' and self.modal_adjust):
            # just pass event..
            return {'MODAL_PROPERTY_ADJUST'}
        elif(event.type == 'LEFTMOUSE' and self.modal_adjust):
            # kill adjust on left mouse and set adjusted value
            setattr(self.brush, self.modal_adjust_current['property'], self.modal_adjust_property_modified, )
            self.modal_adjust = False
            self.modal_adjust_current = None
            self.modal_adjust_property_init = None
            self.modal_adjust_property_modified = None
            self.modal_adjust_mouse_init = None
            self.modal_adjust_abort = True
            if(self.__class__.__name__ in SC5ToolTip._cache.keys()):
                del SC5ToolTip._cache[self.__class__.__name__]
            SC5GestureCursor2D.remove(self.surface.name, )
        elif(event.type == 'RIGHTMOUSE' and self.modal_adjust):
            # kill adjust on right mouse and set initial value
            setattr(self.brush, self.modal_adjust_current['property'], self.modal_adjust_property_init, )
            self.modal_adjust = False
            self.modal_adjust_current = None
            self.modal_adjust_property_init = None
            self.modal_adjust_property_modified = None
            self.modal_adjust_mouse_init = None
            self.modal_adjust_abort = True
            if(self.__class__.__name__ in SC5ToolTip._cache.keys()):
                del SC5ToolTip._cache[self.__class__.__name__]
            SC5GestureCursor2D.remove(self.surface.name, )
        elif(self.modal_adjust_current is not None and self.modal_adjust_current['key'] == event.type and event.value == 'RELEASE'):
            # kill adjust on release of main key and set adjusted value
            setattr(self.brush, self.modal_adjust_current['property'], self.modal_adjust_property_modified, )
            self.modal_adjust = False
            self.modal_adjust_current = None
            self.modal_adjust_property_init = None
            self.modal_adjust_property_modified = None
            self.modal_adjust_mouse_init = None
            self.modal_adjust_abort = False
            if(self.__class__.__name__ in SC5ToolTip._cache.keys()):
                del SC5ToolTip._cache[self.__class__.__name__]
            SC5GestureCursor2D.remove(self.surface.name, )
        elif(event.type in modal_adjust_keys and event.value == 'RELEASE' and self.modal_adjust_abort):
            # allow running it again after
            self.modal_adjust_abort = False
        
        # if i am here, good job mate, lets continue..
        return {'RUNNING_MODAL'}
    
    def _self_brush_modal_update(self, context, ):
        # NOTE: with undo/redo, `self.brush` reference to properties is invalid, all brushes must get new reference to properties here. and it have to be called in modal() at first place!
        pass
    
    def modal(self, context, event, ):
        # NOTE: call this first! always!
        self._self_brush_modal_update(context, )
        
        try:
            # run modal
            r = self._modal(context, event, )
        except Exception as e:
            # abort if some error there..
            self._cleanup()
            traceback.print_exc()
            self.report({'ERROR'}, traceback.format_exc(), )
            
            # NOTE: should be called upon any type of brush exit, escape, brush switch, error, anything, so it put here, and it does not restore interface, it is a bug.
            self._integration_on_finish(context, event, )
            
            return {'CANCELLED'}
        
        if(event.type == 'MOUSEMOVE'):
            mouse = Vector((event.mouse_x, event.mouse_y, ))
            if(self._mouse_2d_prev.to_tuple() != mouse.to_tuple()):
                self._mouse_2d_prev = self._mouse_2d
                self._mouse_2d = mouse
                
                prev = None
                for i in reversed(range(len(self._mouse_2d_path))):
                    d = self._distance_vectors_2d(self._mouse_2d_path[i], mouse)
                    if(d >= self._mouse_2d_direction_minimal_distance):
                        prev = self._mouse_2d_path[i]
                        break
                
                if(prev is not None):
                    self._mouse_2d_prev = prev
                    
                    n = self._mouse_2d - self._mouse_2d_prev
                    n.normalize()
                    self._mouse_2d_direction = n
                
                self._mouse_2d_path.append(mouse)
            
            self._mouse_2d_region_prev = self._mouse_2d_region
            self._mouse_2d_region = Vector((event.mouse_region_x, event.mouse_region_y, ))
            rdiff = self._mouse_2d - self._mouse_2d_region
            self._mouse_2d_region_prev = self._mouse_2d_prev - rdiff
        
        # lock cursor while in gesture
        loc, nor, idx, dst = self._project(context, event, )
        
        _loc = None
        if(loc is not None):
            # copy for 3d path and direction so i don't need to ray_cast again..
            _loc = loc.copy()
        
        if(self.modal_adjust and self.modal_adjust_cursor is None):
            self.modal_adjust_cursor = (loc, nor, )
            self.modal_adjust_cursor_2d = (event.mouse_region_x, event.mouse_region_y, )
        if(not self.modal_adjust and self.modal_adjust_cursor is not None):
            self.modal_adjust_cursor = None
            self.modal_adjust_cursor_2d = None
        if(self.modal_adjust):
            loc, nor = self.modal_adjust_cursor
        
        if(event.type == 'MOUSEMOVE'):
            if(_loc is not None):
                if(self._mouse_3d is None):
                    self._mouse_3d = _loc
                if(_loc != self._mouse_3d):
                    d = self._distance_vectors_3d(_loc, self._mouse_3d)
                    if(d > self._mouse_3d_direction_minimal_distance):
                        self._path_3d.append(_loc)
                        self._path_direction_3d.append(self._mouse_3d_direction)
                        
                        self._mouse_3d_prev = self._mouse_3d
                        self._mouse_3d = _loc
                        if(self._mouse_3d is not None and self._mouse_3d_prev is not None):
                            n = self._mouse_3d - self._mouse_3d_prev
                            n.normalize()
                            self._mouse_3d_direction = n
                        else:
                            self._mouse_3d_direction = None
                    else:
                        pass
                else:
                    pass
            else:
                self._mouse_3d_prev = self._mouse_3d
                self._mouse_3d = None
                self._mouse_3d_direction = None
        
        if(r == {'MODAL_PROPERTY_ADJUST'}):
            d = ((event.mouse_region_x - self.modal_adjust_mouse_init) / self.modal_adjust_current['change_pixels']) * self.modal_adjust_current['change']
            if(self.modal_adjust_current['type'] in ('vector', )):
                vv = Vector(self.modal_adjust_property_init)
                vv.x += d
                vv.y += d
                vv.z += d
                # set value, let it sanitize
                setattr(self.brush, self.modal_adjust_current['property'], vv, )
                # Vector have to be copied.. this returns just reference..
                vv = Vector(getattr(self.brush, self.modal_adjust_current['property']))
                # and set it back to initial
                setattr(self.brush, self.modal_adjust_current['property'], self.modal_adjust_property_init, )
                self.modal_adjust_property_modified = vv
                SC5ToolTip._cache[self.__class__.__name__] = (self.modal_adjust_current['text'].format(vv.x, vv.y, vv.z),
                                                              self.modal_adjust_cursor_2d[0] + 20,
                                                              self.modal_adjust_cursor_2d[1] - 20, )
            else:
                v = self.modal_adjust_property_init + d
                # set value, let it sanitize
                setattr(self.brush, self.modal_adjust_current['property'], v, )
                v = getattr(self.brush, self.modal_adjust_current['property'])
                # and set it back to initial
                setattr(self.brush, self.modal_adjust_current['property'], self.modal_adjust_property_init, )
                self.modal_adjust_property_modified = v
                SC5ToolTip._cache[self.__class__.__name__] = (self.modal_adjust_current['text'].format(v),
                                                              self.modal_adjust_cursor_2d[0] + 20,
                                                              self.modal_adjust_cursor_2d[1] - 20, )
            
            v = self.modal_adjust_property_modified
            if(self.modal_adjust_current['cursor'] in (SC5GestureCursor2D.STRENGTH, )):
                r = getattr(self.brush, 'radius', )
                v = v * r
            extra = 1.0
            if(self.modal_adjust_current['cursor'] in (SC5GestureCursor2D.COUNT, )):
                extra = getattr(self.brush, 'radius', )
            
            SC5GestureCursor2D.update(self.surface.name, enable=True, value=v, color=SC5ViewportTheme.BRUSH_UP, extra=extra, )
            
            r = {'RUNNING_MODAL'}
        
        if(r != {'RUNNING_MODAL'}):
            # NOTE: skip following when sidebar props are adjusted. it slows down buttons, it was ray casting in background when it is not needed.
            return r
        
        try:
            self.surface.name
            self.target.name
        except ReferenceError:
            # NOTE: this is only quick hack to fix. i got so far with undo, that objects set in invoke are no longer valid. so do following:
            # FIXME: get rid of direct references to objects, always use name..
            
            # NOTE: whole modal is handled, lets handle all exceptions in following as well
            # TODO: try to disable using other tools while drawing.. somehow. or at least remove them from mouse pointer access, most keys are already disabled except navigation and undo/redo, i think bet would be allow access only to viewport and sidebar, other areas events send to void..
            
            self.surface = bpy.data.objects.get(self.surface_name)
            self.target = bpy.data.objects.get(self.target_name)
        except AttributeError:
            # object has been removed, abort all
            self._on_cancel(context, event, )
            context.window.cursor_modal_restore()
            self._cleanup()
            
            # NOTE: should be called upon any type of brush exit, escape, brush switch, error, anything, so it put here, and it does not restore interface, it is a bug.
            self._integration_on_finish(context, event, )
            
            return {'CANCELLED'}
        
        # and this as well.. undoing too far can change that as well.. do it here so refewrences are correct without new try-except, ray casting is done at bvh, so i don't really need surface visible..
        self._ensure_surface_and_target_visibility()
        
        radius = getattr(self.brush, 'radius', 0.0, )
        if(hasattr(self.brush, 'radius')):
            radius = self.brush.radius
        if(event.is_tablet) and (hasattr(self.brush, 'radius_pressure')) and (self.brush.radius_pressure) and self.lmb:
            p = event.pressure
            if(p == 0.0):
                p = 0.001
            radius *= p
        
        enable = True
        if(self.modal_adjust):
            if(self.modal_adjust_current['cursor'] not in (SC5GestureCursor2D.RADIUS, SC5GestureCursor2D.STRENGTH, )):
                enable = False
        else:
            # update coords..
            self._coords = (event.mouse_region_x, event.mouse_region_y, )
        
        is_3dview, is_viewport = self._is_viewport(context, event, )
        if(not is_viewport):
            enable = False
        
        self._cursor_update_2d(enable=enable, coords=self._coords, radius=radius, )
        
        self._tag_redraw()
        
        return r
    
    def _prepare(self, context, ):
        # NOTE: this is obsolete now.., but leave it here for reference..
        
        o = self.surface
        m = o.matrix_world
        
        depsgraph = context.evaluated_depsgraph_get()
        eo = o.evaluated_get(depsgraph)
        bm = bmesh.new()
        bm.from_object(eo, depsgraph, cage=False, face_normals=True, )
        bm.transform(m)
        if(self.triangulate):
            bmesh.ops.triangulate(bm, faces=bm.faces, )
        bm.verts.ensure_lookup_table()
        bm.faces.ensure_lookup_table()
        
        bvh = BVHTree.FromBMesh(bm, epsilon=self.epsilon, )
        
        # TODO: surface matrix, might be better to be more descriptive
        self.m = m
        self.bm = bm
        self.bvh = bvh
        
        me = self.target.data
        for n, t in self.attribute_map.items():
            nm = '{}{}'.format(self.attribute_prefix, n)
            a = me.attributes.get(nm)
            if(a is None):
                me.attributes.new(nm, t[0], t[1])
    
    def _prepare_cached(self, context, ):
        m, bm, bvh = SC5SessionCache.get(context, )
        self.m = m
        self.bm = bm
        self.bvh = bvh
        
        # initialize attributes on target
        me = self.target.data
        for n, t in self.attribute_map.items():
            nm = '{}{}'.format(self.attribute_prefix, n)
            a = me.attributes.get(nm)
            if(a is None):
                me.attributes.new(nm, t[0], t[1])
    
    def _cleanup(self, ):
        # back with cursor
        # SC5Cursor.remove(self.surface.name, )
        SC5Cursor2D.remove(self.surface.name, )
        
        SC5Stats.remove(self.target.name, )
        bpy.context.window.cursor_modal_restore()
        # clean up data, bvhtree should be garbage collected
        # NOTE: brush bmesh should be freed only when whole mode stops..
        # self.bm.free()
        # and remove reference to operator
        SC5Toolbox.set(None, )
    
    def invoke(self, context, event, ):
        # some defaults (triangulate should be true anyway..)
        self.epsilon = 0.001
        self.triangulate = True
        
        self._coords = (event.mouse_region_x, event.mouse_region_y, )
        
        # to detect if user moving with cursor while pressing left button
        self.lmb = False
        
        # define modifier keys attributes
        self.ctrl = False
        self.shift = False
        self.alt = False
        
        # reconfigure modal key map from config..
        self.modal_adjust_map = config.gesture_reconfigure(self.modal_adjust_map)
        
        self._mouse_2d = Vector((event.mouse_x, event.mouse_y, ))
        self._mouse_2d_prev = Vector((event.mouse_x, event.mouse_y, ))
        self._mouse_2d_direction = Vector()
        self._mouse_2d_region = Vector((event.mouse_region_x, event.mouse_region_y, ))
        self._mouse_2d_region_prev = Vector((event.mouse_region_x, event.mouse_region_y, ))
        self._mouse_2d_direction_minimal_distance = 10
        self._mouse_2d_path = [Vector((event.mouse_region_x, event.mouse_region_y, )), ]
        
        self._mouse_3d = None
        self._mouse_3d_prev = None
        self._mouse_3d_direction = None
        # self._mouse_3d_direction_minimal_distance = 0.01
        self._mouse_3d_direction_minimal_distance = 0.05
        self._path_3d = []
        self._path_direction_3d = []
        
        # main props..
        self.props = context.scene.scatter5.manual
        
        self.surface = bpy.context.scene.scatter5.emitter
        self.target = self.surface.scatter5.get_psy_active().scatter_obj
        # self.space = self.surface.scatter5.get_psy_active().s_distribution_space.upper()
        # NOTE: keep also names for fallback after undo/redo
        self.surface_name = self.surface.name
        self.target_name = self.target.name
        
        # brush props..
        if(not hasattr(self, 'brush')):
            # brushes have to set its own set of properties before calling super().invoke()
            self.brush = self.props.default_brush_2d
        
        if(not hasattr(self, 'is_timer')):
            # if it is timer enabled brush, set this befor calling super().invoke()
            self.is_timer = False
        
        # process surface mesh to bmesh and bvhtree, at first click, user can expect some processing..
        # self._prepare(context, )
        self._prepare_cached(context, )
        
        # for brushes working with existing data, note, some brushes need to call this and each mouse press
        self._collect(context, )
        
        # init cursor drawing (if isn't already)
        # SC5Cursor.init()
        SC5Cursor2D.init()
        # set cursor from brush props..
        # SC5Cursor.add(self.surface.name, self.brush.cursor, )
        SC5Cursor2D.add(self.surface.name, self.brush.cursor, )
        # store active tool, so i can detect if some brush modal is already running
        SC5Toolbox.set(self)
        # init text drawing (if isn't already)
        SC5Stats.init()
        SC5Stats.add(self.target.name, )
        # init cursor gesture drawing (if isn't already)
        SC5GestureCursor2D.init()
        
        # # -- SWITCHER v2 --
        # abort brush on timer
        self._abort = False
        self._abort_timer = context.window_manager.event_timer_add(0.1, window=context.window, )
        # # -- SWITCHER v2 --
        
        # finally!
        context.window_manager.modal_handler_add(self)
        
        # i guess this is better place for it.. call it once all is set.. i.e. SC5Toolbox is no longer None, it points to `self`
        self._integration_on_invoke(context, event, )
        
        # at one redraw so cursor is ready..
        self._tag_redraw()
        return {'RUNNING_MODAL'}


"""
class SCATTER5_OT_manual_debug_brush_2d(SCATTER5_OT_manual_base_brush_2d, ):
    bl_idname = "scatter5.manual_debug_brush_2d"
    bl_label = translate("Dot Brush 2D")
    bl_description = translate("Dot Brush 2D")
    
    brush_type = "debug_brush_2d"
    icon = "W_CLICK"
    dat_icon = "SCATTER5_CLICK"
    
    modal_adjust_map = [
        {
            'enabled': True,
            'key': 'F',
            'oskey': False,
            'shift': False,
            'property': 'radius',
            'type': 'int',
            'change': 1,
            'change_pixels': 1,
            'text': 'Radius: {:.0f}',
            'cursor': 'RADIUS',
        },
        {
            'enabled': True,
            'key': 'S',
            'oskey': False,
            'shift': False,
            'property': 'strength',
            'type': 'float',
            'change': 1 / 200,
            'change_pixels': 2,
            'text': 'Strength: {:.3f}',
            'cursor': 'STRENGTH',
        },
        {
            'enabled': True,
            'key': 'C',
            'oskey': False,
            'shift': False,
            'property': 'count',
            'type': 'int',
            'change': 1,
            'change_pixels': 5,
            'text': 'Count: {:.0f}',
            'cursor': 'COUNT',
        },
        {
            'enabled': True,
            'key': 'L',
            'oskey': False,
            'shift': False,
            'property': 'length',
            'type': 'int',
            'change': 1,
            'change_pixels': 2,
            'text': 'Length: {:.0f}',
            'cursor': 'LENGTH',
        },
    ]
    
    def invoke(self, context, event, ):
        # set brush props here so subclass can inject its own collection..
        self.brush = context.scene.scatter5.manual.debug_brush_2d
        self.is_timer = True
        return super().invoke(context, event, )
    
    def _self_brush_modal_update(self, context, ):
        self.brush = context.scene.scatter5.manual.debug_brush_2d
    
    # def _on_lmb_press(self, context, event, ):
    #     # NOTE: very important, if there was some drawing done, then undo without dropping tool, this is pointing somewhere invalid, each brush MUST set this again on each use AND before super()
    #     self.brush = context.scene.scatter5.manual.debug_brush_2d
    #     super()._on_lmb_press(context, event, )
    #     self._drawing(context, event, )
    #
    #     # push to history..
    #     bpy.ops.ed.undo_push(message=self.bl_label, )
    
    def _on_lmb_press(self, context, event, ):
        # NOTE: very important, if there was some drawing done, then undo without dropping tool, this is pointing somewhere invalid, each brush MUST set this again on each use AND before super()
        self.brush = context.scene.scatter5.manual.debug_brush_2d
        super()._on_lmb_press(context, event, )
        self._drawing(context, event, )
    
    # def _on_lmb_move(self, context, event, ):
    #     super()._on_lmb_move(context, event, )
    #     self._drawing(context, event, )
    
    def _on_lmb_move(self, context, event, ):
        super()._on_lmb_move(context, event, )
        
        if(self.brush.draw_on in ('MOUSEMOVE', 'BOTH', )):
            self._drawing(context, event, )
"""


class SCATTER5_OT_manual_z_align_brush(SCATTER5_OT_manual_base_brush_2d, ):
    bl_idname = "scatter5.manual_z_align_brush"
    bl_label = translate("Normal Alignment Brush")
    bl_description = translate("Normal Alignment Brush")
    
    brush_type = "z_align_brush"
    icon = "W_ARROW_NORMAL"
    dat_icon = "SCATTER5_ROTATION_ALIGN_Z"
    
    modal_adjust_map = [
        {
            'enabled': True,
            'key': 'F',
            'oskey': False,
            'shift': False,
            'property': 'radius',
            'type': 'int',
            'change': 1,
            'change_pixels': 1,
            'text': 'Radius: {:.0f}',
            'cursor': 'RADIUS',
        },
    ]
    
    def invoke(self, context, event, ):
        # set brush props here so subclass can inject its own collection..
        self.brush = context.scene.scatter5.manual.z_align_brush
        return super().invoke(context, event, )
    
    def _self_brush_modal_update(self, context, ):
        self.brush = context.scene.scatter5.manual.z_align_brush
    
    def _on_lmb_press(self, context, event, ):
        # NOTE: very important, if there was some drawing done, then undo without dropping tool, this is pointing somewhere invalid, each brush MUST set this again on each use AND before super()
        self.brush = context.scene.scatter5.manual.z_align_brush
        super()._on_lmb_press(context, event, )
        self._drawing(context, event, )
    
    def _on_lmb_move(self, context, event, ):
        super()._on_lmb_move(context, event, )
        
        # if(self.brush.draw_on in ('MOUSEMOVE', 'BOTH', )):
        #     self._drawing(context, event, )
        self._drawing(context, event, )
    
    def _on_lmb_release(self, context, event, ):
        super()._on_lmb_release(context, event, )
        # push to history..
        bpy.ops.ed.undo_push(message=self.bl_label, )
    
    def _calc_rotation_components_from_attributes(self, i, ):
        me = self.target.data
        # rotation = np.array(me.attributes['{}rotation'.format(self.attribute_prefix)].data[i].vector, dtype=np.float, )
        
        vec, nor = self._surface_to_global_space(me.vertices[i].co, me.attributes['{}normal'.format(self.attribute_prefix)].data[i].vector, )
        _, nor_1 = self._surface_to_global_space(Vector((0.0, 0.0, 0.0, )), Vector((0.0, 0.0, 1.0, )), )
        
        private_r_align = me.attributes['{}private_r_align'.format(self.attribute_prefix)].data[i].value
        if(private_r_align == 0):
            nor = Vector(nor)
        elif(private_r_align == 1):
            nor = nor_1.copy()
        elif(private_r_align == 2):
            nor = Vector((0.0, 0.0, 1.0, ))
        elif(private_r_align == 3):
            nor = Vector(me.attributes['{}private_r_align_vector'.format(self.attribute_prefix)].data[i].vector)
        
        locy_1 = Vector((0.0, 1.0, 0.0, ))
        mwi_1 = self.surface.matrix_world.copy()
        _, cr_1, _ = mwi_1.decompose()
        locy_1.rotate(cr_1)
        
        private_r_up = me.attributes['{}private_r_up'.format(self.attribute_prefix)].data[i].value
        if(private_r_up == 0):
            aq = self._direction_to_rotation_with_m3x3(nor, )
        elif(private_r_up == 1):
            aq = self._direction_to_rotation_with_m3x3(nor, locy_1, )
        elif(private_r_up == 2):
            aq = self._direction_to_rotation_with_m3x3(nor, Vector(me.attributes['{}private_r_up_vector'.format(self.attribute_prefix)].data[i].vector), )
        
        private_r_random = np.array(me.attributes['{}private_r_random'.format(self.attribute_prefix)].data[i].vector, dtype=np.float, )
        private_r_random_random = np.array(me.attributes['{}private_r_random_random'.format(self.attribute_prefix)].data[i].vector, dtype=np.float, )
        err = Euler(private_r_random * private_r_random_random)
        
        mwi = self.surface.matrix_world.inverted()
        _, cr, _ = mwi.decompose()
        
        eb = Euler(me.attributes['{}private_r_base'.format(self.attribute_prefix)].data[i].vector)
        
        # q = Quaternion()
        # q.rotate(eb)
        # q.rotate(err)
        # q.rotate(aq)
        # q.rotate(cr)
        #
        # e = q.to_euler('XYZ')
        # return eb, err, aq, cr, e
        return eb, err, aq, cr
    
    def _distance_vectors(self, a, b, ):
        return ((a.x - b.x) ** 2 + (a.y - b.y) ** 2 + (a.z - b.z) ** 2) ** 0.5
    
    def _calc_rotation_components_from_attributes(self, i, ):
        me = self.target.data
        # rotation = np.array(me.attributes['{}rotation'.format(self.attribute_prefix)].data[i].vector, dtype=np.float, )
        
        vec, nor = self._surface_to_global_space(me.vertices[i].co, me.attributes['{}normal'.format(self.attribute_prefix)].data[i].vector, )
        _, nor_1 = self._surface_to_global_space(Vector((0.0, 0.0, 0.0, )), Vector((0.0, 0.0, 1.0, )), )
        
        private_r_align = me.attributes['{}private_r_align'.format(self.attribute_prefix)].data[i].value
        if(private_r_align == 0):
            nor = Vector(nor)
        elif(private_r_align == 1):
            nor = nor_1.copy()
        elif(private_r_align == 2):
            nor = Vector((0.0, 0.0, 1.0, ))
        elif(private_r_align == 3):
            nor = Vector(me.attributes['{}private_r_align_vector'.format(self.attribute_prefix)].data[i].vector)
        
        locy_1 = Vector((0.0, 1.0, 0.0, ))
        mwi_1 = self.surface.matrix_world.copy()
        _, cr_1, _ = mwi_1.decompose()
        locy_1.rotate(cr_1)
        
        private_r_up = me.attributes['{}private_r_up'.format(self.attribute_prefix)].data[i].value
        if(private_r_up == 0):
            aq = self._direction_to_rotation_with_m3x3(nor, )
        elif(private_r_up == 1):
            aq = self._direction_to_rotation_with_m3x3(nor, locy_1, )
        elif(private_r_up == 2):
            aq = self._direction_to_rotation_with_m3x3(nor, Vector(me.attributes['{}private_r_up_vector'.format(self.attribute_prefix)].data[i].vector), )
        
        private_r_random = np.array(me.attributes['{}private_r_random'.format(self.attribute_prefix)].data[i].vector, dtype=np.float, )
        private_r_random_random = np.array(me.attributes['{}private_r_random_random'.format(self.attribute_prefix)].data[i].vector, dtype=np.float, )
        err = Euler(private_r_random * private_r_random_random)
        
        mwi = self.surface.matrix_world.inverted()
        _, cr, _ = mwi.decompose()
        
        eb = Euler(me.attributes['{}private_r_base'.format(self.attribute_prefix)].data[i].vector)
        
        # q = Quaternion()
        # q.rotate(eb)
        # q.rotate(err)
        # q.rotate(aq)
        # q.rotate(cr)
        #
        # e = q.to_euler('XYZ')
        # return eb, err, aq, cr, e
        return eb, err, aq, cr
    
    def _drawing(self, context, event, ):
        # NOTE: this bit id from 3d brush, i think i need to keep it here for compatibility..
        loc, nor, idx, dst = self._project(context, event, )
        if(loc is not None):
            # for each draw event, those two should be the same for all generated points, so i can keep this on class.. might get easier in future to access that
            self._loc = loc.copy()
            self._nor = nor.copy()
        
        # vertices and their indices that are under cursor and affected
        vs, indices, distances, vs_2d = self._project_2d(context, event, )
        
        view_direction = self.rv3d.view_rotation.to_matrix() @ Vector((0.0, 0.0, -1.0, ))
        up_direction = self.rv3d.view_rotation.to_matrix() @ Vector((0.0, 1.0, 0.0, ))
        # view_location = self.rv3d.view_matrix.inverted().translation
        view_location = view3d_utils.region_2d_to_origin_3d(self.region, self.rv3d, (self.region.width / 2, self.region.height / 2), )
        view_target = self.rv3d.view_location
        
        # current = self._mouse_2d
        current = self._mouse_2d_region
        previous = self._mouse_2d_region_prev
        direction = self._mouse_2d_direction
        if(direction == Vector()):
            return
        
        axis = view_direction
        
        def get_set_axes(i, ):
            me = self.target.data
            a = me.attributes['{}private_r_align'.format(self.attribute_prefix)].data[i].value
            if(a == 0):
                vec, nor = self._surface_to_global_space(me.vertices[i].co, me.attributes['{}normal'.format(self.attribute_prefix)].data[i].vector, )
                z_axis = Vector(nor)
            elif(a == 1):
                _, nor_1 = self._surface_to_global_space(Vector((0.0, 0.0, 0.0, )), Vector((0.0, 0.0, 1.0, )), )
                z_axis = nor_1.copy()
            elif(a == 2):
                z_axis = Vector((0.0, 0.0, 1.0, ))
            elif(a == 3):
                z_axis = Vector(me.attributes['{}private_r_align_vector'.format(self.attribute_prefix)].data[i].vector)
            
            if(a < 3):
                # change to custom..
                me.attributes['{}private_r_align'.format(self.attribute_prefix)].data[i].value = 3
                me.attributes['{}private_r_align_vector'.format(self.attribute_prefix)].data[i].vector = z_axis
            
            locy_1 = Vector((0.0, 1.0, 0.0, ))
            mwi_1 = self.surface.matrix_world.copy()
            _, cr_1, _ = mwi_1.decompose()
            locy_1.rotate(cr_1)
            
            up = me.attributes['{}private_r_up'.format(self.attribute_prefix)].data[i].value
            if(up == 0):
                y_axis = Vector((0.0, 1.0, 0.0, ))
            elif(up == 1):
                y_axis = Vector((0.0, 1.0, 0.0, ))
                gm = self.surface.matrix_world.copy()
                _, gr, _ = gm.decompose()
                y_axis.rotate(gr)
            elif(up == 2):
                y_axis = Vector(me.attributes['{}private_r_up_vector'.format(self.attribute_prefix)].data[i].vector)
            
            if(up < 2):
                # change to custom..
                me.attributes['{}private_r_up'.format(self.attribute_prefix)].data[i].value = 2
                me.attributes['{}private_r_up_vector'.format(self.attribute_prefix)].data[i].vector = y_axis
            
            return z_axis, y_axis
        
        def project_on_plane(p, n, q, ):
            return q - Vector(q - p).dot(n) * n
        
        # TODO: why half radius? what's going on here?
        radius = self.brush.radius / 2
        if(self.brush.radius_pressure):
            radius = radius * self.pressure
        
        # # DEBUG
        # _vs = []
        # _ns = []
        # _cs = []
        # # DEBUG
        
        view_un_rotate = self._rotation_to(view_direction, Vector((0.0, 0.0, 1.0, )), )
        view_rotate = self._rotation_to(Vector((0.0, 0.0, 1.0, )), view_direction, )
        
        flip_axis = axis.copy()
        flip_axis.negate()
        
        coord = current.copy()
        vec = view3d_utils.region_2d_to_vector_3d(self.region, self.rv3d, coord, )
        loc = view3d_utils.region_2d_to_location_3d(self.region, self.rv3d, coord, vec, )
        
        coord = current + (direction * radius)
        vec2 = view3d_utils.region_2d_to_vector_3d(self.region, self.rv3d, coord, )
        loc2 = view3d_utils.region_2d_to_location_3d(self.region, self.rv3d, coord, vec, )
        
        # # DEBUG
        # _vs.append(np.array(loc))
        # _ns.append(np.array(vec))
        # _cs.append((0,1,0,1))
        # _vs.append(np.array(loc2))
        # _ns.append(np.array(vec2))
        # _cs.append((0,1,0,1))
        # # DEBUG
        
        direction_3d = loc2 - loc
        direction_3d.normalize()
        
        # # DEBUG
        # _vs.append(np.array(loc))
        # _ns.append(np.array(direction_3d))
        # _cs.append((0,1,0,1))
        # # DEBUG
        
        strength = self.brush.strength
        if(self.brush.strength_pressure):
            strength = strength * self.pressure
        
        distances_normalized = 1.0 - (distances / radius)
        
        me = self.target.data
        for j, i in enumerate(indices):
            z_axis, y_axis = get_set_axes(i, )
            
            # # DEBUG
            # _vs.append(np.array(me.vertices[i].co))
            # _ns.append(np.array(direction_3d))
            # _cs.append((1,1,0,1))
            # # DEBUG
            
            s = strength
            if(self.brush.falloff):
                d = distances_normalized[j]
                s = strength * d
            
            q = self._rotation_to(z_axis, direction_3d)
            # q = Quaternion().slerp(q, strength)
            q = Quaternion().slerp(q, s, )
            
            rot_mat = q.to_matrix()
            
            z_axis = rot_mat @ z_axis
            me.attributes['{}private_r_align_vector'.format(self.attribute_prefix)].data[i].vector = z_axis
            y_axis = rot_mat @ y_axis
            me.attributes['{}private_r_up_vector'.format(self.attribute_prefix)].data[i].vector = y_axis
        
        # # DEBUG
        # _vs.append(np.array((current[0], current[1], 0.0)) / 100)
        # _vs.append(np.array((previous[0], previous[1], 0.0)) / 100)
        # _ns.append(np.array((direction[0], direction[1], 0.0)))
        # _ns.append(np.array((direction[0], direction[1], 0.0)))
        # _cs.append((1,0,0,1))
        # _cs.append((1,0,0,1))
        # # DEBUG
        
        # # DEBUG
        # debug.points(self.target, _vs, _ns, _cs, )
        # # DEBUG
        
        self._regenerate_rotation_from_attributes(indices, )
        self.target.data.update()


"""
class SCATTER5_OT_manual_gizmo_brush(SCATTER5_OT_manual_base_brush, ):
    bl_idname = "scatter5.manual_gizmo_brush"
    bl_label = translate("Gizmo Brush")
    bl_description = translate("Gizmo Brush")
    
    brush_type = "gizmo_brush"
    icon = "W_CLICK"
    dat_icon = "SCATTER5_CLICK"
    
    modal_adjust_map = []
    
    def invoke(self, context, event, ):
        # set brush props here so subclass can inject its own collection..
        self.brush = context.scene.scatter5.manual.gizmo_brush
        return super().invoke(context, event, )
    
    def _self_brush_modal_update(self, context, ):
        self.brush = context.scene.scatter5.manual.gizmo_brush
    
    def _on_lmb_press(self, context, event, ):
        # NOTE: very important, if there was some drawing done, then undo without dropping tool, this is pointing somewhere invalid, each brush MUST set this again on each use AND before super()
        self.brush = context.scene.scatter5.manual.gizmo_brush
        super()._on_lmb_press(context, event, )
        
        self._drawing(context, event, )
        
        # push to history..
        # NOTE: how to handle history?
        bpy.ops.ed.undo_push(message=self.bl_label, )
    
    def _find_closest(self, vs, point, ):
        d = ((vs[:, 0] - point[0]) ** 2 + (vs[:, 1] - point[1]) ** 2 + (vs[:, 2] - point[2]) ** 2) ** 0.5
        return np.argmin(d, )
    
    def _store(self, loc, nor, ):
        self._ensure_attributes()
        
        me = self.target.data
        l = len(me.vertices)
        vs = np.zeros(l * 3, dtype=np.float, )
        me.vertices.foreach_get('co', vs, )
        vs.shape = (-1, 3, )
        
        if(not len(vs)):
            return
        
        # index of picked point..
        i = self._find_closest(vs, loc, )
        # print(i, vs[i], )
        
        from .gizmos import SC5GizmoManager
        SC5GizmoManager.set(self.target.name, i, )
        
        debug.points(self.target, np.array(vs[i], dtype=np.float, ).reshape((-1, 3), ), None, None, )
"""


classes = (
    SCATTER5_OT_manual_dot_brush,
    SCATTER5_OT_manual_pose_brush,
    SCATTER5_OT_manual_path_brush,
    SCATTER5_OT_manual_spatter_brush,
    SCATTER5_OT_manual_spray_brush,
    
    SCATTER5_OT_manual_move_brush,
    
    SCATTER5_OT_manual_eraser_brush,
    SCATTER5_OT_manual_dilute_brush,
    
    SCATTER5_OT_manual_rotation_brush,
    SCATTER5_OT_manual_random_rotation_brush,
    
    SCATTER5_OT_manual_comb_brush,
    SCATTER5_OT_manual_z_align_brush,
    
    SCATTER5_OT_manual_scale_brush,
    SCATTER5_OT_manual_scale_grow_shrink_brush,
    
    SCATTER5_OT_manual_object_brush,
    
    # SCATTER5_OT_manual_debug_brush_2d,
    # SCATTER5_OT_manual_gizmo_brush,
)


def all_brush_classes():
    # return [module for name, module in globals().items() if name.startswith("SCATTER5_OT") and "brush_type" in module.__dict__]
    return classes + tuple()


def all_brush_types():
    return [cl.brush_type for cl in all_brush_classes()]


def get_brush_class_by_brush_type(brush_type):
    return [cl for cl in all_brush_classes() if cl.brush_type == brush_type][0]
