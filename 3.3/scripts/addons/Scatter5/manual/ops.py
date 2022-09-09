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
from bpy.types import Operator
from mathutils import Matrix
from mathutils.bvhtree import BVHTree
import bmesh

from .debug import log
# from .manager import SC5Toolbox
from . import manager

from .. resources.translate import translate
from .. ui import templates
from .. utils.str_utils import word_wrap


class SCATTER5_OT_apply_brush(Operator, ):

    bl_idname = "scatter5.manual_apply_brush"
    bl_label = translate("Apply Brush Settings")
    bl_description = translate("Apply Brush Settings to all points")
    bl_options = set()
    
    _allowed = (
        'rotation_brush',
        'scale_brush',
        'scale_grow_shrink_brush',
        'object_brush',
    )
    
    @classmethod
    def poll(cls, context, ):

        try:
            emitter = bpy.context.scene.scatter5.emitter
            target = emitter.scatter5.get_psy_active().scatter_obj
            if(len(target.data.vertices)):
                tool = manager.SC5Toolbox.get()
                if(tool is not None):
                    if(tool.brush_type in cls._allowed):
                        return True
        except Exception as e:
            pass
        return False
    
    def execute(self, context):
        
        tool = manager.SC5Toolbox.get()
        
        try:
            tool.selected = np.ones(len(tool.locations), np.bool, )
            if(tool.brush_type in ('rotation_brush', 'scale_brush', 'scale_grow_shrink_brush', )):
                tool._execute()
            elif(tool.brush_type in ('object_brush', )):
                tool._object()
                tool._store()
            tool.target.data.update()
        except Exception as e:
            import traceback
            traceback.print_exc()
            self.report({'ERROR'}, traceback.format_exc(), )
            return {'CANCELLED'}
        
        return {'FINISHED'}


class SCATTER5_OT_manual_exit(Operator, ):

    bl_idname = "scatter5.manual_exit"
    bl_label = translate("Exit")
    bl_description = translate("Exit")
    bl_options = set()
    
    @classmethod
    def poll(cls, context, ):
        # allow running anytime..
        return True
    
    def execute(self, context):
        try:
            # tool = manager.SC5Toolbox.get()
            manager.SC5Toolbox.set(None, )
        except Exception as e:
            pass
        
        # restart everything..
        manager.deinit()
        manager.init()
        
        return {'FINISHED'}


class SCATTER5_OT_manual_clear(Operator, ):

    bl_idname = "scatter5.manual_clear"
    bl_label = translate("Clear Points")
    bl_description = translate("Clear all points Created")
    bl_options = {'INTERNAL', 'UNDO'}
    
    confirmed: bpy.props.BoolProperty(default=True, options={'SKIP_SAVE', 'HIDDEN', }, )
    
    @classmethod
    def poll(cls, context, ):

        try:
            emitter = bpy.context.scene.scatter5.emitter
            target = emitter.scatter5.get_psy_active().scatter_obj
            if(len(target.data.vertices)):
                return True
        except Exception:
            pass
        return False
    
    def execute(self, context, ):

        emitter = bpy.context.scene.scatter5.emitter
        target = emitter.scatter5.get_psy_active().scatter_obj
        me = target.data
        me.clear_geometry()
        return {'FINISHED'}
    
    def invoke(self, context, event, ):

        if(self.confirmed):
            self.execute(context)
            return {'FINISHED'}
        
        def draw(self, context):
            self.layout.operator("scatter5.manual_clear", text=translate("confirm")).confirmed = True
        
        context.window_manager.popup_menu(draw, title=translate("Clear All Points ?"), icon="TRASH", )
        return {'FINISHED'}


def get_data(o, ):

    # TODO get points `id` attr from here? how???? if we don't have the same ID then instances and seed will vary when importing...
    
    e = bpy.context.scene.scatter5.emitter
    '''
    ps = e.scatter5.get_psy_active()
    v = ps.s_instances_allow
    ps.s_instances_allow = False
    # ng = o.modifiers['Scatter5 Geonode Engine MKI'].node_group
    # a = ng.nodes['s_instances_allow False'].outputs[0]
    # b = ng.nodes['s_instances_allow'].inputs[0]
    # c = ng.nodes['s_instances_allow True'].outputs[0]
    # ng.links.new(a, b)
    # depsgraph = bpy.context.evaluated_depsgraph_get()
    # eo = o.evaluated_get(depsgraph)
    # # # me = eo.data
    # # # me = eo.to_mesh()
    # # bm = bmesh.new()
    # # bm.from_object(eo, depsgraph, cage=False, face_normals=True, )
    # # import uuid
    # # me = bpy.data.meshes.new(str(uuid.uuid1()))
    # # bm.to_mesh(me)
    # # bm.free()
    # me = bpy.data.meshes.new_from_object(eo)
    # vs = np.zeros((len(me.vertices) * 3), dtype=np.float, )
    # me.vertices.foreach_get('co', vs, )
    # vs.shape = (-1, 3, )
    # ps.s_instances_allow = v
    # # ng.links.new(c, b)
    # bpy.data.meshes.remove(me)
    # print(vs)
    usel = []
    uact = bpy.context.view_layer.objects.active
    o.hide_select = False
    for i in bpy.context.scene.objects:
        if(i.select_get()):
            usel.append(i)
        i.select_set(False)
    o.select_set(True)
    bpy.context.view_layer.objects.active = o
    bpy.ops.object.duplicate()
    bpy.ops.object.apply_all_modifiers()
    oo = bpy.context.view_layer.objects.active
    me = oo.data
    vs = np.zeros((len(me.vertices) * 3), dtype=np.float, )
    me.vertices.foreach_get('co', vs, )
    vs.shape = (-1, 3, )
    # print(vs)
    bpy.data.objects.remove(oo, do_unlink=True, )
    bpy.data.meshes.remove(me)
    o.hide_select = True
    for i in usel:
        i.select_set(True)
    bpy.context.view_layer.objects.active = uact
    ps.s_instances_allow = v
    
    from mathutils.kdtree import KDTree
    tree = KDTree(len(vs))
    for i, v in enumerate(vs):
        tree.insert(v, i)
    tree.balance()
    '''
    em = e.matrix_world.copy().inverted()
    
    d = bpy.context.evaluated_depsgraph_get()
    instances = []
    for i in d.object_instances:
        if(i.is_instance):
            if(i.parent.original == o):
                # handle transformed emitter by 'sutracting' its transformation from instance transformation, so they can be trasformed back in nodes
                im = em @ i.matrix_world.copy()
                instances.append((i.object.original, im, ))
    
    l = len(instances)
    loc = np.zeros((l, 3, ), dtype=np.float, )
    rot = np.zeros((l, 3, ), dtype=np.float, )
    sca = np.zeros((l, 3, ), dtype=np.float, )

    for i, v in enumerate(instances):
        b, m = v
        n = b.name
        l, r, s = m.decompose()
        loc[i] = l
        e = r.to_euler('XYZ', )
        rot[i] = (e.x, e.y, e.z, )
        sca[i] = s
    
    '''
    indices = []
    for _, co in enumerate(loc):
        _, ii, _ = tree.find(co)
        indices.append(ii)
    # print(indices)
    loc = loc[indices]
    rot = rot[indices]
    sca = sca[indices]
    '''
    
    return loc, rot, sca


def set_mesh(me, loc=None, rot=None, sca=None, ):

    me.clear_geometry()
    
    from . import brushes
    import copy
    attribute_map = copy.deepcopy(brushes.SCATTER5_OT_manual_base_brush.attribute_map)
    attribute_prefix = str(brushes.SCATTER5_OT_manual_base_brush.attribute_prefix)
    
    for n, t in attribute_map.items():
        nm = '{}{}'.format(attribute_prefix, n)
        a = me.attributes.get(nm)
        if(a is None):
            me.attributes.new(nm, t[0], t[1])
    
    l = len(loc)
    me.vertices.add(l)
    me.vertices.foreach_set('co', loc.flatten(), )
    
    emitter = bpy.context.scene.scatter5.emitter
    psys = emitter.scatter5.particle_systems
    psy_active = emitter.scatter5.get_psy_active()
    
    o = emitter
    m = o.matrix_world
    depsgraph = bpy.context.evaluated_depsgraph_get()
    eo = o.evaluated_get(depsgraph)
    bm = bmesh.new()
    bm.from_object(eo, depsgraph, cage=False, face_normals=True, )
    bm.transform(m)
    bmesh.ops.triangulate(bm, faces=bm.faces, )
    bm.verts.ensure_lookup_table()
    bm.faces.ensure_lookup_table()
    bvh = BVHTree.FromBMesh(bm, epsilon=0.001, )
    bm.free()
    
    rng = np.random.default_rng()
    
    _normal = np.zeros((l, 3), dtype=np.float, )
    for i in range(l):
        _, n, _, _ = bvh.find_nearest(loc[i])
        _normal[i] = n
    
    _rotation = np.array(rot, dtype=np.float, )
    _scale = np.array(sca, dtype=np.float, )
    _index = np.ones(l, dtype=np.int, )
    _id = np.arange(l, dtype=np.int, )
    
    d = {"meth_align_z_local": 1, "meth_align_z_global": 2, "meth_align_z_normal": 0, }
    v = 0
    if(psy_active.s_rot_align_z_method in d.keys()):
        v = d[psy_active.s_rot_align_z_method]
    _private_r_align = np.full(l, v, dtype=np.int, )
    # _private_r_align_vector
    
    d = {"meth_align_y_global": 0, "meth_align_y_local": 1, }
    v = 0
    if(psy_active.s_rot_align_y_method in d.keys()):
        v = d[psy_active.s_rot_align_y_method]
    _private_r_up = np.full(l, v, dtype=np.int, )
    # _private_r_up_vector
    
    _private_r_base = np.full((l, 3), (psy_active.s_rot_add_default.x, psy_active.s_rot_add_default.y, psy_active.s_rot_add_default.z, ), dtype=np.float, )
    _private_r_random = np.full((l, 3), (psy_active.s_rot_add_random.x, psy_active.s_rot_add_random.y, psy_active.s_rot_add_random.z, ), dtype=np.float, )
    # _private_r_random_random = np.ones(l, dtype=np.float, )
    _private_r_random_random = rng.random((l, 3, ), )
    
    _private_s_base = np.full((l, 3), psy_active.s_scale_default_value, dtype=np.float, )
    _private_s_random = np.full((l, 3), psy_active.s_scale_random_factor, dtype=np.float, )
    # _private_s_random_random = np.ones(l, dtype=np.float, )
    _private_s_random_random = rng.random((l, 3, ), )
    
    d = {"random_uniform": 0, "random_vectorial": 1, }
    v = 0
    if(psy_active.s_scale_random_method in d.keys()):
        v = d[psy_active.s_scale_random_method]
    _private_s_random_type = np.full(l, v, dtype=np.int, )
    # _private_s_change
    
    me.attributes['{}normal'.format(attribute_prefix)].data.foreach_set('vector', _normal.flatten(), )
    me.attributes['{}rotation'.format(attribute_prefix)].data.foreach_set('vector', _rotation.flatten(), )
    me.attributes['{}scale'.format(attribute_prefix)].data.foreach_set('vector', _scale.flatten(), )
    
    me.attributes['{}index'.format(attribute_prefix)].data.foreach_set('value', _index.flatten(), )
    me.attributes['{}id'.format(attribute_prefix)].data.foreach_set('value', _id.flatten(), )
    
    me.attributes['{}private_r_align'.format(attribute_prefix)].data.foreach_set('value', _private_r_align.flatten(), )
    me.attributes['{}private_r_up'.format(attribute_prefix)].data.foreach_set('value', _private_r_up.flatten(), )
    me.attributes['{}private_r_base'.format(attribute_prefix)].data.foreach_set('vector', _private_r_base.flatten(), )
    me.attributes['{}private_r_random'.format(attribute_prefix)].data.foreach_set('vector', _private_r_random.flatten(), )
    me.attributes['{}private_r_random_random'.format(attribute_prefix)].data.foreach_set('vector', _private_r_random_random.flatten(), )
    
    me.attributes['{}private_s_base'.format(attribute_prefix)].data.foreach_set('vector', _private_s_base.flatten(), )
    me.attributes['{}private_s_random'.format(attribute_prefix)].data.foreach_set('vector', _private_s_random.flatten(), )
    me.attributes['{}private_s_random_random'.format(attribute_prefix)].data.foreach_set('vector', _private_s_random_random.flatten(), )
    
    me.attributes['{}private_s_random_type'.format(attribute_prefix)].data.foreach_set('value', _private_s_random_type.flatten(), )


class SCATTER5_OT_manual_convert_dialog(Operator, ):

    bl_idname = "scatter5.manual_convert_dialog"
    bl_label = translate("Convert Points to Manual")
    bl_description = translate("Convert Points to Manual")
    bl_options = {'INTERNAL', 'UNDO'}

    @classmethod
    def poll(cls, context, ):

        return (bpy.context.mode == "OBJECT")

    def execute(self, context):

        emitter = bpy.context.scene.scatter5.emitter
        psys = emitter.scatter5.particle_systems
        psy_active = emitter.scatter5.get_psy_active()
        scatter_obj = psy_active.scatter_obj
        
        #s_display_placeholder_scale special actions needed, shall not influence real scale
        _s_display_override = False 
        if psy_active.s_display_allow:
            psy_active.s_display_allow = False
            _s_display_override = True
        
        loc, rot, sca = get_data(scatter_obj)
        set_mesh(scatter_obj.data, loc=loc, rot=rot, sca=sca, )

        # Set all procedural settings to False
        to_disable = [
            "s_scale_default_allow",
            "s_scale_random_allow",
            "s_scale_min_allow",
            "s_scale_mirror_allow",
            "s_scale_shrink_allow",
            "s_scale_grow_allow",
            
            "s_rot_align_z_allow",
            "s_rot_align_y_allow",
            "s_rot_random_allow",
            "s_rot_add_allow",
            "s_rot_tilt_allow",
            
            "s_pattern1_allow",
            "s_pattern2_allow",
            
            "s_push_offset_allow",
            "s_push_dir_allow",
            "s_push_noise_allow",
            "s_push_fall_allow",
            
            "s_abiotic_elev_allow",
            "s_abiotic_slope_allow",
            "s_abiotic_dir_allow",
            "s_abiotic_cur_allow",
            "s_abiotic_border_allow",
            
            "s_proximity_removenear_allow",
            "s_proximity_learnover_allow",
            "s_proximity_outskirt_allow",

            "s_ecosystem_affinity_allow",
            
            "s_wind_wave_allow",
            "s_wind_noise_allow",
        ]
        
        for prop in to_disable:
            setattr(psy_active, prop, False)
        
        # got to manual distribution method
        setattr(psy_active, "s_distribution_method", "manual_all")

        # restore display 
        if _s_display_override:
            psy_active.s_display_allow = True

        #send refresh signal 
        mod = scatter_obj.modifiers.get("Scatter5 Geonode Engine MKI")
        mod.show_viewport = not mod.show_viewport
        mod.show_viewport = not mod.show_viewport
        
        return {'FINISHED'}
    
    def invoke(self, context, event):

        return bpy.context.window_manager.invoke_props_dialog(self)
    
    def draw(self, context):

        layout = self.layout

        layout.separator(factor=0.33)
        word_wrap(layout=layout, alignment="CENTER", active=True, max_char=55, string=translate("This operator will transfer the procedurally generated points to Manual distribution where you will be able to have precise control thanks to the help of the various brushes."),)
        layout.separator(factor=0.33)
        word_wrap(layout=layout, alignment="CENTER", active=True, max_char=55, string=translate("Note that this operator is semi-destructive, as it will turn off most procedural features. Manual mode can handle up to 50.000 points depending on your computer."),)
        layout.separator(factor=0.33)
        word_wrap(layout=layout, alignment="CENTER", active=True, max_char=55, string=translate("Note that manual mode Press 'OK' to proceed to the conversion"),)
            
        layout.separator()

        return None


class SCATTER5_OT_manual_drop(Operator, ):

    bl_idname = "scatter5.manual_drop"
    bl_label = translate("Drop Points to Emitter")
    bl_description = translate("Drop Points to Emitter")
    bl_options = {'INTERNAL', 'UNDO'}
    
    @classmethod
    def poll(cls, context, ):

        emitter = bpy.context.scene.scatter5.emitter
        psy_active = emitter.scatter5.get_psy_active()
        scatter_obj = psy_active.scatter_obj
        return len(scatter_obj.data.vertices) > 0
    
    def execute(self, context):

        emitter = bpy.context.scene.scatter5.emitter
        psys = emitter.scatter5.particle_systems
        psy_active = emitter.scatter5.get_psy_active()
        scatter_obj = psy_active.scatter_obj
        
        import numpy as np
        from ..utils.np_utils import np_apply_transforms, np_global_to_local
        from mathutils import Vector, Quaternion, Euler, Matrix
        
        # Get Points Coordinate on global space
        
        l = len(scatter_obj.data.vertices)
        pts_co = np.zeros((l * 3), dtype=np.float, )
        scatter_obj.data.vertices.foreach_get("co", pts_co, )
        pts_co.shape = (l, 3, )
        
        # array transforms to emitter space
        if(psy_active.s_distribution_space == "global"):
            pts_co = np_apply_transforms(scatter_obj, pts_co)  # local_point_space to global
            pts_co = np_global_to_local(emitter, pts_co)  # global to local_emitter_space
        
        depsgraph = bpy.context.evaluated_depsgraph_get()
        eo = emitter.evaluated_get(depsgraph)
        
        for (vert, co) in zip(scatter_obj.data.vertices, pts_co):
            # adjust direction, UP is not (0,0,-1)
            
            direction = Vector((0, 0, -1)) @ emitter.rotation_euler.to_matrix()
            
            # Get Projected Points fro ray cast
            result, loc, normal, _ = eo.ray_cast(co, direction, depsgraph=depsgraph, )
            
            # if did not intersect just skip
            if not result:
                continue
            
            # adjust points position
            
            # if(psy_active.s_distribution_space=="local"):
            #     loc = emitter.matrix_world @ loc
            #     loc = emitter.scatter_obj.inverted() @ loc
            
            if(psy_active.s_distribution_space == "global"):
                loc = emitter.matrix_world @ loc
            
            # re-arrange vertices position
            vert.co = loc
            
            # TODO: maybe there's a need to update 'manual_normal' ? or other
            
            continue
        
        return {'FINISHED'}


class SCATTER5_OT_manual_switch(Operator, ):

    bl_idname = "scatter5.manual_switch"
    bl_label = translate("Switch")
    bl_description = translate("Switch")
    bl_options = set()
    
    name: bpy.props.StringProperty()
    
    @classmethod
    def poll(cls, context, ):
        # allow running anytime..
        return True
    
    def execute(self, context):
        # DONE: after switch, navigation is not working for a first time because previous brush will catch event and cancel itself, interestingly, new brush does not get event at all..
        # DONE: after switch, one instance of stats is drawn extra, those stats are drawn even after manual edit exit
        
        # find desired system index
        e = bpy.context.scene.scatter5.emitter
        idx = -1
        for i, p in enumerate(e.scatter5.particle_systems):
            if(p.name == self.name):
                idx = i
                break
        if(idx > -1):
            # set index to switch
            e.scatter5.particle_systems_idx = idx
            # re-run active brush operator
            tool = context.workspace.tools.from_space_view3d_mode(context.mode).idname
            from .brushes import get_brush_class_by_brush_type
            brush = get_brush_class_by_brush_type(tool)
            nm = brush.bl_idname.split('.', 1)
            op = getattr(getattr(bpy.ops, nm[0]), nm[1])
            if(op.poll()):
                # i can run next brush (i guess it will always be true since i just artifically ended the same brush)
                
                # old brush..
                t = manager.SC5Toolbox.get()
                t._abort = True
                # remove brush stats now, so i don't have two drawing at the same time..
                manager.SC5Stats.remove(t.target.name, )
                
                # run it again but in different context.. i.e. different target
                op('INVOKE_DEFAULT', )
            else:
                return {'CANCELLED'}
        else:
            return {'CANCELLED'}
        
        return {'FINISHED'}


class SCATTER5_OT_disable_procedural(Operator, ):

    bl_idname = "scatter5.manual_disable_procedural"
    bl_label = translate("Disable All Procedural Settings")
    bl_description = translate("Disable All Procedural Settings")
    bl_options = set()
    
    @classmethod
    def poll(cls, context, ):
        return True
    
    def execute(self, context):
        e = bpy.context.scene.scatter5.emitter
        ps = e.scatter5.get_psy_active()
        ls = ("s_mask_vcol_allow", "s_mask_vg_allow", "s_mask_curve_allow", "s_mask_bitmap_allow", "s_mask_material_allow",
              "s_scale_default_allow", "s_scale_random_allow", "s_scale_min_allow", "s_scale_mirror_allow", "s_scale_shrink_allow", "s_scale_grow_allow",
              "s_rot_align_z_allow", "s_rot_align_y_allow", "s_rot_random_allow", "s_rot_add_allow", "s_rot_tilt_allow",
              "s_pattern1_allow", "s_pattern2_allow",
              "s_abiotic_elev_allow", "s_abiotic_slope_allow", "s_abiotic_dir_allow", "s_abiotic_cur_allow", "s_abiotic_border_allow",
              "s_proximity_removenear_allow", "s_proximity_learnover_allow", "s_proximity_outskirt_allow",
              "s_ecosystem_affinity_allow",
              "s_push_offset_allow", "s_push_dir_allow", "s_push_noise_allow", "s_push_fall_allow",
              "s_wind_wave_allow", "s_wind_noise_allow", )
        for n in ls:
            setattr(ps, n, False)
        
        return {'FINISHED'}


classes = (
    SCATTER5_OT_manual_clear,
    SCATTER5_OT_manual_convert_dialog,
    SCATTER5_OT_manual_exit,
    SCATTER5_OT_apply_brush,
    SCATTER5_OT_manual_drop,
    SCATTER5_OT_manual_switch,
    SCATTER5_OT_disable_procedural,
)
