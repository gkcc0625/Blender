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

import bpy
from .debug import log, debug_mode
from bpy.types import PropertyGroup, Panel, Operator
from bpy.props import StringProperty, BoolProperty, EnumProperty, CollectionProperty
from .. resources.translate import translate


def first_run():
    cfg = preferences()
    ls = cfg.items
    if(len(ls) > 0):
        return
    
    data = [
        ('ONE', 'dot_brush', "Dot", False, (False, False, False, False, ), ),
        ('TWO', 'pose_brush', "Pose", False, (False, False, False, False, ), ),
        ('THREE', 'path_brush', "Path", False, (False, False, False, False, ), ),
        ('FOUR', 'spatter_brush', "Spatter", False, (False, False, False, False, ), ),
        ('FIVE', 'spray_brush', "Spray", False, (False, False, False, False, ), ),
        ('M', 'move_brush', "Move", False, (False, False, False, False, ), ),
        ('E', 'eraser_brush', "Eraser", False, (False, False, False, False, ), ),
        ('D', 'dilute_brush', "Dilute", False, (False, False, False, False, ), ),
        ('Y', 'comb_brush', "Tangent Align", False, (False, False, False, False, ), ),
        ('U', 'z_align_brush', "Normal Align", False, (False, False, False, False, ), ),
        ('R', 'rotation_brush', "Rotation Settings", False, (False, False, False, False, ), ),
        ('T', 'random_rotation_brush', "Random Rotation", False, (False, False, False, False, ), ),
        ('S', 'scale_brush', "Scale Settings", False, (False, False, False, False, ), ),
        ('A', 'scale_grow_shrink_brush', "Grow/Shrink", False, (False, False, False, False, ), ),
        ('O', 'object_brush', "Index", False, (False, False, False, False, ), ),
        ('F', '_gesture', "Gesture", True, (False, False, False, False, ), ),
        # ('F', '_gesture_alternate', "Gesture Alternate", True, (True, True, False, False, ), ),
        ('F', '_gesture_alternate', "Alternative Gesture", True, (True, False, False, False, ), ),
    ]
    # nums = {'ONE': '1', 'TWO': '2', 'THREE': '3', 'FOUR': '4', 'FIVE': '5', 'SIX': '6', 'SEVEN': '7', 'EIGHT': '8', 'NINE': '9', 'ZERO': '0', }
    flags = ['oskey', 'ctrl', 'alt', 'shift', ]
    
    for i, di in enumerate(data):
        k, n, l, u, f = di
        a = k
        # if(a in nums):
        #     a = nums[k]
        
        i = ls.add()
        i.name = n
        i.label = l
        i.char = a
        i.ascii = a
        i.unicode = a
        i.type = k
        i.utility = u
        for j, v in enumerate(f):
            setattr(i, flags[j], v)


def preferences():
    return bpy.context.preferences.addons["Scatter5"].preferences.manual_key_config


def switch_shortcuts():
    r = {}
    cfg = preferences()
    ls = cfg.items
    for i in ls:
        if(i.utility):
            continue
        n = i.name
        if(n in ('_gesture', '_gesture_alternate', )):
            continue
        t = i.type
        r[n] = t
    
    return r


def gesture_reconfigure(modal_adjust_map, ):
    cfg = preferences()
    ls = cfg.items
    f = None
    falt = None
    for i in ls:
        if(i.name == '_gesture'):
            f = i
        if(i.name == '_gesture_alternate'):
            falt = i
    
    r = []
    for i, d in enumerate(modal_adjust_map):
        n = {}
        
        alt = False
        if(d['oskey'] or d['shift']):
            alt = True
        
        for k, v in d.items():
            if(k == 'key'):
                if(alt):
                    v = falt.type
                else:
                    v = f.type
            if(k in ('oskey', 'shift', )):
                if(alt):
                    if(k == 'oskey'):
                        v = falt.oskey
                    if(k == 'shift'):
                        v = falt.shift
            n[k] = v
        r.append(n)
    return r


class SCATTER5_manual_key_item(PropertyGroup, ):
    name: StringProperty(default="", )
    label: StringProperty(default="", )
    char: StringProperty(default='', )
    
    oskey: BoolProperty(default=False, )
    ctrl: BoolProperty(default=False, )
    alt: BoolProperty(default=False, )
    shift: BoolProperty(default=False, )
    
    flag: BoolProperty(default=False, )
    type: StringProperty(default='', )
    ascii: StringProperty(default='', )
    unicode: StringProperty(default='', )
    utility: BoolProperty(default=False, )


class SCATTER5_manual_key_config(PropertyGroup, ):
    items: CollectionProperty(name="Items", type=SCATTER5_manual_key_item, )


class SCATTER5_OT_manual_key_config_set_key(Operator, ):
    bl_idname = "scatter5.manual_key_config_set_key"
    bl_label = "Set Key"
    bl_description = ""
    
    name: StringProperty(default="", options={'SKIP_SAVE', 'HIDDEN', })
    
    @classmethod
    def poll(cls, context, ):
        return True
    
    def tag_redraw(self, ):
        for window in bpy.context.window_manager.windows:
            for area in window.screen.areas:
                # if(area.type == 'VIEW_3D'):
                #     area.tag_redraw()
                
                # NOTE: now i am going to redraw averything.. right?
                area.tag_redraw()
    
    def get_item(self, context, ):
        cfg = preferences()
        ref = None
        for i in cfg.items:
            if(i.name == self.name):
                ref = i
                break
        return ref
    
    def modal(self, context, event, ):
        ref = self.get_item(context, )
        if(event.type in {'LEFTMOUSE', 'MIDDLEMOUSE', 'RIGHTMOUSE', 'ESC', }):
            ref.flag = False
            self.tag_redraw()
            return {'FINISHED'}
        elif(event.type in {'LEFT_CTRL', 'LEFT_ALT', 'LEFT_SHIFT', 'RIGHT_ALT', 'RIGHT_CTRL', 'RIGHT_SHIFT', 'OSKEY', }):
            return {'RUNNING_MODAL'}
        elif(event.value == 'PRESS'):
            # # NOTE: do not set modifiers in this case.. it will mess with hidden checkboxes
            # ref.oskey = event.oskey
            # ref.ctrl = event.ctrl
            # ref.alt = event.alt
            # ref.shift = event.shift
            
            ref.type = event.type
            ref.ascii = event.ascii
            ref.unicode = event.unicode
            
            # if(event.ascii != ''):
            #     ref.char = event.ascii.upper()
            # else:
            #     ref.char = event.type
            # NOTE: use real value, so strange types are identifiable..
            ref.char = event.type
            
            ref.flag = False
            self.tag_redraw()
            return {'FINISHED'}
        
        return {'RUNNING_MODAL'}
    
    def invoke(self, context, event):
        ref = self.get_item(context, )
        if(ref is None):
            return {'CANCELLED'}
        ref.flag = True
        
        context.window_manager.modal_handler_add(self)
        return {'RUNNING_MODAL'}


class SCATTER5_OT_manual_key_config_reset_key(Operator, ):
    bl_idname = "scatter5.manual_key_config_reset_key"
    bl_label = "Reset Key"
    bl_description = ""
    
    name: StringProperty(default="", options={'SKIP_SAVE', 'HIDDEN', })
    
    @classmethod
    def poll(cls, context, ):
        return True
    
    def get_item(self, context, ):
        cfg = preferences()
        ref = None
        for i in cfg.items:
            if(i.name == self.name):
                ref = i
                break
        return ref
    
    def execute(self, context, ):
        o = self.get_item(context, )
        for n in o.__annotations__:
            if(n in {'name', 'label', 'utility', }):
                continue
            o.property_unset(n)
        
        return {'FINISHED'}


classes = (
    SCATTER5_manual_key_item,
    SCATTER5_manual_key_config,
    SCATTER5_OT_manual_key_config_set_key,
    SCATTER5_OT_manual_key_config_reset_key,
)
