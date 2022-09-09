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

import os
import copy
import math
import numpy as np

import bpy
import bgl
import blf
import gpu
import bmesh
from mathutils.bvhtree import BVHTree
from gpu.types import GPUShader
from gpu_extras.batch import batch_for_shader
from mathutils import Vector, Quaternion, Euler, Matrix

from .debug import log, debug_mode, verbose


class SC5Toolbox():
    _tool = None
    
    @classmethod
    def init(cls, ):
        cls._tool = None
    
    @classmethod
    def deinit(cls, ):
        cls._tool = None
    
    @classmethod
    def get(cls,):
        return cls._tool
    
    @classmethod
    def set(cls, t, ):
        cls._tool = t


class SC5Cursor():
    _cache = {}
    _handle = None
    _initialized = False
    
    CIRCLE = 'CIRCLE'
    CROSS = 'CROSS'
    NONE = 'NONE'
    RETICLE = 'RETICLE'
    SPRAY = 'SPRAY'
    COMPASS = 'COMPASS'
    
    # use brush rotation
    _use_tool_align = True
    _tool_align = False
    
    @classmethod
    def init(cls, ):
        if(cls._initialized):
            return
        
        cls._cache = {}
        cls._handle = bpy.types.SpaceView3D.draw_handler_add(cls._draw_handler, (), 'WINDOW', 'POST_VIEW', )
        cls._initialized = True
        cls._tag_redraw()
    
    @classmethod
    def deinit(cls, ):
        if(not cls._initialized):
            return
        
        bpy.types.SpaceView3D.draw_handler_remove(cls._handle, 'WINDOW', )
        cls._handle = None
        cls._cache = {}
        cls._initialized = False
    
    @classmethod
    def _draw_handler(cls, ):
        obs = bpy.data.objects
        rm = []
        for k, v in cls._cache.items():
            if(not obs.get(k)):
                rm.append(k)
            else:
                if(v['draw']):
                    if(v['cursor'] is not cls.NONE):
                        cls._draw(k)
        if(len(rm)):
            for k in rm:
                del cls._cache[k]
    
    @classmethod
    def gc(cls, scene=None, depsgraph=None, ):
        obs = bpy.data.objects
        rm = []
        for k, v in cls._cache.items():
            if(not obs.get(k)):
                rm.append(k)
        if(len(rm)):
            for k in rm:
                del cls._cache[k]
    
    @classmethod
    def _circle2d_coords(cls, radius, steps, offset, ox, oy):
        import math
        r = []
        angstep = 2 * math.pi / steps
        for i in range(steps):
            x = math.sin(i * angstep + offset) * radius + ox
            y = math.cos(i * angstep + offset) * radius + oy
            r.append((x, y))
        return r
    
    @classmethod
    def _circle2d_coords_np(cls, radius, steps, offset, ox, oy):
        vs = np.zeros((steps, 3), dtype=np.float32, )
        angstep = 2 * np.pi / steps
        indices = np.indices((steps, ), dtype=np.int32, )[0]
        vs[:, 0] = np.sin(indices * angstep + offset) * radius + ox
        vs[:, 1] = np.cos(indices * angstep + offset) * radius + oy
        
        a = indices
        b = np.copy(indices)
        b = b + 1
        b[-1] = 0
        indices = np.c_[a, b]
        
        return vs, indices
    
    @classmethod
    def _cross2d_coords_np(cls, r, ):
        vs = (
            (0, r, 0),
            (0, -r, 0),
            (r, 0, 0),
            (-r, 0, 0),
        )
        vs = np.array(vs, dtype=np.float32, )
        indices = (
            (0, 1),
            (2, 3),
        )
        indices = np.array(indices, dtype=np.int32, )
        return vs, indices
    
    @classmethod
    def _arrow_coords_np(cls, f=(0, 0), t=(1, 0), ):
        a = 0.1
        vs = (
            (f[0], f[1], 0, ),
            (-a, t[1] - a, 0, ),
            (a, t[1] - a, 0, ),
            (t[0], t[1], 0, ),
        )
        vs = np.array(vs, dtype=np.float32, )
        indices = (
            (0, 3, ),
            (1, 3, ),
            (2, 3, ),
        )
        indices = np.array(indices, dtype=np.int32, )
        return vs, indices
    
    @classmethod
    def add(cls, key, cursor='CIRCLE', ):
        if(cursor is not cls.NONE):
            if(cursor == cls.CIRCLE):
                vs, indices = cls._circle2d_coords_np(1.0, 64, 0, 0.0, 0.0, )
                if(cls._use_tool_align):
                    cls._tool_align = False
            elif(cursor == cls.CROSS):
                vs, indices = cls._cross2d_coords_np(1.0, )
                if(cls._use_tool_align):
                    cls._tool_align = True
            elif(cursor == cls.RETICLE):
                vs0, indices0 = cls._circle2d_coords_np(0.5, 64, 0, 0.0, 0.0, )
                vs1, indices1 = cls._cross2d_coords_np(1.0, )
                indices1 += len(indices0)
                vs = np.concatenate((vs0, vs1), )
                indices = np.concatenate((indices0, indices1), )
                if(cls._use_tool_align):
                    cls._tool_align = True
            elif(cursor == cls.SPRAY):
                vs0, indices0 = cls._circle2d_coords_np(1.0, 64, 0, 0.0, 0.0, )
                # vs1 = np.array([[0.0, 0.0, 2.0], [0.0, 0.0, 1.9], ], dtype=np.float32, )
                # indices1 = np.array([[len(vs0), len(vs0) + 1], ], dtype=np.int32, )
                # vs = np.concatenate((vs0, vs1), )
                # indices = np.concatenate((indices0, indices1), )
                
                vs1, indices1 = cls._cross2d_coords_np(0.1, )
                vs1[:, 2] = 2.0
                indices1 += len(indices0)
                vs = np.concatenate((vs0, vs1), )
                indices = np.concatenate((indices0, indices1), )
                
                if(cls._use_tool_align):
                    cls._tool_align = False
            elif(cursor == cls.COMPASS):
                vs0, indices0 = cls._circle2d_coords_np(0.1, 64, 0, 0.0, 0.0, )
                vs1, indices1 = cls._arrow_coords_np((0.0, 0.1, ), (0.0, 1.0, ))
                indices1 += len(indices0)
                vs = np.concatenate((vs0, vs1), )
                indices = np.concatenate((indices0, indices1), )
                if(cls._use_tool_align):
                    cls._tool_align = True
            elif(cursor == cls.NONE):
                return False
            else:
                raise Exception('Unknown cursor type')
            
            # d = gpu.shader.code_from_builtin('3D_UNIFORM_COLOR')
            # print(d['vertex_shader'])
            # print(d['fragment_shader'])
            
            # vertex_shader = '''
            # in vec3 position;
            # uniform mat4 model;
            # uniform mat4 view;
            # uniform mat4 projection;
            #
            # void main()
            # {
            #     gl_Position = projection * view * model * vec4(position, 1.0);
            # }
            # '''
            # fragment_shader = '''
            # uniform vec4 color;
            # out vec4 fragColor;
            #
            # void main()
            # {
            #     fragColor = color;
            #     fragColor = blender_srgb_to_framebuffer_space(fragColor);
            # }
            # '''
            
            vertex_shader, fragment_shader, _ = load_shader_code('BRUSH')
            
            shader = GPUShader(vertex_shader, fragment_shader, )
            
            # TODO: anyway, is it good idea to use builtin shader? line width is not even fixed for a months, there seems to be a way to draw lines from fragment shader
            # https://stackoverflow.com/questions/15276454/is-it-possible-to-draw-line-thickness-in-a-fragment-shader
            
            """
            shader = gpu.shader.from_builtin('3D_UNIFORM_COLOR')
            # # https://developer.blender.org/rBb35b8c884909307bff2f71ce766621144fbc85a1
            # shader = gpu.shader.from_builtin('3D_POLYLINE_UNIFORM_COLOR')
            """
            
            batch = batch_for_shader(shader, 'LINES', {'position': vs, }, indices=indices, )
            """
            batch = batch_for_shader(shader, 'LINES', {'pos': vs, }, indices=indices, )
            """
            
            c = {
                'name': key,
                'vs': vs,
                'indices': indices,
                'draw': False,
                'shader': shader,
                'batch': batch,
                'matrix': Matrix(),
                'cursor': cursor,
                # 'color': (1.0, 1.0, 1.0, 1.0, ),
                'color': (0.9, 0.9, 0.9, 1.0, ),
                'angle': 0.0,
            }
            cls._cache[key] = c
            cls._tag_redraw()
            return True
        
        return False
    
    @classmethod
    def remove(cls, key, ):
        if(key not in cls._cache.keys()):
            return False
        del cls._cache[key]
        cls._tag_redraw()
        return True
    
    @classmethod
    def _rotation_to(cls, a, b):
        """Calculates shortest Quaternion from Vector a to Vector b"""
        # a - up vector
        # b - direction to point to
    
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
            # tmpvec3 = cross(xUnitVec3, a)
            tmpvec3 = xUnitVec3.cross(a)
            if(tmpvec3.length < 0.000001):
                tmpvec3 = yUnitVec3.cross(a)
            tmpvec3.normalize()
            # q = Quaternion(tmpvec3, Math.PI)
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
    
    @classmethod
    def _draw(cls, key, ):
        bgl.glEnable(bgl.GL_BLEND)
        bgl.glEnable(bgl.GL_LINE_SMOOTH)
        
        c = cls._cache[key]
        shader = c['shader']
        batch = c['batch']
        
        shader.bind()
        shader.uniform_float("model", c['matrix'])
        shader.uniform_float("view", bpy.context.region_data.view_matrix)
        shader.uniform_float("projection", bpy.context.region_data.window_matrix)
        shader.uniform_float('color', c['color'])
        batch.draw(shader)
        # NOTE: hacky way to get somewhat thicker line because `glLineWidth` does nothing, deprecated i guess, or unsupported in newer opengl version?
        batch.draw(shader)
        batch.draw(shader)
        
        """
        gpu.matrix.push()
        gpu.matrix.load_matrix(c['matrix'])
        perspective_matrix = bpy.context.region_data.window_matrix @ bpy.context.region_data.view_matrix
        gpu.matrix.load_projection_matrix(perspective_matrix)
        shader.bind()
        shader.uniform_float('color', c['color'])
        # shader.uniform_float('lineWidth', 5, )
        batch.draw(shader)
        gpu.matrix.pop()
        """
        
        bgl.glDisable(bgl.GL_BLEND)
        bgl.glDisable(bgl.GL_LINE_SMOOTH)
        
        return True
    
    @classmethod
    def update(cls, key, enable=True, loc=None, nor=None, radius=None, color=None, z_scale=1.0, angle=0.0, ):
        if(key not in cls._cache.keys()):
            return False
        
        c = cls._cache[key]
        
        if(not enable):
            c['draw'] = False
            cls._tag_redraw()
            return True
        else:
            c['draw'] = True
        
        if(loc is None and color is not None):
            # for just color change
            c['color'] = color
            cls._tag_redraw()
            return True
        
        mt = Matrix.Translation(loc, )
        if(cls._use_tool_align):
            if(cls._tool_align):
                tool = SC5Toolbox.get()
                if(tool is not None):
                    mr = tool._cursor_align(loc, nor, ).to_matrix().to_4x4()
                else:
                    mr = cls._rotation_to(Vector((0.0, 0.0, 1.0, )), nor, ).to_matrix().to_4x4()
            else:
                mr = cls._rotation_to(Vector((0.0, 0.0, 1.0, )), nor, ).to_matrix().to_4x4()
        else:
            mr = cls._rotation_to(Vector((0.0, 0.0, 1.0, )), nor, ).to_matrix().to_4x4()
        # if(z_scale != 1.0):
        #     # ms = Matrix(((1 * radius, 0.0, 0.0, 0.0), (0.0, 1 * radius, 0.0, 0.0), (0.0, 0.0, 1 * radius * z_scale, 0.0), (0.0, 0.0, 0.0, 1.0)))
        #     ms = Matrix(((1 * radius, 0.0, 0.0, 0.0), (0.0, 1 * radius, 0.0, 0.0), (0.0, 0.0, z_scale * 0.5, 0.0), (0.0, 0.0, 0.0, 1.0)))
        # else:
        #     ms = Matrix.Scale(1 * radius, 4, )
        ms = Matrix(((1 * radius, 0.0, 0.0, 0.0), (0.0, 1 * radius, 0.0, 0.0), (0.0, 0.0, z_scale * 0.5, 0.0), (0.0, 0.0, 0.0, 1.0)))
        
        am = Matrix.Identity(4)
        if(angle is not None):
            if(c['angle'] != angle):
                a = Vector((0.0, 0.0, 1.0))
                a.rotate(mr)
                am = Matrix.Rotation(angle, 4, a, )
        
        m = mt @ am @ mr @ ms
        
        c['matrix'] = m
        if(color is not None):
            c['color'] = color
        
        cls._tag_redraw()
        return True
    
    @classmethod
    def _tag_redraw(cls, ):
        for window in bpy.context.window_manager.windows:
            for area in window.screen.areas:
                if(area.type == 'VIEW_3D'):
                    area.tag_redraw()


class SC5Cursor2D():
    _cache = {}
    _handle = None
    _initialized = False
    
    CIRCLE = 'CIRCLE'
    CROSS = 'CROSS'
    NONE = 'NONE'
    RETICLE = 'RETICLE'
    COMPASS = 'COMPASS'
    ARROW = 'ARROW'
    ARROW_TO = 'ARROW_TO'
    ARROW_FROM_TO = 'ARROW_FROM_TO'
    
    @classmethod
    def init(cls, ):
        if(cls._initialized):
            return
        
        cls._cache = {}
        cls._handle = bpy.types.SpaceView3D.draw_handler_add(cls._draw_handler, (), 'WINDOW', 'POST_PIXEL', )
        cls._initialized = True
        cls._tag_redraw()
    
    @classmethod
    def deinit(cls, ):
        if(not cls._initialized):
            return
        
        bpy.types.SpaceView3D.draw_handler_remove(cls._handle, 'WINDOW', )
        cls._handle = None
        cls._cache = {}
        cls._initialized = False
    
    @classmethod
    def _draw_handler(cls, ):
        obs = bpy.data.objects
        rm = []
        for k, v in cls._cache.items():
            if(not obs.get(k)):
                rm.append(k)
            else:
                if(v['draw']):
                    if(v['cursor'] is not cls.NONE):
                        cls._draw(k)
        if(len(rm)):
            for k in rm:
                del cls._cache[k]
    
    @classmethod
    def gc(cls, scene=None, depsgraph=None, ):
        obs = bpy.data.objects
        rm = []
        for k, v in cls._cache.items():
            if(not obs.get(k)):
                rm.append(k)
        if(len(rm)):
            for k in rm:
                del cls._cache[k]
    
    @classmethod
    def _circle2d_coords(cls, radius, steps, offset, ox, oy):
        import math
        r = []
        angstep = 2 * math.pi / steps
        for i in range(steps):
            x = math.sin(i * angstep + offset) * radius + ox
            y = math.cos(i * angstep + offset) * radius + oy
            r.append((x, y))
        return r
    
    @classmethod
    def _circle2d_coords_np(cls, radius, steps, offset, ox, oy):
        vs = np.zeros((steps, 2), dtype=np.float32, )
        angstep = 2 * np.pi / steps
        indices = np.indices((steps, ), dtype=np.int32, )[0]
        vs[:, 0] = np.sin(indices * angstep + offset) * radius + ox
        vs[:, 1] = np.cos(indices * angstep + offset) * radius + oy
        
        a = indices
        b = np.copy(indices)
        b = b + 1
        b[-1] = 0
        indices = np.c_[a, b]
        
        return vs, indices
    
    @classmethod
    def _cross2d_coords_np(cls, r, ):
        vs = (
            (0, r, ),
            (0, -r, ),
            (r, 0, ),
            (-r, 0, ),
        )
        vs = np.array(vs, dtype=np.float32, )
        indices = (
            (0, 1),
            (2, 3),
        )
        indices = np.array(indices, dtype=np.int32, )
        return vs, indices
    
    '''
    @classmethod
    def _arrow_coords_np(cls, l, ):
        # vs = (
        #     (0, r, ),
        #     (0, -r, ),
        #     (r, 0, ),
        #     (-r, 0, ),
        # )
        a = 0.1
        vs = (
            (0, 0, ),
            (-a, l - a, ),
            (a, l - a, ),
            (0, l, ),
        )
        vs = np.array(vs, dtype=np.float32, )
        indices = (
            (0, 3),
            (1, 3),
            (2, 3),
        )
        indices = np.array(indices, dtype=np.int32, )
        return vs, indices
    '''
    
    @classmethod
    def _arrow_coords_np(cls, f=0.0, l=1.0, ):
        a = 0.1
        vs = (
            (0, f, ),
            (-a, l - a, ),
            (a, l - a, ),
            (0, l, ),
        )
        vs = np.array(vs, dtype=np.float32, )
        indices = (
            (0, 3, ),
            (1, 3, ),
            (2, 3, ),
        )
        indices = np.array(indices, dtype=np.int32, )
        return vs, indices
    
    @classmethod
    def _arrow_to_coords_np(cls, f=-1.0, l=1.0, ):
        x = 0.035
        y = 0.2
        vs = (
            (0, f, ),
            (-x, f + l - y, ),
            (x, f + l - y, ),
            (0, f + l, ),
        )
        vs = np.array(vs, dtype=np.float32, )
        indices = (
            (0, 3, ),
            (1, 3, ),
            (2, 3, ),
        )
        indices = np.array(indices, dtype=np.int32, )
        return vs, indices
    
    @classmethod
    def _arrow_to_line_coords_np(cls, f=-1.0, l=1.0, ):
        # x = 0.035
        x = 0.05
        y = 0.2
        vs = (
            (0, f, ),
            # (-x, f + l - y, ),
            # (x, f + l - y, ),
            (0, f + l, ),
        )
        vs = np.array(vs, dtype=np.float32, )
        indices = (
            # (0, 3, ),
            # (1, 3, ),
            # (2, 3, ),
            (0, 1, ),
        )
        indices = np.array(indices, dtype=np.int32, )
        return vs, indices
    
    @classmethod
    def _arrow_to_head_coords_np(cls, f=-1.0, l=1.0, ):
        if(l < 0.2):
            # r = 1.0 * l
            # l = r
            # f = -l
            # x = 0.05
            # y = l
            
            r = l / 0.2
            l = 1.0 * l
            f = -l
            x = 0.05 * r
            y = 0.2 * r
            
        else:
            # x = 0.035
            x = 0.05
            y = 0.2
        vs = (
            # (0, f, ),
            (-x, f + l - y, ),
            (x, f + l - y, ),
            (0, f + l, ),
        )
        vs = np.array(vs, dtype=np.float32, )
        indices = (
            # (0, 3, ),
            # (1, 3, ),
            # (2, 3, ),
            (0, 1, 2, ),
        )
        indices = np.array(indices, dtype=np.int32, )
        return vs, indices
    
    @classmethod
    def add(cls, key, cursor='CIRCLE', ):
        if(cursor is not cls.NONE):
            if(cursor == cls.CIRCLE):
                vs, indices = cls._circle2d_coords_np(1.0, 64, 0, 0.0, 0.0, )
            elif(cursor == cls.CROSS):
                vs, indices = cls._cross2d_coords_np(1.0, )
            elif(cursor == cls.RETICLE):
                vs0, indices0 = cls._circle2d_coords_np(0.5, 64, 0, 0.0, 0.0, )
                vs1, indices1 = cls._cross2d_coords_np(1.0, )
                indices1 += len(indices0)
                vs = np.concatenate((vs0, vs1), )
                indices = np.concatenate((indices0, indices1), )
            elif(cursor == cls.COMPASS):
                # vs0, indices0 = cls._circle2d_coords_np(0.5, 64, 0, 0.0, 0.0, )
                vs0, indices0 = cls._circle2d_coords_np(0.1, 64, 0, 0.0, 0.0, )
                # vs1, indices1 = cls._arrow_coords_np(1.0, )
                # vs1, indices1 = cls._arrow_coords_np((0.0, 0.1, ), (0.0, 1.0, ))
                vs1, indices1 = cls._arrow_coords_np(0.1, 1.0)
                
                indices1 += len(indices0)
                vs = np.concatenate((vs0, vs1), )
                indices = np.concatenate((indices0, indices1), )
            elif(cursor == cls.ARROW):
                vs, indices = cls._arrow_coords_np(0.0, 1.0)
            elif(cursor == cls.ARROW_TO):
                vs, indices = cls._arrow_to_coords_np(-1.0, 1.0)
            elif(cursor == cls.ARROW_FROM_TO):
                # vs, indices = cls._arrow_to_coords_np(-1.0, 1.0)
                vs, indices = cls._arrow_to_line_coords_np(-1.0, 1.0)
                vs2, indices2 = cls._arrow_to_head_coords_np(-1.0, 1.0)
            elif(cursor == cls.NONE):
                return False
            else:
                raise Exception('Unknown cursor type')
            
            vertex_shader, fragment_shader, _ = load_shader_code('BRUSH_2D')
            shader = GPUShader(vertex_shader, fragment_shader, )
            batch = batch_for_shader(shader, 'LINES', {'position': vs, }, indices=indices, )
            if(cursor == cls.ARROW_FROM_TO):
                # shader2 = gpu.shader.from_builtin('2D_UNIFORM_COLOR')
                shader2 = GPUShader(vertex_shader, fragment_shader, )
                batch2 = batch_for_shader(shader2, 'TRIS', {'position': vs2, }, indices=indices2, )
            else:
                shader2 = None
                batch2 = None
                vs2 = None
                indices2 = None
            
            c = {
                'name': key,
                'vs': vs,
                'indices': indices,
                'vs2': vs2,
                'indices2': indices2,
                'draw': False,
                'shader': shader,
                'batch': batch,
                'shader2': shader2,
                'batch2': batch2,
                'coordinates': (0.0, 0.0, ),
                'radius': 0.0,
                'color': (0.9, 0.9, 0.9, 1.0, ),
                'angle': 0.0,
                'length': 0.0,
                'cursor': cursor,
            }
            cls._cache[key] = c
            cls._tag_redraw()
            return True
        
        return False
    
    @classmethod
    def remove(cls, key, ):
        if(key not in cls._cache.keys()):
            return False
        del cls._cache[key]
        cls._tag_redraw()
        return True
    
    @classmethod
    def _draw(cls, key, ):
        bgl.glEnable(bgl.GL_BLEND)
        bgl.glEnable(bgl.GL_LINE_SMOOTH)
        
        c = cls._cache[key]
        shader = c['shader']
        batch = c['batch']
        
        shader.bind()
        matrix = gpu.matrix.get_projection_matrix()
        shader.uniform_float('viewProjectionMatrix', matrix)
        shader.uniform_float('coordinates', c['coordinates'])
        # shader.uniform_float('angle', c['angle'])
        shader.uniform_float('radius', c['radius'])
        shader.uniform_float('color', c['color'])
        batch.draw(shader)
        # NOTE: hacky way to get somewhat thicker line because `glLineWidth` does nothing, deprecated i guess, or unsupported in newer opengl version?
        batch.draw(shader)
        batch.draw(shader)
        
        bgl.glDisable(bgl.GL_BLEND)
        bgl.glDisable(bgl.GL_LINE_SMOOTH)
        
        if(c['cursor'] == 'ARROW_FROM_TO'):
            bgl.glEnable(bgl.GL_BLEND)
            bgl.glEnable(bgl.GL_POLYGON_SMOOTH)
            
            c = cls._cache[key]
            shader = c['shader2']
            batch = c['batch2']
            
            shader.bind()
            matrix = gpu.matrix.get_projection_matrix()
            shader.uniform_float('viewProjectionMatrix', matrix)
            shader.uniform_float('coordinates', c['coordinates'])
            # shader.uniform_float('angle', c['angle'])
            shader.uniform_float('radius', c['radius'])
            shader.uniform_float('color', c['color'])
            batch.draw(shader)
            # NOTE: hacky way to get somewhat thicker line because `glLineWidth` does nothing, deprecated i guess, or unsupported in newer opengl version?
            batch.draw(shader)
            batch.draw(shader)
        
            bgl.glDisable(bgl.GL_BLEND)
            bgl.glDisable(bgl.GL_POLYGON_SMOOTH)
        
        return True
    
    @classmethod
    def update(cls, key, enable=True, coords=None, radius=None, color=None, angle=None, length=None, ):
        if(key not in cls._cache.keys()):
            return False
        
        c = cls._cache[key]
        
        if(not enable):
            c['draw'] = False
            cls._tag_redraw()
            return True
        else:
            c['draw'] = True
        
        if(coords is not None):
            c['coordinates'] = coords
        if(radius is not None):
            c['radius'] = radius / 2
        if(color is not None):
            c['color'] = color
        if(angle is not None):
            if(length is None):
                if(c['cursor'] == 'ARROW_FROM_TO'):
                    length = 0.0
                else:
                    length = 1.0
            mr = Matrix.Rotation(angle, 2)
            if(c['cursor'] == 'ARROW_FROM_TO'):
                vs, indices = cls._arrow_to_line_coords_np(-(length * 2), length * 2)
                vs2, indices2 = cls._arrow_to_head_coords_np(-(length * 2), length * 2)
            else:
                vs = c['vs'].copy()
            a = [Vector(vs[i]) for i in range(len(vs))]
            b = [mr @ a[i] for i in range(len(a))]
            vs = np.array(b, dtype=np.float32, )
            batch = batch_for_shader(c['shader'], 'LINES', {'position': vs, }, indices=c['indices'], )
            c['batch'] = batch
            if(c['cursor'] == 'ARROW_FROM_TO'):
                a = [Vector(vs2[i]) for i in range(len(vs2))]
                b = [mr @ a[i] for i in range(len(a))]
                vs2 = np.array(b, dtype=np.float32, )
                batch2 = batch_for_shader(c['shader2'], 'TRIS', {'position': vs2, }, indices=c['indices2'], )
                c['batch2'] = batch2
            c['angle'] = angle
            c['length'] = length
        
        cls._tag_redraw()
        return True
    
    @classmethod
    def _tag_redraw(cls, ):
        for window in bpy.context.window_manager.windows:
            for area in window.screen.areas:
                if(area.type == 'VIEW_3D'):
                    area.tag_redraw()


class SC5GestureCursor():
    _cache = {}
    _handle = None
    _initialized = False
    
    NONE = 'NONE'
    RADIUS = 'RADIUS'
    STRENGTH = 'STRENGTH'
    COUNT = 'COUNT'
    LENGTH = 'LENGTH'
    
    @classmethod
    def init(cls, ):
        if(cls._initialized):
            return
        
        cls._cache = {}
        cls._handle = bpy.types.SpaceView3D.draw_handler_add(cls._draw_handler, (), 'WINDOW', 'POST_VIEW', )
        cls._initialized = True
        cls._tag_redraw()
    
    @classmethod
    def deinit(cls, ):
        if(not cls._initialized):
            return
        
        bpy.types.SpaceView3D.draw_handler_remove(cls._handle, 'WINDOW', )
        cls._handle = None
        cls._cache = {}
        cls._initialized = False
    
    @classmethod
    def _draw_handler(cls, ):
        for k, v in cls._cache.items():
            if(v['draw']):
                if(v['cursor'] is not cls.NONE):
                    cls._draw(k, )
    
    @classmethod
    def _arrow_coords_np(cls, ):
        vs = (
            (0.0, 0.0, 0.0),
            (1.0, 0.0, 0.0),
            (0.8, 0.1, 0.0),
            (0.8, -0.1, 0.0),
            
            (0.0, 0.0, 0.0),
            (-1.0, 0.0, 0.0),
            (-0.8, 0.1, 0.0),
            (-0.8, -0.1, 0.0),
            
            (0.0, 0.0, 0.0),
            (0.0, 1.0, 0.0),
            (0.1, 0.8, 0.0),
            (-0.1, 0.8, 0.0),
            
            (0.0, 0.0, 0.0),
            (0.0, -1.0, 0.0),
            (0.1, -0.8, 0.0),
            (-0.1, -0.8, 0.0),
        )
        vs = np.array(vs, dtype=np.float32, )
        indices = (
            (0, 1),
            (1, 2),
            (1, 3),
            
            (0 + 4 * 1, 1 + 4 * 1),
            (1 + 4 * 1, 2 + 4 * 1),
            (1 + 4 * 1, 3 + 4 * 1),
            
            (0 + 4 * 2, 1 + 4 * 2),
            (1 + 4 * 2, 2 + 4 * 2),
            (1 + 4 * 2, 3 + 4 * 2),
            
            (0 + 4 * 3, 1 + 4 * 3),
            (1 + 4 * 3, 2 + 4 * 3),
            (1 + 4 * 3, 3 + 4 * 3),
        )
        indices = np.array(indices, dtype=np.int32, )
        return vs, indices
    
    @classmethod
    def _count_coords_np(cls, n, r, ):
        rng_r = np.random.default_rng(seed=123, )
        rng_t = np.random.default_rng(seed=456, )
        s = r / 100
        
        def cross(x, y, offset, ):
            vs = (
                (x - s, y, 0.0, ),
                (x + s, y, 0.0, ),
                (x, y - s, 0.0, ),
                (x, y + s, 0.0, ),
            )
            vs = np.array(vs, dtype=np.float32, )
            indices = (
                (0, 1),
                (2, 3),
            )
            indices = np.array(indices, dtype=np.int32, )
            indices = indices + offset
            return vs, indices
        
        r = r * np.sqrt(rng_r.random(n, ))
        theta = rng_t.random(n, ) * 2 * np.pi
        x = r * np.cos(theta)
        y = r * np.sin(theta)
        
        vs = []
        indices = []
        c = 0
        for i in range(n):
            a, b = cross(x[i], y[i], c, )
            c += len(a)
            vs.append(a)
            indices.append(b)
        
        vs = np.concatenate(vs, )
        indices = np.concatenate(indices, )
        
        return vs, indices
    
    @classmethod
    def add(cls, key, cursor='NONE', ):
        if(key in SC5Cursor._cache.keys()):
            if(cursor == cls.RADIUS):
                vs, indices = SC5Cursor._circle2d_coords_np(1.0, 64, 0, 0.0, 0.0, )
            elif(cursor == cls.STRENGTH):
                vs, indices = SC5Cursor._circle2d_coords_np(1.0, 64, 0, 0.0, 0.0, )
            elif(cursor == cls.COUNT):
                # vs, indices = cls._count_coords_np(1, 1.0, )
                vs = np.array(((0.0, 0.0, 0.0, ), (0.0, 0.0, 0.0, ), ), dtype=np.float32, )
                indices = np.array(((0, 1, ), ), dtype=np.int32, )
            elif(cursor == cls.LENGTH):
                vs, indices = cls._arrow_coords_np()
            elif(cursor == cls.NONE):
                return False
            else:
                raise Exception('Unknown cursor type')
            
            vertex_shader, fragment_shader, _ = load_shader_code('BRUSH')
            shader = GPUShader(vertex_shader, fragment_shader, )
            batch = batch_for_shader(shader, 'LINES', {'position': vs, }, indices=indices, )
            cls._cache[key] = {
                'draw': False,
                'shader': shader,
                'batch': batch,
                'cursor': cursor,
                'matrix': Matrix(),
                'color': (0.9, 0.9, 0.9, 1.0, ),
            }
            cls._tag_redraw()
            return True
        return False
    
    @classmethod
    def remove(cls, key, ):
        if(key not in cls._cache.keys()):
            return False
        del cls._cache[key]
        cls._tag_redraw()
        return True
    
    @classmethod
    def _draw(cls, key, ):
        bgl.glEnable(bgl.GL_BLEND)
        bgl.glEnable(bgl.GL_LINE_SMOOTH)
        
        c = cls._cache[key]
        shader = c['shader']
        batch = c['batch']
        
        shader.bind()
        shader.uniform_float("model", c['matrix'])
        shader.uniform_float("view", bpy.context.region_data.view_matrix)
        shader.uniform_float("projection", bpy.context.region_data.window_matrix)
        shader.uniform_float('color', c['color'])
        batch.draw(shader)
        
        bgl.glDisable(bgl.GL_BLEND)
        bgl.glDisable(bgl.GL_LINE_SMOOTH)
        
        return True
    
    @classmethod
    def update(cls, key, enable=True, value=None, color=None, extra=1.0, ):
        if(key not in cls._cache.keys()):
            return False
        
        c = cls._cache[key]
        
        if(not enable):
            c['draw'] = False
            cls._tag_redraw()
            return True
        else:
            c['draw'] = True
        
        if(c['cursor'] == cls.COUNT):
            vs, indices = cls._count_coords_np(value, 1.0, )
            c['batch'] = batch_for_shader(c['shader'], 'LINES', {'position': vs, }, indices=indices, )
        
        m = Matrix(SC5Cursor._cache[key]['matrix'])
        if(value is not None):
            loc, rot, sca = m.decompose()
            mt = Matrix.Translation(loc, )
            mr = rot.to_matrix().to_4x4()
            if(c['cursor'] == cls.COUNT):
                ms = Matrix.Scale(1 * extra, 4, )
            else:
                ms = Matrix.Scale(1 * value, 4, )
            m = mt @ mr @ ms
        c['matrix'] = m
        
        if(color is not None):
            c['color'] = color
        
        cls._tag_redraw()
        return True
    
    @classmethod
    def _tag_redraw(cls, ):
        for window in bpy.context.window_manager.windows:
            for area in window.screen.areas:
                if(area.type == 'VIEW_3D'):
                    area.tag_redraw()


class SC5GestureCursor2D():
    _cache = {}
    _handle = None
    _initialized = False
    
    NONE = 'NONE'
    RADIUS = 'RADIUS'
    STRENGTH = 'STRENGTH'
    COUNT = 'COUNT'
    LENGTH = 'LENGTH'
    
    @classmethod
    def init(cls, ):
        if(cls._initialized):
            return
        
        cls._cache = {}
        cls._handle = bpy.types.SpaceView3D.draw_handler_add(cls._draw_handler, (), 'WINDOW', 'POST_PIXEL', )
        cls._initialized = True
        cls._tag_redraw()
    
    @classmethod
    def deinit(cls, ):
        if(not cls._initialized):
            return
        
        bpy.types.SpaceView3D.draw_handler_remove(cls._handle, 'WINDOW', )
        cls._handle = None
        cls._cache = {}
        cls._initialized = False
    
    @classmethod
    def _draw_handler(cls, ):
        for k, v in cls._cache.items():
            if(v['draw']):
                if(v['cursor'] is not cls.NONE):
                    cls._draw(k, )
    
    @classmethod
    def _arrow_coords_np(cls, ):
        vs = (
            (0.0, 0.0, ),
            (1.0, 0.0, ),
            (0.8, 0.1, ),
            (0.8, -0.1, ),
            
            (0.0, 0.0, ),
            (-1.0, 0.0, ),
            (-0.8, 0.1, ),
            (-0.8, -0.1, ),
            
            (0.0, 0.0, ),
            (0.0, 1.0, ),
            (0.1, 0.8, ),
            (-0.1, 0.8, ),
            
            (0.0, 0.0, ),
            (0.0, -1.0, ),
            (0.1, -0.8, ),
            (-0.1, -0.8, ),
        )
        vs = np.array(vs, dtype=np.float32, )
        indices = (
            (0, 1),
            (1, 2),
            (1, 3),
            
            (0 + 4 * 1, 1 + 4 * 1),
            (1 + 4 * 1, 2 + 4 * 1),
            (1 + 4 * 1, 3 + 4 * 1),
            
            (0 + 4 * 2, 1 + 4 * 2),
            (1 + 4 * 2, 2 + 4 * 2),
            (1 + 4 * 2, 3 + 4 * 2),
            
            (0 + 4 * 3, 1 + 4 * 3),
            (1 + 4 * 3, 2 + 4 * 3),
            (1 + 4 * 3, 3 + 4 * 3),
        )
        indices = np.array(indices, dtype=np.int32, )
        return vs, indices
    
    @classmethod
    def _count_coords_np(cls, n, r, ):
        rng_r = np.random.default_rng(seed=123, )
        rng_t = np.random.default_rng(seed=456, )
        s = r / 100
        
        def cross(x, y, offset, ):
            vs = (
                (x - s, y, ),
                (x + s, y, ),
                (x, y - s, ),
                (x, y + s, ),
            )
            vs = np.array(vs, dtype=np.float32, )
            indices = (
                (0, 1),
                (2, 3),
            )
            indices = np.array(indices, dtype=np.int32, )
            indices = indices + offset
            return vs, indices
        
        r = r * np.sqrt(rng_r.random(n, ))
        theta = rng_t.random(n, ) * 2 * np.pi
        x = r * np.cos(theta)
        y = r * np.sin(theta)
        
        vs = []
        indices = []
        c = 0
        for i in range(n):
            a, b = cross(x[i], y[i], c, )
            c += len(a)
            vs.append(a)
            indices.append(b)
        
        vs = np.concatenate(vs, )
        indices = np.concatenate(indices, )
        
        return vs, indices
    
    @classmethod
    def add(cls, key, cursor='NONE', ):
        if(key in SC5Cursor2D._cache.keys()):
            if(cursor == cls.RADIUS):
                vs, indices = SC5Cursor2D._circle2d_coords_np(1.0, 64, 0, 0.0, 0.0, )
            elif(cursor == cls.STRENGTH):
                vs, indices = SC5Cursor2D._circle2d_coords_np(1.0, 64, 0, 0.0, 0.0, )
            elif(cursor == cls.COUNT):
                vs = np.array(((0.0, 0.0, ), (0.0, 0.0, ), ), dtype=np.float32, )
                indices = np.array(((0, 1, ), ), dtype=np.int32, )
            elif(cursor == cls.LENGTH):
                vs, indices = cls._arrow_coords_np()
            elif(cursor == cls.NONE):
                return False
            else:
                raise Exception('Unknown cursor type')
            
            vertex_shader, fragment_shader, _ = load_shader_code('BRUSH_2D')
            shader = GPUShader(vertex_shader, fragment_shader, )
            batch = batch_for_shader(shader, 'LINES', {'position': vs, }, indices=indices, )
            cls._cache[key] = {
                'draw': False,
                'shader': shader,
                'batch': batch,
                'cursor': cursor,
                'coordinates': (0.0, 0.0, ),
                'radius': 0.0,
                'color': (0.9, 0.9, 0.9, 1.0, ),
            }
            cls._tag_redraw()
            return True
        return False
    
    @classmethod
    def remove(cls, key, ):
        if(key not in cls._cache.keys()):
            return False
        del cls._cache[key]
        cls._tag_redraw()
        return True
    
    @classmethod
    def _draw(cls, key, ):
        bgl.glEnable(bgl.GL_BLEND)
        bgl.glEnable(bgl.GL_LINE_SMOOTH)
        
        c = cls._cache[key]
        shader = c['shader']
        batch = c['batch']
        
        shader.bind()
        
        matrix = gpu.matrix.get_projection_matrix()
        shader.uniform_float('viewProjectionMatrix', matrix)
        shader.uniform_float('coordinates', c['coordinates'])
        shader.uniform_float('radius', c['radius'])
        shader.uniform_float('color', c['color'])
        
        batch.draw(shader)
        
        bgl.glDisable(bgl.GL_BLEND)
        bgl.glDisable(bgl.GL_LINE_SMOOTH)
        
        return True
    
    @classmethod
    def update(cls, key, enable=True, value=None, color=None, extra=1.0, ):
        if(key not in cls._cache.keys()):
            return False
        
        c = cls._cache[key]
        
        if(not enable):
            c['draw'] = False
            cls._tag_redraw()
            return True
        else:
            c['draw'] = True
        
        if(c['cursor'] == cls.COUNT):
            vs, indices = cls._count_coords_np(value, 1.0, )
            c['batch'] = batch_for_shader(c['shader'], 'LINES', {'position': vs, }, indices=indices, )
        
        coords = SC5Cursor2D._cache[key]['coordinates']
        # radius = SC5Cursor2D._cache[key]['radius']
        
        # TODO: have a look why i need to take half of value.. it seems strange to me..
        radius = value / 2
        if(c['cursor'] == cls.COUNT):
            radius = extra / 2
        
        # m = Matrix(SC5Cursor._cache[key]['matrix'])
        # if(value is not None):
        #     loc, rot, sca = m.decompose()
        #     mt = Matrix.Translation(loc, )
        #     mr = rot.to_matrix().to_4x4()
        #     if(c['cursor'] == cls.COUNT):
        #         ms = Matrix.Scale(1 * extra, 4, )
        #     else:
        #         ms = Matrix.Scale(1 * value, 4, )
        #     m = mt @ mr @ ms
        # c['matrix'] = m
        
        c['coordinates'] = coords
        c['radius'] = radius
        
        if(color is not None):
            c['color'] = color
        
        cls._tag_redraw()
        return True
    
    @classmethod
    def _tag_redraw(cls, ):
        for window in bpy.context.window_manager.windows:
            for area in window.screen.areas:
                if(area.type == 'VIEW_3D'):
                    area.tag_redraw()


class SC5Stats():
    _cache = {}
    _handle = None
    _initialized = False
    
    logo_beta_vs = [(0.2907400131225586, 0.12975230813026428, 0.0), (0.3201458156108856, 0.12973013520240784, 0.0), (0.3205573558807373, 0.12966430187225342, 0.0), (0.3209274709224701, 0.129555806517601, 0.0), (0.32125529646873474, 0.1294056624174118, 0.0), (0.3215399384498596, 0.12921488285064697, 0.0), (0.3217804729938507, 0.1289844661951065, 0.0), (0.32197603583335876, 0.1287154257297516, 0.0), (0.32212573289871216, 0.1284087747335434, 0.0), (0.32222867012023926, 0.12806552648544312, 0.0), (0.32228395342826843, 0.12768667936325073, 0.0), (0.32229068875312805, 0.12727324664592743, 0.0), (0.3210456371307373, 0.11875903606414795, 0.0), (0.2981710433959961, 0.12024323642253876, 0.0), (0.29573825001716614, 0.10538142919540405, 0.0), (0.3032175302505493, 0.10468310117721558, 0.0), (0.30757278203964233, 0.10381081700325012, 0.0), (0.31176432967185974, 0.10235819965600967, 0.0), (0.31378108263015747, 0.10135488212108612, 0.0), (0.3163819909095764, 0.09962792694568634, 0.0), (0.3175017833709717, 0.09865819662809372, 0.0), (0.3185022473335266, 0.09761825203895569, 0.0), (0.31938421726226807, 0.09650854766368866, 0.0), (0.3201485276222229, 0.09532954543828964, 0.0), (0.32079601287841797, 0.09408169984817505, 0.0), (0.32132747769355774, 0.09276548027992249, 0.0), (0.32174378633499146, 0.09138134121894836, 0.0), (0.32223424315452576, 0.08841116726398468, 0.0), (0.32225459814071655, 0.084585040807724, 0.0), (0.32165172696113586, 0.08035586774349213, 0.0), (0.32040536403656006, 0.07645953446626663, 0.0), (0.31954559683799744, 0.0746345967054367, 0.0), (0.3173622488975525, 0.07122797518968582, 0.0), (0.3145730495452881, 0.06814146041870117, 0.0), (0.31119304895401, 0.06536995619535446, 0.0), (0.30732491612434387, 0.06286340206861496, 0.0), (0.30330905318260193, 0.0607474111020565, 0.0), (0.2970151901245117, 0.058296993374824524, 0.0), (0.2926439344882965, 0.05713993310928345, 0.0), (0.2817341089248657, 0.05581008642911911, 0.0), (0.2815231382846832, 0.05632384121417999, 0.0), (0.2814771234989166, 0.056486811488866806, 0.0), (0.28078025579452515, 0.06254927814006805, 0.0), (0.28079459071159363, 0.06292788684368134, 0.0), (0.28084850311279297, 0.06327255815267563, 0.0), (0.28094184398651123, 0.06358372420072556, 0.0), (0.28107455372810364, 0.06386180967092514, 0.0), (0.28124651312828064, 0.0641072541475296, 0.0), (0.2814576327800751, 0.06432048231363297, 0.0), (0.2817078232765198, 0.06450192630290985, 0.0), (0.2819969654083252, 0.06465201824903488, 0.0), (0.28232496976852417, 0.06477119028568268, 0.0), (0.28937169909477234, 0.06589510291814804, 0.0), (0.2954253852367401, 0.06762415915727615, 0.0), (0.30120500922203064, 0.0702599287033081, 0.0), (0.30429592728614807, 0.07222548872232437, 0.0), (0.305703729391098, 0.07338070869445801, 0.0), (0.30753588676452637, 0.0753517895936966, 0.0), (0.30827638506889343, 0.07639683037996292, 0.0), (0.30890244245529175, 0.077479787170887, 0.0), (0.3094159960746765, 0.07859934866428375, 0.0), (0.30981898307800293, 0.07975419610738754, 0.0), (0.3101133704185486, 0.0809430256485939, 0.0), (0.31030112504959106, 0.08216451853513718, 0.0), (0.3103644847869873, 0.08470024913549423, 0.0), (0.310024619102478, 0.08735086768865585, 0.0), (0.30968520045280457, 0.08856570720672607, 0.0), (0.3091775178909302, 0.08966077864170074, 0.0), (0.3088631331920624, 0.09016404300928116, 0.0), (0.30811840295791626, 0.09108329564332962, 0.0), (0.3072258234024048, 0.09188787639141083, 0.0), (0.3061935305595398, 0.09257981926202774, 0.0), (0.30492714047431946, 0.09321346133947372, 0.0), (0.30350029468536377, 0.0937717854976654, 0.0), (0.30056232213974, 0.09454905241727829, 0.0), (0.28632789850234985, 0.0956968143582344, 0.0), (0.28601208329200745, 0.09578179568052292, 0.0), (0.2857222259044647, 0.0959068313241005, 0.0), (0.28546053171157837, 0.09606872498989105, 0.0), (0.2852292060852051, 0.09626428037881851, 0.0), (0.2850304841995239, 0.09649030864238739, 0.0), (0.2848665714263916, 0.0967436134815216, 0.0), (0.2847396731376648, 0.09702099859714508, 0.0), (0.2846520245075226, 0.09731926769018173, 0.0), (0.28460583090782166, 0.09763523191213608, 0.0), (0.2846032977104187, 0.09796570241451263, 0.0), (0.03170831501483917, 0.10323977470397949, 0.0), (0.03253823518753052, 0.10556338727474213, 0.0), (0.03363070636987686, 0.10767890512943268, 0.0), (0.03497263416647911, 0.10959596186876297, 0.0), (0.03655093163251877, 0.11132419854402542, 0.0), (0.03835250064730644, 0.11287326365709305, 0.0), (0.04036425054073334, 0.11425280570983887, 0.0), (0.04244827851653099, 0.11540178954601288, 0.0), (0.04459776729345322, 0.11633029580116272, 0.0), (0.0468142107129097, 0.11704450845718384, 0.0), (0.049099091440439224, 0.11755061894655228, 0.0), (0.05388014763593674, 0.11796331405639648, 0.0), (0.05388014763593674, 0.10918505489826202, 0.0), (0.05176253616809845, 0.1089133620262146, 0.0), (0.04976557940244675, 0.1084044948220253, 0.0), (0.0478951521217823, 0.10764794051647186, 0.0), (0.04615713655948639, 0.10663320869207382, 0.0), (0.04455741494894028, 0.10534978657960892, 0.0), (0.04310185834765434, 0.10378717631101608, 0.0), (0.04220442846417427, 0.10254529118537903, 0.0), (0.041471000760793686, 0.10123741626739502, 0.0), (0.040897659957408905, 0.09985867887735367, 0.0), (0.04048048332333565, 0.09840423613786697, 0.0), (0.04021555557847023, 0.09686921536922455, 0.0), (0.04009895399212837, 0.0952487587928772, 0.0), (0.05731486156582832, 0.0952487587928772, 0.0), (0.05731569603085518, 0.08211147040128708, 0.0), (0.0568198636174202, 0.07822554558515549, 0.0), (0.05634661391377449, 0.07639332860708237, 0.0), (0.05496566742658615, 0.07294335216283798, 0.0), (0.053027085959911346, 0.06976989656686783, 0.0), (0.05055681988596916, 0.06686168164014816, 0.0), (0.047580815851688385, 0.06420741230249405, 0.0), (0.04436961188912392, 0.06197981536388397, 0.0), (0.0409998893737793, 0.060198746621608734, 0.0), (0.0374777615070343, 0.05883951857686043, 0.0), (0.033809348940849304, 0.057877447456121445, 0.0), (0.030000761151313782, 0.05728783458471298, 0.0), (0.02605811133980751, 0.057045988738536835, 0.0), (0.02605811133980751, 0.06584399193525314, 0.0), (0.030474979430437088, 0.06630110740661621, 0.0), (0.034430354833602905, 0.06719766557216644, 0.0), (0.0363163948059082, 0.06787101924419403, 0.0), (0.03813423216342926, 0.06870685517787933, 0.0), (0.03987853229045868, 0.0697144940495491, 0.0), (0.04154396057128906, 0.07090327143669128, 0.0), (0.043613843619823456, 0.07279510796070099, 0.0), (0.045293621718883514, 0.07488100975751877, 0.0), (0.04599246382713318, 0.07599389553070068, 0.0), (0.047118548303842545, 0.07835385203361511, 0.0), (0.04789647087454796, 0.080885149538517, 0.0), (0.04834301397204399, 0.0835786983370781, 0.0), (0.04849523678421974, 0.08667366951704025, 0.0), (0.04849359393119812, 0.08668990433216095, 0.0), (0.048488911241292953, 0.08670622110366821, 0.0), (0.04848156496882439, 0.08672269433736801, 0.0), (0.04847192391753197, 0.08673939853906631, 0.0), (0.04835694283246994, 0.08689093589782715, 0.0), (0.047301143407821655, 0.08445091545581818, 0.0), (0.04607582092285156, 0.08226974308490753, 0.0), (0.044687844812870026, 0.08033563196659088, 0.0), (0.04314408451318741, 0.0786367729306221, 0.0), (0.041451409459114075, 0.07716137915849686, 0.0), (0.03961668908596039, 0.07589764893054962, 0.0), (0.03764679655432701, 0.07483378797769547, 0.0), (0.03554859757423401, 0.07395800203084946, 0.0), (0.030994758009910583, 0.07272345572710037, 0.0), (0.02601013332605362, 0.07209966331720352, 0.0), (0.02601013332605362, 0.08098796755075455, 0.0), (0.02824319526553154, 0.0812794417142868, 0.0), (0.030339926481246948, 0.08183364570140839, 0.0), (0.03229287639260292, 0.08266124129295349, 0.0), (0.03409460186958313, 0.08377288281917572, 0.0), (0.03493642807006836, 0.08443855494260788, 0.0), (0.03649734705686569, 0.08599625527858734, 0.0), (0.03763901814818382, 0.08749609440565109, 0.0), (0.0383775420486927, 0.08876880258321762, 0.0), (0.0389631912112236, 0.09010465443134308, 0.0), (0.03938906639814377, 0.0914795771241188, 0.0), (0.03964827209711075, 0.09286951273679733, 0.0), (0.03973390907049179, 0.0942503958940506, 0.0), (0.03970947861671448, 0.09492991119623184, 0.0), (0.022866111248731613, 0.09492991119623184, 0.0), (0.022880027070641518, 0.11010055243968964, 0.0), (0.02313265949487686, 0.11198396235704422, 0.0), (0.023581910878419876, 0.11380450427532196, 0.0), (0.02421390637755394, 0.11556696891784668, 0.0), (0.025970619171857834, 0.11893679201602936, 0.0), (0.02824445068836212, 0.12206391245126724, 0.0), (0.03083445504307747, 0.12475688755512238, 0.0), (0.033718131482601166, 0.12704385817050934, 0.0), (0.0368729829788208, 0.12895295023918152, 0.0), (0.040276508778333664, 0.1305123120546341, 0.0), (0.043906211853027344, 0.13175006210803986, 0.0), (0.047151416540145874, 0.1325170397758484, 0.0), (0.05047125369310379, 0.13296295702457428, 0.0), (0.05388578772544861, 0.1331072896718979, 0.0), (0.05388578772544861, 0.12439675629138947, 0.0), (0.048012625426054, 0.12359821796417236, 0.0), (0.04544142261147499, 0.1229378804564476, 0.0), (0.04300694540143013, 0.1220429539680481, 0.0), (0.04072408750653267, 0.12089187651872635, 0.0), (0.03860774263739586, 0.11946309357881546, 0.0), (0.03667281195521355, 0.11773505806922913, 0.0), (0.03493418172001839, 0.11568622291088104, 0.0), (0.03402387723326683, 0.11431637406349182, 0.0), (0.033266209065914154, 0.1128896176815033, 0.0), (0.03265342116355896, 0.1114092543721199, 0.0), (0.032177750021219254, 0.10987856984138489, 0.0), (0.03160671144723892, 0.10667940229177475, 0.0), (0.03144019842147827, 0.10332442075014114, 0.0), (0.06863784790039062, 0.0857340395450592, 0.0), (0.07587134838104248, 0.0857340395450592, 0.0), (0.07587699592113495, 0.08386608958244324, 0.0), (0.07592873275279999, 0.08333121985197067, 0.0), (0.07603076845407486, 0.08282571285963058, 0.0), (0.07618166506290436, 0.08235177397727966, 0.0), (0.07637998461723328, 0.0819116085767746, 0.0), (0.07662428170442581, 0.08150741457939148, 0.0), (0.07691311836242676, 0.0811414048075676, 0.0), (0.07724505662918091, 0.08081577718257904, 0.0), (0.07761865109205246, 0.0805327445268631, 0.0), (0.0780324637889862, 0.08029450476169586, 0.0), (0.07848504930734634, 0.08010326325893402, 0.0), (0.07897497713565826, 0.07996122539043427, 0.0), (0.07950080186128616, 0.07987058162689209, 0.0), (0.08111514896154404, 0.07977642118930817, 0.0), (0.08272949606180191, 0.07987058162689209, 0.0), (0.08322355151176453, 0.07995118200778961, 0.0), (0.08368206769227982, 0.08007259666919708, 0.0), (0.08410421013832092, 0.08023414015769958, 0.0), (0.0844891369342804, 0.0804351270198822, 0.0), (0.08483599871397018, 0.08067487925291061, 0.0), (0.08514395356178284, 0.0809527039527893, 0.0), (0.0854121670126915, 0.08126791566610336, 0.0), (0.08563978970050812, 0.08161982893943787, 0.0), (0.08582597970962524, 0.0820077583193779, 0.0), (0.08596989512443542, 0.08243101090192795, 0.0), (0.08607069402933121, 0.08288890868425369, 0.0), (0.08612751960754395, 0.08338075876235962, 0.0), (0.08610917627811432, 0.08869118243455887, 0.0), (0.08604899048805237, 0.08905527740716934, 0.0), (0.0859561488032341, 0.08939697593450546, 0.0), (0.08583138138055801, 0.0897163674235344, 0.0), (0.08567541092634201, 0.0900135412812233, 0.0), (0.08548896759748459, 0.09028857946395874, 0.0), (0.08527277410030365, 0.09054157882928848, 0.0), (0.0850275531411171, 0.09077262133359909, 0.0), (0.08475402742624283, 0.09098179638385773, 0.0), (0.08445292711257935, 0.09116918593645096, 0.0), (0.08412498235702515, 0.09133488684892654, 0.0), (0.07375746220350266, 0.09524311870336533, 0.0), (0.07270777225494385, 0.09584804624319077, 0.0), (0.0717928409576416, 0.09656858444213867, 0.0), (0.0710110291838646, 0.09740135818719864, 0.0), (0.0703606903553009, 0.09834299981594086, 0.0), (0.06984017789363861, 0.09939014166593552, 0.0), (0.0694478452205658, 0.10053941607475281, 0.0), (0.06899168342351913, 0.10285434871912003, 0.0), (0.06891432404518127, 0.10517994314432144, 0.0), (0.06903024762868881, 0.10634536296129227, 0.0), (0.06925592571496964, 0.10751180350780487, 0.0), (0.06976058334112167, 0.10912435501813889, 0.0), (0.07046052068471909, 0.11058147996664047, 0.0), (0.07135817408561707, 0.11187447607517242, 0.0), (0.0724559798836708, 0.11299464851617813, 0.0), (0.07375635951757431, 0.11393328756093979, 0.0), (0.07526174187660217, 0.11468169093132019, 0.0), (0.07761482894420624, 0.11545941233634949, 0.0), (0.0799543559551239, 0.11587798595428467, 0.0), (0.08227475732564926, 0.11592676490545273, 0.0), (0.08457046002149582, 0.11559508740901947, 0.0), (0.08683589845895767, 0.1148722916841507, 0.0), (0.08906550705432892, 0.11374771595001221, 0.0), (0.08993734419345856, 0.11317026615142822, 0.0), (0.0907168984413147, 0.11254186928272247, 0.0), (0.09140408039093018, 0.11186354607343674, 0.0), (0.09199880063533783, 0.1111363098025322, 0.0), (0.09250097721815109, 0.11036118119955063, 0.0), (0.0929105132818222, 0.10953918099403381, 0.0), (0.0932273268699646, 0.10867132991552353, 0.0), (0.09345132857561111, 0.10775864869356155, 0.0), (0.09358242899179459, 0.10680215060710907, 0.0), (0.09362054616212845, 0.10580285638570786, 0.0), (0.0934174656867981, 0.10367995500564575, 0.0), (0.08640128374099731, 0.10367995500564575, 0.0), (0.08614163100719452, 0.10608402639627457, 0.0), (0.08599337190389633, 0.10671868175268173, 0.0), (0.08579281717538834, 0.10729648917913437, 0.0), (0.08554013073444366, 0.10781750828027725, 0.0), (0.08523546904325485, 0.10828180611133575, 0.0), (0.08487898856401443, 0.10868943482637405, 0.0), (0.08447084575891495, 0.10904044657945633, 0.0), (0.08401118963956833, 0.10933490842580795, 0.0), (0.08350018411874771, 0.1095728799700737, 0.0), (0.08293798565864563, 0.10975442081689835, 0.0), (0.08232475072145462, 0.10987958312034607, 0.0), (0.08166064321994781, 0.10994842648506165, 0.0), (0.0803164690732956, 0.10991962999105453, 0.0), (0.07972630113363266, 0.10982272028923035, 0.0), (0.07917685806751251, 0.1096709594130516, 0.0), (0.07866969704627991, 0.10946503281593323, 0.0), (0.07820636034011841, 0.10920561105012894, 0.0), (0.07778839021921158, 0.10889337211847305, 0.0), (0.07741734385490417, 0.1085289865732193, 0.0), (0.07709476351737976, 0.108113132417202, 0.0), (0.0768221989274025, 0.10764649510383606, 0.0), (0.07660119980573654, 0.10712973773479462, 0.0), (0.07643331587314606, 0.10656354576349258, 0.0), (0.0763200968503952, 0.10594858229160309, 0.0), (0.07623458653688431, 0.10483109205961227, 0.0), (0.07633137702941895, 0.10257667303085327, 0.0), (0.07637655735015869, 0.10225274413824081, 0.0), (0.07644937187433243, 0.10194560885429382, 0.0), (0.07654887437820435, 0.10165548324584961, 0.0), (0.07667413353919983, 0.10138258337974548, 0.0), (0.07682420313358307, 0.10112711787223816, 0.0), (0.07699814438819885, 0.10088931024074554, 0.0), (0.07719501852989197, 0.10066936910152435, 0.0), (0.0774138793349266, 0.10046751797199249, 0.0), (0.07765379548072815, 0.10028396546840668, 0.0), (0.07819300889968872, 0.09997263550758362, 0.0), (0.08872868120670319, 0.09615582972764969, 0.0), (0.09016906470060349, 0.0952894538640976, 0.0), (0.09079504758119583, 0.09478527307510376, 0.0), (0.09135650843381882, 0.094233438372612, 0.0), (0.09185216575860977, 0.09363370388746262, 0.0), (0.09228073060512543, 0.09298582375049591, 0.0), (0.09264092892408371, 0.09228955209255219, 0.0), (0.09293147176504135, 0.09154464304447174, 0.0), (0.09315107017755508, 0.09075085818767548, 0.0), (0.09329845011234283, 0.0899079442024231, 0.0), (0.09344355762004852, 0.08523198217153549, 0.0), (0.09320861846208572, 0.08256246894598007, 0.0), (0.09297195076942444, 0.08141172677278519, 0.0), (0.0926528200507164, 0.0803472176194191, 0.0), (0.09225119650363922, 0.07936771214008331, 0.0), (0.09176705032587051, 0.07847197353839874, 0.0), (0.09120035171508789, 0.0776587724685669, 0.0), (0.09055107831954956, 0.07692687213420868, 0.0), (0.08981919288635254, 0.07627503573894501, 0.0), (0.08900466561317444, 0.07570202648639679, 0.0), (0.08810747414827347, 0.07520661503076553, 0.0), (0.08712758123874664, 0.07478756457567215, 0.0), (0.08606495708227158, 0.07444363832473755, 0.0), (0.08332673460245132, 0.0739184245467186, 0.0), (0.0801573395729065, 0.07379338145256042, 0.0), (0.0785847157239914, 0.07394829392433167, 0.0), (0.07702275365591049, 0.07426466047763824, 0.0), (0.07547341287136078, 0.07475487142801285, 0.0), (0.07429319620132446, 0.07525983452796936, 0.0), (0.07322236150503159, 0.07584051042795181, 0.0), (0.07226140052080154, 0.07649654895067215, 0.0), (0.07141079753637314, 0.07722759991884232, 0.0), (0.07067105174064636, 0.07803330570459366, 0.0), (0.07004264742136002, 0.07891331613063812, 0.0), (0.0695260763168335, 0.07986728101968765, 0.0), (0.0691218301653862, 0.0808948427438736, 0.0), (0.06883039325475693, 0.0819956511259079, 0.0), (0.06865225732326508, 0.0831693559885025, 0.0), (0.06858791410923004, 0.08441559970378876, 0.0), (0.07783283293247223, 0.05327621102333069, 0.0), (0.07828722894191742, 0.059729404747486115, 0.0), (0.07857459783554077, 0.06094357743859291, 0.0), (0.07900591939687729, 0.0620906688272953, 0.0), (0.07957004755735397, 0.06316272914409637, 0.0), (0.08025582134723663, 0.0641518160700798, 0.0), (0.08105210214853287, 0.06504998356103897, 0.0), (0.08194772899150848, 0.06584928184747696, 0.0), (0.08293154835700989, 0.06654176861047745, 0.0), (0.08399241417646408, 0.06711949408054352, 0.0), (0.08511917293071747, 0.06757451593875885, 0.0), (0.08630067110061646, 0.06789889186620712, 0.0), (0.08752576261758804, 0.06808467209339142, 0.0), (0.08878327906131744, 0.06812391430139542, 0.0), (0.09000366181135178, 0.06802599132061005, 0.0), (0.09118158370256424, 0.06780797988176346, 0.0), (0.09230915457010269, 0.06747559458017349, 0.0), (0.09337848424911499, 0.06703454256057739, 0.0), (0.09438168257474899, 0.066490538418293, 0.0), (0.09531086683273315, 0.06584928929805756, 0.0), (0.09615814685821533, 0.0651165172457695, 0.0), (0.09691563248634338, 0.06429792940616608, 0.0), (0.09757543355226517, 0.06339923292398453, 0.0), (0.09812966734170914, 0.06242614611983299, 0.0), (0.09857044368982315, 0.061384379863739014, 0.0), (0.09888987243175507, 0.060279637575149536, 0.0), (0.099210225045681, 0.05817187950015068, 0.0), (0.09901100397109985, 0.04552594944834709, 0.0), (0.09872701019048691, 0.04437657818198204, 0.0), (0.0982704609632492, 0.04322902858257294, 0.0), (0.09764816612005234, 0.042109549045562744, 0.0), (0.0968669205904007, 0.041044387966394424, 0.0), (0.09593352675437927, 0.04005979374051094, 0.0), (0.09485478699207306, 0.03918201103806496, 0.0), (0.09363749623298645, 0.038437288254499435, 0.0), (0.09228846430778503, 0.03785187005996704, 0.0), (0.0908144861459732, 0.037452008575201035, 0.0), (0.08922236412763596, 0.03726394847035408, 0.0), (0.08751890063285828, 0.03731393814086914, 0.0), (0.0862298384308815, 0.037525489926338196, 0.0), (0.08499965071678162, 0.03788566216826439, 0.0), (0.08383829891681671, 0.03838270530104637, 0.0), (0.08275572955608368, 0.039004869759082794, 0.0), (0.0817619115114212, 0.03974040970206261, 0.0), (0.08086679130792618, 0.04057757928967476, 0.0), (0.08008033037185669, 0.0415046326816082, 0.0), (0.07941248267889023, 0.04250982031226158, 0.0), (0.07887320220470428, 0.04358139634132385, 0.0), (0.07847245037555695, 0.044707611203193665, 0.0), (0.0782201811671257, 0.04587671905755997, 0.0), (0.07811928540468216, 0.048108506947755814, 0.0), (0.0781235322356224, 0.05326774716377258, 0.0), (0.09365453571081161, 0.05768933147192001, 0.0), (0.09357547760009766, 0.05832579731941223, 0.0), (0.0934324562549591, 0.0589294508099556, 0.0), (0.09322912991046906, 0.059497106820344925, 0.0), (0.09296914935112, 0.06002558395266533, 0.0), (0.09265617281198502, 0.060511697083711624, 0.0), (0.09229385852813721, 0.060952261090278625, 0.0), (0.09188585728406906, 0.06134409084916115, 0.0), (0.09143581986427307, 0.061684004962444305, 0.0), (0.09094741195440292, 0.061968814581632614, 0.0), (0.09042428433895111, 0.06219533830881119, 0.0), (0.08987008780241013, 0.06236039474606514, 0.0), (0.08928846567869186, 0.06246078759431839, 0.0), (0.08853022754192352, 0.06249939277768135, 0.0), (0.08780451118946075, 0.06244276463985443, 0.0), (0.0871170312166214, 0.06229466572403908, 0.0), (0.0864735022187233, 0.062058862298727036, 0.0), (0.08587963879108429, 0.06173911318182945, 0.0), (0.08534115552902222, 0.061339180916547775, 0.0), (0.08486375957727432, 0.06086282804608345, 0.0), (0.08445316553115845, 0.060313817113637924, 0.0), (0.08411508798599243, 0.059695906937122345, 0.0), (0.08385524153709412, 0.05901286378502846, 0.0), (0.08367934077978134, 0.05826845020055771, 0.0), (0.08359310775995255, 0.05746641755104065, 0.0), (0.08361004292964935, 0.04790937155485153, 0.0), (0.08371032029390335, 0.04713362827897072, 0.0), (0.08384596556425095, 0.0466129407286644, 0.0), (0.08425061404705048, 0.045604366809129715, 0.0), (0.08464299887418747, 0.04491274803876877, 0.0), (0.0849500223994255, 0.044496193528175354, 0.0), (0.0852990448474884, 0.0441245399415493, 0.0), (0.08568503707647324, 0.04379848390817642, 0.0), (0.08610295504331589, 0.04351872205734253, 0.0), (0.08654776215553284, 0.043285951018333435, 0.0), (0.08701442182064056, 0.04310086369514465, 0.0), (0.08749789744615555, 0.042964156717061996, 0.0), (0.08799315243959427, 0.04287652671337128, 0.0), (0.0884951502084732, 0.04283866658806801, 0.0), (0.08899885416030884, 0.0428512766957283, 0.0), (0.08949922025203705, 0.04291504994034767, 0.0), (0.08999121189117432, 0.04303067922592163, 0.0), (0.09049124270677567, 0.04320388287305832, 0.0), (0.09096383303403854, 0.04342307522892952, 0.0), (0.09140659123659134, 0.04368627816438675, 0.0), (0.09181712567806244, 0.043991513550281525, 0.0), (0.09219305217266083, 0.044336799532175064, 0.0), (0.0925319716334343, 0.044720157980918884, 0.0), (0.09283149987459183, 0.0451396107673645, 0.0), (0.09308924525976181, 0.045593179762363434, 0.0), (0.09330280870199203, 0.0460788831114769, 0.0), (0.09346980601549149, 0.04659474641084671, 0.0), (0.09358784556388855, 0.04713878408074379, 0.0), (0.09365453571081161, 0.04770902544260025, 0.0), (0.1255829930305481, 0.10373073816299438, 0.0), (0.11845673620700836, 0.10373073816299438, 0.0), (0.11845390498638153, 0.1054491475224495, 0.0), (0.11832967400550842, 0.10651402175426483, 0.0), (0.11804729700088501, 0.10742300003767014, 0.0), (0.11762795597314835, 0.10818231105804443, 0.0), (0.11709284782409668, 0.10879818350076675, 0.0), (0.11646314710378647, 0.10927685350179672, 0.0), (0.11576005071401596, 0.10962454974651337, 0.0), (0.11500474065542221, 0.10984750092029572, 0.0), (0.11421840637922287, 0.1099519431591034, 0.0), (0.11342222988605499, 0.10994410514831543, 0.0), (0.11263740062713623, 0.10983021557331085, 0.0), (0.11188510805368423, 0.10961651057004929, 0.0), (0.11118653416633606, 0.10930921137332916, 0.0), (0.11104090511798859, 0.10922182351350784, 0.0), (0.11076289415359497, 0.10899829864501953, 0.0), (0.11050757020711899, 0.10872256755828857, 0.0), (0.11028098315000534, 0.10841000080108643, 0.0), (0.11008916050195694, 0.10807595402002335, 0.0), (0.10993814468383789, 0.10773579776287079, 0.0), (0.10968927294015884, 0.10682860016822815, 0.0), (0.10953517258167267, 0.10580840706825256, 0.0), (0.10947281122207642, 0.08350269496440887, 0.0), (0.10960166156291962, 0.08264325559139252, 0.0), (0.10983303934335709, 0.08190616965293884, 0.0), (0.11015975475311279, 0.0812862366437912, 0.0), (0.1105746254324913, 0.08077827095985413, 0.0), (0.11107046902179718, 0.08037707954645157, 0.0), (0.11164011061191559, 0.08007746934890747, 0.0), (0.1122763603925705, 0.07987424731254578, 0.0), (0.11297202855348587, 0.07976222038269043, 0.0), (0.11371994018554688, 0.07973619550466537, 0.0), (0.11451291292905807, 0.07979097962379456, 0.0), (0.1157846748828888, 0.08002869784832001, 0.0), (0.11619038134813309, 0.08016977459192276, 0.0), (0.11656118184328079, 0.08034414052963257, 0.0), (0.11689738184213638, 0.08055134117603302, 0.0), (0.11719927936792374, 0.0807909145951271, 0.0), (0.11746717989444733, 0.08106239885091782, 0.0), (0.11770138889551163, 0.08136533200740814, 0.0), (0.11790221184492111, 0.08169925212860107, 0.0), (0.11806995421648026, 0.0820637047290802, 0.0), (0.11820491403341293, 0.08245822042226791, 0.0), (0.11837770789861679, 0.08333560824394226, 0.0), (0.1185244619846344, 0.08582998067140579, 0.0), (0.12563660740852356, 0.08582998067140579, 0.0), (0.1257382184267044, 0.08326809853315353, 0.0), (0.1255953460931778, 0.08202776312828064, 0.0), (0.12528854608535767, 0.08082034438848495, 0.0), (0.124791719019413, 0.07965023070573807, 0.0), (0.12407872080802917, 0.07852181792259216, 0.0), (0.12331308424472809, 0.07759944349527359, 0.0), (0.12247586995363235, 0.07677676528692245, 0.0), (0.12156794220209122, 0.07605426013469696, 0.0), (0.12059016525745392, 0.07543238997459412, 0.0), (0.1195433959364891, 0.07491163164377213, 0.0), (0.11842850595712662, 0.0744924545288086, 0.0), (0.11658541113138199, 0.07401847094297409, 0.0), (0.1147480383515358, 0.0737772062420845, 0.0), (0.11292117834091187, 0.07376622408628464, 0.0), (0.11110960692167282, 0.0739830881357193, 0.0), (0.10931809991598129, 0.07442537695169449, 0.0), (0.1075514405965805, 0.07509064674377441, 0.0), (0.10596664994955063, 0.07594883441925049, 0.0), (0.10527068376541138, 0.07645193487405777, 0.0), (0.10464104264974594, 0.07700406759977341, 0.0), (0.10407925397157669, 0.0776049867272377, 0.0), (0.103586845099926, 0.07825446128845215, 0.0), (0.10316534340381622, 0.07895226031541824, 0.0), (0.10281628370285034, 0.07969814538955688, 0.0), (0.10254119336605072, 0.08049187809228897, 0.0), (0.10234159231185913, 0.081333227455616, 0.0), (0.10221901535987854, 0.08222196251153946, 0.0), (0.10222098231315613, 0.1074230894446373, 0.0), (0.10233631730079651, 0.10823202133178711, 0.0), (0.10252170264720917, 0.1090017780661583, 0.0), (0.10277500003576279, 0.10973235964775085, 0.0), (0.10309407114982605, 0.1104237511754036, 0.0), (0.10347677767276764, 0.11107593774795532, 0.0), (0.10392098873853683, 0.11168891936540604, 0.0), (0.10442456603050232, 0.11226268112659454, 0.0), (0.10498537123203278, 0.11279721558094025, 0.0), (0.10627012699842453, 0.11374855041503906, 0.0), (0.10802920162677765, 0.11467526853084564, 0.0), (0.11013118922710419, 0.1154380813241005, 0.0), (0.11225810647010803, 0.11586182564496994, 0.0), (0.11332865804433823, 0.1159479171037674, 0.0), (0.11547944694757462, 0.11587128788232803, 0.0), (0.11763712763786316, 0.11546655744314194, 0.0), (0.11979448795318604, 0.11473813652992249, 0.0), (0.12084151059389114, 0.1142379492521286, 0.0), (0.1217949241399765, 0.11364040523767471, 0.0), (0.12265200167894363, 0.11295195668935776, 0.0), (0.12341003865003586, 0.11217907071113586, 0.0), (0.1240663155913353, 0.11132819205522537, 0.0), (0.12461812049150467, 0.11040578037500381, 0.0), (0.1250627338886261, 0.10941829532384872, 0.0), (0.1253974437713623, 0.10837219655513763, 0.0), (0.1256195455789566, 0.10727392882108688, 0.0), (0.12572631239891052, 0.1061299592256546, 0.0), (0.12571503221988678, 0.10494673997163773, 0.0), (0.11015640944242477, 0.05823955684900284, 0.0), (0.11109651625156403, 0.058779701590538025, 0.0), (0.11203646659851074, 0.059202902019023895, 0.0), (0.11298362910747528, 0.059503670781850815, 0.0), (0.113945372402668, 0.05967652425169945, 0.0), (0.11492907255887985, 0.05971597507596016, 0.0), (0.11594208329916, 0.059616535902023315, 0.0), (0.11673586815595627, 0.05944356694817543, 0.0), (0.11749356240034103, 0.05919520556926727, 0.0), (0.11820965260267258, 0.0588751845061779, 0.0), (0.11887861043214798, 0.05848723649978638, 0.0), (0.11949492990970612, 0.058035098016262054, 0.0), (0.12005308270454407, 0.057522498071193695, 0.0), (0.12054756283760071, 0.05695316940546036, 0.0), (0.12097284942865372, 0.0563308447599411, 0.0), (0.12132342159748077, 0.05565926060080528, 0.0), (0.12159376591444016, 0.05494214594364166, 0.0), (0.12177836149930954, 0.0541832372546196, 0.0), (0.1218716949224472, 0.05338626354932785, 0.0), (0.12192118912935257, 0.04448750987648964, 0.0), (0.12186604738235474, 0.043682485818862915, 0.0), (0.12166443467140198, 0.0424506738781929, 0.0), (0.12126866728067398, 0.041324276477098465, 0.0), (0.12070026993751526, 0.040313705801963806, 0.0), (0.11998076736927032, 0.039429374039173126, 0.0), (0.1191316694021225, 0.038681697100400925, 0.0), (0.11817450821399689, 0.0380810908973217, 0.0), (0.11713079363107681, 0.037637971341609955, 0.0), (0.11602205038070679, 0.03736275061964989, 0.0), (0.11486979573965073, 0.037265844643116, 0.0), (0.11369554698467255, 0.037357669323682785, 0.0), (0.11252082884311676, 0.03764863684773445, 0.0), (0.11136716604232788, 0.038149163126945496, 0.0), (0.11006609350442886, 0.038896918296813965, 0.0), (0.11003242433071136, 0.029996616765856743, 0.0), (0.10999734699726105, 0.02979513257741928, 0.0), (0.10994536429643631, 0.02962392196059227, 0.0), (0.10987433046102524, 0.029480691999197006, 0.0), (0.10978209972381592, 0.029363151639699936, 0.0), (0.10966652631759644, 0.029269007965922356, 0.0), (0.10952546447515488, 0.029195968061685562, 0.0), (0.10935676842927933, 0.029141739010810852, 0.0), (0.1089278906583786, 0.029080543667078018, 0.0), (0.10590822249650955, 0.029063139110803604, 0.0), (0.1057140901684761, 0.029085036367177963, 0.0), (0.10554057359695435, 0.029126077890396118, 0.0), (0.10538728535175323, 0.02918613702058792, 0.0), (0.10525383055210114, 0.029265085235238075, 0.0), (0.10513981431722641, 0.029362795874476433, 0.0), (0.10504484921693802, 0.029479140415787697, 0.0), (0.10496854037046432, 0.02961399219930172, 0.0), (0.10491050034761429, 0.029767224565148354, 0.0), (0.10487033426761627, 0.02993871085345745, 0.0), (0.10484765470027924, 0.030128322541713715, 0.0), (0.10485555976629257, 0.05833948776125908, 0.0), (0.10488426685333252, 0.05863335356116295, 0.0), (0.10493405163288116, 0.05887255072593689, 0.0), (0.10501044988632202, 0.05906271934509277, 0.0), (0.1051190048456192, 0.05920950695872307, 0.0), (0.10526524484157562, 0.059318553656339645, 0.0), (0.1054547131061554, 0.059395503252744675, 0.0), (0.10569294542074203, 0.059445999562740326, 0.0), (0.10598547756671906, 0.05947568640112877, 0.0), (0.10900790244340897, 0.05949977785348892, 0.0), (0.1091967523097992, 0.05947360023856163, 0.0), (0.10937119275331497, 0.05942925810813904, 0.0), (0.10953046381473541, 0.05936524271965027, 0.0), (0.10967380553483963, 0.059280045330524445, 0.0), (0.10980044305324554, 0.05917215719819069, 0.0), (0.10990962386131287, 0.059040069580078125, 0.0), (0.11000057309865952, 0.058882273733615875, 0.0), (0.1100725308060646, 0.05869726091623306, 0.0), (0.11012472957372665, 0.05848352238535881, 0.0), (0.11702302098274231, 0.04846806079149246, 0.0), (0.11650653928518295, 0.05229426175355911, 0.0), (0.11640120297670364, 0.05265302211046219, 0.0), (0.11627252399921417, 0.05297400429844856, 0.0), (0.11611997336149216, 0.05325857922434807, 0.0), (0.11594302207231522, 0.05350811779499054, 0.0), (0.11574114114046097, 0.05372399091720581, 0.0), (0.11551380157470703, 0.053907569497823715, 0.0), (0.11526047438383102, 0.054060228168964386, 0.0), (0.11498062312602997, 0.05418333783745766, 0.0), (0.11467372626066208, 0.05427826941013336, 0.0), (0.11397667974233627, 0.05438908562064171, 0.0), (0.11321868002414703, 0.05440043658018112, 0.0), (0.11286968737840652, 0.05436434969305992, 0.0), (0.11253947019577026, 0.05429920554161072, 0.0), (0.11222900450229645, 0.054204754531383514, 0.0), (0.11193927377462387, 0.05408075451850891, 0.0), (0.11167126148939133, 0.05392695963382721, 0.0), (0.11142594367265701, 0.05374312773346901, 0.0), (0.11120430380105972, 0.053529009222984314, 0.0), (0.11100731790065765, 0.05328436195850372, 0.0), (0.1108359694480896, 0.05300894007086754, 0.0), (0.11069123446941376, 0.05270250141620636, 0.0), (0.11057411134243011, 0.05236480385065079, 0.0), (0.11026120185852051, 0.051074981689453125, 0.0), (0.11007373034954071, 0.049780458211898804, 0.0), (0.1100124716758728, 0.04848358407616615, 0.0), (0.11007821559906006, 0.0471867099404335, 0.0), (0.11027174443006516, 0.04589218273758888, 0.0), (0.11059385538101196, 0.04460235685110092, 0.0), (0.11070898920297623, 0.044277507811784744, 0.0), (0.1108493059873581, 0.04398273676633835, 0.0), (0.11101412028074265, 0.04371767118573189, 0.0), (0.11120274662971497, 0.043481938540935516, 0.0), (0.11141449958086014, 0.043275170028209686, 0.0), (0.11164869368076324, 0.04309698939323425, 0.0), (0.11190464347600937, 0.04294702410697937, 0.0), (0.1121816635131836, 0.04282490536570549, 0.0), (0.1124790608882904, 0.04273025691509247, 0.0), (0.11279615759849548, 0.04266270995140076, 0.0), (0.11313226819038391, 0.04262188822031021, 0.0), (0.11387023329734802, 0.04261874035000801, 0.0), (0.11456678807735443, 0.04272029548883438, 0.0), (0.11487912386655807, 0.04281226173043251, 0.0), (0.115167036652565, 0.04293283820152283, 0.0), (0.11543018370866776, 0.043082885444164276, 0.0), (0.11566822975873947, 0.0432632640004158, 0.0), (0.1158808246254921, 0.04347483813762665, 0.0), (0.11606762558221817, 0.04371846839785576, 0.0), (0.11622828990221024, 0.04399501904845238, 0.0), (0.11636247485876083, 0.04430535063147545, 0.0), (0.1164698451757431, 0.04465032368898392, 0.0), (0.14021086692810059, 0.04460235685110092, 0.0), (0.14332951605319977, 0.041869957000017166, 0.0), (0.14343717694282532, 0.04174015298485756, 0.0), (0.14352034032344818, 0.041608817875385284, 0.0), (0.14357951283454895, 0.04147624969482422, 0.0), (0.1436152160167694, 0.04134273901581764, 0.0), (0.14362794160842896, 0.04120858013629913, 0.0), (0.14361821115016937, 0.04107407107949257, 0.0), (0.14358653128147125, 0.04093950241804123, 0.0), (0.14353340864181519, 0.04080516844987869, 0.0), (0.14345934987068176, 0.04067136347293854, 0.0), (0.14336487650871277, 0.04053838178515434, 0.0), (0.1432504653930664, 0.04040651023387909, 0.0), (0.1419392228126526, 0.039234086871147156, 0.0), (0.14051352441310883, 0.038341861218214035, 0.0), (0.13900792598724365, 0.03771845996379852, 0.0), (0.1374569535255432, 0.037352509796619415, 0.0), (0.13589516282081604, 0.03723263368010521, 0.0), (0.13435710966587067, 0.0373474545776844, 0.0), (0.13287732005119324, 0.03768559917807579, 0.0), (0.1314903348684311, 0.03823569416999817, 0.0), (0.13023070991039276, 0.038986366242170334, 0.0), (0.12913298606872559, 0.03992623835802078, 0.0), (0.1282317042350769, 0.04104393720626831, 0.0), (0.12756140530109406, 0.042328089475631714, 0.0), (0.1268775463104248, 0.044387806206941605, 0.0), (0.1264660507440567, 0.046446897089481354, 0.0), (0.12632736563682556, 0.04850473999977112, 0.0), (0.1264619678258896, 0.05056070163846016, 0.0), (0.12687033414840698, 0.052614159882068634, 0.0), (0.12755294144153595, 0.0546644851565361, 0.0), (0.1279185265302658, 0.05545584484934807, 0.0), (0.12835922837257385, 0.05619568005204201, 0.0), (0.12887103855609894, 0.05687902122735977, 0.0), (0.12944993376731873, 0.05750090256333351, 0.0), (0.13009190559387207, 0.05805635824799538, 0.0), (0.13079293072223663, 0.05854041874408722, 0.0), (0.13154898583889008, 0.05894811823964119, 0.0), (0.13235606253147125, 0.05927448719739914, 0.0), (0.13321013748645782, 0.05951455980539322, 0.0), (0.13410718739032745, 0.05966337025165558, 0.0), (0.135043203830719, 0.05971594899892807, 0.0), (0.13601413369178772, 0.059667326509952545, 0.0), (0.13705703616142273, 0.059512875974178314, 0.0), (0.13804131746292114, 0.05927024036645889, 0.0), (0.1389635056257248, 0.058942463248968124, 0.0), (0.1398201435804367, 0.05853259190917015, 0.0), (0.14060774445533752, 0.058043673634529114, 0.0), (0.14132285118103027, 0.057478755712509155, 0.0), (0.1419619917869568, 0.05684088543057442, 0.0), (0.1425216943025589, 0.05613311007618904, 0.0), (0.14299848675727844, 0.05535847693681717, 0.0), (0.14338891208171844, 0.05452003329992294, 0.0), (0.14368949830532074, 0.053620826452970505, 0.0), (0.1439589560031891, 0.052238062024116516, 0.0), (0.14415699243545532, 0.04725398123264313, 0.0), (0.1441272348165512, 0.0470614954829216, 0.0), (0.14407417178153992, 0.04689563810825348, 0.0), (0.14399920403957367, 0.04675467684864998, 0.0), (0.1439037322998047, 0.046636875718832016, 0.0), (0.1437891572713852, 0.046540502458810806, 0.0), (0.1436568945646286, 0.046463821083307266, 0.0), (0.14350832998752594, 0.04640509933233261, 0.0), (0.14334487915039062, 0.046362604945898056, 0.0), (0.14297887682914734, 0.046319350600242615, 0.0), (0.13170450925827026, 0.04632076621055603, 0.0), (0.13179360330104828, 0.045486580580472946, 0.0), (0.13188162446022034, 0.045105282217264175, 0.0), (0.13199856877326965, 0.044747937470674515, 0.0), (0.13214440643787384, 0.044414617121219635, 0.0), (0.13231909275054932, 0.04410538822412491, 0.0), (0.1325225830078125, 0.043820321559906006, 0.0), (0.132754847407341, 0.0435594841837883, 0.0), (0.13301584124565125, 0.04332294687628746, 0.0), (0.13330553472042084, 0.04311077669262886, 0.0), (0.1336238831281662, 0.04292304068803787, 0.0), (0.13397081196308136, 0.04275980591773987, 0.0), (0.13457894325256348, 0.0425444096326828, 0.0), (0.13516780734062195, 0.04241033270955086, 0.0), (0.13573838770389557, 0.042353302240371704, 0.0), (0.13629165291786194, 0.0423690490424633, 0.0), (0.13682857155799866, 0.04245330020785332, 0.0), (0.13735011219978333, 0.04260178282856941, 0.0), (0.13785725831985474, 0.04281022772192955, 0.0), (0.1383509635925293, 0.043074361979961395, 0.0), (0.13930195569992065, 0.04375261068344116, 0.0), (0.13185973465442657, 0.05104144662618637, 0.0), (0.1387997269630432, 0.05104144662618637, 0.0), (0.1387077122926712, 0.051632530987262726, 0.0), (0.13857440650463104, 0.05216989666223526, 0.0), (0.1384001523256302, 0.05265355110168457, 0.0), (0.1381853073835373, 0.05308350548148155, 0.0), (0.13793019950389862, 0.0534597709774971, 0.0), (0.13763518631458282, 0.05378235504031181, 0.0), (0.13730059564113617, 0.054051268845796585, 0.0), (0.1369267851114273, 0.05426651984453201, 0.0), (0.1365140825510025, 0.05442812293767929, 0.0), (0.1360628455877304, 0.05453608185052872, 0.0), (0.1355734020471573, 0.054590411484241486, 0.0), (0.1350460946559906, 0.05459111928939819, 0.0), (0.1345672607421875, 0.054542671889066696, 0.0), (0.1341223418712616, 0.054444774985313416, 0.0), (0.1337127983570099, 0.0542987696826458, 0.0), (0.13334009051322937, 0.05410600081086159, 0.0), (0.13300567865371704, 0.05386781319975853, 0.0), (0.1327110230922699, 0.05358554422855377, 0.0), (0.13245758414268494, 0.05326053872704506, 0.0), (0.13224682211875916, 0.05289413779973984, 0.0), (0.13208019733428955, 0.05248768627643585, 0.0), (0.13195917010307312, 0.05204252526164055, 0.0), (0.13188520073890686, 0.051559995859861374, 0.0), (0.14938609302043915, 0.11553384363651276, 0.0), (0.16071756184101105, 0.07424979656934738, 0.0), (0.15345019102096558, 0.07424979656934738, 0.0), (0.15131089091300964, 0.0829518660902977, 0.0), (0.14137929677963257, 0.0829518660902977, 0.0), (0.1392287164926529, 0.07421875, 0.0), (0.1321391463279724, 0.07421875, 0.0), (0.13216455280780792, 0.0748857706785202, 0.0), (0.132187157869339, 0.07502724230289459, 0.0), (0.13580967485904694, 0.08822643756866455, 0.0), (0.13761331140995026, 0.09479095786809921, 0.0), (0.143062561750412, 0.114675372838974, 0.0), (0.14318835735321045, 0.11498886346817017, 0.0), (0.14326246082782745, 0.11511780321598053, 0.0), (0.1433461308479309, 0.11522887647151947, 0.0), (0.14344093203544617, 0.11532257497310638, 0.0), (0.14354844391345978, 0.11539940536022186, 0.0), (0.1436702162027359, 0.1154598593711853, 0.0), (0.14380782842636108, 0.1155044436454773, 0.0), (0.14396284520626068, 0.11553365737199783, 0.0), (0.14643964171409607, 0.10336674749851227, 0.0), (0.1461743414402008, 0.10334417223930359, 0.0), (0.14385986328125, 0.09360413998365402, 0.0), (0.14269165694713593, 0.08868834376335144, 0.0), (0.14330801367759705, 0.08868834376335144, 0.0), (0.14993645250797272, 0.08868834376335144, 0.0), (0.16880902647972107, 0.10997794568538666, 0.0), (0.1603873372077942, 0.10997794568538666, 0.0), (0.1603873372077942, 0.11544637382030487, 0.0), (0.18443599343299866, 0.11544637382030487, 0.0), (0.18443599343299866, 0.11004285514354706, 0.0), (0.17611026763916016, 0.11004285514354706, 0.0), (0.17611026763916016, 0.07423003762960434, 0.0), (0.16880902647972107, 0.07423003762960434, 0.0), (0.15448595583438873, 0.0583411380648613, 0.0), (0.15589870512485504, 0.05908743292093277, 0.0), (0.15660333633422852, 0.059358395636081696, 0.0), (0.1573069840669632, 0.059559788554906845, 0.0), (0.15800981223583221, 0.05969052016735077, 0.0), (0.1587119698524475, 0.059749506413936615, 0.0), (0.15941359102725983, 0.05973565950989723, 0.0), (0.1601148396730423, 0.05964788794517517, 0.0), (0.16081584990024567, 0.05948510766029358, 0.0), (0.16151677072048187, 0.059246230870485306, 0.0), (0.16221775114536285, 0.0589301697909832, 0.0), (0.16291894018650055, 0.05853583663702011, 0.0), (0.16389566659927368, 0.05782141536474228, 0.0), (0.16470062732696533, 0.05699843913316727, 0.0), (0.16503867506980896, 0.05654876306653023, 0.0), (0.16533374786376953, 0.05607497692108154, 0.0), (0.16558584570884705, 0.0555780865252018, 0.0), (0.16596105694770813, 0.054519038647413254, 0.0), (0.16616423428058624, 0.053379688411951065, 0.0), (0.16627684235572815, 0.0384952574968338, 0.0), (0.16625502705574036, 0.03831581398844719, 0.0), (0.16621723771095276, 0.0381552018225193, 0.0), (0.16616307199001312, 0.03801319748163223, 0.0), (0.1660921275615692, 0.037889573723077774, 0.0), (0.16600401699543, 0.03778410330414772, 0.0), (0.16589832305908203, 0.037696562707424164, 0.0), (0.1657746434211731, 0.0376267284154892, 0.0), (0.16563257575035095, 0.03757437318563461, 0.0), (0.16547173261642456, 0.037539269775152206, 0.0), (0.1652916967868805, 0.03752119466662407, 0.0), (0.16190966963768005, 0.03755778446793556, 0.0), (0.1617150455713272, 0.0375869981944561, 0.0), (0.16155441105365753, 0.03763176128268242, 0.0), (0.16142454743385315, 0.03769576549530029, 0.0), (0.1613222360610962, 0.0377827063202858, 0.0), (0.1612442582845688, 0.03789627552032471, 0.0), (0.16118741035461426, 0.0380401685833931, 0.0), (0.16114848852157593, 0.03821808099746704, 0.0), (0.16112425923347473, 0.03843370079994202, 0.0), (0.16104350984096527, 0.05068378895521164, 0.0), (0.1608840674161911, 0.05179482698440552, 0.0), (0.16077984869480133, 0.05218421295285225, 0.0), (0.16063807904720306, 0.052547212690114975, 0.0), (0.16046106815338135, 0.052882369607686996, 0.0), (0.16025114059448242, 0.05318821966648102, 0.0), (0.16001059114933014, 0.05346330627799034, 0.0), (0.15974174439907074, 0.05370616912841797, 0.0), (0.15944691002368927, 0.053915347903966904, 0.0), (0.15912839770317078, 0.05408938229084015, 0.0), (0.1587885171175003, 0.05422681197524071, 0.0), (0.1584295928478241, 0.05432618036866188, 0.0), (0.1580539345741272, 0.05438602343201637, 0.0), (0.15766385197639465, 0.054404884576797485, 0.0), (0.15725982189178467, 0.05438045412302017, 0.0), (0.1568707674741745, 0.05431266874074936, 0.0), (0.15649931132793427, 0.054203443229198456, 0.0), (0.15614807605743408, 0.054054681211709976, 0.0), (0.15581969916820526, 0.05386829748749733, 0.0), (0.15551680326461792, 0.05364620313048363, 0.0), (0.15524201095104218, 0.05339030548930168, 0.0), (0.15499794483184814, 0.0531025193631649, 0.0), (0.15478724241256714, 0.0527847521007061, 0.0), (0.15461252629756927, 0.05243891477584839, 0.0), (0.15447641909122467, 0.05206691846251488, 0.0), (0.15438154339790344, 0.05167067050933838, 0.0), (0.15431152284145355, 0.05118609219789505, 0.0), (0.15421833097934723, 0.038495540618896484, 0.0), (0.15419305860996246, 0.03825017437338829, 0.0), (0.1541503220796585, 0.038050513714551926, 0.0), (0.15408554673194885, 0.03789180517196655, 0.0), (0.15399417281150818, 0.03776929900050163, 0.0), (0.15387164056301117, 0.03767824172973633, 0.0), (0.1537133753299713, 0.0376138836145401, 0.0), (0.1535148173570633, 0.03757147118449211, 0.0), (0.1532713919878006, 0.03754625469446182, 0.0), (0.15010105073451996, 0.03754163905978203, 0.0), (0.14966489374637604, 0.0375923290848732, 0.0), (0.14949847757816315, 0.037639070302248, 0.0), (0.14936254918575287, 0.03770438954234123, 0.0), (0.14925415813922882, 0.03779151663184166, 0.0), (0.14917035400867462, 0.037903688848018646, 0.0), (0.1491081565618515, 0.03804413601756096, 0.0), (0.14906463027000427, 0.03821609169244766, 0.0), (0.14903679490089417, 0.03842278942465782, 0.0), (0.14903593063354492, 0.0584842711687088, 0.0), (0.1490621268749237, 0.05873207002878189, 0.0), (0.14910587668418884, 0.05893504619598389, 0.0), (0.14917141199111938, 0.059097737073898315, 0.0), (0.14926299452781677, 0.059224676340818405, 0.0), (0.14938485622406006, 0.059320397675037384, 0.0), (0.1495412439107895, 0.05938944220542908, 0.0), (0.14973638951778412, 0.05943634361028671, 0.0), (0.14997455477714539, 0.05946563929319382, 0.0), (0.15335921943187714, 0.05946327745914459, 0.0), (0.15351217985153198, 0.05943698808550835, 0.0), (0.15364381670951843, 0.059395335614681244, 0.0), (0.15376029908657074, 0.05933436378836632, 0.0), (0.15386778116226196, 0.0592501126229763, 0.0), (0.15397243201732635, 0.059138622134923935, 0.0), (0.15408040583133698, 0.058995939791202545, 0.0), (0.20097173750400543, 0.0531802773475647, 0.0), (0.20236250758171082, 0.051853276789188385, 0.0), (0.20292764902114868, 0.05114328861236572, 0.0), (0.20340536534786224, 0.05040290579199791, 0.0), (0.2037951946258545, 0.04963258281350136, 0.0), (0.2040966898202896, 0.04883277043700218, 0.0), (0.2043094038963318, 0.0480039156973362, 0.0), (0.204432874917984, 0.047146473079919815, 0.0), (0.20446667075157166, 0.04626089334487915, 0.0), (0.20441032946109772, 0.04534762352705002, 0.0), (0.20402543246746063, 0.043439820408821106, 0.0), (0.2037336230278015, 0.04260380566120148, 0.0), (0.20335637032985687, 0.04181332886219025, 0.0), (0.20290005207061768, 0.04107348620891571, 0.0), (0.20237106084823608, 0.040389370173215866, 0.0), (0.20177578926086426, 0.03976607695221901, 0.0), (0.20112061500549316, 0.039208702743053436, 0.0), (0.20041193068027496, 0.038722340017557144, 0.0), (0.19965612888336182, 0.03831208497285843, 0.0), (0.19885960221290588, 0.03798303380608559, 0.0), (0.19802874326705933, 0.037740278989076614, 0.0), (0.1971699297428131, 0.03758891671895981, 0.0), (0.1843988448381424, 0.0375480093061924, 0.0), (0.1841646283864975, 0.03757385537028313, 0.0), (0.18397220969200134, 0.03761660307645798, 0.0), (0.1838175356388092, 0.03768019750714302, 0.0), (0.18369655311107635, 0.037768591195344925, 0.0), (0.18360520899295807, 0.03788572922348976, 0.0), (0.18353945016860962, 0.0380355641245842, 0.0), (0.18349520862102509, 0.038222040981054306, 0.0), (0.18346843123435974, 0.038449108600616455, 0.0), (0.1834498792886734, 0.041320037096738815, 0.0), (0.1834477186203003, 0.054995886981487274, 0.0), (0.18345186114311218, 0.0668068528175354, 0.0), (0.18347544968128204, 0.06699378788471222, 0.0), (0.18351320922374725, 0.06716611236333847, 0.0), (0.18356770277023315, 0.06732256710529327, 0.0), (0.18364150822162628, 0.06746188551187515, 0.0), (0.18373718857765198, 0.06758280098438263, 0.0), (0.18385730683803558, 0.06768405437469482, 0.0), (0.18400444090366364, 0.06776437908411026, 0.0), (0.18418113887310028, 0.06782250851392746, 0.0), (0.18438997864723206, 0.06785718351602554, 0.0), (0.19661131501197815, 0.06772323697805405, 0.0), (0.19822971522808075, 0.067483089864254, 0.0), (0.19963356852531433, 0.06700717657804489, 0.0), (0.2008296102285385, 0.06632790714502335, 0.0), (0.2018245905637741, 0.06547769159078598, 0.0), (0.20262525975704193, 0.06448893994092941, 0.0), (0.203238382935524, 0.06339406222105026, 0.0), (0.2036706954240799, 0.06222546845674515, 0.0), (0.20392896234989166, 0.06101556867361069, 0.0), (0.2040199339389801, 0.0597967728972435, 0.0), (0.20395036041736603, 0.058601491153240204, 0.0), (0.20372699201107025, 0.05746213346719742, 0.0), (0.2033565491437912, 0.05641110986471176, 0.0), (0.20321369171142578, 0.056117285043001175, 0.0), (0.20287439227104187, 0.055553536862134933, 0.0), (0.18895728886127472, 0.04289805889129639, 0.0), (0.19071677327156067, 0.0428861565887928, 0.0), (0.19295911490917206, 0.042865898460149765, 0.0), (0.19566866755485535, 0.0429234504699707, 0.0), (0.19613862037658691, 0.042977411299943924, 0.0), (0.1965792328119278, 0.043086376041173935, 0.0), (0.19698865711688995, 0.043247152119874954, 0.0), (0.19736506044864655, 0.0434565432369709, 0.0), (0.19770662486553192, 0.043711353093385696, 0.0), (0.19801150262355804, 0.044008392840623856, 0.0), (0.19827787578105927, 0.0443444661796093, 0.0), (0.19850389659404755, 0.044716376811265945, 0.0), (0.19868774712085724, 0.045120932161808014, 0.0), (0.1988275796175003, 0.04555493965744972, 0.0), (0.1989215761423111, 0.04601520299911499, 0.0), (0.19896790385246277, 0.046498529613018036, 0.0), (0.1989646703004837, 0.04698452726006508, 0.0), (0.19891215860843658, 0.04745360463857651, 0.0), (0.19881179928779602, 0.04790165647864342, 0.0), (0.19866497814655304, 0.0483245775103569, 0.0), (0.19847312569618225, 0.04871826246380806, 0.0), (0.19823764264583588, 0.04907860606908798, 0.0), (0.19795994460582733, 0.049401503056287766, 0.0), (0.19764143228530884, 0.049682848155498505, 0.0), (0.197283536195755, 0.04991853982210159, 0.0), (0.19688765704631805, 0.05010446906089783, 0.0), (0.1964551955461502, 0.0502365306019783, 0.0), (0.19598758220672607, 0.05031061917543411, 0.0), (0.18907582759857178, 0.050358593463897705, 0.0), (0.18897420167922974, 0.04958563670516014, 0.0), (0.1890052706003189, 0.05560410022735596, 0.0), (0.19222688674926758, 0.05557835474610329, 0.0), (0.19274955987930298, 0.055576179176568985, 0.0), (0.19532999396324158, 0.05562668293714523, 0.0), (0.1957407146692276, 0.055671218782663345, 0.0), (0.19613051414489746, 0.05576194077730179, 0.0), (0.19649739563465118, 0.055895887315273285, 0.0), (0.19683937728405, 0.056070104241371155, 0.0), (0.1971544772386551, 0.05628162994980812, 0.0), (0.19744069874286652, 0.056527502834796906, 0.0), (0.1976960450410843, 0.05680476874113083, 0.0), (0.19791853427886963, 0.057110466063022614, 0.0), (0.19810618460178375, 0.05744163691997528, 0.0), (0.19825699925422668, 0.05779532343149185, 0.0), (0.19836898148059845, 0.05816856771707535, 0.0), (0.19844014942646027, 0.05855840444564819, 0.0), (0.19848008453845978, 0.0594690777361393, 0.0), (0.19844156503677368, 0.05989658832550049, 0.0), (0.1983644813299179, 0.060301996767520905, 0.0), (0.19824913144111633, 0.06068263575434685, 0.0), (0.19809584319591522, 0.06103584170341492, 0.0), (0.19790491461753845, 0.06135895103216171, 0.0), (0.1976766735315323, 0.061649296432733536, 0.0), (0.1974114328622818, 0.061904214322566986, 0.0), (0.19710950553417206, 0.06212104111909866, 0.0), (0.19677118957042694, 0.06229710951447487, 0.0), (0.1963968127965927, 0.0624297559261322, 0.0), (0.19518430531024933, 0.06268808990716934, 0.0), (0.19396308064460754, 0.06281089782714844, 0.0), (0.1890052706003189, 0.06269782036542892, 0.0), (0.19608354568481445, 0.0742272138595581, 0.0), (0.19608354568481445, 0.10992151498794556, 0.0), (0.18773524463176727, 0.10992151498794556, 0.0), (0.18773524463176727, 0.11542944610118866, 0.0), (0.21163995563983917, 0.11542944610118866, 0.0), (0.21163995563983917, 0.11002874374389648, 0.0), (0.20337067544460297, 0.11002874374389648, 0.0), (0.20337067544460297, 0.0742272138595581, 0.0), (0.213965505361557, 0.04632076621055603, 0.0), (0.21416790783405304, 0.04530155286192894, 0.0), (0.2144927680492401, 0.04443708062171936, 0.0), (0.2149314284324646, 0.043728429824113846, 0.0), (0.21547521650791168, 0.04317667335271835, 0.0), (0.21611547470092773, 0.042782895267009735, 0.0), (0.21684353053569794, 0.04254816845059395, 0.0), (0.21765072643756866, 0.04247357323765755, 0.0), (0.2185284048318863, 0.042560186237096786, 0.0), (0.219467893242836, 0.04280908405780792, 0.0), (0.22046053409576416, 0.04322134703397751, 0.0), (0.22149766981601715, 0.0437980517745018, 0.0), (0.22257064282894135, 0.04454027861356735, 0.0), (0.2254689782857895, 0.04195427522063255, 0.0), (0.2256070375442505, 0.04179394245147705, 0.0), (0.22571420669555664, 0.041639409959316254, 0.0), (0.22579073905944824, 0.04148899018764496, 0.0), (0.22583690285682678, 0.04134100303053856, 0.0), (0.22585293650627136, 0.04119376093149185, 0.0), (0.22583910822868347, 0.041045576333999634, 0.0), (0.2257956564426422, 0.040894765406847, 0.0), (0.22572284936904907, 0.040739644318819046, 0.0), (0.22562094032764435, 0.04057852923870087, 0.0), (0.22533082962036133, 0.04023157060146332, 0.0), (0.22441545128822327, 0.03939082473516464, 0.0), (0.22340168058872223, 0.038687873631715775, 0.0), (0.22230777144432068, 0.03812377154827118, 0.0), (0.22115197777748108, 0.03769957646727562, 0.0), (0.2199525535106659, 0.03741635009646416, 0.0), (0.21872775256633759, 0.03727514669299126, 0.0), (0.2174958437681198, 0.03727702796459198, 0.0), (0.21627508103847504, 0.03742305189371109, 0.0), (0.21508370339870453, 0.03771427273750305, 0.0), (0.21393999457359314, 0.03815175220370293, 0.0), (0.21286219358444214, 0.03873654827475548, 0.0), (0.211868554353714, 0.03946971893310547, 0.0), (0.21124771237373352, 0.04006998986005783, 0.0), (0.21071277558803558, 0.04072599112987518, 0.0), (0.21025703847408295, 0.04143042862415314, 0.0), (0.2098737359046936, 0.0421760194003582, 0.0), (0.20929746329784393, 0.043761491775512695, 0.0), (0.20888324081897736, 0.04552309960126877, 0.0), (0.2086460441350937, 0.047284312546253204, 0.0), (0.2085954248905182, 0.04904191941022873, 0.0), (0.2087409645318985, 0.05079270899295807, 0.0), (0.20909221470355988, 0.05253346636891365, 0.0), (0.20965871214866638, 0.0542609766125679, 0.0), (0.2100968211889267, 0.05522904917597771, 0.0), (0.2106112688779831, 0.0561075359582901, 0.0), (0.21119822561740875, 0.05689466744661331, 0.0), (0.21185381710529327, 0.05758868530392647, 0.0), (0.21257421374320984, 0.0581878237426281, 0.0), (0.21335554122924805, 0.05869032070040703, 0.0), (0.21419396996498108, 0.05909441038966179, 0.0), (0.21508564054965973, 0.05939833074808121, 0.0), (0.2160266935825348, 0.05960031598806381, 0.0), (0.21701328456401825, 0.05969860404729843, 0.0), (0.2180415689945221, 0.05969143286347389, 0.0), (0.2191077023744583, 0.05957704037427902, 0.0), (0.22008797526359558, 0.059368398040533066, 0.0), (0.22101843357086182, 0.059056803584098816, 0.0), (0.22189345955848694, 0.05864817649126053, 0.0), (0.22270746529102325, 0.05814843252301216, 0.0), (0.22345483303070068, 0.05756348744034767, 0.0), (0.22412995994091034, 0.056899260729551315, 0.0), (0.22472722828388214, 0.05616167187690735, 0.0), (0.2252410501241684, 0.05535663664340973, 0.0), (0.22566580772399902, 0.054490070790052414, 0.0), (0.22599589824676514, 0.05356789380311966, 0.0), (0.22622571885585785, 0.05259602516889572, 0.0), (0.22634968161582947, 0.05158037692308426, 0.0), (0.22636966407299042, 0.04722575843334198, 0.0), (0.22634068131446838, 0.04701092094182968, 0.0), (0.2262951135635376, 0.046832941472530365, 0.0), (0.2262294441461563, 0.04668843373656273, 0.0), (0.2261401265859604, 0.046574003994464874, 0.0), (0.22602364420890808, 0.0464862622320652, 0.0), (0.22587648034095764, 0.04642181843519211, 0.0), (0.22569508850574493, 0.046377282589673996, 0.0), (0.2254759520292282, 0.046349264681339264, 0.0), (0.2139965444803238, 0.05105837434530258, 0.0), (0.2186959683895111, 0.05105837434530258, 0.0), (0.2210071086883545, 0.05105837434530258, 0.0), (0.22095391154289246, 0.05158354341983795, 0.0), (0.22085975110530853, 0.052068181335926056, 0.0), (0.220725417137146, 0.05251184478402138, 0.0), (0.22055168449878693, 0.0529140941798687, 0.0), (0.2203393429517746, 0.0532744899392128, 0.0), (0.2200891673564911, 0.05359258875250816, 0.0), (0.21980194747447968, 0.05386795103549957, 0.0), (0.21947847306728363, 0.05410013720393181, 0.0), (0.21911953389644623, 0.054288703948259354, 0.0), (0.21872590482234955, 0.05443321168422699, 0.0), (0.21829836070537567, 0.0545332208275795, 0.0), (0.21783767640590668, 0.05458829551935196, 0.0), (0.21731846034526825, 0.05459902435541153, 0.0), (0.21683718264102936, 0.054557256400585175, 0.0), (0.21639332175254822, 0.05446211248636246, 0.0), (0.21598635613918304, 0.05431270971894264, 0.0), (0.21561576426029205, 0.054108165204524994, 0.0), (0.21528102457523346, 0.053847599774599075, 0.0), (0.21498163044452667, 0.05353013053536415, 0.0), (0.2147170603275299, 0.053154874593019485, 0.0), (0.21448677778244019, 0.05272095277905464, 0.0), (0.21429027616977692, 0.052227482199668884, 0.0), (0.2259065806865692, 0.08007374405860901, 0.0), (0.2401675432920456, 0.08007374405860901, 0.0), (0.2401675432920456, 0.07426672428846359, 0.0), (0.2186279147863388, 0.07426672428846359, 0.0), (0.2186279147863388, 0.1154407262802124, 0.0), (0.24015061557292938, 0.1154407262802124, 0.0), (0.24015061557292938, 0.11004002392292023, 0.0), (0.225937619805336, 0.11004002392292023, 0.0), (0.225937619805336, 0.09782777726650238, 0.0), (0.23836694657802582, 0.09782777726650238, 0.0), (0.23836694657802582, 0.09223520755767822, 0.0), (0.22590939700603485, 0.09223520755767822, 0.0), (0.23156523704528809, 0.05493254214525223, 0.0), (0.2303982675075531, 0.05511877313256264, 0.0), (0.2301415503025055, 0.05518868938088417, 0.0), (0.2299397587776184, 0.05527212470769882, 0.0), (0.22978614270687103, 0.05537484213709831, 0.0), (0.22967398166656494, 0.055502600967884064, 0.0), (0.22959654033184052, 0.0556611642241478, 0.0), (0.22954708337783813, 0.05585629120469093, 0.0), (0.22951889038085938, 0.056093744933605194, 0.0), (0.2295141965150833, 0.05821530893445015, 0.0), (0.22955526411533356, 0.05854691192507744, 0.0), (0.2296263575553894, 0.058811891824007034, 0.0), (0.2297346591949463, 0.05902045965194702, 0.0), (0.22988735139369965, 0.05918281897902489, 0.0), (0.2300916165113449, 0.059309184551239014, 0.0), (0.23035463690757751, 0.05940976366400719, 0.0), (0.23156806826591492, 0.05965886265039444, 0.0), (0.23159325122833252, 0.06475444883108139, 0.0), (0.2316235899925232, 0.06500864773988724, 0.0), (0.23167259991168976, 0.06521737575531006, 0.0), (0.2317446917295456, 0.0653851106762886, 0.0), (0.23184429109096527, 0.06551633030176163, 0.0), (0.23197582364082336, 0.06561551243066788, 0.0), (0.23214370012283325, 0.0656871348619461, 0.0), (0.2323523461818695, 0.06573567539453506, 0.0), (0.2326061725616455, 0.0657656118273735, 0.0), (0.23573356866836548, 0.06578722596168518, 0.0), (0.2359250783920288, 0.06576626747846603, 0.0), (0.23609687387943268, 0.06572724878787994, 0.0), (0.23624920845031738, 0.06566988676786423, 0.0), (0.23638233542442322, 0.0655939131975174, 0.0), (0.23649650812149048, 0.06549904495477676, 0.0), (0.23659197986125946, 0.06538501381874084, 0.0), (0.23666900396347046, 0.06525154411792755, 0.0), (0.23672784864902496, 0.0650983601808548, 0.0), (0.23676875233650208, 0.0649251937866211, 0.0), (0.23679198324680328, 0.06473176926374435, 0.0), (0.23679211735725403, 0.05964192748069763, 0.0), (0.2385386973619461, 0.0593448132276535, 0.0), (0.23891706764698029, 0.059234872460365295, 0.0), (0.23921069502830505, 0.059102319180965424, 0.0), (0.23942987620830536, 0.05893685668706894, 0.0), (0.23958490788936615, 0.058728188276290894, 0.0), (0.23968608677387238, 0.05846601352095604, 0.0), (0.23974372446537018, 0.05814003944396973, 0.0), (0.2397320717573166, 0.05606533959507942, 0.0), (0.23969592154026031, 0.05583556741476059, 0.0), (0.23963110148906708, 0.05564841255545616, 0.0), (0.2395276427268982, 0.05549797788262367, 0.0), (0.2393755465745926, 0.05537836626172066, 0.0), (0.2391648292541504, 0.05528368055820465, 0.0), (0.23888550698757172, 0.05520801991224289, 0.0), (0.23688243329524994, 0.05497768521308899, 0.0), (0.23680701851844788, 0.054179321974515915, 0.0), (0.23682479560375214, 0.043312061578035355, 0.0), (0.23685944080352783, 0.04312056303024292, 0.0), (0.23691414296627045, 0.0429692305624485, 0.0), (0.23699355125427246, 0.042852915823459625, 0.0), (0.23710229992866516, 0.04276646301150322, 0.0), (0.23724502325057983, 0.04270472005009651, 0.0), (0.23742635548114777, 0.04266253486275673, 0.0), (0.23880279064178467, 0.04256149381399155, 0.0), (0.23902007937431335, 0.04252533242106438, 0.0), (0.23920170962810516, 0.042474180459976196, 0.0), (0.23935088515281677, 0.04240480437874794, 0.0), (0.23947080969810486, 0.04231397062540054, 0.0), (0.2395646870136261, 0.04219844937324524, 0.0), (0.23963572084903717, 0.042055003345012665, 0.0), (0.23968711495399475, 0.04188040271401405, 0.0), (0.23974379897117615, 0.04142480343580246, 0.0), (0.23975619673728943, 0.03852810710668564, 0.0), (0.2397328019142151, 0.03833572193980217, 0.0), (0.2396908551454544, 0.03816428780555725, 0.0), (0.23963028192520142, 0.0380135141313076, 0.0), (0.23955096304416656, 0.03788312152028084, 0.0), (0.2394528090953827, 0.03777282312512398, 0.0), (0.23933573067188263, 0.03768233582377434, 0.0), (0.23919962346553802, 0.03761137276887894, 0.0), (0.23904438316822052, 0.03755965083837509, 0.0), (0.23886992037296295, 0.03752688691020012, 0.0), (0.2364901304244995, 0.03753122687339783, 0.0), (0.23588404059410095, 0.03759896010160446, 0.0), (0.23529954254627228, 0.037732161581516266, 0.0), (0.23474153876304626, 0.037927400320768356, 0.0), (0.23421494662761688, 0.03818124905228615, 0.0), (0.23372463881969452, 0.03849027678370476, 0.0), (0.23327553272247314, 0.0388510562479496, 0.0), (0.23287253081798553, 0.03926015645265579, 0.0), (0.23252052068710327, 0.03971415013074875, 0.0), (0.23222440481185913, 0.040209606289863586, 0.0), (0.2319890856742859, 0.04074309766292572, 0.0), (0.23181946575641632, 0.04131119325757027, 0.0), (0.2317204624414444, 0.04191046953201294, 0.0), (0.2551312744617462, 0.05093421787023544, 0.0), (0.2551189064979553, 0.05291324481368065, 0.0), (0.2550877034664154, 0.05311470478773117, 0.0), (0.25503817200660706, 0.05330411344766617, 0.0), (0.2549707591533661, 0.05348062142729759, 0.0), (0.2548859417438507, 0.053643371909856796, 0.0), (0.2547841966152191, 0.05379151552915573, 0.0), (0.25466597080230713, 0.05392419919371605, 0.0), (0.25453174114227295, 0.0540405698120594, 0.0), (0.25438201427459717, 0.05413977429270744, 0.0), (0.2542172372341156, 0.05422096326947212, 0.0), (0.25403785705566406, 0.05428327992558479, 0.0), (0.25196489691734314, 0.05461275205016136, 0.0), (0.25103509426116943, 0.054645437747240067, 0.0), (0.25057676434516907, 0.05460570007562637, 0.0), (0.25012436509132385, 0.05451775714755058, 0.0), (0.2496790587902069, 0.054373499006032944, 0.0), (0.24924200773239136, 0.054164811968803406, 0.0), (0.2488143891096115, 0.05388358235359192, 0.0), (0.24832528829574585, 0.05346638709306717, 0.0), (0.24823430180549622, 0.053420379757881165, 0.0), (0.24812787771224976, 0.05338370054960251, 0.0), (0.24788272380828857, 0.05333840101957321, 0.0), (0.24761788547039032, 0.05333064869046211, 0.0), (0.2473614364862442, 0.05336059629917145, 0.0), (0.24724513292312622, 0.05338975787162781, 0.0), (0.24714145064353943, 0.05342840403318405, 0.0), (0.24705392122268677, 0.05347654968500137, 0.0), (0.24384215474128723, 0.05598503351211548, 0.0), (0.24444712698459625, 0.056852925568819046, 0.0), (0.2451286017894745, 0.05759705230593681, 0.0), (0.24588409066200256, 0.058221571147441864, 0.0), (0.24671107530593872, 0.05873063579201698, 0.0), (0.2476070374250412, 0.059128399938344955, 0.0), (0.24856947362422943, 0.05941901355981827, 0.0), (0.24985425174236298, 0.05966251716017723, 0.0), (0.25113630294799805, 0.059776533395051956, 0.0), (0.252413809299469, 0.059763263911008835, 0.0), (0.25368496775627136, 0.05962489917874336, 0.0), (0.2549479901790619, 0.059363629668951035, 0.0), (0.2567794919013977, 0.05875076353549957, 0.0), (0.2573131024837494, 0.05848304182291031, 0.0), (0.2578021287918091, 0.05817893147468567, 0.0), (0.25824686884880066, 0.05783887580037117, 0.0), (0.2586476802825928, 0.05746331438422203, 0.0), (0.2590048611164093, 0.05705268681049347, 0.0), (0.2593187689781189, 0.056607432663440704, 0.0), (0.2595897316932678, 0.05612799525260925, 0.0), (0.25981810688972473, 0.05561481788754463, 0.0), (0.2601483464241028, 0.05448899418115616, 0.0), (0.26034015417099, 0.053036995232105255, 0.0), (0.26036307215690613, 0.04584812372922897, 0.0), (0.26033973693847656, 0.03847743943333626, 0.0), (0.26031213998794556, 0.03824577108025551, 0.0), (0.2602672874927521, 0.03805522248148918, 0.0), (0.26020142436027527, 0.03790174424648285, 0.0), (0.2601107954978943, 0.03778129443526268, 0.0), (0.25999167561531067, 0.037689823657274246, 0.0), (0.2598402798175812, 0.037623289972543716, 0.0), (0.25965285301208496, 0.03757764399051666, 0.0), (0.25942564010620117, 0.037548840045928955, 0.0), (0.25686416029930115, 0.03753969073295593, 0.0), (0.2546260952949524, 0.038047581911087036, 0.0), (0.2537873089313507, 0.03769875317811966, 0.0), (0.2529161870479584, 0.037439268082380295, 0.0), (0.2520231008529663, 0.03726876154541969, 0.0), (0.25111839175224304, 0.0371868722140789, 0.0), (0.2502124309539795, 0.037193238735198975, 0.0), (0.24931558966636658, 0.037287499755620956, 0.0), (0.24843820929527283, 0.0374692901968956, 0.0), (0.24759064614772797, 0.03773824870586395, 0.0), (0.24678325653076172, 0.038094013929367065, 0.0), (0.246026411652565, 0.03853622078895569, 0.0), (0.24533045291900635, 0.03906451165676117, 0.0), (0.24470578134059906, 0.03967851400375366, 0.0), (0.24427130818367004, 0.04020926356315613, 0.0), (0.24390125274658203, 0.04075410217046738, 0.0), (0.24359442293643951, 0.04131218418478966, 0.0), (0.24334962666034698, 0.04188267141580582, 0.0), (0.24316567182540894, 0.0424647182226181, 0.0), (0.24304135143756866, 0.043057482689619064, 0.0), (0.24297547340393066, 0.04366012290120125, 0.0), (0.24296684563159943, 0.0442717969417572, 0.0), (0.243116557598114, 0.04551887512207031, 0.0), (0.24348092079162598, 0.04679197818040848, 0.0), (0.2437235713005066, 0.04737816005945206, 0.0), (0.24400627613067627, 0.04791788384318352, 0.0), (0.24432791769504547, 0.04841136187314987, 0.0), (0.24468739330768585, 0.04885881394147873, 0.0), (0.24508360028266907, 0.0492604523897171, 0.0), (0.24551543593406677, 0.0496164932847023, 0.0), (0.24598178267478943, 0.04992714896798134, 0.0), (0.2464815378189087, 0.050192639231681824, 0.0), (0.24701358377933502, 0.05041317641735077, 0.0), (0.24757683277130127, 0.050588980317115784, 0.0), (0.24879245460033417, 0.05080723762512207, 0.0), (0.25501275062561035, 0.046168386936187744, 0.0), (0.24962218105793, 0.046137355268001556, 0.0), (0.2494223266839981, 0.04611758142709732, 0.0), (0.24922893941402435, 0.04608050361275673, 0.0), (0.2490437626838684, 0.046025633811950684, 0.0), (0.24886853992938995, 0.045952484011650085, 0.0), (0.24870504438877106, 0.04586055874824524, 0.0), (0.2485550194978714, 0.045749373733997345, 0.0), (0.24842022359371185, 0.045618437230587006, 0.0), (0.2483024150133133, 0.045467257499694824, 0.0), (0.2482033371925354, 0.0452953465282917, 0.0), (0.24812474846839905, 0.04510221257805824, 0.0), (0.2480684071779251, 0.04488736763596535, 0.0), (0.24803607165813446, 0.04465032368898392, 0.0), (0.24802862107753754, 0.044407736510038376, 0.0), (0.2480451762676239, 0.04417948052287102, 0.0), (0.24808479845523834, 0.043965667486190796, 0.0), (0.24814656376838684, 0.04376640543341637, 0.0), (0.24822953343391418, 0.043581798672676086, 0.0), (0.24833276867866516, 0.04341195896267891, 0.0), (0.24845534563064575, 0.04325699061155319, 0.0), (0.24859634041786194, 0.04311700165271759, 0.0), (0.2487548142671585, 0.04299210011959076, 0.0), (0.24892984330654144, 0.04288239777088165, 0.0), (0.24912048876285553, 0.04278799891471863, 0.0), (0.24932584166526794, 0.04270900785923004, 0.0), (0.2500841021537781, 0.04251765087246895, 0.0), (0.2508724629878998, 0.042417846620082855, 0.0), (0.2523731291294098, 0.042394429445266724, 0.0), (0.25298821926116943, 0.04243919253349304, 0.0), (0.2535134553909302, 0.04252436012029648, 0.0), (0.25395429134368896, 0.042655497789382935, 0.0), (0.25431618094444275, 0.04283817112445831, 0.0), (0.2546045780181885, 0.04307794198393822, 0.0), (0.2548249363899231, 0.04338037967681885, 0.0), (0.25498273968696594, 0.04375104606151581, 0.0), (0.25508344173431396, 0.044195506721735, 0.0), (0.2551324665546417, 0.04471932724118233, 0.0), (0.2550974190235138, 0.046027302742004395, 0.0), (0.25509533286094666, 0.046037785708904266, 0.0), (0.25509193539619446, 0.04604814201593399, 0.0), (0.25508737564086914, 0.046058475971221924, 0.0), (0.2550751864910126, 0.046079520136117935, 0.0), (0.25505101680755615, 0.04611363261938095, 0.0), (0.2669396996498108, 0.09288137406110764, 0.0), (0.2747207283973694, 0.0741538479924202, 0.0), (0.26806944608688354, 0.07419031113386154, 0.0), (0.26773160696029663, 0.07424027472734451, 0.0), (0.26745179295539856, 0.0743226483464241, 0.0), (0.26721805334091187, 0.07444553822278976, 0.0), (0.26701846718788147, 0.07461704313755035, 0.0), (0.2668411135673523, 0.07484526187181473, 0.0), (0.26667407155036926, 0.07513830065727234, 0.0), (0.2606021463871002, 0.09087610244750977, 0.0), (0.2604234516620636, 0.09121551364660263, 0.0), (0.2603225111961365, 0.09135661274194717, 0.0), (0.2602119445800781, 0.09147874265909195, 0.0), (0.2600903809070587, 0.09158198535442352, 0.0), (0.259956419467926, 0.09166641533374786, 0.0), (0.25980865955352783, 0.09173211455345154, 0.0), (0.2596456706523895, 0.09177915751934052, 0.0), (0.2594660818576813, 0.09180761873722076, 0.0), (0.2559243440628052, 0.09179219603538513, 0.0), (0.2559243440628052, 0.07423850148916245, 0.0), (0.24867673218250275, 0.07423850148916245, 0.0), (0.24867673218250275, 0.11536736786365509, 0.0), (0.24899621307849884, 0.11549436300992966, 0.0), (0.24905987083911896, 0.11550677567720413, 0.0), (0.26247939467430115, 0.11541079729795456, 0.0), (0.26442837715148926, 0.11513128131628036, 0.0), (0.26645082235336304, 0.11457566916942596, 0.0), (0.26812851428985596, 0.1138235554099083, 0.0), (0.268877774477005, 0.11335822194814682, 0.0), (0.26956698298454285, 0.11283347755670547, 0.0), (0.2701959013938904, 0.11224940419197083, 0.0), (0.2707642614841461, 0.11160607635974884, 0.0), (0.27127179503440857, 0.11090356856584549, 0.0), (0.27171826362609863, 0.11014196276664734, 0.0), (0.272426962852478, 0.10844176262617111, 0.0), (0.27296626567840576, 0.1061067059636116, 0.0), (0.2731766104698181, 0.10331595689058304, 0.0), (0.2731013894081116, 0.10192308574914932, 0.0), (0.2729005813598633, 0.10053272545337677, 0.0), (0.272379994392395, 0.0985519215464592, 0.0), (0.27215683460235596, 0.0979844182729721, 0.0), (0.2716127336025238, 0.09692703187465668, 0.0), (0.27129238843917847, 0.09643685817718506, 0.0), (0.27055656909942627, 0.09553281217813492, 0.0), (0.26969587802886963, 0.09472952783107758, 0.0), (0.2687126398086548, 0.09402582049369812, 0.0), (0.26718807220458984, 0.09317200630903244, 0.0), (0.267170250415802, 0.09315971285104752, 0.0), (0.26715320348739624, 0.09314537793397903, 0.0), (0.2671198844909668, 0.09311044961214066, 0.0), (0.25598078966140747, 0.11009645462036133, 0.0), (0.25598078966140747, 0.09694176912307739, 0.0), (0.2623676061630249, 0.09733116626739502, 0.0), (0.2628083825111389, 0.0974075123667717, 0.0), (0.2632223963737488, 0.09752294421195984, 0.0), (0.2636081278324127, 0.09767632931470871, 0.0), (0.26396408677101135, 0.09786654263734818, 0.0), (0.2642887532711029, 0.0980924591422081, 0.0), (0.264580637216568, 0.09835295379161835, 0.0), (0.26483824849128723, 0.09864689409732819, 0.0), (0.26506006717681885, 0.09897316247224808, 0.0), (0.26524463295936584, 0.09933062642812729, 0.0), (0.26539039611816406, 0.09971815347671509, 0.0), (0.2654958963394165, 0.10013462603092194, 0.0), (0.26567667722702026, 0.10248272120952606, 0.0), (0.26558783650398254, 0.1063041165471077, 0.0), (0.265531063079834, 0.10675086826086044, 0.0), (0.2654322683811188, 0.107170470058918, 0.0), (0.2652929425239563, 0.10756175220012665, 0.0), (0.26511457562446594, 0.10792355984449387, 0.0), (0.2648986577987671, 0.10825471580028534, 0.0), (0.26464664936065674, 0.10855406522750854, 0.0), (0.26436007022857666, 0.10882043093442917, 0.0), (0.26404041051864624, 0.10905265063047409, 0.0), (0.26368916034698486, 0.10924956202507019, 0.0), (0.2633078098297119, 0.10940999537706375, 0.0), (0.2628978490829468, 0.10953278839588165, 0.0), (0.26246073842048645, 0.10961677134037018, 0.0)]
    logo_beta_fs = [(720, 780, 779), (192, 172, 193), (315, 228, 227), (795, 794, 815), (702, 753, 752), (481, 480, 516), (677, 676, 576), (1383, 1382, 1330), (998, 997, 934), (878, 877, 827), (555, 649, 648), (1031, 1030, 976), (948, 947, 955), (1049, 1046, 1044), (1131, 1155, 1096), (1138, 1137, 1116), (1160, 1167, 1164), (817, 823, 822), (1168, 1220, 1205), (1303, 1269, 1268), (1441, 1459, 1458), (800, 814, 801), (1471, 1470, 1431), (402, 401, 371), (427, 426, 394), (63, 62, 29), (770, 769, 732), (769, 734, 733), (733, 732, 769), (732, 731, 770), (731, 730, 771), (730, 729, 772), (729, 728, 772), (730, 772, 771), (728, 727, 773), (727, 726, 774), (726, 725, 775), (725, 724, 775), (724, 723, 776), (723, 722, 777), (778, 721, 779), (722, 721, 778), (721, 720, 779), (780, 719, 781), (720, 719, 780), (719, 718, 781), (782, 718, 717), (717, 716, 783), (783, 716, 715), (715, 714, 784), (714, 713, 785), (713, 712, 785), (714, 785, 784), (712, 711, 786), (711, 710, 787), (710, 709, 789), (709, 708, 766), (786, 711, 787), (708, 767, 766), (766, 790, 709), (785, 712, 786), (715, 784, 783), (718, 782, 781), (772, 728, 773), (727, 774, 773), (731, 771, 770), (717, 783, 782), (790, 789, 709), (789, 788, 710), (788, 787, 710), (774, 726, 775), (776, 775, 724), (777, 776, 723), (778, 777, 722), (150, 149, 158), (149, 148, 159), (150, 158, 157), (148, 147, 159), (147, 146, 160), (146, 145, 161), (145, 144, 162), (147, 160, 159), (144, 143, 163), (160, 146, 161), (152, 151, 156), (151, 150, 157), (154, 153, 155), (153, 152, 155), (151, 157, 156), (158, 149, 159), (156, 155, 152), (161, 145, 162), (162, 144, 163), (164, 163, 143), (165, 164, 143), (166, 165, 110), (165, 143, 110), (167, 166, 110), (169, 168, 196), (168, 167, 86), (196, 168, 86), (171, 170, 194), (170, 169, 194), (171, 194, 193), (173, 172, 192), (172, 171, 193), (173, 192, 191), (175, 174, 189), (174, 173, 190), (189, 174, 190), (177, 176, 187), (176, 175, 188), (187, 176, 188), (179, 178, 185), (178, 177, 186), (185, 178, 186), (181, 180, 184), (180, 179, 184), (183, 182, 181), (184, 183, 181), (184, 179, 185), (173, 191, 190), (126, 125, 123), (125, 124, 123), (123, 122, 126), (122, 121, 127), (121, 120, 128), (128, 120, 129), (120, 119, 129), (119, 118, 131), (118, 117, 132), (117, 116, 133), (118, 132, 131), (116, 115, 134), (115, 114, 135), (116, 134, 133), (114, 113, 136), (113, 112, 136), (114, 136, 135), (112, 111, 141), (111, 110, 143), (119, 131, 130), (129, 119, 130), (127, 126, 122), (128, 127, 121), (99, 98, 97), (97, 96, 99), (96, 95, 100), (95, 94, 101), (94, 93, 101), (101, 93, 102), (93, 92, 102), (92, 91, 103), (91, 90, 103), (90, 89, 104), (103, 90, 104), (89, 88, 105), (88, 87, 105), (89, 105, 104), (87, 86, 106), (92, 103, 102), (96, 100, 99), (101, 100, 95), (105, 87, 106), (107, 106, 86), (108, 107, 86), (108, 86, 109), (109, 86, 167), (110, 109, 167), (134, 115, 135), (187, 186, 177), (132, 117, 133), (137, 136, 112), (138, 137, 112), (139, 138, 112), (140, 139, 112), (141, 140, 112), (142, 141, 111), (143, 142, 111), (188, 175, 189), (169, 196, 195), (169, 195, 194), (323, 322, 222), (322, 321, 223), (321, 320, 223), (320, 319, 224), (223, 320, 224), (319, 318, 225), (318, 317, 226), (317, 316, 227), (316, 315, 227), (317, 227, 226), (315, 314, 228), (314, 313, 229), (229, 312, 230), (313, 312, 229), (312, 311, 230), (230, 311, 231), (311, 310, 231), (310, 309, 231), (309, 308, 232), (308, 307, 236), (309, 232, 231), (224, 319, 225), (322, 223, 222), (325, 324, 221), (324, 323, 221), (327, 326, 219), (326, 325, 220), (329, 328, 217), (328, 327, 218), (329, 216, 330), (331, 330, 214), (331, 214, 213), (333, 332, 211), (332, 331, 212), (211, 332, 212), (335, 334, 209), (334, 333, 210), (210, 333, 211), (337, 336, 206), (336, 335, 207), (339, 338, 204), (338, 337, 205), (206, 336, 207), (341, 340, 203), (340, 339, 204), (204, 338, 205), (343, 342, 201), (342, 341, 202), (203, 340, 204), (345, 344, 200), (344, 343, 200), (197, 346, 198), (346, 345, 199), (199, 345, 200), (199, 198, 346), (205, 337, 206), (335, 209, 208), (209, 334, 210), (216, 329, 217), (325, 221, 220), (323, 222, 221), (214, 330, 215), (201, 200, 343), (335, 208, 207), (272, 271, 269), (271, 270, 269), (269, 268, 272), (268, 267, 272), (267, 266, 273), (273, 266, 265), (265, 264, 274), (274, 264, 263), (263, 262, 275), (275, 262, 261), (261, 260, 276), (276, 260, 277), (260, 259, 277), (259, 258, 278), (280, 258, 257), (257, 256, 282), (281, 257, 282), (256, 255, 283), (255, 254, 285), (254, 253, 287), (253, 252, 289), (252, 251, 290), (251, 250, 291), (292, 249, 293), (250, 249, 292), (249, 248, 293), (295, 246, 296), (248, 247, 294), (247, 246, 295), (296, 245, 244), (246, 245, 296), (297, 244, 243), (243, 242, 299), (301, 240, 302), (242, 241, 300), (241, 240, 301), (302, 239, 303), (240, 239, 302), (239, 238, 303), (303, 238, 304), (238, 237, 304), (237, 236, 307), (244, 297, 296), (282, 256, 283), (285, 254, 286), (258, 280, 279), (257, 281, 280), (277, 259, 278), (273, 272, 267), (263, 275, 274), (278, 258, 279), (247, 295, 294), (304, 237, 305), (236, 235, 308), (274, 273, 265), (305, 237, 306), (235, 234, 308), (306, 237, 307), (276, 275, 261), (202, 201, 342), (203, 202, 341), (283, 255, 284), (284, 255, 285), (286, 254, 287), (287, 253, 288), (212, 331, 213), (288, 253, 289), (215, 330, 216), (290, 289, 252), (291, 290, 251), (217, 328, 218), (292, 291, 250), (294, 293, 248), (219, 218, 327), (220, 219, 326), (298, 297, 243), (299, 298, 243), (300, 299, 242), (301, 300, 241), (234, 233, 308), (233, 232, 308), (225, 318, 226), (314, 229, 228), (794, 793, 792), (792, 791, 816), (791, 810, 802), (816, 791, 811), (810, 809, 804), (809, 808, 806), (808, 807, 806), (806, 805, 804), (804, 803, 810), (803, 802, 810), (802, 801, 812), (801, 813, 812), (806, 804, 809), (794, 792, 816), (797, 796, 798), (796, 795, 799), (798, 796, 799), (802, 812, 811), (816, 815, 794), (815, 800, 795), (802, 811, 791), (800, 799, 795), (697, 696, 760), (696, 695, 761), (761, 695, 762), (695, 694, 763), (694, 693, 764), (695, 763, 762), (693, 692, 681), (692, 691, 681), (691, 690, 681), (690, 689, 681), (689, 688, 685), (688, 687, 685), (687, 686, 685), (685, 684, 683), (683, 682, 689), (682, 681, 689), (681, 680, 765), (681, 765, 693), (765, 764, 693), (685, 683, 689), (699, 698, 757), (698, 697, 759), (757, 698, 758), (701, 700, 755), (700, 699, 756), (756, 699, 757), (703, 702, 751), (702, 701, 753), (705, 704, 748), (704, 703, 750), (753, 701, 754), (707, 706, 745), (706, 705, 745), (767, 708, 745), (708, 707, 745), (734, 769, 768), (734, 768, 767), (736, 735, 743), (735, 734, 767), (738, 737, 736), (740, 739, 738), (742, 741, 738), (741, 740, 738), (744, 743, 735), (743, 742, 736), (745, 744, 767), (767, 744, 735), (738, 736, 742), (701, 755, 754), (755, 700, 756), (764, 763, 694), (696, 761, 760), (746, 745, 705), (697, 760, 759), (747, 746, 705), (748, 747, 705), (759, 758, 698), (749, 748, 704), (750, 749, 704), (751, 750, 703), (752, 751, 702), (455, 454, 453), (453, 554, 455), (554, 553, 455), (455, 553, 456), (553, 552, 456), (552, 551, 456), (456, 551, 550), (550, 549, 457), (549, 548, 457), (548, 547, 458), (457, 548, 458), (547, 546, 458), (546, 545, 458), (458, 545, 459), (545, 544, 459), (544, 543, 459), (459, 543, 460), (543, 542, 460), (542, 541, 462), (463, 541, 540), (540, 539, 464), (539, 538, 465), (538, 537, 467), (539, 465, 464), (537, 536, 469), (536, 535, 470), (535, 534, 471), (534, 533, 472), (469, 536, 470), (533, 532, 472), (532, 531, 473), (531, 530, 473), (530, 529, 474), (529, 528, 474), (528, 527, 474), (474, 527, 475), (527, 526, 475), (526, 525, 477), (525, 524, 477), (524, 523, 477), (523, 522, 478), (522, 521, 478), (523, 478, 477), (521, 520, 478), (520, 519, 479), (478, 520, 479), (519, 518, 479), (518, 517, 479), (517, 516, 480), (516, 515, 481), (515, 514, 482), (514, 513, 484), (487, 511, 510), (513, 512, 485), (512, 511, 486), (488, 510, 489), (510, 509, 489), (489, 509, 490), (509, 508, 490), (508, 507, 491), (490, 508, 491), (507, 506, 492), (506, 505, 493), (505, 504, 494), (504, 503, 495), (492, 506, 493), (503, 502, 496), (502, 501, 497), (501, 500, 497), (500, 499, 498), (494, 504, 495), (498, 497, 500), (497, 496, 502), (493, 505, 494), (491, 507, 492), (511, 487, 486), (510, 488, 487), (479, 517, 480), (526, 477, 476), (530, 474, 473), (470, 535, 471), (467, 537, 468), (541, 463, 462), (540, 464, 463), (550, 457, 456), (465, 538, 466), (466, 538, 467), (496, 495, 503), (526, 476, 475), (461, 460, 542), (462, 461, 542), (512, 486, 485), (468, 537, 469), (513, 485, 484), (514, 484, 483), (514, 483, 482), (471, 534, 472), (515, 482, 481), (472, 532, 473), (673, 672, 576), (576, 575, 678), (575, 574, 679), (576, 674, 673), (679, 678, 575), (678, 677, 576), (674, 576, 675), (675, 576, 676), (1321, 1320, 1313), (1320, 1319, 1314), (1313, 1320, 1314), (1319, 1318, 1317), (1317, 1316, 1319), (1316, 1315, 1319), (1315, 1314, 1319), (1312, 1400, 1399), (1312, 1399, 1398), (1313, 1312, 1392), (1322, 1391, 1390), (1322, 1321, 1313), (1325, 1324, 1385), (1324, 1323, 1386), (1389, 1323, 1322), (1391, 1322, 1313), (1312, 1398, 1397), (1312, 1397, 1396), (1322, 1390, 1389), (1326, 1325, 1385), (1323, 1389, 1388), (1328, 1327, 1384), (1327, 1326, 1384), (1384, 1326, 1385), (1330, 1329, 1383), (1329, 1328, 1383), (1383, 1328, 1384), (1332, 1331, 1381), (1331, 1330, 1382), (1380, 1333, 1332), (1334, 1333, 1379), (1334, 1379, 1378), (1336, 1335, 1377), (1335, 1334, 1378), (1338, 1337, 1376), (1337, 1336, 1376), (1340, 1339, 1375), (1339, 1338, 1375), (1342, 1341, 1375), (1341, 1340, 1375), (1376, 1375, 1338), (1377, 1376, 1336), (1335, 1378, 1377), (1333, 1380, 1379), (1386, 1323, 1387), (1323, 1388, 1387), (1312, 1396, 1395), (1312, 1395, 1394), (1312, 1394, 1393), (1312, 1393, 1392), (1380, 1332, 1381), (1392, 1391, 1313), (1381, 1331, 1382), (1324, 1386, 1385), (956, 984, 983), (956, 983, 1012), (1014, 957, 1011), (957, 956, 1012), (1011, 957, 1012), (925, 982, 1015), (925, 1015, 1010), (1015, 1014, 1011), (1010, 1015, 1011), (927, 926, 1003), (926, 925, 1004), (929, 928, 1001), (928, 927, 1002), (931, 930, 1000), (930, 929, 1001), (1001, 928, 1002), (933, 932, 998), (932, 931, 999), (935, 934, 996), (934, 933, 998), (986, 985, 936), (987, 986, 936), (936, 935, 995), (932, 999, 998), (931, 1000, 999), (927, 1003, 1002), (926, 1004, 1003), (988, 987, 936), (989, 988, 936), (925, 1010, 1009), (925, 1009, 1008), (990, 989, 936), (991, 990, 936), (925, 1008, 1007), (925, 1007, 1006), (992, 991, 936), (993, 992, 936), (925, 1006, 1005), (925, 1005, 1004), (994, 993, 936), (995, 994, 936), (930, 1001, 1000), (996, 995, 935), (997, 996, 934), (864, 863, 844), (863, 862, 855), (844, 863, 854), (862, 861, 856), (861, 860, 856), (860, 859, 858), (858, 857, 860), (857, 856, 860), (856, 855, 862), (855, 854, 863), (854, 853, 844), (853, 852, 844), (852, 851, 848), (851, 850, 848), (850, 849, 848), (848, 847, 846), (846, 845, 852), (845, 844, 852), (844, 843, 864), (843, 842, 866), (864, 843, 865), (842, 841, 867), (841, 840, 868), (842, 867, 866), (840, 839, 869), (839, 838, 869), (870, 838, 837), (837, 836, 871), (871, 836, 872), (836, 835, 872), (835, 834, 872), (834, 833, 873), (833, 832, 874), (834, 873, 872), (832, 831, 874), (831, 830, 875), (830, 829, 875), (829, 828, 876), (828, 827, 877), (827, 826, 878), (825, 924, 918), (924, 923, 918), (829, 876, 875), (826, 825, 879), (833, 874, 873), (831, 875, 874), (838, 870, 869), (848, 846, 852), (865, 843, 866), (837, 871, 870), (923, 922, 918), (922, 921, 920), (920, 919, 922), (919, 918, 922), (918, 917, 909), (917, 916, 910), (916, 915, 910), (915, 914, 911), (910, 915, 911), (914, 913, 912), (912, 911, 914), (910, 909, 917), (909, 908, 890), (888, 909, 889), (908, 907, 901), (907, 906, 902), (906, 905, 902), (905, 904, 902), (904, 903, 902), (902, 901, 907), (901, 900, 908), (900, 899, 891), (899, 898, 891), (898, 897, 893), (897, 896, 894), (896, 895, 894), (894, 893, 897), (893, 892, 898), (892, 891, 898), (891, 890, 908), (908, 900, 891), (909, 888, 887), (889, 909, 890), (918, 909, 825), (825, 909, 885), (909, 887, 886), (867, 841, 868), (909, 886, 885), (825, 885, 884), (825, 884, 883), (869, 868, 840), (825, 883, 882), (825, 882, 881), (825, 881, 880), (825, 880, 879), (876, 828, 877), (879, 878, 826), (590, 589, 596), (589, 588, 608), (597, 608, 598), (588, 587, 666), (587, 586, 668), (668, 586, 669), (586, 585, 669), (585, 584, 669), (584, 583, 670), (583, 582, 671), (584, 670, 669), (582, 581, 672), (581, 580, 672), (580, 579, 672), (579, 578, 672), (578, 577, 672), (577, 576, 672), (672, 671, 582), (671, 670, 583), (591, 590, 596), (608, 597, 589), (593, 592, 591), (595, 594, 593), (597, 596, 589), (596, 595, 591), (599, 598, 607), (607, 598, 608), (601, 600, 605), (600, 599, 605), (603, 602, 601), (605, 604, 601), (604, 603, 601), (607, 606, 599), (606, 605, 599), (609, 608, 655), (656, 608, 588), (611, 610, 616), (610, 609, 617), (613, 612, 611), (615, 614, 613), (617, 616, 610), (616, 615, 611), (619, 618, 555), (618, 617, 555), (621, 620, 626), (620, 619, 626), (623, 622, 621), (625, 624, 621), (624, 623, 621), (627, 626, 619), (626, 625, 621), (557, 556, 641), (556, 555, 642), (638, 560, 639), (555, 627, 619), (615, 613, 611), (608, 656, 655), (595, 593, 591), (587, 668, 667), (558, 557, 640), (560, 638, 561), (617, 609, 555), (587, 667, 666), (656, 588, 657), (559, 558, 639), (561, 638, 637), (561, 637, 562), (588, 666, 665), (560, 559, 639), (562, 637, 636), (636, 563, 562), (564, 563, 636), (564, 635, 565), (566, 565, 634), (634, 565, 635), (568, 567, 633), (567, 566, 633), (568, 632, 569), (570, 569, 632), (570, 632, 631), (572, 571, 631), (571, 570, 631), (574, 573, 628), (573, 572, 630), (630, 572, 631), (628, 679, 574), (629, 628, 573), (632, 568, 633), (635, 564, 636), (588, 665, 664), (588, 664, 663), (630, 629, 573), (588, 663, 662), (588, 662, 661), (634, 633, 566), (588, 661, 660), (588, 660, 659), (639, 558, 640), (588, 659, 658), (588, 658, 657), (640, 557, 641), (641, 556, 642), (609, 655, 654), (609, 654, 653), (642, 555, 643), (643, 555, 644), (609, 653, 652), (609, 652, 651), (644, 555, 645), (645, 555, 646), (609, 651, 650), (609, 650, 649), (646, 555, 647), (647, 555, 648), (609, 649, 555), (957, 1014, 1013), (957, 1013, 1042), (959, 958, 967), (958, 957, 1042), (961, 960, 967), (960, 959, 967), (963, 962, 961), (965, 964, 963), (967, 966, 961), (966, 965, 961), (969, 968, 1039), (968, 967, 1042), (1039, 968, 1040), (971, 970, 1037), (970, 969, 1038), (1038, 969, 1039), (973, 972, 1035), (972, 971, 1036), (1037, 970, 1038), (975, 974, 1032), (974, 973, 1033), (977, 976, 1030), (976, 975, 1031), (1028, 978, 1029), (979, 978, 1028), (978, 977, 1029), (1026, 981, 980), (980, 979, 1027), (1026, 980, 1027), (1016, 1015, 982), (1017, 1016, 982), (982, 981, 1026), (982, 1025, 1024), (982, 1026, 1025), (972, 1036, 1035), (965, 963, 961), (958, 1042, 967), (1042, 1041, 968), (971, 1037, 1036), (982, 1024, 1023), (1018, 1017, 982), (1019, 1018, 982), (1041, 1040, 968), (1020, 1019, 982), (1021, 1020, 982), (1022, 1021, 982), (1023, 1022, 982), (973, 1035, 1034), (1027, 979, 1028), (973, 1034, 1033), (974, 1033, 1032), (1029, 977, 1030), (975, 1032, 1031), (947, 946, 984), (946, 945, 985), (984, 946, 985), (945, 944, 985), (944, 943, 985), (943, 942, 985), (942, 941, 985), (941, 940, 985), (940, 939, 985), (939, 938, 985), (938, 937, 985), (937, 936, 985), (984, 956, 947), (947, 956, 955), (955, 954, 948), (954, 953, 948), (953, 952, 949), (948, 953, 949), (952, 951, 950), (950, 949, 952), (1044, 1043, 1050), (1049, 1048, 1047), (1044, 1050, 1049), (1046, 1045, 1044), (1049, 1047, 1046), (1095, 1132, 1131), (1155, 1154, 1096), (1095, 1131, 1096), (1076, 1075, 1062), (1075, 1074, 1064), (1074, 1073, 1064), (1073, 1072, 1064), (1072, 1071, 1068), (1071, 1070, 1068), (1070, 1069, 1068), (1068, 1067, 1066), (1066, 1065, 1072), (1065, 1064, 1072), (1064, 1063, 1062), (1064, 1062, 1075), (1062, 1061, 1076), (1068, 1066, 1072), (1078, 1077, 1060), (1077, 1076, 1061), (1080, 1079, 1059), (1079, 1078, 1060), (1080, 1059, 1058), (1082, 1081, 1058), (1081, 1080, 1058), (1082, 1058, 1057), (1084, 1083, 1056), (1083, 1082, 1057), (1084, 1056, 1085), (1086, 1085, 1055), (1055, 1085, 1056), (1088, 1087, 1054), (1087, 1086, 1055), (1090, 1089, 1053), (1089, 1088, 1054), (1092, 1091, 1052), (1091, 1090, 1053), (1053, 1089, 1054), (1094, 1093, 1051), (1093, 1092, 1051), (1132, 1095, 1051), (1095, 1094, 1051), (1133, 1132, 1130), (1087, 1055, 1054), (1077, 1061, 1060), (1060, 1059, 1079), (1083, 1057, 1056), (1096, 1154, 1097), (1154, 1153, 1098), (1097, 1154, 1098), (1153, 1099, 1098), (1100, 1099, 1152), (1100, 1152, 1151), (1102, 1101, 1151), (1101, 1100, 1151), (1104, 1103, 1149), (1103, 1102, 1150), (1150, 1102, 1151), (1106, 1105, 1147), (1105, 1104, 1148), (1106, 1147, 1107), (1108, 1107, 1146), (1145, 1109, 1108), (1110, 1109, 1143), (1143, 1109, 1144), (1112, 1111, 1142), (1111, 1110, 1143), (1114, 1113, 1140), (1113, 1112, 1141), (1116, 1115, 1138), (1115, 1114, 1139), (1140, 1113, 1141), (1118, 1117, 1137), (1117, 1116, 1137), (1138, 1115, 1139), (1120, 1119, 1135), (1119, 1118, 1136), (1122, 1121, 1133), (1121, 1120, 1134), (1133, 1121, 1134), (1124, 1123, 1128), (1123, 1122, 1129), (1128, 1123, 1129), (1126, 1125, 1124), (1128, 1127, 1124), (1127, 1126, 1124), (1130, 1129, 1122), (1051, 1130, 1132), (1133, 1130, 1122), (1118, 1137, 1136), (1112, 1142, 1141), (1111, 1143, 1142), (1109, 1145, 1144), (1145, 1108, 1146), (1099, 1153, 1152), (1114, 1140, 1139), (1103, 1150, 1149), (1104, 1149, 1148), (1148, 1147, 1105), (1091, 1053, 1052), (1092, 1052, 1051), (1147, 1146, 1107), (1135, 1134, 1120), (1136, 1135, 1119), (1159, 1158, 1156), (1158, 1157, 1156), (1162, 1161, 1163), (1161, 1160, 1163), (1160, 1159, 1167), (1159, 1156, 1167), (1167, 1166, 1164), (1166, 1165, 1164), (1164, 1163, 1160), (820, 819, 822), (819, 818, 817), (817, 824, 823), (819, 817, 822), (822, 821, 820), (1220, 1219, 1212), (1219, 1218, 1213), (1212, 1219, 1213), (1218, 1217, 1214), (1217, 1216, 1214), (1216, 1215, 1214), (1214, 1213, 1218), (1212, 1211, 1207), (1211, 1210, 1208), (1210, 1209, 1208), (1208, 1207, 1211), (1207, 1206, 1212), (1205, 1204, 1184), (1204, 1203, 1194), (1185, 1204, 1194), (1206, 1205, 1220), (1212, 1206, 1220), (1204, 1185, 1184), (1203, 1202, 1194), (1202, 1201, 1200), (1200, 1199, 1198), (1198, 1197, 1200), (1197, 1196, 1200), (1196, 1195, 1202), (1195, 1194, 1202), (1194, 1193, 1185), (1193, 1192, 1185), (1192, 1191, 1187), (1191, 1190, 1188), (1190, 1189, 1188), (1188, 1187, 1191), (1187, 1186, 1192), (1186, 1185, 1192), (1184, 1183, 1177), (1183, 1182, 1178), (1182, 1181, 1180), (1180, 1179, 1182), (1179, 1178, 1182), (1178, 1177, 1183), (1177, 1176, 1168), (1176, 1175, 1170), (1175, 1174, 1170), (1174, 1173, 1172), (1172, 1171, 1174), (1171, 1170, 1174), (1170, 1169, 1176), (1169, 1168, 1176), (1168, 1260, 1222), (1260, 1259, 1223), (1259, 1258, 1224), (1258, 1257, 1224), (1259, 1224, 1223), (1257, 1256, 1224), (1256, 1255, 1224), (1255, 1254, 1225), (1254, 1253, 1226), (1226, 1252, 1251), (1253, 1252, 1226), (1227, 1251, 1250), (1250, 1249, 1227), (1227, 1249, 1248), (1248, 1247, 1238), (1228, 1248, 1237), (1247, 1246, 1239), (1246, 1245, 1239), (1245, 1244, 1243), (1243, 1242, 1241), (1241, 1240, 1245), (1240, 1239, 1245), (1239, 1238, 1247), (1238, 1237, 1248), (1237, 1236, 1229), (1236, 1235, 1231), (1235, 1234, 1233), (1233, 1232, 1235), (1232, 1231, 1235), (1231, 1230, 1236), (1230, 1229, 1236), (1229, 1228, 1237), (1243, 1241, 1245), (1248, 1228, 1227), (1251, 1227, 1226), (1260, 1223, 1222), (1254, 1226, 1225), (1177, 1168, 1184), (1255, 1225, 1224), (1168, 1222, 1221), (1168, 1221, 1220), (1184, 1168, 1205), (1196, 1202, 1200), (1311, 1310, 1262), (1310, 1309, 1264), (1262, 1310, 1263), (1309, 1308, 1265), (1308, 1307, 1266), (1307, 1306, 1266), (1306, 1305, 1267), (1265, 1308, 1266), (1305, 1304, 1267), (1304, 1303, 1268), (1266, 1306, 1267), (1303, 1302, 1269), (1302, 1301, 1270), (1271, 1301, 1300), (1300, 1299, 1272), (1299, 1298, 1273), (1298, 1297, 1273), (1275, 1296, 1276), (1297, 1296, 1274), (1296, 1295, 1276), (1276, 1295, 1277), (1295, 1294, 1277), (1294, 1293, 1278), (1277, 1294, 1278), (1293, 1292, 1278), (1292, 1291, 1288), (1279, 1288, 1284), (1291, 1290, 1288), (1290, 1289, 1288), (1288, 1287, 1285), (1287, 1286, 1285), (1285, 1284, 1288), (1284, 1283, 1279), (1283, 1282, 1281), (1281, 1280, 1283), (1280, 1279, 1283), (1292, 1288, 1279), (1278, 1292, 1279), (1296, 1275, 1274), (1301, 1271, 1270), (1300, 1272, 1271), (1309, 1265, 1264), (1310, 1264, 1263), (1400, 1312, 1357), (1312, 1311, 1261), (1357, 1312, 1261), (1261, 1311, 1262), (1342, 1375, 1374), (1344, 1343, 1370), (1343, 1342, 1371), (1346, 1367, 1366), (1346, 1345, 1367), (1345, 1344, 1369), (1366, 1347, 1346), (1348, 1347, 1366), (1348, 1365, 1349), (1350, 1349, 1364), (1364, 1349, 1365), (1352, 1351, 1364), (1351, 1350, 1364), (1354, 1353, 1363), (1353, 1352, 1364), (1356, 1355, 1360), (1355, 1354, 1362), (1261, 1356, 1358), (1354, 1363, 1362), (1353, 1364, 1363), (1365, 1348, 1366), (1342, 1374, 1373), (1342, 1373, 1372), (1342, 1372, 1371), (1371, 1370, 1343), (1370, 1369, 1344), (1369, 1368, 1345), (1368, 1367, 1345), (1355, 1362, 1361), (1355, 1361, 1360), (1356, 1360, 1359), (1356, 1359, 1358), (1297, 1274, 1273), (1261, 1358, 1357), (1299, 1273, 1272), (1302, 1270, 1269), (1267, 1304, 1268), (1441, 1440, 1459), (800, 815, 814), (814, 813, 801), (1403, 1402, 1409), (1402, 1401, 1409), (1404, 1403, 1409), (1406, 1405, 1404), (1408, 1407, 1406), (1410, 1409, 1401), (1409, 1408, 1404), (1408, 1406, 1404), (1411, 1410, 1401), (1411, 1401, 1412), (1401, 1450, 1454), (1412, 1401, 1454), (1450, 1449, 1454), (1413, 1412, 1454), (1449, 1448, 1454), (1414, 1413, 1453), (1447, 1446, 1458), (1446, 1445, 1458), (1447, 1458, 1457), (1413, 1454, 1453), (1448, 1447, 1454), (1415, 1414, 1453), (1445, 1444, 1458), (1444, 1443, 1458), (1443, 1442, 1458), (1442, 1441, 1458), (1416, 1415, 1453), (1417, 1416, 1453), (1447, 1457, 1456), (1418, 1417, 1453), (1421, 1420, 1419), (1419, 1418, 1452), (1447, 1456, 1455), (1447, 1455, 1454), (1422, 1421, 1452), (1421, 1419, 1452), (1418, 1453, 1452), (1423, 1422, 1424), (1425, 1424, 1451), (1451, 1424, 1422), (1427, 1426, 1476), (1426, 1425, 1478), (1429, 1428, 1472), (1428, 1427, 1474), (1476, 1426, 1477), (1431, 1430, 1471), (1430, 1429, 1472), (1472, 1428, 1473), (1433, 1432, 1469), (1432, 1431, 1470), (1469, 1434, 1433), (1435, 1434, 1468), (1435, 1467, 1466), (1437, 1436, 1465), (1436, 1435, 1466), (1439, 1465, 1464), (1439, 1438, 1465), (1438, 1437, 1465), (1464, 1440, 1439), (1459, 1440, 1460), (1460, 1440, 1461), (1461, 1440, 1462), (1440, 1464, 1463), (1467, 1435, 1468), (1434, 1469, 1468), (1426, 1478, 1477), (1478, 1425, 1451), (1452, 1451, 1422), (1427, 1476, 1475), (1462, 1440, 1463), (1427, 1475, 1474), (1465, 1436, 1466), (1428, 1474, 1473), (1469, 1432, 1470), (1430, 1472, 1471), (384, 383, 439), (383, 382, 440), (437, 385, 384), (382, 381, 441), (381, 380, 443), (439, 383, 440), (380, 379, 444), (379, 378, 445), (378, 377, 447), (377, 376, 448), (449, 376, 375), (375, 374, 450), (374, 373, 452), (373, 372, 400), (374, 451, 450), (372, 371, 401), (371, 370, 402), (372, 401, 400), (370, 369, 403), (369, 368, 404), (405, 368, 367), (367, 366, 406), (407, 366, 365), (365, 364, 408), (409, 364, 363), (363, 362, 410), (410, 362, 411), (362, 361, 411), (361, 360, 411), (411, 360, 412), (360, 359, 412), (359, 358, 413), (412, 359, 413), (358, 357, 414), (357, 356, 415), (358, 414, 413), (356, 355, 415), (355, 354, 416), (354, 353, 417), (353, 352, 418), (418, 352, 419), (352, 351, 419), (351, 350, 420), (420, 350, 349), (349, 348, 421), (348, 347, 398), (398, 397, 424), (398, 424, 423), (349, 421, 420), (348, 398, 423), (421, 348, 422), (364, 409, 408), (368, 405, 404), (366, 407, 406), (451, 374, 452), (376, 449, 448), (375, 450, 449), (381, 443, 442), (384, 438, 437), (385, 437, 436), (385, 436, 386), (387, 386, 434), (435, 386, 436), (389, 388, 432), (388, 387, 433), (391, 390, 432), (390, 389, 432), (432, 388, 433), (393, 392, 432), (392, 391, 432), (434, 433, 387), (386, 435, 434), (438, 384, 439), (365, 408, 407), (351, 420, 419), (423, 422, 348), (363, 410, 409), (353, 418, 417), (440, 382, 441), (354, 417, 416), (441, 381, 442), (416, 415, 355), (415, 414, 357), (443, 380, 444), (444, 379, 445), (446, 445, 378), (447, 446, 378), (448, 447, 377), (367, 406, 405), (452, 373, 399), (369, 404, 403), (399, 373, 400), (370, 403, 402), (425, 424, 397), (397, 396, 425), (396, 395, 426), (426, 395, 394), (394, 393, 427), (428, 393, 429), (393, 432, 431), (393, 431, 430), (393, 428, 427), (429, 393, 430), (426, 425, 396), (13, 12, 1), (12, 11, 1), (1, 11, 2), (11, 10, 2), (10, 9, 3), (9, 8, 3), (8, 7, 3), (7, 6, 5), (5, 4, 7), (4, 3, 7), (3, 2, 10), (0, 85, 14), (85, 84, 75), (14, 85, 75), (84, 83, 82), (82, 81, 78), (81, 80, 78), (80, 79, 78), (78, 77, 76), (76, 75, 84), (75, 74, 14), (78, 76, 82), (84, 82, 76), (1, 0, 13), (16, 15, 73), (15, 14, 74), (73, 15, 74), (14, 13, 0), (52, 51, 41), (51, 50, 43), (42, 51, 43), (50, 49, 46), (49, 48, 46), (48, 47, 46), (46, 45, 44), (44, 43, 50), (42, 41, 51), (41, 40, 39), (52, 41, 38), (39, 38, 41), (38, 37, 52), (37, 36, 53), (36, 35, 54), (35, 34, 55), (54, 35, 55), (34, 33, 56), (33, 32, 58), (34, 56, 55), (32, 31, 59), (31, 30, 61), (30, 29, 62), (29, 28, 64), (65, 26, 66), (28, 27, 64), (27, 26, 65), (66, 25, 24), (26, 25, 66), (67, 24, 23), (23, 22, 67), (67, 22, 68), (22, 21, 68), (21, 20, 68), (68, 20, 69), (20, 19, 69), (19, 18, 69), (70, 18, 17), (17, 16, 72), (72, 16, 73), (18, 70, 69), (24, 67, 66), (58, 32, 59), (37, 53, 52), (53, 36, 54), (46, 44, 50), (56, 33, 57), (17, 72, 71), (17, 71, 70), (57, 33, 58), (59, 31, 60), (27, 65, 64), (60, 31, 61), (62, 61, 30), (29, 64, 63)]
    
    logo_vs = [(0.26797428727149963, 0.07412988692522049, 0.0), (0.2973800599575043, 0.07410771399736404, 0.0), (0.29779163002967834, 0.07404188066720963, 0.0), (0.29816171526908875, 0.07393338531255722, 0.0), (0.2984895408153534, 0.07378324121236801, 0.0), (0.29877421259880066, 0.07359246164560318, 0.0), (0.29901471734046936, 0.07336204499006271, 0.0), (0.2992102801799774, 0.0730930045247078, 0.0), (0.2993600070476532, 0.0727863535284996, 0.0), (0.2994629442691803, 0.07244310528039932, 0.0), (0.2995181977748871, 0.07206425815820694, 0.0), (0.2995249330997467, 0.07165082544088364, 0.0), (0.29827991127967834, 0.06313661485910416, 0.0), (0.27540531754493713, 0.06462081521749496, 0.0), (0.2729724943637848, 0.04975900799036026, 0.0), (0.28045180439949036, 0.04906067997217178, 0.0), (0.2848070561885834, 0.04818839579820633, 0.0), (0.2889985740184784, 0.04673577845096588, 0.0), (0.2910153567790985, 0.04573246091604233, 0.0), (0.29361626505851746, 0.04400550574064255, 0.0), (0.2947360575199127, 0.04303577542304993, 0.0), (0.29573652148246765, 0.041995830833911896, 0.0), (0.2966184914112091, 0.04088612645864487, 0.0), (0.29738280177116394, 0.03970712423324585, 0.0), (0.298030287027359, 0.038459278643131256, 0.0), (0.2985617220401764, 0.03714305907487869, 0.0), (0.2989780604839325, 0.03575892001390457, 0.0), (0.2994684875011444, 0.03278874605894089, 0.0), (0.2994888722896576, 0.028962619602680206, 0.0), (0.2988859713077545, 0.024733446538448334, 0.0), (0.2976396381855011, 0.02083711326122284, 0.0), (0.2967798411846161, 0.019012175500392914, 0.0), (0.29459652304649353, 0.015605553984642029, 0.0), (0.2918073236942291, 0.01251903921365738, 0.0), (0.28842732310295105, 0.009747534990310669, 0.0), (0.2845591604709625, 0.007240980863571167, 0.0), (0.2805432975292206, 0.005124989897012711, 0.0), (0.27424946427345276, 0.002674572169780731, 0.0), (0.26987817883491516, 0.0015175119042396545, 0.0), (0.25896838307380676, 0.00018766522407531738, 0.0), (0.2587573826313019, 0.0007014200091362, 0.0), (0.2587113678455353, 0.0008643902838230133, 0.0), (0.2580145299434662, 0.0069268569350242615, 0.0), (0.2580288350582123, 0.007305465638637543, 0.0), (0.258082777261734, 0.007650136947631836, 0.0), (0.25817611813545227, 0.007961302995681763, 0.0), (0.2583087980747223, 0.008239388465881348, 0.0), (0.2584807574748993, 0.00848483294248581, 0.0), (0.2586918771266937, 0.008698061108589172, 0.0), (0.2589420974254608, 0.008879505097866058, 0.0), (0.25923123955726624, 0.009029597043991089, 0.0), (0.2595592439174652, 0.009148769080638885, 0.0), (0.266605943441391, 0.010272681713104248, 0.0), (0.27265962958335876, 0.01200173795223236, 0.0), (0.2784392535686493, 0.014637507498264313, 0.0), (0.2815301716327667, 0.01660306751728058, 0.0), (0.2829379737377167, 0.017758287489414215, 0.0), (0.2847701609134674, 0.0197293683886528, 0.0), (0.2855106294155121, 0.02077440917491913, 0.0), (0.2861367166042328, 0.0218573659658432, 0.0), (0.28665027022361755, 0.02297692745923996, 0.0), (0.28705325722694397, 0.02413177490234375, 0.0), (0.2873476445674896, 0.02532060444355011, 0.0), (0.2875353991985321, 0.026542097330093384, 0.0), (0.28759875893592834, 0.02907782793045044, 0.0), (0.28725889325141907, 0.03172844648361206, 0.0), (0.2869194447994232, 0.03294328600168228, 0.0), (0.2864117920398712, 0.03403835743665695, 0.0), (0.28609737753868103, 0.034541621804237366, 0.0), (0.2853526771068573, 0.03546087443828583, 0.0), (0.2844600975513458, 0.036265455186367035, 0.0), (0.28342780470848083, 0.03695739805698395, 0.0), (0.2821613848209381, 0.03759104013442993, 0.0), (0.2807345688343048, 0.03814936429262161, 0.0), (0.27779659628868103, 0.0389266312122345, 0.0), (0.2635621726512909, 0.04007439315319061, 0.0), (0.2632463276386261, 0.040159374475479126, 0.0), (0.2629564702510834, 0.0402844101190567, 0.0), (0.2626948058605194, 0.04044630378484726, 0.0), (0.2624634802341461, 0.04064185917377472, 0.0), (0.26226475834846497, 0.0408678874373436, 0.0), (0.26210084557533264, 0.041121192276477814, 0.0), (0.26197394728660583, 0.04139857739210129, 0.0), (0.26188626885414124, 0.04169684648513794, 0.0), (0.2618400752544403, 0.042012810707092285, 0.0), (0.26183757185935974, 0.04234328120946884, 0.0), (0.008942576125264168, 0.0476173534989357, 0.0), (0.009772496297955513, 0.049940966069698334, 0.0), (0.010864967480301857, 0.052056483924388885, 0.0), (0.012206895276904106, 0.05397354066371918, 0.0), (0.013785192742943764, 0.05570177733898163, 0.0), (0.015586761757731438, 0.057250842452049255, 0.0), (0.017598511651158333, 0.058630384504795074, 0.0), (0.019682539626955986, 0.059779368340969086, 0.0), (0.021832028403878212, 0.06070787459611893, 0.0), (0.024048471823334694, 0.061422087252140045, 0.0), (0.02633335255086422, 0.061928197741508484, 0.0), (0.031114406883716583, 0.06234089285135269, 0.0), (0.031114406883716583, 0.05356263369321823, 0.0), (0.028996797278523445, 0.05329094082117081, 0.0), (0.026999840512871742, 0.052782073616981506, 0.0), (0.0251294132322073, 0.05202551931142807, 0.0), (0.023391397669911385, 0.05101078748703003, 0.0), (0.021791676059365273, 0.049727365374565125, 0.0), (0.020336119458079338, 0.04816475510597229, 0.0), (0.019438689574599266, 0.046922869980335236, 0.0), (0.01870526187121868, 0.04561499506235123, 0.0), (0.0181319210678339, 0.044236257672309875, 0.0), (0.017714744433760643, 0.04278181493282318, 0.0), (0.017449816688895226, 0.041246794164180756, 0.0), (0.017333215102553368, 0.039626337587833405, 0.0), (0.03454912453889847, 0.039626337587833405, 0.0), (0.034549959003925323, 0.026489049196243286, 0.0), (0.03405412286520004, 0.022603124380111694, 0.0), (0.033580876886844635, 0.020770907402038574, 0.0), (0.032199926674366, 0.01732093095779419, 0.0), (0.030261345207691193, 0.014147475361824036, 0.0), (0.027791080996394157, 0.01123926043510437, 0.0), (0.02481507696211338, 0.008584991097450256, 0.0), (0.021603872999548912, 0.0063573941588401794, 0.0), (0.018234150484204292, 0.004576325416564941, 0.0), (0.014712022617459297, 0.003217097371816635, 0.0), (0.0110436100512743, 0.002255026251077652, 0.0), (0.007235022261738777, 0.0016654133796691895, 0.0), (0.003292372450232506, 0.001423567533493042, 0.0), (0.003292372450232506, 0.01022157073020935, 0.0), (0.0077092405408620834, 0.010678686201572418, 0.0), (0.0116646159440279, 0.01157524436712265, 0.0), (0.013550655916333199, 0.012248598039150238, 0.0), (0.015368493273854256, 0.01308443397283554, 0.0), (0.017112793400883675, 0.01409207284450531, 0.0), (0.018778221681714058, 0.015280850231647491, 0.0), (0.02084810473024845, 0.017172686755657196, 0.0), (0.02252788282930851, 0.019258588552474976, 0.0), (0.023226724937558174, 0.02037147432565689, 0.0), (0.02435280941426754, 0.02273143082857132, 0.0), (0.025130731984972954, 0.025262728333473206, 0.0), (0.025577275082468987, 0.027956277132034302, 0.0), (0.025729497894644737, 0.03105124831199646, 0.0), (0.025727855041623116, 0.031067483127117157, 0.0), (0.02572317235171795, 0.03108379989862442, 0.0), (0.025715826079249382, 0.03110027313232422, 0.0), (0.025706185027956963, 0.031116977334022522, 0.0), (0.025591203942894936, 0.031268514692783356, 0.0), (0.02453540451824665, 0.028828494250774384, 0.0), (0.023310082033276558, 0.02664732187986374, 0.0), (0.02192210592329502, 0.02471321076154709, 0.0), (0.020378345623612404, 0.023014351725578308, 0.0), (0.01868567056953907, 0.021538957953453064, 0.0), (0.016850950196385384, 0.02027522772550583, 0.0), (0.014881057664752007, 0.019211366772651672, 0.0), (0.012782858684659004, 0.018335580825805664, 0.0), (0.008229019120335579, 0.01710103452205658, 0.0), (0.003244394436478615, 0.01647724211215973, 0.0), (0.003244394436478615, 0.025365546345710754, 0.0), (0.005477456375956535, 0.02565702050924301, 0.0), (0.007574187591671944, 0.026211224496364594, 0.0), (0.009527137503027916, 0.0270388200879097, 0.0), (0.011328862980008125, 0.028150461614131927, 0.0), (0.012170689180493355, 0.028816133737564087, 0.0), (0.013731608167290688, 0.03037383407354355, 0.0), (0.014873279258608818, 0.0318736732006073, 0.0), (0.015611803159117699, 0.03314638137817383, 0.0), (0.016197452321648598, 0.034482233226299286, 0.0), (0.016623327508568764, 0.03585715591907501, 0.0), (0.016882533207535744, 0.03724709153175354, 0.0), (0.016968170180916786, 0.038627974689006805, 0.0), (0.016943739727139473, 0.03930748999118805, 0.0), (0.00010037235915660858, 0.03930748999118805, 0.0), (0.00011428818106651306, 0.054478131234645844, 0.0), (0.000366920605301857, 0.05636154115200043, 0.0), (0.0008161719888448715, 0.05818208307027817, 0.0), (0.0014481674879789352, 0.05994454771280289, 0.0), (0.0032048802822828293, 0.06331437081098557, 0.0), (0.005478711798787117, 0.06644149124622345, 0.0), (0.008068716153502464, 0.06913446635007858, 0.0), (0.010952392593026161, 0.07142143696546555, 0.0), (0.014107244089245796, 0.07333052903413773, 0.0), (0.01751076988875866, 0.0748898908495903, 0.0), (0.02114047296345234, 0.07612764090299606, 0.0), (0.02438567765057087, 0.0768946185708046, 0.0), (0.027705514803528786, 0.07734053581953049, 0.0), (0.031120046973228455, 0.0774848684668541, 0.0), (0.031120046973228455, 0.06877433508634567, 0.0), (0.025246886536478996, 0.06797579675912857, 0.0), (0.022675683721899986, 0.06731545925140381, 0.0), (0.020241206511855125, 0.0664205327630043, 0.0), (0.017958348616957664, 0.06526945531368256, 0.0), (0.015842003747820854, 0.06384067237377167, 0.0), (0.013907073065638542, 0.06211263686418533, 0.0), (0.012168442830443382, 0.06006380170583725, 0.0), (0.011258138343691826, 0.05869395285844803, 0.0), (0.01050047017633915, 0.0572671964764595, 0.0), (0.009887682273983955, 0.05578683316707611, 0.0), (0.009412011131644249, 0.054256148636341095, 0.0), (0.008840972557663918, 0.05105698108673096, 0.0), (0.008674459531903267, 0.04770199954509735, 0.0), (0.04587210714817047, 0.03011161834001541, 0.0), (0.05310560762882233, 0.03011161834001541, 0.0), (0.053111255168914795, 0.028243668377399445, 0.0), (0.053162992000579834, 0.02770879864692688, 0.0), (0.053265027701854706, 0.027203291654586792, 0.0), (0.053415924310684204, 0.02672935277223587, 0.0), (0.05361424386501312, 0.026289187371730804, 0.0), (0.05385854095220566, 0.025884993374347687, 0.0), (0.054147377610206604, 0.025518983602523804, 0.0), (0.054479315876960754, 0.025193355977535248, 0.0), (0.054852910339832306, 0.024910323321819305, 0.0), (0.05526672303676605, 0.02467208355665207, 0.0), (0.05571930855512619, 0.02448084205389023, 0.0), (0.05620923638343811, 0.024338804185390472, 0.0), (0.05673506110906601, 0.024248160421848297, 0.0), (0.05834940820932388, 0.024153999984264374, 0.0), (0.05996375530958176, 0.024248160421848297, 0.0), (0.06045781075954437, 0.02432876080274582, 0.0), (0.06091632694005966, 0.02445017546415329, 0.0), (0.06133846938610077, 0.024611718952655792, 0.0), (0.06172339618206024, 0.02481270581483841, 0.0), (0.06207025796175003, 0.02505245804786682, 0.0), (0.06237821280956268, 0.025330282747745514, 0.0), (0.06264642626047134, 0.02564549446105957, 0.0), (0.06287404894828796, 0.025997407734394073, 0.0), (0.06306023895740509, 0.026385337114334106, 0.0), (0.06320415437221527, 0.026808589696884155, 0.0), (0.06330495327711105, 0.0272664874792099, 0.0), (0.06336177885532379, 0.027758337557315826, 0.0), (0.06334343552589417, 0.033068761229515076, 0.0), (0.06328324973583221, 0.03343285620212555, 0.0), (0.06319040805101395, 0.03377455472946167, 0.0), (0.06306564062833786, 0.0340939462184906, 0.0), (0.06290967017412186, 0.034391120076179504, 0.0), (0.06272322684526443, 0.03466615825891495, 0.0), (0.0625070333480835, 0.03491915762424469, 0.0), (0.06226181238889694, 0.0351502001285553, 0.0), (0.061988286674022675, 0.035359375178813934, 0.0), (0.06168718636035919, 0.035546764731407166, 0.0), (0.06135924160480499, 0.03571246564388275, 0.0), (0.0509917214512825, 0.03962069749832153, 0.0), (0.049942031502723694, 0.04022562503814697, 0.0), (0.04902710020542145, 0.04094616323709488, 0.0), (0.04824528843164444, 0.041778936982154846, 0.0), (0.04759494960308075, 0.042720578610897064, 0.0), (0.04707443714141846, 0.043767720460891724, 0.0), (0.04668210446834564, 0.044916994869709015, 0.0), (0.04622594267129898, 0.04723192751407623, 0.0), (0.04614858329296112, 0.04955752193927765, 0.0), (0.04626450687646866, 0.050722941756248474, 0.0), (0.04649018496274948, 0.05188938230276108, 0.0), (0.04699484258890152, 0.05350193381309509, 0.0), (0.04769477993249893, 0.05495905876159668, 0.0), (0.04859243333339691, 0.05625205487012863, 0.0), (0.04969023913145065, 0.05737222731113434, 0.0), (0.050990618765354156, 0.058310866355895996, 0.0), (0.05249600112438202, 0.0590592697262764, 0.0), (0.054849088191986084, 0.059836991131305695, 0.0), (0.05718861520290375, 0.060255564749240875, 0.0), (0.05950901657342911, 0.060304343700408936, 0.0), (0.061804719269275665, 0.05997266620397568, 0.0), (0.06407015770673752, 0.0592498704791069, 0.0), (0.06629976630210876, 0.058125294744968414, 0.0), (0.0671716034412384, 0.05754784494638443, 0.0), (0.06795115768909454, 0.05691944807767868, 0.0), (0.06863833963871002, 0.056241124868392944, 0.0), (0.06923305988311768, 0.0555138885974884, 0.0), (0.06973523646593094, 0.054738759994506836, 0.0), (0.07014477252960205, 0.05391675978899002, 0.0), (0.07046158611774445, 0.053048908710479736, 0.0), (0.07068558782339096, 0.05213622748851776, 0.0), (0.07081668823957443, 0.05117972940206528, 0.0), (0.0708548054099083, 0.05018043518066406, 0.0), (0.07065172493457794, 0.04805753380060196, 0.0), (0.06363554298877716, 0.04805753380060196, 0.0), (0.06337589025497437, 0.050461605191230774, 0.0), (0.06322763115167618, 0.05109626054763794, 0.0), (0.06302707642316818, 0.051674067974090576, 0.0), (0.06277438998222351, 0.05219508707523346, 0.0), (0.0624697282910347, 0.05265938490629196, 0.0), (0.06211324781179428, 0.05306701362133026, 0.0), (0.061705105006694794, 0.05341802537441254, 0.0), (0.061245448887348175, 0.05371248722076416, 0.0), (0.06073444336652756, 0.05395045876502991, 0.0), (0.060172244906425476, 0.05413199961185455, 0.0), (0.05955900996923447, 0.05425716191530228, 0.0), (0.05889490246772766, 0.05432600528001785, 0.0), (0.05755072832107544, 0.05429720878601074, 0.0), (0.056960560381412506, 0.054200299084186554, 0.0), (0.05641111731529236, 0.05404853820800781, 0.0), (0.05590395629405975, 0.053842611610889435, 0.0), (0.055440619587898254, 0.053583189845085144, 0.0), (0.055022649466991425, 0.05327095091342926, 0.0), (0.05465160310268402, 0.05290656536817551, 0.0), (0.05432902276515961, 0.0524907112121582, 0.0), (0.05405645817518234, 0.05202407389879227, 0.0), (0.05383545905351639, 0.051507316529750824, 0.0), (0.0536675751209259, 0.05094112455844879, 0.0), (0.05355435609817505, 0.050326161086559296, 0.0), (0.053468845784664154, 0.04920867085456848, 0.0), (0.05356563627719879, 0.04695425182580948, 0.0), (0.05361081659793854, 0.04663032293319702, 0.0), (0.053683631122112274, 0.04632318764925003, 0.0), (0.05378313362598419, 0.04603306204080582, 0.0), (0.053908392786979675, 0.04576016217470169, 0.0), (0.054058462381362915, 0.045504696667194366, 0.0), (0.0542324036359787, 0.04526688903570175, 0.0), (0.054429277777671814, 0.04504694789648056, 0.0), (0.05464813858270645, 0.0448450967669487, 0.0), (0.054888054728507996, 0.044661544263362885, 0.0), (0.05542726814746857, 0.044350214302539825, 0.0), (0.06596294045448303, 0.040533408522605896, 0.0), (0.06740332394838333, 0.0396670326590538, 0.0), (0.06802930682897568, 0.03916285187005997, 0.0), (0.06859076768159866, 0.03861101716756821, 0.0), (0.06908642500638962, 0.03801128268241882, 0.0), (0.06951498985290527, 0.03736340254545212, 0.0), (0.06987518817186356, 0.03666713088750839, 0.0), (0.0701657310128212, 0.03592222183942795, 0.0), (0.07038532942533493, 0.03512843698263168, 0.0), (0.07053270936012268, 0.0342855229973793, 0.0), (0.07067781686782837, 0.0296095609664917, 0.0), (0.07044287770986557, 0.02694004774093628, 0.0), (0.07020621001720428, 0.025789305567741394, 0.0), (0.06988707929849625, 0.024724796414375305, 0.0), (0.06948545575141907, 0.02374529093503952, 0.0), (0.06900130957365036, 0.02284955233335495, 0.0), (0.06843461096286774, 0.022036351263523102, 0.0), (0.0677853375673294, 0.021304450929164886, 0.0), (0.06705345213413239, 0.020652614533901215, 0.0), (0.06623892486095428, 0.020079605281352997, 0.0), (0.06534173339605331, 0.01958419382572174, 0.0), (0.06436184048652649, 0.019165143370628357, 0.0), (0.06329921633005142, 0.018821217119693756, 0.0), (0.06056099385023117, 0.018296003341674805, 0.0), (0.05739159882068634, 0.018170960247516632, 0.0), (0.05581897497177124, 0.018325872719287872, 0.0), (0.05425701290369034, 0.018642239272594452, 0.0), (0.052707672119140625, 0.019132450222969055, 0.0), (0.05152745544910431, 0.019637413322925568, 0.0), (0.05045662075281143, 0.02021808922290802, 0.0), (0.04949565976858139, 0.020874127745628357, 0.0), (0.048645056784152985, 0.021605178713798523, 0.0), (0.04790531098842621, 0.022410884499549866, 0.0), (0.04727690666913986, 0.02329089492559433, 0.0), (0.04676033556461334, 0.02424485981464386, 0.0), (0.046356089413166046, 0.025272421538829803, 0.0), (0.046064652502536774, 0.026373229920864105, 0.0), (0.04588651657104492, 0.02754693478345871, 0.0), (0.04582217335700989, 0.028793178498744965, 0.0), (0.10281725227832794, 0.04810831695795059, 0.0), (0.09569099545478821, 0.04810831695795059, 0.0), (0.09568816423416138, 0.0498267263174057, 0.0), (0.09556393325328827, 0.05089160054922104, 0.0), (0.09528155624866486, 0.05180057883262634, 0.0), (0.09486221522092819, 0.05255988985300064, 0.0), (0.09432710707187653, 0.05317576229572296, 0.0), (0.09369740635156631, 0.05365443229675293, 0.0), (0.0929943099617958, 0.054002128541469574, 0.0), (0.09223899990320206, 0.05422507971525192, 0.0), (0.09145266562700272, 0.0543295219540596, 0.0), (0.09065648913383484, 0.05432168394327164, 0.0), (0.08987165987491608, 0.05420779436826706, 0.0), (0.08911936730146408, 0.05399408936500549, 0.0), (0.0884207934141159, 0.05368679016828537, 0.0), (0.08827516436576843, 0.05359940230846405, 0.0), (0.08799715340137482, 0.05337587743997574, 0.0), (0.08774182945489883, 0.05310014635324478, 0.0), (0.08751524239778519, 0.05278757959604263, 0.0), (0.08732341974973679, 0.05245353281497955, 0.0), (0.08717240393161774, 0.052113376557826996, 0.0), (0.08692353218793869, 0.05120617896318436, 0.0), (0.08676943182945251, 0.05018598586320877, 0.0), (0.08670707046985626, 0.027880273759365082, 0.0), (0.08683592081069946, 0.027020834386348724, 0.0), (0.08706729859113693, 0.02628374844789505, 0.0), (0.08739401400089264, 0.025663815438747406, 0.0), (0.08780888468027115, 0.025155849754810333, 0.0), (0.08830472826957703, 0.024754658341407776, 0.0), (0.08887436985969543, 0.024455048143863678, 0.0), (0.08951061964035034, 0.024251826107501984, 0.0), (0.09020628780126572, 0.024139799177646637, 0.0), (0.09095419943332672, 0.024113774299621582, 0.0), (0.09174717217683792, 0.024168558418750763, 0.0), (0.09301893413066864, 0.024406276643276215, 0.0), (0.09342464059591293, 0.024547353386878967, 0.0), (0.09379544109106064, 0.024721719324588776, 0.0), (0.09413164108991623, 0.024928919970989227, 0.0), (0.09443353861570358, 0.025168493390083313, 0.0), (0.09470143914222717, 0.025439977645874023, 0.0), (0.09493564814329147, 0.02574291080236435, 0.0), (0.09513647109270096, 0.02607683092355728, 0.0), (0.0953042134642601, 0.026441283524036407, 0.0), (0.09543917328119278, 0.02683579921722412, 0.0), (0.09561196714639664, 0.027713187038898468, 0.0), (0.09575872123241425, 0.030207559466362, 0.0), (0.1028708666563034, 0.030207559466362, 0.0), (0.10297247767448425, 0.02764567732810974, 0.0), (0.10282960534095764, 0.026405341923236847, 0.0), (0.10252280533313751, 0.025197923183441162, 0.0), (0.10202597826719284, 0.024027809500694275, 0.0), (0.10131298005580902, 0.02289939671754837, 0.0), (0.10054734349250793, 0.021977022290229797, 0.0), (0.0997101292014122, 0.021154344081878662, 0.0), (0.09880220144987106, 0.020431838929653168, 0.0), (0.09782442450523376, 0.019809968769550323, 0.0), (0.09677765518426895, 0.019289210438728333, 0.0), (0.09566276520490646, 0.0188700333237648, 0.0), (0.09381967037916183, 0.018396049737930298, 0.0), (0.09198229759931564, 0.01815478503704071, 0.0), (0.09015543758869171, 0.018143802881240845, 0.0), (0.08834386616945267, 0.018360666930675507, 0.0), (0.08655235916376114, 0.018802955746650696, 0.0), (0.08478569984436035, 0.01946822553873062, 0.0), (0.08320090919733047, 0.020326413214206696, 0.0), (0.08250494301319122, 0.020829513669013977, 0.0), (0.08187530189752579, 0.021381646394729614, 0.0), (0.08131351321935654, 0.02198256552219391, 0.0), (0.08082110434770584, 0.022632040083408356, 0.0), (0.08039960265159607, 0.02332983911037445, 0.0), (0.08005054295063019, 0.024075724184513092, 0.0), (0.07977545261383057, 0.024869456887245178, 0.0), (0.07957585155963898, 0.025710806250572205, 0.0), (0.07945327460765839, 0.026599541306495667, 0.0), (0.07945524156093597, 0.051800668239593506, 0.0), (0.07957057654857635, 0.05260960012674332, 0.0), (0.07975596189498901, 0.0533793568611145, 0.0), (0.08000925928354263, 0.05410993844270706, 0.0), (0.0803283303976059, 0.0548013299703598, 0.0), (0.08071103692054749, 0.05545351654291153, 0.0), (0.08115524798631668, 0.056066498160362244, 0.0), (0.08165882527828217, 0.05664025992155075, 0.0), (0.08221963047981262, 0.057174794375896454, 0.0), (0.08350438624620438, 0.05812612920999527, 0.0), (0.0852634608745575, 0.05905284732580185, 0.0), (0.08736544847488403, 0.0598156601190567, 0.0), (0.08949236571788788, 0.06023940443992615, 0.0), (0.09056291729211807, 0.0603254958987236, 0.0), (0.09271370619535446, 0.06024886667728424, 0.0), (0.094871386885643, 0.059844136238098145, 0.0), (0.09702874720096588, 0.05911571532487869, 0.0), (0.09807576984167099, 0.05861552804708481, 0.0), (0.09902918338775635, 0.05801798403263092, 0.0), (0.09988626092672348, 0.057329535484313965, 0.0), (0.1006442978978157, 0.05655664950609207, 0.0), (0.10130057483911514, 0.05570577085018158, 0.0), (0.10185237973928452, 0.05478335916996002, 0.0), (0.10229699313640594, 0.05379587411880493, 0.0), (0.10263170301914215, 0.05274977535009384, 0.0), (0.10285380482673645, 0.05165150761604309, 0.0), (0.10296057164669037, 0.05050753802061081, 0.0), (0.10294929146766663, 0.04932431876659393, 0.0), (0.126620352268219, 0.059911422431468964, 0.0), (0.1379518210887909, 0.01862737536430359, 0.0), (0.13068446516990662, 0.01862737536430359, 0.0), (0.12854516506195068, 0.027329444885253906, 0.0), (0.11861355602741241, 0.027329444885253906, 0.0), (0.11646297574043274, 0.018596328794956207, 0.0), (0.10937340557575226, 0.018596328794956207, 0.0), (0.10939881205558777, 0.01926334947347641, 0.0), (0.10942141711711884, 0.0194048210978508, 0.0), (0.11304393410682678, 0.03260401636362076, 0.0), (0.1148475706577301, 0.03916853666305542, 0.0), (0.12029682099819183, 0.059052951633930206, 0.0), (0.1204226166009903, 0.05936644226312637, 0.0), (0.1204967200756073, 0.05949538201093674, 0.0), (0.12058039009571075, 0.05960645526647568, 0.0), (0.12067519128322601, 0.05970015376806259, 0.0), (0.12078270316123962, 0.05977698415517807, 0.0), (0.12090447545051575, 0.05983743816614151, 0.0), (0.12104208767414093, 0.0598820224404335, 0.0), (0.12119710445404053, 0.05991123616695404, 0.0), (0.12367390841245651, 0.047744326293468475, 0.0), (0.12340860813856125, 0.047721751034259796, 0.0), (0.12109412252902985, 0.03798171877861023, 0.0), (0.11992591619491577, 0.03306592255830765, 0.0), (0.12054227292537689, 0.03306592255830765, 0.0), (0.12717071175575256, 0.03306592255830765, 0.0), (0.1460433006286621, 0.054355524480342865, 0.0), (0.13762161135673523, 0.054355524480342865, 0.0), (0.13762161135673523, 0.05982395261526108, 0.0), (0.1616702675819397, 0.05982395261526108, 0.0), (0.1616702675819397, 0.054420433938503265, 0.0), (0.1533445417881012, 0.054420433938503265, 0.0), (0.1533445417881012, 0.018607616424560547, 0.0), (0.1460433006286621, 0.018607616424560547, 0.0), (0.1733178198337555, 0.018604792654514313, 0.0), (0.1733178198337555, 0.054299093782901764, 0.0), (0.16496950387954712, 0.054299093782901764, 0.0), (0.16496950387954712, 0.05980702489614487, 0.0), (0.18887421488761902, 0.05980702489614487, 0.0), (0.18887421488761902, 0.05440632253885269, 0.0), (0.1806049346923828, 0.05440632253885269, 0.0), (0.1806049346923828, 0.018604792654514313, 0.0), (0.20314085483551025, 0.024451322853565216, 0.0), (0.21740180253982544, 0.024451322853565216, 0.0), (0.21740180253982544, 0.0186443030834198, 0.0), (0.19586217403411865, 0.0186443030834198, 0.0), (0.19586217403411865, 0.05981830507516861, 0.0), (0.21738487482070923, 0.05981830507516861, 0.0), (0.21738487482070923, 0.054417602717876434, 0.0), (0.20317187905311584, 0.054417602717876434, 0.0), (0.20317187905311584, 0.04220535606145859, 0.0), (0.21560120582580566, 0.04220535606145859, 0.0), (0.21560120582580566, 0.03661278635263443, 0.0), (0.2031436562538147, 0.03661278635263443, 0.0), (0.24417397379875183, 0.03725895285606384, 0.0), (0.2519550025463104, 0.018531426787376404, 0.0), (0.24530372023582458, 0.01856788992881775, 0.0), (0.24496588110923767, 0.01861785352230072, 0.0), (0.2446860671043396, 0.01870022714138031, 0.0), (0.2444523274898529, 0.01882311701774597, 0.0), (0.2442527413368225, 0.01899462193250656, 0.0), (0.24407538771629333, 0.019222840666770935, 0.0), (0.2439083456993103, 0.019515879452228546, 0.0), (0.23783642053604126, 0.03525368124246597, 0.0), (0.23765772581100464, 0.03559309244155884, 0.0), (0.23755678534507751, 0.03573419153690338, 0.0), (0.23744621872901917, 0.03585632145404816, 0.0), (0.23732465505599976, 0.03595956414937973, 0.0), (0.23719069361686707, 0.03604399412870407, 0.0), (0.23704293370246887, 0.036109693348407745, 0.0), (0.23687994480133057, 0.03615673631429672, 0.0), (0.23670035600662231, 0.03618519753217697, 0.0), (0.23315861821174622, 0.03616977483034134, 0.0), (0.23315861821174622, 0.018616080284118652, 0.0), (0.2259109914302826, 0.018616080284118652, 0.0), (0.2259109914302826, 0.0597449466586113, 0.0), (0.2262304723262787, 0.059871941804885864, 0.0), (0.2262941300868988, 0.05988435447216034, 0.0), (0.2397136688232422, 0.05978837609291077, 0.0), (0.2416626513004303, 0.05950886011123657, 0.0), (0.24368509650230408, 0.05895324796438217, 0.0), (0.245362788438797, 0.0582011342048645, 0.0), (0.24611204862594604, 0.05773580074310303, 0.0), (0.2468012571334839, 0.05721105635166168, 0.0), (0.24743017554283142, 0.05662698298692703, 0.0), (0.24799853563308716, 0.05598365515470505, 0.0), (0.2485060691833496, 0.0552811473608017, 0.0), (0.24895253777503967, 0.054519541561603546, 0.0), (0.24966123700141907, 0.05281934142112732, 0.0), (0.2502005398273468, 0.05048428475856781, 0.0), (0.25041088461875916, 0.047693535685539246, 0.0), (0.2503356635570526, 0.04630066454410553, 0.0), (0.2501348555088043, 0.04491030424833298, 0.0), (0.24961426854133606, 0.042929500341415405, 0.0), (0.249391108751297, 0.042361997067928314, 0.0), (0.24884700775146484, 0.041304610669612885, 0.0), (0.2485266625881195, 0.040814436972141266, 0.0), (0.2477908432483673, 0.039910390973091125, 0.0), (0.24693015217781067, 0.03910710662603378, 0.0), (0.24594691395759583, 0.03840339928865433, 0.0), (0.24442234635353088, 0.03754958510398865, 0.0), (0.24440452456474304, 0.03753729164600372, 0.0), (0.24438747763633728, 0.03752295672893524, 0.0), (0.24435415863990784, 0.03748802840709686, 0.0), (0.2332150638103485, 0.054474033415317535, 0.0), (0.2332150638103485, 0.0413193479180336, 0.0), (0.23960188031196594, 0.04170874506235123, 0.0), (0.24004265666007996, 0.041785091161727905, 0.0), (0.24045667052268982, 0.041900523006916046, 0.0), (0.24084240198135376, 0.04205390810966492, 0.0), (0.2411983609199524, 0.04224412143230438, 0.0), (0.24152302742004395, 0.04247003793716431, 0.0), (0.24181491136550903, 0.042730532586574554, 0.0), (0.24207252264022827, 0.04302447289228439, 0.0), (0.2422943413257599, 0.043350741267204285, 0.0), (0.24247890710830688, 0.043708205223083496, 0.0), (0.2426246702671051, 0.044095732271671295, 0.0), (0.24273017048835754, 0.04451220482587814, 0.0), (0.2429109513759613, 0.04686030000448227, 0.0), (0.24282211065292358, 0.050681695342063904, 0.0), (0.24276533722877502, 0.05112844705581665, 0.0), (0.24266654253005981, 0.05154804885387421, 0.0), (0.24252721667289734, 0.051939330995082855, 0.0), (0.24234884977340698, 0.05230113863945007, 0.0), (0.24213293194770813, 0.05263229459524155, 0.0), (0.24188092350959778, 0.05293164402246475, 0.0), (0.2415943443775177, 0.053198009729385376, 0.0), (0.24127468466758728, 0.0534302294254303, 0.0), (0.2409234344959259, 0.0536271408200264, 0.0), (0.24054208397865295, 0.05378757417201996, 0.0), (0.24013212323188782, 0.05391036719083786, 0.0), (0.2396950125694275, 0.053994350135326385, 0.0)]
    logo_fs = [(192, 172, 193), (315, 228, 227), (453, 452, 473), (375, 374, 410), (489, 486, 484), (495, 502, 499), (475, 481, 480), (543, 561, 560), (458, 472, 459), (573, 572, 533), (63, 62, 29), (150, 149, 158), (149, 148, 159), (150, 158, 157), (148, 147, 159), (147, 146, 160), (146, 145, 161), (145, 144, 162), (147, 160, 159), (144, 143, 163), (160, 146, 161), (152, 151, 156), (151, 150, 157), (154, 153, 155), (153, 152, 155), (151, 157, 156), (158, 149, 159), (156, 155, 152), (161, 145, 162), (162, 144, 163), (164, 163, 143), (165, 164, 143), (166, 165, 110), (165, 143, 110), (167, 166, 110), (169, 168, 196), (168, 167, 86), (196, 168, 86), (171, 170, 194), (170, 169, 194), (171, 194, 193), (173, 172, 192), (172, 171, 193), (173, 192, 191), (175, 174, 189), (174, 173, 190), (189, 174, 190), (177, 176, 187), (176, 175, 188), (187, 176, 188), (179, 178, 185), (178, 177, 186), (185, 178, 186), (181, 180, 184), (180, 179, 184), (183, 182, 181), (184, 183, 181), (184, 179, 185), (173, 191, 190), (126, 125, 123), (125, 124, 123), (123, 122, 126), (122, 121, 127), (121, 120, 128), (128, 120, 129), (120, 119, 129), (119, 118, 131), (118, 117, 132), (117, 116, 133), (118, 132, 131), (116, 115, 134), (115, 114, 135), (116, 134, 133), (114, 113, 136), (113, 112, 136), (114, 136, 135), (112, 111, 141), (111, 110, 143), (119, 131, 130), (129, 119, 130), (127, 126, 122), (128, 127, 121), (99, 98, 97), (97, 96, 99), (96, 95, 100), (95, 94, 101), (94, 93, 101), (101, 93, 102), (93, 92, 102), (92, 91, 103), (91, 90, 103), (90, 89, 104), (103, 90, 104), (89, 88, 105), (88, 87, 105), (89, 105, 104), (87, 86, 106), (92, 103, 102), (96, 100, 99), (101, 100, 95), (105, 87, 106), (107, 106, 86), (108, 107, 86), (108, 86, 109), (109, 86, 167), (110, 109, 167), (134, 115, 135), (187, 186, 177), (132, 117, 133), (137, 136, 112), (138, 137, 112), (139, 138, 112), (140, 139, 112), (141, 140, 112), (142, 141, 111), (143, 142, 111), (188, 175, 189), (169, 196, 195), (169, 195, 194), (323, 322, 222), (322, 321, 223), (321, 320, 223), (320, 319, 224), (223, 320, 224), (319, 318, 225), (318, 317, 226), (317, 316, 227), (316, 315, 227), (317, 227, 226), (315, 314, 228), (314, 313, 229), (229, 312, 230), (313, 312, 229), (312, 311, 230), (230, 311, 231), (311, 310, 231), (310, 309, 231), (309, 308, 232), (308, 307, 236), (309, 232, 231), (224, 319, 225), (322, 223, 222), (325, 324, 221), (324, 323, 221), (327, 326, 219), (326, 325, 220), (329, 328, 217), (328, 327, 218), (329, 216, 330), (331, 330, 214), (331, 214, 213), (333, 332, 211), (332, 331, 212), (211, 332, 212), (335, 334, 209), (334, 333, 210), (210, 333, 211), (337, 336, 206), (336, 335, 207), (339, 338, 204), (338, 337, 205), (206, 336, 207), (341, 340, 203), (340, 339, 204), (204, 338, 205), (343, 342, 201), (342, 341, 202), (203, 340, 204), (345, 344, 200), (344, 343, 200), (197, 346, 198), (346, 345, 199), (199, 345, 200), (199, 198, 346), (205, 337, 206), (335, 209, 208), (209, 334, 210), (216, 329, 217), (325, 221, 220), (323, 222, 221), (214, 330, 215), (201, 200, 343), (335, 208, 207), (272, 271, 269), (271, 270, 269), (269, 268, 272), (268, 267, 272), (267, 266, 273), (273, 266, 265), (265, 264, 274), (274, 264, 263), (263, 262, 275), (275, 262, 261), (261, 260, 276), (276, 260, 277), (260, 259, 277), (259, 258, 278), (280, 258, 257), (257, 256, 282), (281, 257, 282), (256, 255, 283), (255, 254, 285), (254, 253, 287), (253, 252, 289), (252, 251, 290), (251, 250, 291), (292, 249, 293), (250, 249, 292), (249, 248, 293), (295, 246, 296), (248, 247, 294), (247, 246, 295), (296, 245, 244), (246, 245, 296), (297, 244, 243), (243, 242, 299), (301, 240, 302), (242, 241, 300), (241, 240, 301), (302, 239, 303), (240, 239, 302), (239, 238, 303), (303, 238, 304), (238, 237, 304), (237, 236, 307), (244, 297, 296), (282, 256, 283), (285, 254, 286), (258, 280, 279), (257, 281, 280), (277, 259, 278), (273, 272, 267), (263, 275, 274), (278, 258, 279), (247, 295, 294), (304, 237, 305), (236, 235, 308), (274, 273, 265), (305, 237, 306), (235, 234, 308), (306, 237, 307), (276, 275, 261), (202, 201, 342), (203, 202, 341), (283, 255, 284), (284, 255, 285), (286, 254, 287), (287, 253, 288), (212, 331, 213), (288, 253, 289), (215, 330, 216), (290, 289, 252), (291, 290, 251), (217, 328, 218), (292, 291, 250), (294, 293, 248), (219, 218, 327), (220, 219, 326), (298, 297, 243), (299, 298, 243), (300, 299, 242), (301, 300, 241), (234, 233, 308), (233, 232, 308), (225, 318, 226), (314, 229, 228), (452, 451, 450), (450, 449, 474), (449, 468, 460), (474, 449, 469), (468, 467, 462), (467, 466, 464), (466, 465, 464), (464, 463, 462), (462, 461, 468), (461, 460, 468), (460, 459, 470), (459, 471, 470), (464, 462, 467), (452, 450, 474), (455, 454, 456), (454, 453, 457), (456, 454, 457), (460, 470, 469), (474, 473, 452), (473, 458, 453), (460, 469, 449), (458, 457, 453), (349, 348, 347), (347, 448, 349), (448, 447, 349), (349, 447, 350), (447, 446, 350), (446, 445, 350), (350, 445, 444), (444, 443, 351), (443, 442, 351), (442, 441, 352), (351, 442, 352), (441, 440, 352), (440, 439, 352), (352, 439, 353), (439, 438, 353), (438, 437, 353), (353, 437, 354), (437, 436, 354), (436, 435, 356), (357, 435, 434), (434, 433, 358), (433, 432, 359), (432, 431, 361), (433, 359, 358), (431, 430, 363), (430, 429, 364), (429, 428, 365), (428, 427, 366), (363, 430, 364), (427, 426, 366), (426, 425, 367), (425, 424, 367), (424, 423, 368), (423, 422, 368), (422, 421, 368), (368, 421, 369), (421, 420, 369), (420, 419, 371), (419, 418, 371), (418, 417, 371), (417, 416, 372), (416, 415, 372), (417, 372, 371), (415, 414, 372), (414, 413, 373), (372, 414, 373), (413, 412, 373), (412, 411, 373), (411, 410, 374), (410, 409, 375), (409, 408, 376), (408, 407, 378), (381, 405, 404), (407, 406, 379), (406, 405, 380), (382, 404, 383), (404, 403, 383), (383, 403, 384), (403, 402, 384), (402, 401, 385), (384, 402, 385), (401, 400, 386), (400, 399, 387), (399, 398, 388), (398, 397, 389), (386, 400, 387), (397, 396, 390), (396, 395, 391), (395, 394, 391), (394, 393, 392), (388, 398, 389), (392, 391, 394), (391, 390, 396), (387, 399, 388), (385, 401, 386), (405, 381, 380), (404, 382, 381), (373, 411, 374), (420, 371, 370), (424, 368, 367), (364, 429, 365), (361, 431, 362), (435, 357, 356), (434, 358, 357), (444, 351, 350), (359, 432, 360), (360, 432, 361), (390, 389, 397), (420, 370, 369), (355, 354, 436), (356, 355, 436), (406, 380, 379), (362, 431, 363), (407, 379, 378), (408, 378, 377), (408, 377, 376), (365, 428, 366), (409, 376, 375), (366, 426, 367), (484, 483, 490), (489, 488, 487), (484, 490, 489), (486, 485, 484), (489, 487, 486), (494, 493, 491), (493, 492, 491), (497, 496, 498), (496, 495, 498), (495, 494, 502), (494, 491, 502), (502, 501, 499), (501, 500, 499), (499, 498, 495), (478, 477, 480), (477, 476, 475), (475, 482, 481), (477, 475, 480), (480, 479, 478), (543, 542, 561), (458, 473, 472), (472, 471, 459), (505, 504, 511), (504, 503, 511), (506, 505, 511), (508, 507, 506), (510, 509, 508), (512, 511, 503), (511, 510, 506), (510, 508, 506), (513, 512, 503), (513, 503, 514), (503, 552, 556), (514, 503, 556), (552, 551, 556), (515, 514, 556), (551, 550, 556), (516, 515, 555), (549, 548, 560), (548, 547, 560), (549, 560, 559), (515, 556, 555), (550, 549, 556), (517, 516, 555), (547, 546, 560), (546, 545, 560), (545, 544, 560), (544, 543, 560), (518, 517, 555), (519, 518, 555), (549, 559, 558), (520, 519, 555), (523, 522, 521), (521, 520, 554), (549, 558, 557), (549, 557, 556), (524, 523, 554), (523, 521, 554), (520, 555, 554), (525, 524, 526), (527, 526, 553), (553, 526, 524), (529, 528, 578), (528, 527, 580), (531, 530, 574), (530, 529, 576), (578, 528, 579), (533, 532, 573), (532, 531, 574), (574, 530, 575), (535, 534, 571), (534, 533, 572), (571, 536, 535), (537, 536, 570), (537, 569, 568), (539, 538, 567), (538, 537, 568), (541, 567, 566), (541, 540, 567), (540, 539, 567), (566, 542, 541), (561, 542, 562), (562, 542, 563), (563, 542, 564), (542, 566, 565), (569, 537, 570), (536, 571, 570), (528, 580, 579), (580, 527, 553), (554, 553, 524), (529, 578, 577), (564, 542, 565), (529, 577, 576), (567, 538, 568), (530, 576, 575), (571, 534, 572), (532, 574, 573), (13, 12, 1), (12, 11, 1), (1, 11, 2), (11, 10, 2), (10, 9, 3), (9, 8, 3), (8, 7, 3), (7, 6, 5), (5, 4, 7), (4, 3, 7), (3, 2, 10), (0, 85, 14), (85, 84, 75), (14, 85, 75), (84, 83, 82), (82, 81, 78), (81, 80, 78), (80, 79, 78), (78, 77, 76), (76, 75, 84), (75, 74, 14), (78, 76, 82), (84, 82, 76), (1, 0, 13), (16, 15, 73), (15, 14, 74), (73, 15, 74), (14, 13, 0), (52, 51, 41), (51, 50, 43), (42, 51, 43), (50, 49, 46), (49, 48, 46), (48, 47, 46), (46, 45, 44), (44, 43, 50), (42, 41, 51), (41, 40, 39), (52, 41, 38), (39, 38, 41), (38, 37, 52), (37, 36, 53), (36, 35, 54), (35, 34, 55), (54, 35, 55), (34, 33, 56), (33, 32, 58), (34, 56, 55), (32, 31, 59), (31, 30, 61), (30, 29, 62), (29, 28, 64), (65, 26, 66), (28, 27, 64), (27, 26, 65), (66, 25, 24), (26, 25, 66), (67, 24, 23), (23, 22, 67), (67, 22, 68), (22, 21, 68), (21, 20, 68), (68, 20, 69), (20, 19, 69), (19, 18, 69), (70, 18, 17), (17, 16, 72), (72, 16, 73), (18, 70, 69), (24, 67, 66), (58, 32, 59), (37, 53, 52), (53, 36, 54), (46, 44, 50), (56, 33, 57), (17, 72, 71), (17, 71, 70), (57, 33, 58), (59, 31, 60), (27, 65, 64), (60, 31, 61), (62, 61, 30), (29, 64, 63)]
    
    '''
    logo_outline_vs = [(0.26797428727149963, 0.07412988692522049, 0.0), (0.2973800599575043, 0.07410771399736404, 0.0), (0.29779163002967834, 0.07404188066720963, 0.0), (0.29816171526908875, 0.07393338531255722, 0.0), (0.2984895408153534, 0.07378324121236801, 0.0), (0.29877421259880066, 0.07359246164560318, 0.0), (0.29901471734046936, 0.07336204499006271, 0.0), (0.2992102801799774, 0.0730930045247078, 0.0), (0.2993600070476532, 0.0727863535284996, 0.0), (0.2994629442691803, 0.07244310528039932, 0.0), (0.2995181977748871, 0.07206425815820694, 0.0), (0.2995249330997467, 0.07165082544088364, 0.0), (0.29827991127967834, 0.06313661485910416, 0.0), (0.27540531754493713, 0.06462081521749496, 0.0), (0.2729724943637848, 0.04975900799036026, 0.0), (0.28045180439949036, 0.04906067997217178, 0.0), (0.2848070561885834, 0.04818839579820633, 0.0), (0.2889985740184784, 0.04673577845096588, 0.0), (0.2910153567790985, 0.04573246091604233, 0.0), (0.29361626505851746, 0.04400550574064255, 0.0), (0.2947360575199127, 0.04303577542304993, 0.0), (0.29573652148246765, 0.041995830833911896, 0.0), (0.2966184914112091, 0.04088612645864487, 0.0), (0.29738280177116394, 0.03970712423324585, 0.0), (0.298030287027359, 0.038459278643131256, 0.0), (0.2985617220401764, 0.03714305907487869, 0.0), (0.2989780604839325, 0.03575892001390457, 0.0), (0.2994684875011444, 0.03278874605894089, 0.0), (0.2994888722896576, 0.028962619602680206, 0.0), (0.2988859713077545, 0.024733446538448334, 0.0), (0.2976396381855011, 0.02083711326122284, 0.0), (0.2967798411846161, 0.019012175500392914, 0.0), (0.29459652304649353, 0.015605553984642029, 0.0), (0.2918073236942291, 0.01251903921365738, 0.0), (0.28842732310295105, 0.009747534990310669, 0.0), (0.2845591604709625, 0.007240980863571167, 0.0), (0.2805432975292206, 0.005124989897012711, 0.0), (0.27424946427345276, 0.002674572169780731, 0.0), (0.26987817883491516, 0.0015175119042396545, 0.0), (0.25896838307380676, 0.00018766522407531738, 0.0), (0.2587573826313019, 0.0007014200091362, 0.0), (0.2587113678455353, 0.0008643902838230133, 0.0), (0.2580145299434662, 0.0069268569350242615, 0.0), (0.2580288350582123, 0.007305465638637543, 0.0), (0.258082777261734, 0.007650136947631836, 0.0), (0.25817611813545227, 0.007961302995681763, 0.0), (0.2583087980747223, 0.008239388465881348, 0.0), (0.2584807574748993, 0.00848483294248581, 0.0), (0.2586918771266937, 0.008698061108589172, 0.0), (0.2589420974254608, 0.008879505097866058, 0.0), (0.25923123955726624, 0.009029597043991089, 0.0), (0.2595592439174652, 0.009148769080638885, 0.0), (0.266605943441391, 0.010272681713104248, 0.0), (0.27265962958335876, 0.01200173795223236, 0.0), (0.2784392535686493, 0.014637507498264313, 0.0), (0.2815301716327667, 0.01660306751728058, 0.0), (0.2829379737377167, 0.017758287489414215, 0.0), (0.2847701609134674, 0.0197293683886528, 0.0), (0.2855106294155121, 0.02077440917491913, 0.0), (0.2861367166042328, 0.0218573659658432, 0.0), (0.28665027022361755, 0.02297692745923996, 0.0), (0.28705325722694397, 0.02413177490234375, 0.0), (0.2873476445674896, 0.02532060444355011, 0.0), (0.2875353991985321, 0.026542097330093384, 0.0), (0.28759875893592834, 0.02907782793045044, 0.0), (0.28725889325141907, 0.03172844648361206, 0.0), (0.2869194447994232, 0.03294328600168228, 0.0), (0.2864117920398712, 0.03403835743665695, 0.0), (0.28609737753868103, 0.034541621804237366, 0.0), (0.2853526771068573, 0.03546087443828583, 0.0), (0.2844600975513458, 0.036265455186367035, 0.0), (0.28342780470848083, 0.03695739805698395, 0.0), (0.2821613848209381, 0.03759104013442993, 0.0), (0.2807345688343048, 0.03814936429262161, 0.0), (0.27779659628868103, 0.0389266312122345, 0.0), (0.2635621726512909, 0.04007439315319061, 0.0), (0.2632463276386261, 0.040159374475479126, 0.0), (0.2629564702510834, 0.0402844101190567, 0.0), (0.2626948058605194, 0.04044630378484726, 0.0), (0.2624634802341461, 0.04064185917377472, 0.0), (0.26226475834846497, 0.0408678874373436, 0.0), (0.26210084557533264, 0.041121192276477814, 0.0), (0.26197394728660583, 0.04139857739210129, 0.0), (0.26188626885414124, 0.04169684648513794, 0.0), (0.2618400752544403, 0.042012810707092285, 0.0), (0.26183757185935974, 0.04234328120946884, 0.0), (0.008942576125264168, 0.0476173534989357, 0.0), (0.009772496297955513, 0.049940966069698334, 0.0), (0.010864967480301857, 0.052056483924388885, 0.0), (0.012206895276904106, 0.05397354066371918, 0.0), (0.013785192742943764, 0.05570177733898163, 0.0), (0.015586761757731438, 0.057250842452049255, 0.0), (0.017598511651158333, 0.058630384504795074, 0.0), (0.019682539626955986, 0.059779368340969086, 0.0), (0.021832028403878212, 0.06070787459611893, 0.0), (0.024048471823334694, 0.061422087252140045, 0.0), (0.02633335255086422, 0.061928197741508484, 0.0), (0.031114406883716583, 0.06234089285135269, 0.0), (0.031114406883716583, 0.05356263369321823, 0.0), (0.028996797278523445, 0.05329094082117081, 0.0), (0.026999840512871742, 0.052782073616981506, 0.0), (0.0251294132322073, 0.05202551931142807, 0.0), (0.023391397669911385, 0.05101078748703003, 0.0), (0.021791676059365273, 0.049727365374565125, 0.0), (0.020336119458079338, 0.04816475510597229, 0.0), (0.019438689574599266, 0.046922869980335236, 0.0), (0.01870526187121868, 0.04561499506235123, 0.0), (0.0181319210678339, 0.044236257672309875, 0.0), (0.017714744433760643, 0.04278181493282318, 0.0), (0.017449816688895226, 0.041246794164180756, 0.0), (0.017333215102553368, 0.039626337587833405, 0.0), (0.03454912453889847, 0.039626337587833405, 0.0), (0.034549959003925323, 0.026489049196243286, 0.0), (0.03405412286520004, 0.022603124380111694, 0.0), (0.033580876886844635, 0.020770907402038574, 0.0), (0.032199926674366, 0.01732093095779419, 0.0), (0.030261345207691193, 0.014147475361824036, 0.0), (0.027791080996394157, 0.01123926043510437, 0.0), (0.02481507696211338, 0.008584991097450256, 0.0), (0.021603872999548912, 0.0063573941588401794, 0.0), (0.018234150484204292, 0.004576325416564941, 0.0), (0.014712022617459297, 0.003217097371816635, 0.0), (0.0110436100512743, 0.002255026251077652, 0.0), (0.007235022261738777, 0.0016654133796691895, 0.0), (0.003292372450232506, 0.001423567533493042, 0.0), (0.003292372450232506, 0.01022157073020935, 0.0), (0.0077092405408620834, 0.010678686201572418, 0.0), (0.0116646159440279, 0.01157524436712265, 0.0), (0.013550655916333199, 0.012248598039150238, 0.0), (0.015368493273854256, 0.01308443397283554, 0.0), (0.017112793400883675, 0.01409207284450531, 0.0), (0.018778221681714058, 0.015280850231647491, 0.0), (0.02084810473024845, 0.017172686755657196, 0.0), (0.02252788282930851, 0.019258588552474976, 0.0), (0.023226724937558174, 0.02037147432565689, 0.0), (0.02435280941426754, 0.02273143082857132, 0.0), (0.025130731984972954, 0.025262728333473206, 0.0), (0.025577275082468987, 0.027956277132034302, 0.0), (0.025729497894644737, 0.03105124831199646, 0.0), (0.025727855041623116, 0.031067483127117157, 0.0), (0.02572317235171795, 0.03108379989862442, 0.0), (0.025715826079249382, 0.03110027313232422, 0.0), (0.025706185027956963, 0.031116977334022522, 0.0), (0.025591203942894936, 0.031268514692783356, 0.0), (0.02453540451824665, 0.028828494250774384, 0.0), (0.023310082033276558, 0.02664732187986374, 0.0), (0.02192210592329502, 0.02471321076154709, 0.0), (0.020378345623612404, 0.023014351725578308, 0.0), (0.01868567056953907, 0.021538957953453064, 0.0), (0.016850950196385384, 0.02027522772550583, 0.0), (0.014881057664752007, 0.019211366772651672, 0.0), (0.012782858684659004, 0.018335580825805664, 0.0), (0.008229019120335579, 0.01710103452205658, 0.0), (0.003244394436478615, 0.01647724211215973, 0.0), (0.003244394436478615, 0.025365546345710754, 0.0), (0.005477456375956535, 0.02565702050924301, 0.0), (0.007574187591671944, 0.026211224496364594, 0.0), (0.009527137503027916, 0.0270388200879097, 0.0), (0.011328862980008125, 0.028150461614131927, 0.0), (0.012170689180493355, 0.028816133737564087, 0.0), (0.013731608167290688, 0.03037383407354355, 0.0), (0.014873279258608818, 0.0318736732006073, 0.0), (0.015611803159117699, 0.03314638137817383, 0.0), (0.016197452321648598, 0.034482233226299286, 0.0), (0.016623327508568764, 0.03585715591907501, 0.0), (0.016882533207535744, 0.03724709153175354, 0.0), (0.016968170180916786, 0.038627974689006805, 0.0), (0.016943739727139473, 0.03930748999118805, 0.0), (0.00010037235915660858, 0.03930748999118805, 0.0), (0.00011428818106651306, 0.054478131234645844, 0.0), (0.000366920605301857, 0.05636154115200043, 0.0), (0.0008161719888448715, 0.05818208307027817, 0.0), (0.0014481674879789352, 0.05994454771280289, 0.0), (0.0032048802822828293, 0.06331437081098557, 0.0), (0.005478711798787117, 0.06644149124622345, 0.0), (0.008068716153502464, 0.06913446635007858, 0.0), (0.010952392593026161, 0.07142143696546555, 0.0), (0.014107244089245796, 0.07333052903413773, 0.0), (0.01751076988875866, 0.0748898908495903, 0.0), (0.02114047296345234, 0.07612764090299606, 0.0), (0.02438567765057087, 0.0768946185708046, 0.0), (0.027705514803528786, 0.07734053581953049, 0.0), (0.031120046973228455, 0.0774848684668541, 0.0), (0.031120046973228455, 0.06877433508634567, 0.0), (0.025246886536478996, 0.06797579675912857, 0.0), (0.022675683721899986, 0.06731545925140381, 0.0), (0.020241206511855125, 0.0664205327630043, 0.0), (0.017958348616957664, 0.06526945531368256, 0.0), (0.015842003747820854, 0.06384067237377167, 0.0), (0.013907073065638542, 0.06211263686418533, 0.0), (0.012168442830443382, 0.06006380170583725, 0.0), (0.011258138343691826, 0.05869395285844803, 0.0), (0.01050047017633915, 0.0572671964764595, 0.0), (0.009887682273983955, 0.05578683316707611, 0.0), (0.009412011131644249, 0.054256148636341095, 0.0), (0.008840972557663918, 0.05105698108673096, 0.0), (0.008674459531903267, 0.04770199954509735, 0.0), (0.04587210714817047, 0.03011161834001541, 0.0), (0.05310560762882233, 0.03011161834001541, 0.0), (0.053111255168914795, 0.028243668377399445, 0.0), (0.053162992000579834, 0.02770879864692688, 0.0), (0.053265027701854706, 0.027203291654586792, 0.0), (0.053415924310684204, 0.02672935277223587, 0.0), (0.05361424386501312, 0.026289187371730804, 0.0), (0.05385854095220566, 0.025884993374347687, 0.0), (0.054147377610206604, 0.025518983602523804, 0.0), (0.054479315876960754, 0.025193355977535248, 0.0), (0.054852910339832306, 0.024910323321819305, 0.0), (0.05526672303676605, 0.02467208355665207, 0.0), (0.05571930855512619, 0.02448084205389023, 0.0), (0.05620923638343811, 0.024338804185390472, 0.0), (0.05673506110906601, 0.024248160421848297, 0.0), (0.05834940820932388, 0.024153999984264374, 0.0), (0.05996375530958176, 0.024248160421848297, 0.0), (0.06045781075954437, 0.02432876080274582, 0.0), (0.06091632694005966, 0.02445017546415329, 0.0), (0.06133846938610077, 0.024611718952655792, 0.0), (0.06172339618206024, 0.02481270581483841, 0.0), (0.06207025796175003, 0.02505245804786682, 0.0), (0.06237821280956268, 0.025330282747745514, 0.0), (0.06264642626047134, 0.02564549446105957, 0.0), (0.06287404894828796, 0.025997407734394073, 0.0), (0.06306023895740509, 0.026385337114334106, 0.0), (0.06320415437221527, 0.026808589696884155, 0.0), (0.06330495327711105, 0.0272664874792099, 0.0), (0.06336177885532379, 0.027758337557315826, 0.0), (0.06334343552589417, 0.033068761229515076, 0.0), (0.06328324973583221, 0.03343285620212555, 0.0), (0.06319040805101395, 0.03377455472946167, 0.0), (0.06306564062833786, 0.0340939462184906, 0.0), (0.06290967017412186, 0.034391120076179504, 0.0), (0.06272322684526443, 0.03466615825891495, 0.0), (0.0625070333480835, 0.03491915762424469, 0.0), (0.06226181238889694, 0.0351502001285553, 0.0), (0.061988286674022675, 0.035359375178813934, 0.0), (0.06168718636035919, 0.035546764731407166, 0.0), (0.06135924160480499, 0.03571246564388275, 0.0), (0.0509917214512825, 0.03962069749832153, 0.0), (0.049942031502723694, 0.04022562503814697, 0.0), (0.04902710020542145, 0.04094616323709488, 0.0), (0.04824528843164444, 0.041778936982154846, 0.0), (0.04759494960308075, 0.042720578610897064, 0.0), (0.04707443714141846, 0.043767720460891724, 0.0), (0.04668210446834564, 0.044916994869709015, 0.0), (0.04622594267129898, 0.04723192751407623, 0.0), (0.04614858329296112, 0.04955752193927765, 0.0), (0.04626450687646866, 0.050722941756248474, 0.0), (0.04649018496274948, 0.05188938230276108, 0.0), (0.04699484258890152, 0.05350193381309509, 0.0), (0.04769477993249893, 0.05495905876159668, 0.0), (0.04859243333339691, 0.05625205487012863, 0.0), (0.04969023913145065, 0.05737222731113434, 0.0), (0.050990618765354156, 0.058310866355895996, 0.0), (0.05249600112438202, 0.0590592697262764, 0.0), (0.054849088191986084, 0.059836991131305695, 0.0), (0.05718861520290375, 0.060255564749240875, 0.0), (0.05950901657342911, 0.060304343700408936, 0.0), (0.061804719269275665, 0.05997266620397568, 0.0), (0.06407015770673752, 0.0592498704791069, 0.0), (0.06629976630210876, 0.058125294744968414, 0.0), (0.0671716034412384, 0.05754784494638443, 0.0), (0.06795115768909454, 0.05691944807767868, 0.0), (0.06863833963871002, 0.056241124868392944, 0.0), (0.06923305988311768, 0.0555138885974884, 0.0), (0.06973523646593094, 0.054738759994506836, 0.0), (0.07014477252960205, 0.05391675978899002, 0.0), (0.07046158611774445, 0.053048908710479736, 0.0), (0.07068558782339096, 0.05213622748851776, 0.0), (0.07081668823957443, 0.05117972940206528, 0.0), (0.0708548054099083, 0.05018043518066406, 0.0), (0.07065172493457794, 0.04805753380060196, 0.0), (0.06363554298877716, 0.04805753380060196, 0.0), (0.06337589025497437, 0.050461605191230774, 0.0), (0.06322763115167618, 0.05109626054763794, 0.0), (0.06302707642316818, 0.051674067974090576, 0.0), (0.06277438998222351, 0.05219508707523346, 0.0), (0.0624697282910347, 0.05265938490629196, 0.0), (0.06211324781179428, 0.05306701362133026, 0.0), (0.061705105006694794, 0.05341802537441254, 0.0), (0.061245448887348175, 0.05371248722076416, 0.0), (0.06073444336652756, 0.05395045876502991, 0.0), (0.060172244906425476, 0.05413199961185455, 0.0), (0.05955900996923447, 0.05425716191530228, 0.0), (0.05889490246772766, 0.05432600528001785, 0.0), (0.05755072832107544, 0.05429720878601074, 0.0), (0.056960560381412506, 0.054200299084186554, 0.0), (0.05641111731529236, 0.05404853820800781, 0.0), (0.05590395629405975, 0.053842611610889435, 0.0), (0.055440619587898254, 0.053583189845085144, 0.0), (0.055022649466991425, 0.05327095091342926, 0.0), (0.05465160310268402, 0.05290656536817551, 0.0), (0.05432902276515961, 0.0524907112121582, 0.0), (0.05405645817518234, 0.05202407389879227, 0.0), (0.05383545905351639, 0.051507316529750824, 0.0), (0.0536675751209259, 0.05094112455844879, 0.0), (0.05355435609817505, 0.050326161086559296, 0.0), (0.053468845784664154, 0.04920867085456848, 0.0), (0.05356563627719879, 0.04695425182580948, 0.0), (0.05361081659793854, 0.04663032293319702, 0.0), (0.053683631122112274, 0.04632318764925003, 0.0), (0.05378313362598419, 0.04603306204080582, 0.0), (0.053908392786979675, 0.04576016217470169, 0.0), (0.054058462381362915, 0.045504696667194366, 0.0), (0.0542324036359787, 0.04526688903570175, 0.0), (0.054429277777671814, 0.04504694789648056, 0.0), (0.05464813858270645, 0.0448450967669487, 0.0), (0.054888054728507996, 0.044661544263362885, 0.0), (0.05542726814746857, 0.044350214302539825, 0.0), (0.06596294045448303, 0.040533408522605896, 0.0), (0.06740332394838333, 0.0396670326590538, 0.0), (0.06802930682897568, 0.03916285187005997, 0.0), (0.06859076768159866, 0.03861101716756821, 0.0), (0.06908642500638962, 0.03801128268241882, 0.0), (0.06951498985290527, 0.03736340254545212, 0.0), (0.06987518817186356, 0.03666713088750839, 0.0), (0.0701657310128212, 0.03592222183942795, 0.0), (0.07038532942533493, 0.03512843698263168, 0.0), (0.07053270936012268, 0.0342855229973793, 0.0), (0.07067781686782837, 0.0296095609664917, 0.0), (0.07044287770986557, 0.02694004774093628, 0.0), (0.07020621001720428, 0.025789305567741394, 0.0), (0.06988707929849625, 0.024724796414375305, 0.0), (0.06948545575141907, 0.02374529093503952, 0.0), (0.06900130957365036, 0.02284955233335495, 0.0), (0.06843461096286774, 0.022036351263523102, 0.0), (0.0677853375673294, 0.021304450929164886, 0.0), (0.06705345213413239, 0.020652614533901215, 0.0), (0.06623892486095428, 0.020079605281352997, 0.0), (0.06534173339605331, 0.01958419382572174, 0.0), (0.06436184048652649, 0.019165143370628357, 0.0), (0.06329921633005142, 0.018821217119693756, 0.0), (0.06056099385023117, 0.018296003341674805, 0.0), (0.05739159882068634, 0.018170960247516632, 0.0), (0.05581897497177124, 0.018325872719287872, 0.0), (0.05425701290369034, 0.018642239272594452, 0.0), (0.052707672119140625, 0.019132450222969055, 0.0), (0.05152745544910431, 0.019637413322925568, 0.0), (0.05045662075281143, 0.02021808922290802, 0.0), (0.04949565976858139, 0.020874127745628357, 0.0), (0.048645056784152985, 0.021605178713798523, 0.0), (0.04790531098842621, 0.022410884499549866, 0.0), (0.04727690666913986, 0.02329089492559433, 0.0), (0.04676033556461334, 0.02424485981464386, 0.0), (0.046356089413166046, 0.025272421538829803, 0.0), (0.046064652502536774, 0.026373229920864105, 0.0), (0.04588651657104492, 0.02754693478345871, 0.0), (0.04582217335700989, 0.028793178498744965, 0.0), (0.10281725227832794, 0.04810831695795059, 0.0), (0.09569099545478821, 0.04810831695795059, 0.0), (0.09568816423416138, 0.0498267263174057, 0.0), (0.09556393325328827, 0.05089160054922104, 0.0), (0.09528155624866486, 0.05180057883262634, 0.0), (0.09486221522092819, 0.05255988985300064, 0.0), (0.09432710707187653, 0.05317576229572296, 0.0), (0.09369740635156631, 0.05365443229675293, 0.0), (0.0929943099617958, 0.054002128541469574, 0.0), (0.09223899990320206, 0.05422507971525192, 0.0), (0.09145266562700272, 0.0543295219540596, 0.0), (0.09065648913383484, 0.05432168394327164, 0.0), (0.08987165987491608, 0.05420779436826706, 0.0), (0.08911936730146408, 0.05399408936500549, 0.0), (0.0884207934141159, 0.05368679016828537, 0.0), (0.08827516436576843, 0.05359940230846405, 0.0), (0.08799715340137482, 0.05337587743997574, 0.0), (0.08774182945489883, 0.05310014635324478, 0.0), (0.08751524239778519, 0.05278757959604263, 0.0), (0.08732341974973679, 0.05245353281497955, 0.0), (0.08717240393161774, 0.052113376557826996, 0.0), (0.08692353218793869, 0.05120617896318436, 0.0), (0.08676943182945251, 0.05018598586320877, 0.0), (0.08670707046985626, 0.027880273759365082, 0.0), (0.08683592081069946, 0.027020834386348724, 0.0), (0.08706729859113693, 0.02628374844789505, 0.0), (0.08739401400089264, 0.025663815438747406, 0.0), (0.08780888468027115, 0.025155849754810333, 0.0), (0.08830472826957703, 0.024754658341407776, 0.0), (0.08887436985969543, 0.024455048143863678, 0.0), (0.08951061964035034, 0.024251826107501984, 0.0), (0.09020628780126572, 0.024139799177646637, 0.0), (0.09095419943332672, 0.024113774299621582, 0.0), (0.09174717217683792, 0.024168558418750763, 0.0), (0.09301893413066864, 0.024406276643276215, 0.0), (0.09342464059591293, 0.024547353386878967, 0.0), (0.09379544109106064, 0.024721719324588776, 0.0), (0.09413164108991623, 0.024928919970989227, 0.0), (0.09443353861570358, 0.025168493390083313, 0.0), (0.09470143914222717, 0.025439977645874023, 0.0), (0.09493564814329147, 0.02574291080236435, 0.0), (0.09513647109270096, 0.02607683092355728, 0.0), (0.0953042134642601, 0.026441283524036407, 0.0), (0.09543917328119278, 0.02683579921722412, 0.0), (0.09561196714639664, 0.027713187038898468, 0.0), (0.09575872123241425, 0.030207559466362, 0.0), (0.1028708666563034, 0.030207559466362, 0.0), (0.10297247767448425, 0.02764567732810974, 0.0), (0.10282960534095764, 0.026405341923236847, 0.0), (0.10252280533313751, 0.025197923183441162, 0.0), (0.10202597826719284, 0.024027809500694275, 0.0), (0.10131298005580902, 0.02289939671754837, 0.0), (0.10054734349250793, 0.021977022290229797, 0.0), (0.0997101292014122, 0.021154344081878662, 0.0), (0.09880220144987106, 0.020431838929653168, 0.0), (0.09782442450523376, 0.019809968769550323, 0.0), (0.09677765518426895, 0.019289210438728333, 0.0), (0.09566276520490646, 0.0188700333237648, 0.0), (0.09381967037916183, 0.018396049737930298, 0.0), (0.09198229759931564, 0.01815478503704071, 0.0), (0.09015543758869171, 0.018143802881240845, 0.0), (0.08834386616945267, 0.018360666930675507, 0.0), (0.08655235916376114, 0.018802955746650696, 0.0), (0.08478569984436035, 0.01946822553873062, 0.0), (0.08320090919733047, 0.020326413214206696, 0.0), (0.08250494301319122, 0.020829513669013977, 0.0), (0.08187530189752579, 0.021381646394729614, 0.0), (0.08131351321935654, 0.02198256552219391, 0.0), (0.08082110434770584, 0.022632040083408356, 0.0), (0.08039960265159607, 0.02332983911037445, 0.0), (0.08005054295063019, 0.024075724184513092, 0.0), (0.07977545261383057, 0.024869456887245178, 0.0), (0.07957585155963898, 0.025710806250572205, 0.0), (0.07945327460765839, 0.026599541306495667, 0.0), (0.07945524156093597, 0.051800668239593506, 0.0), (0.07957057654857635, 0.05260960012674332, 0.0), (0.07975596189498901, 0.0533793568611145, 0.0), (0.08000925928354263, 0.05410993844270706, 0.0), (0.0803283303976059, 0.0548013299703598, 0.0), (0.08071103692054749, 0.05545351654291153, 0.0), (0.08115524798631668, 0.056066498160362244, 0.0), (0.08165882527828217, 0.05664025992155075, 0.0), (0.08221963047981262, 0.057174794375896454, 0.0), (0.08350438624620438, 0.05812612920999527, 0.0), (0.0852634608745575, 0.05905284732580185, 0.0), (0.08736544847488403, 0.0598156601190567, 0.0), (0.08949236571788788, 0.06023940443992615, 0.0), (0.09056291729211807, 0.0603254958987236, 0.0), (0.09271370619535446, 0.06024886667728424, 0.0), (0.094871386885643, 0.059844136238098145, 0.0), (0.09702874720096588, 0.05911571532487869, 0.0), (0.09807576984167099, 0.05861552804708481, 0.0), (0.09902918338775635, 0.05801798403263092, 0.0), (0.09988626092672348, 0.057329535484313965, 0.0), (0.1006442978978157, 0.05655664950609207, 0.0), (0.10130057483911514, 0.05570577085018158, 0.0), (0.10185237973928452, 0.05478335916996002, 0.0), (0.10229699313640594, 0.05379587411880493, 0.0), (0.10263170301914215, 0.05274977535009384, 0.0), (0.10285380482673645, 0.05165150761604309, 0.0), (0.10296057164669037, 0.05050753802061081, 0.0), (0.10294929146766663, 0.04932431876659393, 0.0), (0.126620352268219, 0.059911422431468964, 0.0), (0.1379518210887909, 0.01862737536430359, 0.0), (0.13068446516990662, 0.01862737536430359, 0.0), (0.12854516506195068, 0.027329444885253906, 0.0), (0.11861355602741241, 0.027329444885253906, 0.0), (0.11646297574043274, 0.018596328794956207, 0.0), (0.10937340557575226, 0.018596328794956207, 0.0), (0.10939881205558777, 0.01926334947347641, 0.0), (0.10942141711711884, 0.0194048210978508, 0.0), (0.11304393410682678, 0.03260401636362076, 0.0), (0.1148475706577301, 0.03916853666305542, 0.0), (0.12029682099819183, 0.059052951633930206, 0.0), (0.1204226166009903, 0.05936644226312637, 0.0), (0.1204967200756073, 0.05949538201093674, 0.0), (0.12058039009571075, 0.05960645526647568, 0.0), (0.12067519128322601, 0.05970015376806259, 0.0), (0.12078270316123962, 0.05977698415517807, 0.0), (0.12090447545051575, 0.05983743816614151, 0.0), (0.12104208767414093, 0.0598820224404335, 0.0), (0.12119710445404053, 0.05991123616695404, 0.0), (0.12367390841245651, 0.047744326293468475, 0.0), (0.12340860813856125, 0.047721751034259796, 0.0), (0.12109412252902985, 0.03798171877861023, 0.0), (0.11992591619491577, 0.03306592255830765, 0.0), (0.12054227292537689, 0.03306592255830765, 0.0), (0.12717071175575256, 0.03306592255830765, 0.0), (0.1460433006286621, 0.054355524480342865, 0.0), (0.13762161135673523, 0.054355524480342865, 0.0), (0.13762161135673523, 0.05982395261526108, 0.0), (0.1616702675819397, 0.05982395261526108, 0.0), (0.1616702675819397, 0.054420433938503265, 0.0), (0.1533445417881012, 0.054420433938503265, 0.0), (0.1533445417881012, 0.018607616424560547, 0.0), (0.1460433006286621, 0.018607616424560547, 0.0), (0.1733178198337555, 0.018604792654514313, 0.0), (0.1733178198337555, 0.054299093782901764, 0.0), (0.16496950387954712, 0.054299093782901764, 0.0), (0.16496950387954712, 0.05980702489614487, 0.0), (0.18887421488761902, 0.05980702489614487, 0.0), (0.18887421488761902, 0.05440632253885269, 0.0), (0.1806049346923828, 0.05440632253885269, 0.0), (0.1806049346923828, 0.018604792654514313, 0.0), (0.20314085483551025, 0.024451322853565216, 0.0), (0.21740180253982544, 0.024451322853565216, 0.0), (0.21740180253982544, 0.0186443030834198, 0.0), (0.19586217403411865, 0.0186443030834198, 0.0), (0.19586217403411865, 0.05981830507516861, 0.0), (0.21738487482070923, 0.05981830507516861, 0.0), (0.21738487482070923, 0.054417602717876434, 0.0), (0.20317187905311584, 0.054417602717876434, 0.0), (0.20317187905311584, 0.04220535606145859, 0.0), (0.21560120582580566, 0.04220535606145859, 0.0), (0.21560120582580566, 0.03661278635263443, 0.0), (0.2031436562538147, 0.03661278635263443, 0.0), (0.24417397379875183, 0.03725895285606384, 0.0), (0.2519550025463104, 0.018531426787376404, 0.0), (0.24530372023582458, 0.01856788992881775, 0.0), (0.24496588110923767, 0.01861785352230072, 0.0), (0.2446860671043396, 0.01870022714138031, 0.0), (0.2444523274898529, 0.01882311701774597, 0.0), (0.2442527413368225, 0.01899462193250656, 0.0), (0.24407538771629333, 0.019222840666770935, 0.0), (0.2439083456993103, 0.019515879452228546, 0.0), (0.23783642053604126, 0.03525368124246597, 0.0), (0.23765772581100464, 0.03559309244155884, 0.0), (0.23755678534507751, 0.03573419153690338, 0.0), (0.23744621872901917, 0.03585632145404816, 0.0), (0.23732465505599976, 0.03595956414937973, 0.0), (0.23719069361686707, 0.03604399412870407, 0.0), (0.23704293370246887, 0.036109693348407745, 0.0), (0.23687994480133057, 0.03615673631429672, 0.0), (0.23670035600662231, 0.03618519753217697, 0.0), (0.23315861821174622, 0.03616977483034134, 0.0), (0.23315861821174622, 0.018616080284118652, 0.0), (0.2259109914302826, 0.018616080284118652, 0.0), (0.2259109914302826, 0.0597449466586113, 0.0), (0.2262304723262787, 0.059871941804885864, 0.0), (0.2262941300868988, 0.05988435447216034, 0.0), (0.2397136688232422, 0.05978837609291077, 0.0), (0.2416626513004303, 0.05950886011123657, 0.0), (0.24368509650230408, 0.05895324796438217, 0.0), (0.245362788438797, 0.0582011342048645, 0.0), (0.24611204862594604, 0.05773580074310303, 0.0), (0.2468012571334839, 0.05721105635166168, 0.0), (0.24743017554283142, 0.05662698298692703, 0.0), (0.24799853563308716, 0.05598365515470505, 0.0), (0.2485060691833496, 0.0552811473608017, 0.0), (0.24895253777503967, 0.054519541561603546, 0.0), (0.24966123700141907, 0.05281934142112732, 0.0), (0.2502005398273468, 0.05048428475856781, 0.0), (0.25041088461875916, 0.047693535685539246, 0.0), (0.2503356635570526, 0.04630066454410553, 0.0), (0.2501348555088043, 0.04491030424833298, 0.0), (0.24961426854133606, 0.042929500341415405, 0.0), (0.249391108751297, 0.042361997067928314, 0.0), (0.24884700775146484, 0.041304610669612885, 0.0), (0.2485266625881195, 0.040814436972141266, 0.0), (0.2477908432483673, 0.039910390973091125, 0.0), (0.24693015217781067, 0.03910710662603378, 0.0), (0.24594691395759583, 0.03840339928865433, 0.0), (0.24442234635353088, 0.03754958510398865, 0.0), (0.24440452456474304, 0.03753729164600372, 0.0), (0.24438747763633728, 0.03752295672893524, 0.0), (0.24435415863990784, 0.03748802840709686, 0.0), (0.2332150638103485, 0.054474033415317535, 0.0), (0.2332150638103485, 0.0413193479180336, 0.0), (0.23960188031196594, 0.04170874506235123, 0.0), (0.24004265666007996, 0.041785091161727905, 0.0), (0.24045667052268982, 0.041900523006916046, 0.0), (0.24084240198135376, 0.04205390810966492, 0.0), (0.2411983609199524, 0.04224412143230438, 0.0), (0.24152302742004395, 0.04247003793716431, 0.0), (0.24181491136550903, 0.042730532586574554, 0.0), (0.24207252264022827, 0.04302447289228439, 0.0), (0.2422943413257599, 0.043350741267204285, 0.0), (0.24247890710830688, 0.043708205223083496, 0.0), (0.2426246702671051, 0.044095732271671295, 0.0), (0.24273017048835754, 0.04451220482587814, 0.0), (0.2429109513759613, 0.04686030000448227, 0.0), (0.24282211065292358, 0.050681695342063904, 0.0), (0.24276533722877502, 0.05112844705581665, 0.0), (0.24266654253005981, 0.05154804885387421, 0.0), (0.24252721667289734, 0.051939330995082855, 0.0), (0.24234884977340698, 0.05230113863945007, 0.0), (0.24213293194770813, 0.05263229459524155, 0.0), (0.24188092350959778, 0.05293164402246475, 0.0), (0.2415943443775177, 0.053198009729385376, 0.0), (0.24127468466758728, 0.0534302294254303, 0.0), (0.2409234344959259, 0.0536271408200264, 0.0), (0.24054208397865295, 0.05378757417201996, 0.0), (0.24013212323188782, 0.05391036719083786, 0.0), (0.2396950125694275, 0.053994350135326385, 0.0)]
    logo_outline_es = [[181, 182], [180, 181], [179, 180], [178, 179], [177, 178], [176, 177], [175, 176], [182, 183], [183, 184], [174, 175], [184, 185], [185, 186], [186, 187], [173, 174], [187, 188], [188, 189], [96, 97], [95, 96], [189, 190], [94, 95], [172, 173], [93, 94], [190, 191], [92, 93], [171, 172], [191, 192], [91, 92], [170, 171], [192, 193], [90, 91], [169, 170], [193, 194], [89, 90], [97, 98], [98, 99], [99, 100], [88, 89], [100, 101], [194, 195], [101, 102], [87, 88], [102, 103], [103, 104], [86, 87], [195, 196], [86, 196], [104, 105], [105, 106], [106, 107], [107, 108], [108, 109], [109, 110], [110, 111], [168, 169], [167, 168], [166, 167], [165, 166], [164, 165], [163, 164], [162, 163], [161, 162], [160, 161], [143, 144], [142, 143], [141, 142], [140, 141], [139, 140], [138, 139], [159, 160], [137, 138], [144, 145], [158, 159], [111, 112], [157, 158], [145, 146], [156, 157], [136, 137], [155, 156], [154, 155], [146, 147], [112, 113], [135, 136], [147, 148], [113, 114], [148, 149], [134, 135], [133, 134], [149, 150], [150, 151], [114, 115], [132, 133], [151, 152], [153, 154], [152, 153], [131, 132], [115, 116], [130, 131], [129, 130], [116, 117], [128, 129], [127, 128], [126, 127], [125, 126], [117, 118], [118, 119], [119, 120], [120, 121], [121, 122], [124, 125], [122, 123], [123, 124], [255, 256], [256, 257], [254, 255], [257, 258], [253, 254], [258, 259], [252, 253], [259, 260], [251, 252], [260, 261], [261, 262], [250, 251], [262, 263], [249, 250], [263, 264], [264, 265], [283, 284], [282, 283], [284, 285], [281, 282], [248, 249], [285, 286], [280, 281], [286, 287], [279, 280], [265, 266], [287, 288], [278, 279], [288, 289], [277, 278], [289, 290], [276, 277], [266, 267], [290, 291], [247, 248], [275, 276], [291, 292], [274, 275], [267, 268], [292, 293], [273, 274], [293, 294], [246, 247], [268, 269], [272, 273], [294, 295], [245, 246], [295, 296], [269, 270], [271, 272], [270, 271], [244, 245], [296, 297], [297, 298], [298, 299], [299, 300], [300, 301], [301, 302], [302, 303], [243, 244], [303, 304], [304, 305], [305, 306], [306, 307], [242, 243], [241, 242], [240, 241], [239, 240], [307, 308], [238, 239], [308, 309], [237, 238], [309, 310], [310, 311], [311, 312], [312, 313], [313, 314], [314, 315], [315, 316], [236, 237], [235, 236], [234, 235], [233, 234], [232, 233], [316, 317], [231, 232], [230, 231], [229, 230], [228, 229], [227, 228], [226, 227], [317, 318], [197, 346], [197, 198], [345, 346], [198, 199], [199, 200], [225, 226], [224, 225], [200, 201], [344, 345], [318, 319], [223, 224], [201, 202], [319, 320], [222, 223], [202, 203], [221, 222], [343, 344], [203, 204], [220, 221], [204, 205], [320, 321], [219, 220], [205, 206], [218, 219], [342, 343], [206, 207], [217, 218], [207, 208], [216, 217], [321, 322], [208, 209], [215, 216], [209, 210], [214, 215], [210, 211], [213, 214], [341, 342], [212, 213], [211, 212], [322, 323], [340, 341], [323, 324], [339, 340], [324, 325], [338, 339], [325, 326], [337, 338], [326, 327], [336, 337], [327, 328], [335, 336], [328, 329], [329, 330], [334, 335], [333, 334], [330, 331], [332, 333], [331, 332], [434, 435], [433, 434], [435, 436], [432, 433], [436, 437], [431, 432], [437, 438], [438, 439], [430, 431], [439, 440], [429, 430], [440, 441], [428, 429], [427, 428], [441, 442], [426, 427], [442, 443], [425, 426], [424, 425], [357, 358], [443, 444], [356, 357], [358, 359], [355, 356], [359, 360], [423, 424], [354, 355], [360, 361], [444, 445], [361, 362], [353, 354], [362, 363], [422, 423], [363, 364], [352, 353], [364, 365], [445, 446], [365, 366], [421, 422], [351, 352], [366, 367], [350, 351], [446, 447], [367, 368], [349, 350], [447, 448], [368, 369], [347, 448], [348, 349], [347, 348], [392, 393], [369, 370], [393, 394], [391, 392], [370, 371], [420, 421], [390, 391], [394, 395], [371, 372], [389, 390], [419, 420], [388, 389], [372, 373], [387, 388], [395, 396], [386, 387], [418, 419], [373, 374], [385, 386], [384, 385], [374, 375], [383, 384], [417, 418], [375, 376], [382, 383], [396, 397], [381, 382], [376, 377], [380, 381], [377, 378], [379, 380], [378, 379], [416, 417], [397, 398], [415, 416], [414, 415], [398, 399], [413, 414], [399, 400], [412, 413], [411, 412], [400, 401], [401, 402], [410, 411], [402, 403], [409, 410], [403, 404], [404, 405], [408, 409], [405, 406], [407, 408], [406, 407], [467, 468], [468, 449], [466, 467], [465, 466], [477, 478], [464, 465], [463, 464], [462, 463], [461, 462], [460, 461], [478, 479], [476, 477], [479, 480], [475, 476], [469, 470], [459, 460], [470, 471], [458, 459], [474, 469], [471, 472], [472, 473], [473, 474], [452, 453], [449, 450], [480, 481], [482, 475], [457, 458], [451, 452], [456, 457], [453, 454], [455, 456], [450, 451], [481, 482], [454, 455], [486, 487], [487, 488], [485, 486], [484, 485], [488, 489], [489, 490], [483, 484], [490, 483], [495, 496], [496, 497], [497, 498], [498, 499], [499, 500], [500, 501], [501, 502], [491, 502], [491, 492], [494, 495], [492, 493], [493, 494], [525, 526], [526, 527], [524, 525], [527, 528], [528, 529], [529, 530], [530, 531], [531, 532], [532, 533], [533, 534], [534, 535], [535, 536], [580, 553], [579, 580], [578, 579], [577, 578], [536, 537], [576, 577], [575, 576], [574, 575], [573, 574], [572, 573], [571, 572], [570, 571], [569, 570], [537, 538], [568, 569], [538, 539], [567, 568], [539, 540], [540, 541], [566, 567], [565, 566], [564, 565], [563, 564], [541, 542], [562, 563], [561, 562], [542, 543], [560, 561], [559, 560], [553, 554], [558, 559], [557, 558], [556, 557], [543, 544], [555, 556], [554, 555], [544, 545], [545, 546], [546, 547], [547, 548], [548, 549], [549, 550], [550, 551], [551, 552], [503, 552], [519, 520], [518, 519], [520, 521], [517, 518], [516, 517], [515, 516], [514, 515], [513, 514], [512, 513], [523, 524], [503, 504], [521, 522], [511, 512], [510, 511], [509, 510], [508, 509], [507, 508], [506, 507], [505, 506], [522, 523], [504, 505], [0, 1], [1, 2], [2, 3], [3, 4], [4, 5], [5, 6], [6, 7], [7, 8], [8, 9], [9, 10], [10, 11], [12, 13], [11, 12], [13, 14], [14, 15], [15, 16], [16, 17], [17, 18], [18, 19], [19, 20], [20, 21], [85, 0], [84, 85], [83, 84], [21, 22], [82, 83], [81, 82], [80, 81], [22, 23], [79, 80], [78, 79], [77, 78], [76, 77], [75, 76], [23, 24], [74, 75], [24, 25], [73, 74], [72, 73], [71, 72], [25, 26], [70, 71], [69, 70], [68, 69], [67, 68], [26, 27], [66, 67], [65, 66], [27, 28], [64, 65], [63, 64], [28, 29], [62, 63], [61, 62], [60, 61], [59, 60], [29, 30], [58, 59], [30, 31], [57, 58], [56, 57], [31, 32], [55, 56], [54, 55], [32, 33], [53, 54], [33, 34], [52, 53], [51, 52], [50, 51], [49, 50], [48, 49], [47, 48], [46, 47], [34, 35], [45, 46], [44, 45], [43, 44], [42, 43], [35, 36], [36, 37], [37, 38], [41, 42], [40, 41], [39, 40], [38, 39]]
    '''
    
    @classmethod
    def init(cls, ):
        if(cls._initialized):
            return
        
        cls._cache = {}
        cls._handle = bpy.types.SpaceView3D.draw_handler_add(cls._draw_handler, (), 'WINDOW', 'POST_PIXEL', )
        cls._initialized = True
        cls._tag_redraw()
    
    @classmethod
    def deinit(cls, ):
        if(not cls._initialized):
            return
        
        bpy.types.SpaceView3D.draw_handler_remove(cls._handle, 'WINDOW', )
        cls._handle = None
        cls._cache = {}
        cls._initialized = False
    
    @classmethod
    def add(cls, key, ):
        c = {
            'name': key,
            'draw': True,
            # 'text': "Active Tool: {} | Vertices/Instances: {}",
        }
        
        '''
        # logo
        from ..resources import directories
        path = os.path.join(directories.addon_images, "logo_alpha_red.png", )
        from ..utils.import_utils import import_image
        image = import_image(path, hide=True, use_fake_user=True, )
        shader = gpu.shader.from_builtin('2D_IMAGE')
        pos_x = 20
        pos_y = 70
        img_y = 100
        img_x = 100 * (image.size[0] / image.size[1])
        batch = batch_for_shader(
            shader, 'TRI_FAN',
            {
                "pos": ((pos_x, pos_y), (pos_x + img_x, pos_y), (pos_x + img_x, pos_y + img_y), (pos_x, pos_y + img_y)),
                "texCoord": ((0, 0), (1, 0), (1, 1), (0, 1)),
            },
        )
        # image.gl_load()
        c['logo'] = {
            'path': path,
            'shader': shader,
            'batch': batch,
            'image': image,
        }
        '''
        
        shader = gpu.shader.from_builtin('2D_UNIFORM_COLOR')

        vs = np.array(cls.logo_vs, dtype=np.float32, )
        vs = vs[:, :2]
        vs = vs * 1000
        
        # batch = batch_for_shader(shader, 'TRIS', {"pos": cls.logo_vs, }, indices=cls.logo_fs, )
        batch = batch_for_shader(shader, 'TRIS', {"pos": vs, }, indices=cls.logo_fs, )
        
        c['logo'] = {
            'shader': shader,
            'batch': batch,
        }
        
        '''
        shader = gpu.shader.from_builtin('2D_UNIFORM_COLOR')
        vs = np.array(cls.logo_outline_vs, dtype=np.float32, )
        vs = vs[:, :2]
        vs = vs * 1000
        batch = batch_for_shader(shader, 'LINES', {"pos": vs, }, indices=cls.logo_outline_es, )
        c['outline'] = {
            'shader': shader,
            'batch': batch,
        }
        '''
        
        cls._cache[key] = c
        cls._tag_redraw()
    
    @classmethod
    def remove(cls, key, ):
        if(key not in cls._cache.keys()):
            return False
        del cls._cache[key]
        cls._tag_redraw()
        return True
    
    @classmethod
    def _draw_handler(cls, ):
        obs = bpy.data.objects
        rm = []
        for k, v in cls._cache.items():
            if(not obs.get(k)):
                rm.append(k)
            else:
                if(v['draw']):
                    cls._draw(k)
        if(len(rm)):
            for k in rm:
                del cls._cache[k]
    
    @classmethod
    def _draw(cls, key, ):
        o = bpy.data.objects.get(key)
        
        # text = cls._cache[key]['text'].format('n/a', 'n/a')
        text0 = ""
        if(o is not None):
            # t = 'n/a'
            # tool = SC5Toolbox.get()
            # if(tool is not None):
            #     t = tool.bl_label
            l = len(o.data.vertices)
            if l > 50_000:
                l = str(l) + " /!\\"
            # text = cls._cache[key]['text'].format(t, l, )
            # text = cls._cache[key]['text'].format(t, l, )
            
            name = ''
            e = bpy.context.scene.scatter5.emitter
            for i, p in enumerate(e.scatter5.particle_systems):
                if(i == e.scatter5.particle_systems_idx):
                    name = p.name
            if(name != ''):
                text0 = "System: {}, Instances: {}".format(name, l, )
            else:
                text0 = "Vertices / Instances: {}".format(l, )
        
        try:
            # NOTE: is this wise? try/except in draw handler
            size = bpy.context.preferences.ui_styles[0].widget_label.points
            # NOTE: is it always 'Default'?
            color = bpy.context.preferences.themes['Default'].view_3d.space.text_hi
            if(len(color) == 3):
                color = color + (1.0, )
        except Exception as e:
            size = 11
            color = (1.0, 1.0, 1.0, 1.0, )
        
        # style
        font_id = 0
        ui_scale = bpy.context.preferences.system.ui_scale
        size = int(size * 1.3)
        s = round(size * ui_scale)
        blf.size(font_id, s, 72)
        blf.color(font_id, *color)
        blf.enable(font_id, blf.SHADOW)
        blf.shadow(font_id, 3, 0.0, 0.0, 0.0, 0.5)
        blf.shadow_offset(font_id, 0, -2)
        
        x = 20
        y = 20
        l = int(size * 1.5)
        
        # brush name and stats
        location = (x, y + (2 * l), 0)
        # location = (x, y + (3 * l), 0)
        blf.position(font_id, *location)
        blf.draw(font_id, text0)
        
        # help
        
        text1 = ""
        # text2 = "Help - Draw: LMB; Undo/(Redo): 'CTRL+(SHIFT)+Z'"
        text2 = "Draw: LMB; Undo/(Redo): 'CTRL+(SHIFT)+Z'"
        '''
        text3 = "Help - {}"
        
        from . import brushes
        bcs = brushes.all_brush_classes()
        d = brushes.switch_shortcuts
        ls = []
        for k, v in d.items():
            for c in bcs:
                if(c.brush_type == v):
                    ls.append("'{}': {}".format(k, c.bl_label))
        text3 = text3.format(", ".join(ls))
        '''
        
        import string
        tool = SC5Toolbox.get()
        if(tool is not None):
            # text1 = "Tool - {}".format(tool.bl_label, )
            text1 = "{}".format(tool.bl_label, )
            
            hs = []
            mm = tool.modal_adjust_map
            for i in range(len(mm)):
                d = mm[i]
                if(d['enabled']):
                    dk = d['key']
                    do = d['oskey']
                    ds = d['shift']
                    dt = d['text']
                    
                    nm = tuple(string.Formatter().parse(dt))
                    nm = nm[0][0]
                    
                    if(do or ds):
                        if(do):
                            tt = "{}{}+{}".format(nm, 'CTRL', dk, )
                        if(ds):
                            tt = "{}{}+{}".format(nm, 'SHIFT', dk, )
                    else:
                        tt = "{}{}".format(nm, dk, )
                    hs.append(tt)
            if(len(hs)):
                text2 = ", ".join(hs)
                if(tool.help_message_extra != ""):
                    # text2 = "Help - Draw: LMB, {}; {}; Undo / (Redo): 'CTRL+(SHIFT)+Z'".format(tool.help_message_extra, text2, )
                    text2 = "Draw: LMB, {}; {}; Undo / (Redo): 'CTRL+(SHIFT)+Z'".format(tool.help_message_extra, text2, )
                else:
                    # text2 = "Help - Draw: LMB, {}; Undo / (Redo): 'CTRL+(SHIFT)+Z'".format(text2, )
                    text2 = "Draw: LMB, {}; Undo / (Redo): 'CTRL+(SHIFT)+Z'".format(text2, )
        
        location = (x, y + (1 * l), 0)
        # location = (x, y + (2 * l), 0)
        blf.position(font_id, *location)
        blf.draw(font_id, text1)
        
        location = (x, y + (0 * l), 0)
        # location = (x, y + (1 * l), 0)
        blf.position(font_id, *location)
        blf.draw(font_id, text2)
        
        # size = int(size * 0.75)
        # s = round(size * ui_scale)
        # blf.size(font_id, s, 72)
        #
        # location = (x, y + (0 * l), 0)
        # blf.position(font_id, *location)
        # blf.draw(font_id, text3)
        
        # esc
        text = "Press ESC to Exit"
        s = 24
        blf.size(font_id, round(s * ui_scale), 72)
        x = 20
        y = 20
        width = bpy.context.region.width
        dim_x = blf.dimensions(font_id, text)[0]
        blf.position(font_id, width - dim_x - x, y, 0)
        blf.draw(font_id, text)
        
        '''
        # Draw some handlers
        from ..utils import draw_utils
        # Draw Esc Instruction
        h = draw_utils.add_font(text="Press ESC to Quit", size=[35,56], position=[245,20], origin="BOTTOM RIGHT", color=[0.9,0.9,0.9,0.9], shadow={"blur":3,"color":[0,0,0,0.4],"offset":[2,-2],})
        self._integration_handlers.append(h)
        """
        # Draw OpenBeta as Font?
        h = draw_utils.add_font(text="Scatter5 OpenBeta", size=[40,62], position=[20,20], origin="BOTTOM LEFT", color=[0.9,0.65,0.65,0.3], shadow=None)
        self._integration_handlers.append(h)
        """
        # Draw OpenBeta as Img
        import os
        from ..resources import directories
        h = draw_utils.add_image(image_data=None, path=os.path.join(directories.addon_images,"logo_alpha_red.png"),position=[20,50], origin="BOTTOM LEFT", height_px=100)
        self._integration_handlers.append(h)
        # Draw some gradient ?
        h = draw_utils.add_gradient(px_height=75,alpha_start=0.85)
        self._integration_handlers.append(h)
        '''
        
        '''
        # logo
        if('logo' in cls._cache[key].keys()):
            shader = cls._cache[key]['logo']['shader']
            batch = cls._cache[key]['logo']['batch']
            image = cls._cache[key]['logo']['image']
            
            if(image.gl_load()):
                # non zero return > error, skip the rest..
                return
            
            bgl.glEnable(bgl.GL_BLEND)
            bgl.glActiveTexture(bgl.GL_TEXTURE0)
            
            # FIXME: not quite elegant doing this while drawing on screen, but i don't see any other way, is user undo so far that image is removed, what can i do?
            try:
                image.bindcode
            except ReferenceError:
                from ..utils.import_utils import import_image
                image = import_image(cls._cache[key]['logo']['path'], hide=True, use_fake_user=True, )
                image.gl_load()
                cls._cache[key]['logo']['image'] = image
            
            bgl.glBindTexture(bgl.GL_TEXTURE_2D, image.bindcode)
            shader.bind()
            shader.uniform_int('image', 0, )
            batch.draw(shader)
            bgl.glDisable(bgl.GL_BLEND)
            
            image.gl_free()
        '''
        
        if('logo' in cls._cache[key].keys()):
            shader = cls._cache[key]['logo']['shader']
            batch = cls._cache[key]['logo']['batch']
            
            bgl.glEnable(bgl.GL_BLEND)
            bgl.glEnable(bgl.GL_POLYGON_SMOOTH)
            # bgl.glEnable(bgl.GL_LINE_SMOOTH)
            gpu.matrix.push()
            # gpu.matrix.translate((0, 30))
            # gpu.matrix.translate((0, 50))
            
            # # beta logo
            # gpu.matrix.translate((0, 60))
            # production logo
            # gpu.matrix.translate((20, 90))
            gpu.matrix.translate((20, 95))
            
            # gpu.matrix.translate((0, 80))
            shader.bind()
            shader.uniform_float("color", (0.7, 0.7, 0.7, 0.3))
            batch.draw(shader)
            # NOTE: drawin once with GL_POLYGON_SMOOTH leaves gaps between polygons, twice it get overdrawn.. hacky..
            batch.draw(shader)
            gpu.matrix.pop()
            bgl.glDisable(bgl.GL_BLEND)
            bgl.glDisable(bgl.GL_POLYGON_SMOOTH)
            # bgl.glDisable(bgl.GL_LINE_SMOOTH)
        
        '''
        if('outline' in cls._cache[key].keys()):
            shader = cls._cache[key]['outline']['shader']
            batch = cls._cache[key]['outline']['batch']
            
            bgl.glEnable(bgl.GL_BLEND)
            bgl.glEnable(bgl.GL_LINE_SMOOTH)
            # bgl.glEnable(bgl.GL_POLYGON_SMOOTH)
            gpu.matrix.push()
            gpu.matrix.translate((20, 95))
            shader.bind()
            # shader.uniform_float("color", (1.0,1.0,1.0,1.0))
            shader.uniform_float("color", (1.0,1.0,1.0,0.5))
            batch.draw(shader)
            # NOTE: drawin once with GL_POLYGON_SMOOTH leaves gaps between polygons, twice it get overdrawn.. hacky..
            batch.draw(shader)
            gpu.matrix.pop()
            bgl.glDisable(bgl.GL_BLEND)
            # bgl.glDisable(bgl.GL_POLYGON_SMOOTH)
            bgl.glDisable(bgl.GL_LINE_SMOOTH)
        '''
        
        # import os
        # from ..resources import directories
        # h = draw_utils.add_image(image_data=None, path=os.path.join(directories.addon_images,"logo_alpha_red.png"),position=[20,50], origin="BOTTOM LEFT", height_px=100)
        # self._integration_handlers.append(h)
        # #Draw some gradient ?
        # h = draw_utils.add_gradient(px_height=75,alpha_start=0.85)
        # self._integration_handlers.append(h)
    
    @classmethod
    def _tag_redraw(cls, ):
        for window in bpy.context.window_manager.windows:
            for area in window.screen.areas:
                if(area.type == 'VIEW_3D'):
                    area.tag_redraw()


class SC5ViewportTheme():
    BRUSH_UP = np.array((0.9, 0.9, 0.9, 1.0), dtype=np.float32, )
    BRUSH_DOWN = np.array((1.0, 0.0, 0.0, 1.0), dtype=np.float32, )


class SC5Overlay():
    _darken = 0.5
    _shader = None
    _batch = None
    _handlers = []
    _initialized = False
    _visible = False
    
    @classmethod
    def init(cls, ):
        if(cls._initialized):
            return
        
        v, f, _ = load_shader_code('OVERLAY')
        cls._shader = gpu.types.GPUShader(v, f, )
        # triangle to cover all: https://stackoverflow.com/a/59739538
        cls._batch = batch_for_shader(cls._shader, 'TRIS', {'position': [(-1, -1), (3, -1), (-1, 3), ], })
        
        cls._handlers = []
        cls._initialized = True
        cls._tag_redraw()
    
    @classmethod
    def deinit(cls, ):
        if(not cls._initialized):
            return
        
        cls.hide()
        
        cls._handlers = []
        cls._shader = None
        cls._batch = None
        
        cls._visible = False
        cls._initialized = False
        cls._tag_redraw()
    
    @classmethod
    def _draw(cls, a, ):
        bgl.glEnable(bgl.GL_BLEND)
        # NOTE: i think it should be disabled by default, but let do it anyway
        bgl.glDisable(bgl.GL_DEPTH_TEST)
        cls._shader.bind()
        cls._shader.uniform_float('darken', cls._darken, )
        cls._batch.draw(cls._shader, )
        # unbind, it is required?
        gpu.shader.unbind()
        bgl.glDisable(bgl.GL_BLEND)
    
    @classmethod
    def show(cls, ):
        if(not cls._initialized):
            cls.init()
        if(cls._visible):
            return
        
        # get all types that begin with `Space`
        spaces = [(getattr(bpy.types, n), n) for n in dir(bpy.types) if n.startswith('Space')]
        # get all of them that define `draw_handler_add`
        spaces = [(s, n) for (s, n) in spaces if hasattr(s, 'draw_handler_add')]
        
        areas = ['WINDOW', 'HEADER', 'CHANNELS', 'TEMPORARY', 'UI', 'TOOLS', 'TOOL_PROPS', 'PREVIEW', 'HUD', 'NAVIGATION_BAR', 'EXECUTE', 'FOOTER', 'TOOL_HEADER']
        sv3d_areas = [
            # 'TOOL_HEADER',
            # 'HEADER',
            # 'TOOLS',
            # 'UI',
            # 'WINDOW',
        ]
        
        for s, n in spaces:
            areas = sv3d_areas if n == 'SpaceView3D' else areas
            for a in areas:
                try:
                    h = s.draw_handler_add(cls._draw, (a, ), a, 'POST_PIXEL', )
                    cls._handlers.append((s, a, h, ))
                except Exception:
                    pass
                # except Exception as e:
                #     print(s, n, a, e)
        
        cls._visible = True
        cls._tag_redraw()
    
    @classmethod
    def hide(cls, ):
        if(not cls._visible):
            return
        
        for s, a, h in cls._handlers:
            s.draw_handler_remove(h, a, )
        cls._handlers = []
        
        cls._visible = False
        cls._tag_redraw()
    
    @classmethod
    def _tag_redraw(cls, ):
        for window in bpy.context.window_manager.windows:
            for area in window.screen.areas:
                # if(area.type == 'VIEW_3D'):
                #     area.tag_redraw()
                area.tag_redraw()


class SC5UISwapper():
    _initialized = False
    _active = False
    
    # CLEAR_HISTORY = True
    
    @classmethod
    def init(cls, ):
        if(cls._initialized):
            return
        cls._initialized = True
    
    @classmethod
    def deinit(cls, ):
        if(not cls._initialized):
            return
        cls.hide()
        cls._active = False
        cls._initialized = False
    
    @classmethod
    def _swap(cls, context, ):
        # global _ignore_integration
        # if _ignore_integration:
        #     return None
        #
        # #On modal invoke:
        
        scat_scene = bpy.context.scene.scatter5
        emitter = scat_scene.emitter
        psy_active = emitter.scatter5.get_psy_active()
        target = psy_active.scatter_obj
        
        # Make sure emitter is visible
        if(emitter.hide_viewport):
            emitter.hide_viewport = False
            
        # And target is visible
        if(target.hide_viewport):
            target.hide_viewport = False
        
        # Hijacking blender interface for our custom "mode" on modal start
        from ..ui import ui_manual
        ui_manual.modal_hijacking(context)
        
        # #set active tool to our newly hijacked registered interface
        # bpy.ops.wm.tool_set_by_id(name=self.brush_type)
        
        '''
        # Draw some handlers
        from ..utils import draw_utils
        # Draw Esc Instruction
        h = draw_utils.add_font(text="Press ESC to Quit", size=[35,56], position=[245,20], origin="BOTTOM RIGHT", color=[0.9,0.9,0.9,0.9], shadow={"blur":3,"color":[0,0,0,0.4],"offset":[2,-2],})
        self._integration_handlers.append(h)
        """
        # Draw OpenBeta as Font?
        h = draw_utils.add_font(text="Scatter5 OpenBeta", size=[40,62], position=[20,20], origin="BOTTOM LEFT", color=[0.9,0.65,0.65,0.3], shadow=None)
        self._integration_handlers.append(h)
        """
        # Draw OpenBeta as Img
        import os
        from ..resources import directories
        h = draw_utils.add_image(image_data=None, path=os.path.join(directories.addon_images,"logo_alpha_red.png"),position=[20,50], origin="BOTTOM LEFT", height_px=100)
        self._integration_handlers.append(h)
        # Draw some gradient ?
        h = draw_utils.add_gradient(px_height=75,alpha_start=0.85)
        self._integration_handlers.append(h)
        '''
        
        # # empty undo history after ui change so any prop changes are not affected while undoing..
        # if(cls.CLEAR_HISTORY):
        #     for i in range(bpy.context.preferences.edit.undo_steps):
        #         bpy.ops.ed.undo_push(message="Initialize", )
        bpy.ops.ed.undo_push(message="Initialize", )
    
    @classmethod
    def _unswap(cls, context, ):
        # global _ignore_integration
        # if _ignore_integration:
        #     return None
        
        # On modal cancel:
        
        # restoring old interface on modal cancel
        from ..ui import ui_manual
        ui_manual.modal_hijack_restore(context)
                
        '''
        #remove all handlers from class storage
        for h in self._integration_handlers:
            if h is not None:
                bpy.types.SpaceView3D.draw_handler_remove(h, "WINDOW")
        self._integration_handlers.clear()
        '''
        
        # # empty undo history after ui change so any prop changes are not affected while undoing..
        # if(cls.CLEAR_HISTORY):
        #     for i in range(bpy.context.preferences.edit.undo_steps):
        #         bpy.ops.ed.undo_push(message="Deinitialize", )
        bpy.ops.ed.undo_push(message="Deinitialize", )
    
    @classmethod
    def show(cls, context=None, ):
        if(not cls._initialized):
            cls.init()
        if(cls._active):
            return
        if(context is None):
            context = bpy.context
        cls._swap(context, )
        cls._active = True
    
    @classmethod
    def hide(cls, context=None, ):
        if(not cls._active):
            return
        if(context is None):
            context = bpy.context
        cls._unswap(context, )
        cls._active = False


class SC5SessionCache():
    _initialized = False
    _m = None
    _bm = None
    _bvh = None
    epsilon = 0.001
    
    @classmethod
    def init(cls, ):
        if(cls._initialized):
            return
        # cls._initialized = True
    
    @classmethod
    def deinit(cls, ):
        if(not cls._initialized):
            return
        if(cls._bm is not None):
            cls._bm.free()
        cls._m = None
        cls._bm = None
        cls._bvh = None
        cls._initialized = False
    
    @classmethod
    def get(cls, context, ):
        if(not cls._initialized):
            cls._generate(context, )
            # NOTE: just a prototype..
            # cls._generate_multi(context, )
            cls._initialized = True
        return cls._m, cls._bm, cls._bvh
    
    @classmethod
    def _generate_multi(cls, context, ):
        # NOTE: somehow get list of emitters, this is for testing now
        ls = [
            bpy.data.objects['Plane'],
            bpy.data.objects['Plane.001'],
            bpy.data.objects['Plane.002'],
            bpy.data.objects['Plane.003'],
        ]
        
        import uuid
        depsgraph = context.evaluated_depsgraph_get()
        dt = []
        for o in ls:
            eo = o.evaluated_get(depsgraph)
            m = eo.matrix_world
            bm = bmesh.new()
            bm.from_object(eo, depsgraph, cage=False, face_normals=True, )
            bm.transform(m)
            bmesh.ops.triangulate(bm, faces=bm.faces, )
            me = bpy.data.meshes.new(name='tmp-{}'.format(uuid.uuid1()), )
            bm.to_mesh(me)
            bm.free()
            me.calc_loop_triangles()
            vs = np.zeros((len(me.vertices) * 3), dtype=np.float, )
            me.vertices.foreach_get('co', vs, )
            vs.shape = (-1, 3, )
            tris = np.zeros((len(me.loop_triangles) * 3), dtype=np.int, )
            me.loop_triangles.foreach_get('vertices', tris, )
            tris.shape = (-1, 3, )
            bpy.data.meshes.remove(me)
            dt.append([vs, tris, ])
        
        vl = 0
        tl = 0
        for i, d in enumerate(dt):
            vs, tris = d
            vl += len(vs)
            tl += len(tris)
        
        vi = 0
        ti = 0
        avs = np.zeros((vl, 3), dtype=np.float, )
        atris = np.zeros((tl, 3), dtype=np.int, )
        for i, d in enumerate(dt):
            vs, tris = d
            avs[vi:vi + len(vs)] = vs
            tris = tris + vi
            atris[ti:ti + len(tris)] = tris
            vi += len(vs)
            ti += len(tris)
        
        me = bpy.data.meshes.new(name='tmp-{}'.format(uuid.uuid1()), )
        me.vertices.add(len(avs))
        me.vertices.foreach_set('co', avs.flatten(), )
        
        me.loops.add(len(atris) * 3)
        me.polygons.add(len(atris))
        lt = np.full(len(atris), 3, dtype=np.int, )
        ls = np.arange(0, len(atris) * 3, 3, dtype=np.int, )
        me.polygons.foreach_set('loop_total', lt.flatten(), )
        me.polygons.foreach_set('loop_start', ls.flatten(), )
        me.polygons.foreach_set('vertices', atris.flatten(), )
        me.validate()
        
        # # debug..
        # o = bpy.data.objects.new('debug', me, )
        # bpy.context.view_layer.active_layer_collection.collection.objects.link(o)
        
        cls._m = Matrix()
        bm = bmesh.new()
        bm.from_mesh(me)
        cls._bm = bm
        bvh = BVHTree.FromBMesh(bm, epsilon=cls.epsilon, )
        cls._bvh = bvh
        
        bpy.data.meshes.remove(me)
    
    @classmethod
    def _generate(cls, context, ):
        o = bpy.context.scene.scatter5.emitter
        m = o.matrix_world
        
        depsgraph = context.evaluated_depsgraph_get()
        eo = o.evaluated_get(depsgraph)
        bm = bmesh.new()
        bm.from_object(eo, depsgraph, cage=False, face_normals=True, )
        bm.transform(m)
        # always triangulate..
        bmesh.ops.triangulate(bm, faces=bm.faces, )
        bm.verts.ensure_lookup_table()
        bm.faces.ensure_lookup_table()
        
        bvh = BVHTree.FromBMesh(bm, epsilon=cls.epsilon, )
        
        cls._m = m
        cls._bm = bm
        cls._bvh = bvh
    
    @classmethod
    def free(cls, ):
        cls.deinit()


class SC5ToolTip():
    _cache = {}
    _handle = None
    _initialized = False
    
    @classmethod
    def init(cls, ):
        if(cls._initialized):
            return
        
        cls._cache = {}
        cls._handle = bpy.types.SpaceView3D.draw_handler_add(cls._draw, (), 'WINDOW', 'POST_PIXEL', )
        cls._initialized = True
        cls._tag_redraw()
    
    @classmethod
    def deinit(cls, ):
        if(not cls._initialized):
            return
        
        bpy.types.SpaceView3D.draw_handler_remove(cls._handle, 'WINDOW', )
        cls._handle = None
        cls._initialized = False
        cls._cache = {}
    
    @classmethod
    def _rectangle(cls, font_id, t, x, y, p, ):
        w, h = blf.dimensions(font_id, t)
        vertices = np.array((
            (x - p, y - p - 2),
            (x + w + p, y - p - 2),
            (x - p, y + h + p),
            (x + w + p, y + h + p)
        ), dtype=np.float32, )
        indices = np.array(((0, 1, 3), (0, 3, 2)), dtype=np.int32, )
        shader = gpu.shader.from_builtin('2D_UNIFORM_COLOR')
        batch = batch_for_shader(shader, 'TRIS', {'pos': vertices, }, indices=indices, )
        
        bgl.glEnable(bgl.GL_BLEND)
        shader.bind()
        shader.uniform_float('color', (0, 0, 0, 0.5))
        batch.draw(shader)
        bgl.glDisable(bgl.GL_BLEND)
    
    @classmethod
    def _draw(cls, ):
        size = 11
        color = (1.0, 1.0, 1.0, 1.0, )
        font_id = 0
        ui_scale = bpy.context.preferences.system.ui_scale
        # size = int(size * 1.3)
        s = round(size * ui_scale)
        blf.size(font_id, s, 72)
        blf.color(font_id, *color)
        blf.enable(font_id, blf.SHADOW)
        blf.shadow(font_id, 3, 0.0, 0.0, 0.0, 0.5)
        blf.shadow_offset(font_id, 0, -2)
        
        for k, v in cls._cache.items():
            t, x, y = v
            
            cls._rectangle(font_id, t, x, y, 5, )
            
            blf.position(font_id, x, y, 0.0, )
            blf.draw(font_id, t)
    
    @classmethod
    def _tag_redraw(cls, ):
        for window in bpy.context.window_manager.windows:
            for area in window.screen.areas:
                if(area.type == 'VIEW_3D'):
                    area.tag_redraw()


class SC5Debug():
    _cache = {}
    _handle = None
    _initialized = False
    
    @classmethod
    def init(cls, ):
        if(cls._initialized):
            return
        
        cls._handle = bpy.types.SpaceView3D.draw_handler_add(cls._draw, (), 'WINDOW', 'POST_PIXEL', )
        cls._initialized = True
        cls._tag_redraw()
    
    @classmethod
    def deinit(cls, ):
        if(not cls._initialized):
            return
        
        bpy.types.SpaceView3D.draw_handler_remove(cls._handle, 'WINDOW', )
        cls._handle = None
        cls._initialized = False
    
    @classmethod
    def _draw(cls, ):
        size = 11
        # color = (1.0, 1.0, 1.0, 1.0, )
        color = (1.0, 1.0, 1.0, 0.5, )
        font_id = 0
        ui_scale = bpy.context.preferences.system.ui_scale
        # size = int(size * 1.3)
        s = round(size * ui_scale)
        blf.size(font_id, s, 72)
        blf.color(font_id, *color)
        blf.enable(font_id, blf.SHADOW)
        # blf.shadow(font_id, 3, 0.0, 0.0, 0.0, 0.5)
        blf.shadow(font_id, 3, 0.0, 0.0, 0.0, 0.25)
        blf.shadow_offset(font_id, 0, -2)
        
        x = 20
        # y = bpy.context.region.height - 20 - 200
        y = bpy.context.region.height - 20 - 20
        # l = int(size * 1.5)
        l = int(size * 1.25)
        i = 0
        
        def line(i, t, ):
            location = (x, y - (i * l), 0)
            blf.position(font_id, *location)
            blf.draw(font_id, t)
            i += 1
            return i
        
        i = line(i, 'SC5Toolbox', )
        i = line(i, 'tool: {}'.format(SC5Toolbox.get()), )
        i = line(i, '', )
        i = line(i, 'SC5Cursor', )
        i = line(i, 'initialized: {}'.format(SC5Cursor._initialized), )
        i = line(i, 'cache: {}'.format(tuple(SC5Cursor._cache.keys())), )
        i = line(i, '', )
        i = line(i, 'SC5Stats', )
        i = line(i, 'initialized: {}'.format(SC5Stats._initialized), )
        i = line(i, 'cache: {}'.format(tuple(SC5Stats._cache.keys())), )
        i = line(i, '', )
        i = line(i, 'SC5Overlay', )
        i = line(i, 'initialized: {}'.format(SC5Overlay._initialized), )
        i = line(i, 'handlers: {}'.format(len(SC5Overlay._handlers)), )
        i = line(i, '', )
        i = line(i, 'SC5UISwapper', )
        i = line(i, 'initialized: {}'.format(SC5UISwapper._initialized), )
        i = line(i, 'active: {}'.format(SC5UISwapper._active), )
        i = line(i, '', )
        i = line(i, 'SC5SessionCache', )
        i = line(i, 'initialized: {}'.format(SC5SessionCache._initialized), )
        i = line(i, 'm: {}'.format("".join(str(repr(SC5SessionCache._m)).split())), )
        i = line(i, 'bm: {}'.format(SC5SessionCache._bm), )
        i = line(i, 'bvh: {}'.format(SC5SessionCache._bvh), )
        i = line(i, '', )
        i = line(i, 'SC5ToolTip', )
        i = line(i, 'initialized: {}'.format(SC5ToolTip._initialized), )
        i = line(i, 'cache: {}'.format(tuple(SC5ToolTip._cache.keys())), )
        i = line(i, '', )
        i = line(i, 'SC5GestureCursor', )
        i = line(i, 'initialized: {}'.format(SC5GestureCursor._initialized), )
        i = line(i, 'cache: {}'.format(tuple(SC5GestureCursor._cache.keys())), )
        i = line(i, '', )
        i = line(i, 'SC5Cursor2D', )
        i = line(i, 'initialized: {}'.format(SC5Cursor2D._initialized), )
        i = line(i, 'cache: {}'.format(tuple(SC5Cursor2D._cache.keys())), )
        i = line(i, '', )
        i = line(i, 'SC5GestureCursor2D', )
        i = line(i, 'initialized: {}'.format(SC5GestureCursor2D._initialized), )
        i = line(i, 'cache: {}'.format(tuple(SC5GestureCursor2D._cache.keys())), )
        
        tool = SC5Toolbox.get()
        if(tool is not None):
            i = line(i, '', )
            i = line(i, '{}'.format(tool.__class__.__name__), )
            i = line(i, 'mouse 3d path: prev: {}, current: {}'.format(tool._mouse_3d_prev, tool._mouse_3d, ))
            i = line(i, 'mouse 3d direction: {}'.format(tool._mouse_3d_direction, ))
            i = line(i, 'mouse 2d path: prev: {}, current: {}'.format(tool._mouse_2d_prev, tool._mouse_2d, ))
            i = line(i, 'mouse 2d direction: {}'.format(tool._mouse_2d_direction, ))
            i = line(i, 'surface: {}, surface_name: {}'.format(tool.surface, tool.surface_name, ))
            i = line(i, 'target: {}, target_name: {}'.format(tool.target, tool.target_name, ))
            i = line(i, 'lmb: {}, ctrl: {}, shift: {}, alt: {}'.format(tool.lmb, tool.ctrl, tool.shift, tool.alt, ))
            
            # x = 20 + 400
            # y = bpy.context.region.height - 20 - 20
            # i = 0
            # ls = dir(tool)
            # skip = ('_mouse_3d_prev', '_mouse_3d', '_mouse_3d_direction', '_mouse_2d_prev', '_mouse_2d', '_mouse_2d_direction',
            #         'surface', 'surface_name', 'target', 'target_name', 'lmb', 'ctrl', 'shift', 'alt', )
            # for k in ls:
            #     if(k not in skip):
            #         i = line(i, '{}: {}'.format(k, getattr(tool, k), ))
            
            if(tool.brush_type in ('path_brush', 'spatter_brush', 'comb_brush', )):
                if(len(tool.direction)):
                    i = line(i, 'direction[-1]: {}'.format(tool.direction[-1], ))
                else:
                    i = line(i, 'direction[-1]: {}'.format(None, ))
                if(len(tool.path)):
                    i = line(i, 'path[-1]: {}'.format(tool.path[-1], ))
                else:
                    i = line(i, 'path[-1]: {}'.format(None, ))
    
    @classmethod
    def _tag_redraw(cls, ):
        for window in bpy.context.window_manager.windows:
            for area in window.screen.areas:
                if(area.type == 'VIEW_3D'):
                    area.tag_redraw()


class DebugPoints2DManager():
    _initialized = False
    _handle = None
    _cache = {}
    
    vertex_shader = '''
    in vec3 position;
    in vec4 color;
    uniform mat4 viewProjectionMatrix;
    uniform float point_size;
    out vec4 f_color;
    void main()
    {
        gl_Position = viewProjectionMatrix * vec4(position, 1.0);
        gl_PointSize = point_size;
        f_color = color;
    }
    '''
    fragment_shader = '''
    in vec4 f_color;
    out vec4 fragColor;
    void main()
    {
        fragColor = blender_srgb_to_framebuffer_space(f_color);
    }
    '''
    
    @classmethod
    def init(cls, ):
        if(cls._initialized):
            return
        cls._cache = {}
        cls._handle = bpy.types.SpaceView3D.draw_handler_add(cls._draw_handler, (), 'WINDOW', 'POST_PIXEL', )
        cls._initialized = True
        cls._tag_redraw()
    
    @classmethod
    def deinit(cls, ):
        if(not cls._initialized):
            return
        bpy.types.SpaceView3D.draw_handler_remove(cls._handle, 'WINDOW', )
        cls._handle = None
        cls._cache = {}
        cls._initialized = False
        cls._tag_redraw()
    
    @classmethod
    def _draw_handler(cls, ):
        for k, c in cls._cache.items():
            bgl.glEnable(bgl.GL_PROGRAM_POINT_SIZE)
            shader = c['shader']
            batch = c['batch']
            shader.bind()
            matrix = gpu.matrix.get_projection_matrix()
            shader.uniform_float('viewProjectionMatrix', matrix)
            shader.uniform_float('point_size', 3.0, )
            batch.draw(shader)
            bgl.glDisable(bgl.GL_PROGRAM_POINT_SIZE)
    
    @classmethod
    def add(cls, key, vs, cs, ):
        if(key in cls._cache.keys()):
            # return False
            del cls._cache[key]
        
        shader = GPUShader(cls.vertex_shader, cls.fragment_shader, )
        batch = batch_for_shader(shader, 'POINTS', {'position': vs, 'color': cs, }, )
        c = {
            'name': key,
            'vs': vs,
            'cs': cs,
            'draw': True,
            'shader': shader,
            'batch': batch,
        }
        cls._cache[key] = c
        cls._tag_redraw()
        return True
    
    @classmethod
    def remove(cls, ):
        if(key not in cls._cache.keys()):
            return False
        del cls._cache[key]
        cls._tag_redraw()
        return True
    
    @classmethod
    def _tag_redraw(cls, ):
        for window in bpy.context.window_manager.windows:
            for area in window.screen.areas:
                if(area.type == 'VIEW_3D'):
                    area.tag_redraw()


@bpy.app.handlers.persistent
def watcher(undefined):
    SC5Cursor.deinit()
    SC5Stats.deinit()
    SC5Toolbox.deinit()
    SC5Overlay.deinit()
    SC5UISwapper.deinit()
    SC5SessionCache.deinit()
    SC5ToolTip.deinit()
    SC5GestureCursor.deinit()
    SC5GestureCursor2D.deinit()
    
    SC5Debug.deinit()


@verbose
def init():
    SC5Toolbox.init()
    
    if(debug_mode()):
        SC5Debug.init()


@verbose
def deinit():
    SC5Cursor.deinit()
    SC5Stats.deinit()
    SC5Toolbox.deinit()
    SC5Overlay.deinit()
    SC5UISwapper.deinit()
    SC5SessionCache.deinit()
    SC5ToolTip.deinit()
    SC5GestureCursor.deinit()
    SC5Cursor2D.deinit()
    
    SC5Debug.deinit()
    DebugPoints2DManager.deinit()


shader_registry = {
    'BRUSH': {'v': "brush.vert", 'f': "brush.frag", },
    'BRUSH_2D': {'v': "brush_2d.vert", 'f': "brush_2d.frag", },
    'OVERLAY': {'v': "overlay.vert", 'f': "overlay.frag", },
}
shader_directory = os.path.join(os.path.dirname(__file__), 'shaders', )


def load_shader_code(name):
    if(name not in shader_registry.keys()):
        raise TypeError("Unknown shader requested..")
    d = shader_registry[name]
    vf = d['v']
    ff = d['f']
    gf = None
    if('g' in d.keys()):
        gf = d['g']
    with open(os.path.join(shader_directory, vf), mode='r', encoding='utf-8') as f:
        vs = f.read()
    with open(os.path.join(shader_directory, ff), mode='r', encoding='utf-8') as f:
        fs = f.read()
    gs = None
    if(gf is not None):
        with open(os.path.join(shader_directory, gf), mode='r', encoding='utf-8') as f:
            gs = f.read()
    return vs, fs, gs


classes = ()
