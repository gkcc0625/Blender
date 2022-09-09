from math import radians

import bmesh
import bpy
import numpy as np
from bpy.props import *
from bpy.utils import register_class, unregister_class
from mathutils import Vector, geometry
from mathutils.bvhtree import BVHTree as BVH
from collections import defaultdict

_conform_obj_group_name = "Conform Object Gradient Group"
_blend_obj_group_name = "Conform Object Blend Group"
_deform_mod_name = 'Conform Deformation'
_deform_shrinkwrap_mod_name = 'Conform Shrinkwrap'
_transfer_mod_name = "Conform Object Normal Transfer"
_subd_mod_name = "Conform Object Subdivisions"
in_use = False


def translate(value, leftMin, leftMax, rightMin, rightMax):
    
    # Figure out how 'wide' each range is
    leftSpan = leftMax - leftMin
    rightSpan = rightMax - rightMin

    # Convert the left range into a 0-1 range (float)
    if leftSpan > 0:
        valueScaled = float(value - leftMin) / float(leftSpan)
    else:
        valueScaled = rightMin

    # Convert the 0-1 range into a value in the right range.
    return rightMin + (valueScaled * rightSpan)

def create_vertex_group(source_obj, group_name, gradient_type, gradient_start, gradient_end):

    bm = bmesh.new()
    mesh = source_obj.data
    bm.from_mesh(mesh)

    if group_name not in source_obj.vertex_groups:
        group = source_obj.vertex_groups.new(name=group_name)
    else:
        group = source_obj.vertex_groups.get(group_name)

    index_weight_map = {}
    max_vert_pos = max([v.co.z for v in bm.verts])
    min_vert_pos = min([v.co.z for v in bm.verts])

    # max_vert_pos = np.interp(self.gradient_end, [0,1], [min_vert_pos, max_vert_pos])
    min_vert_pos_trans = translate(gradient_start, 0, 1, min_vert_pos, max_vert_pos)
    max_vert_pos_trans = translate(gradient_end, 0, 1, min_vert_pos, max_vert_pos)
    
    for v in bm.verts:
        if gradient_type == 'LINEAR' and min_vert_pos_trans != max_vert_pos_trans:
            index_weight_map[v.index] =  translate(v.co.z, min_vert_pos_trans, max_vert_pos_trans, 1,0)
        else:
            gradient_point = translate(v.co.z, min_vert_pos, max_vert_pos, 0, 1)
            if gradient_point < gradient_end:
                index_weight_map[v.index] = 1
            else:
                index_weight_map[v.index] = 0

    # go through each vert and lerp in terms of vertex position
    group_index = source_obj.vertex_groups[group.name].index
    for v in mesh.vertices:
        group.add([v.index], index_weight_map[v.index], 'REPLACE' )
    
    mesh.update()

    bm.free()

    return group
    
def get_target_obj(source_obj):
    if _deform_shrinkwrap_mod_name in source_obj.modifiers:
        deform_mod = source_obj.modifiers[_deform_shrinkwrap_mod_name]
        target_obj = deform_mod.target
        return target_obj
    grid_object = get_grid_obj(source_obj)
    if grid_object:
        for mod in grid_object.modifiers:
            if mod.type == 'SHRINKWRAP':
                target_obj = mod.target
                return target_obj
    return None

def get_grid_obj(source_obj):
    if _deform_mod_name in source_obj.modifiers:
        mod = source_obj.modifiers[_deform_mod_name]
        grid_object = mod.target
        return grid_object
    return None

class CONFORMOBJECT_OT_ToggleGridSnap(bpy.types.Operator):
    """Toggle Surface Blender's Snapping settings when moving an object"""
    bl_idname = "conform_object.toggle_snapping"
    bl_label = "Toggle Surface Snapping"

    bl_options = {'INTERNAL', 'UNDO'}

    def execute(self, context):
        context.scene.tool_settings.use_snap = not context.scene.tool_settings.use_snap
        if context.scene.tool_settings.use_snap:
            context.scene.tool_settings.snap_elements = {'FACE'}
        else:
            context.scene.tool_settings.snap_elements = {'INCREMENT'}
        context.scene.tool_settings.use_snap_align_rotation = context.scene.tool_settings.use_snap
        context.scene.tool_settings.use_snap_project = context.scene.tool_settings.use_snap
        return {'FINISHED'}

class CONFORMOBJECT_OT_Dig(bpy.types.Operator):
    """Dig Object"""
    bl_idname = "conform_object.dig"
    bl_label = "Dig Object"

    bl_options = {'REGISTER', 'UNDO', 'PRESET'}

    
    thickness : FloatVectorProperty(
            name="Thickness X/Y/Z",
            description="Thickness of dug object",
            default=[0.1, 0.1, 0],
            step=1,
            precision=4
            )

    @classmethod
    def poll(cls, context):
        return context.active_object is not None and len(context.selected_objects) > 1 \
                and len([o for o in context.selected_objects if o.type == 'MESH']) == len(context.selected_objects)


    def draw(self, context):
        layout = self.layout
        col = layout.column()
        col.prop(self, 'thickness')

    def execute(self, context):

        target_obj = context.active_object
        source_objs = [obj for obj in context.selected_objects if obj != context.active_object]

        for source_obj in source_objs:
            # make a copy of the object

            new_obj = source_obj.copy()
            new_obj.data = source_obj.data.copy()
            new_obj.animation_data_clear()
            context.collection.objects.link(new_obj)

            bm = bmesh.new()
            bm.from_mesh(new_obj.data)

            for v in bm.verts:
                v.co = v.co + (Vector((v.normal.x * self.thickness[0], v.normal.y * self.thickness[1], v.normal.z * self.thickness[2])))
            bm.to_mesh(new_obj.data)

            bm.free()

            new_obj.display_type = 'WIRE'

            mod = target_obj.modifiers.new(name="Dig Boolean", type="BOOLEAN")

            mod.object = new_obj
            mod.operation = 'DIFFERENCE'




        return {'FINISHED'}

mod_items = []

class CONFORMOBJECT_OT_Conform(bpy.types.Operator):
    """Conform Object"""
    bl_idname = "conform_object.conform"
    bl_label = "Conform Object"

    bl_options = {'REGISTER', 'UNDO', 'PRESET'}


    conform_type : EnumProperty(items= (('GRID', 'Grid', ''),
                                        ('SHRINKWRAP', 'Shrinkwrap', '')),
                                        name = "Method", default='GRID')



    make_copy :  BoolProperty (
            name="Make Copy",
            description="Make a Copy of the Source Object)",
            default=False
            )

    collapse_modifiers :  BoolProperty (
            name="Collapse Modifiers",
            description="Collapse the modifiers on the Source Object (Useful for when complex modifiers are involved)",
            default=False
            )

    deform_modifier_pos : EnumProperty(items= (('START', 'Start', ''),
                                        ('BEFORE', 'Before', ''),
                                        ('END', 'End', '')),
                                        name = "Deform Modifier Postion", default='END')

    def get_modifiers(self, context):
        global mod_items
        mod_items = []
        mod_items.append(('NONE', 'Choose Modifier', ''))
        mods = [m for m in context.active_object.modifiers if m.name not in [_deform_shrinkwrap_mod_name, _deform_mod_name]]
        i = 0
        for mod in mods:
            mod_items.append((mod.name, mod.name, ''))
            i+=1
        return mod_items



    deform_before_mod : EnumProperty(items=get_modifiers,
                                        name = "Modifier")

    falloff : FloatProperty(
            name="Interpolation Falloff",
            description="Controls how much nearby polygons influence deformation",
            default=4.000,
            step=1,
            precision=4,
            min = 2,
            max = 16
            )

    vertical_subdivisions : IntProperty(
            name="Grid Vertical Subdivisions",
            description="Number of vertical subdivisions for grid",
            default=20,
            min = 0
        )

    source_object_offset : FloatProperty(
            name="Offset",
            description="Amount of offset from the surface of the target object",
            default=0,
            step=1,
            precision=4
            )

    hide_grid : BoolProperty (
            name="Hide Grid",
            description="Hide the deformation grid that is used to form the deformation",
            default=True
            )

    grid_transform_x : FloatProperty(
            name="Grid X",
            description="Relative X location of Deformation Grid",
            default=0,
            step=1,
            precision=4
            )


    grid_transform_y : FloatProperty(
            name="Grid Y",
            description="Relative Y location of Deformation Grid",
            default=0,
            step=1,
            precision=4
            )

    grid_transform_z : FloatProperty(
            name="Grid Z",
            description="Relative Z location of Deformation Grid",
            default=0,
            step=1,
            precision=4,
            min=0
            )

    grid_size_x : FloatProperty(
            name="Grid Scale X",
            description="Width of Deformation Grid",
            default=1,
            step=1,
            precision=4,
            min=0
            )

    grid_rotation : FloatProperty(
            name="Grid Rotation",
            description="Z Rotation of Deformation Grid",
            default=0,
            precision=4
            )


    grid_size_y : FloatProperty(
            name="Grid Scale Y",
            description="Height of Deformation Grid",
            default=1,
            step=1,
            precision=4
            )

    parent_grid_to_source :  BoolProperty (
            name="Parent Deform Grid to Source",
            description="Parent the deformation grid to the original source object, useful if you wish to move the object later.",
            default=True
            )


    place_mod_at_start : BoolProperty (
            name="Deform Modifier at Start",
            description="Place the Surface Deform Modifier at the start of the start of the modifier stack",
            default=False
        )

    is_graduated : BoolProperty (
            name = "Gradient Effect",
            description = "Restrict the effect from the bottom to the top",
            default = True
    )

    gradient_type : EnumProperty(items= (('LINEAR', 'Linear', ''),
                                        ('CONSTANT', 'Constant', '')),
                                        name = "Gradient Type", default='LINEAR', description="Type of gradient to apply.")

    def check_grad_start(self, context):
        if self.gradient_start > self.gradient_end:
            self.gradient_end = self.gradient_start

    gradient_start : FloatProperty(
            name = "Start",
            description = "This is the lower end point of the effect (0=bottom of object)",
            default = 0,
            min=0,
            step=1,
            precision=4,
            update=check_grad_start
    )

    def check_grad_end(self, context):
        if self.gradient_end < self.gradient_start:
            self.gradient_start = self.gradient_end

    gradient_end : FloatProperty(
            name = "End",
            description = "This is the upper end point of the effect (1=top of object)",
            default = 1,
            min=0,
            step=1,
            precision=4,
            update=check_grad_end
    )

    is_blend_normals : BoolProperty (
            name = "Blend normals",
            description = "Blend the normals of the target surface",
            default = False
    )

    blend_gradient_type : EnumProperty(items= (('LINEAR', 'Linear', ''),
                                        ('CONSTANT', 'Constant', '')),
                                        name = "Blend Gradient Type", default='LINEAR', description="Type of gradient to apply.")

    def check_blend_grad_start(self, context):
        if self.blend_gradient_start > self.blend_gradient_end:
            self.blend_gradient_end = self.blend_gradient_start

    blend_gradient_start : FloatProperty(
            name = "Start",
            description = "This is the lower end point of the effect (0=bottom of object)",
            default = 0.0,
            min=0,
            step=1,
            precision=4,
            update=check_blend_grad_start

    )

    def check_blend_grad_end(self, context):
        if self.blend_gradient_end < self.blend_gradient_start:
            self.blend_gradient_start = self.blend_gradient_end

    blend_gradient_end : FloatProperty(
            name = "End",
            description = "This is the upper end point of the effect (1=top of object)",
            default = 0.2,
            min=0,
            step=1,
            precision=4,
            update=check_blend_grad_end
    )

    is_blend_whole_obj : BoolProperty (
            name = "Blend whole object",
            description = "Blend the normals of the entire object",
            default = False
    )

    add_subsurf_simple : BoolProperty (
        name="Add Simple Subdivisions",
        description="Add a simple Subdivision Surface modifier to automatically subdivide the mesh",
        default=False
    )

    subsurf_divisions : IntProperty (
        name="Subdivisions",
        description="Number of Subdivisions",
        default=1,
        min=1,
        soft_max=6
    )

    align_to_face : BoolProperty (
        name="Align Object to Face",
        description="Automatically align the source object to the target object's face.",
        default=False
    )

    source_object_position : EnumProperty(items= (('LOWEST', 'Lowest Point', ''),
                                        ('CENTER', 'Center', '')),
                                        name = "Source Object Point", default='LOWEST', description="Which point on the object is used for placement.")


    def draw(self, context):
        layout = self.layout
        col = layout.column()

        box = col.box()
        box.label(text='Source Object')
        col_props = box.column(align=True)

        col_props.separator()

        # col_props.label(text="Type:")
        col_props.row().prop(self, 'conform_type')

        col_props.separator()

        col_props.prop(self, "is_graduated")
        col_grad_props = col_props.column()
        col_grad_props.enabled = self.is_graduated
        
                
        col_grad_props.prop(self, "gradient_type", text="")

        row_grad_props = col_grad_props.row(align=True)
        if self.gradient_type == 'LINEAR':
            row_grad_props.prop(self, "gradient_start", text="Start")
        row_grad_props.prop(self, "gradient_end", text="End")

        col_props.separator()

        col_props.prop(self, "is_blend_normals")
        col_blend_props = col_props.column()
        col_blend_props.enabled = self.is_blend_normals

        
        col_blend_props.prop(self, "blend_gradient_type", text="")
        
        
        col_blend_grad_end = col_blend_props.column()
        col_blend_grad_end.enabled = not self.is_blend_whole_obj

        row_blend_grad_end = col_blend_grad_end.row(align=True)
        if self.blend_gradient_type == 'LINEAR':
            row_blend_grad_end.prop(self, "blend_gradient_start")
        row_blend_grad_end.prop(self, "blend_gradient_end")

        col_is_blend_whole_obj = col_blend_props.column()
        col_is_blend_whole_obj.prop(self, "is_blend_whole_obj")

        col_props.separator()

        col_props.prop(self, 'source_object_offset')
    

        col_props.separator()
        col_props.prop(self, 'align_to_face')

        col_props.separator()
        col_props.label(text="Positioning: ")
        col_props.prop(self, 'source_object_position', text="")

        col_props.separator()
        col_props.prop(self, 'add_subsurf_simple')
        col_props_subd = col_props.column()
        col_props_subd.enabled = self.add_subsurf_simple
        col_props_subd.prop(self, 'subsurf_divisions')

        col_props.separator()
        col_props.prop(self, 'collapse_modifiers')
        
        col_props.separator()
        col_props.label(text="Deform Modifier Position: ")
        row_mod_pos_props = col_props.row()
        row_mod_pos_props.prop(self, 'deform_modifier_pos', text="")
        if self.deform_modifier_pos == 'BEFORE':
            row_mod_pos_props.prop(self, 'deform_before_mod', text="")

        if self.conform_type == "GRID":
            box = col.box()
            box.label(text='Deformation Grid')
            col_props = box.column(align=True)
            col_props.prop(self, 'hide_grid')

            col_props.prop(self, 'vertical_subdivisions', text="Grid Subdivisions")

            col_props.prop(self, 'grid_transform_x') 
            col_props.prop(self, 'grid_transform_y') 
            col_props.prop(self, 'grid_transform_z') 
            col_props.prop(self, 'grid_size_x') 
            col_props.prop(self, 'grid_size_y')
            col_props.prop(self, 'grid_rotation')
            col_props.prop(self, 'falloff')
        elif self.conform_type == "SHRINKWRAP":
            pass

    @classmethod
    def poll(cls, context):
        return context.active_object is not None and len(context.selected_objects) > 1 \
                and len([o for o in context.selected_objects if o.type == 'MESH']) == len(context.selected_objects)


    def invoke(self, context, event):
        return self.execute(context)


    def execute(self, context):
        

        # for source_obj in context.selected_objects:
        #     conform_undo(source_obj, context)


        target_obj = context.active_object
        source_objs = [obj for obj in context.selected_objects if obj != context.active_object]
        old_active = context.view_layer.objects.active

        for source_obj in source_objs:
        
            context.view_layer.objects.active = target_obj

            collection = source_obj.users_collection[0] if len(source_obj.users_collection) else context.collection

            # create a copy of this source object for processing
            if self.make_copy:
                source_obj_name = source_obj.name + " Conformed"
                source_obj = source_obj.copy()
                source_obj.name = source_obj_name
                source_obj.data = source_obj.data.copy()
                source_obj.animation_data_clear()
                collection.objects.link(source_obj)
            
            conform_undo(source_obj, context)
            source_obj.conform_object.is_conform_obj = False
            source_obj.conform_object.is_conform_shrinkwrap = False


            if self.collapse_modifiers:
                old_data = source_obj.data
                source_object_data = bpy.data.meshes.new_from_object(source_obj.evaluated_get(context.evaluated_depsgraph_get()))
                source_obj.modifiers.clear()
                source_obj.data = source_object_data
                bpy.data.meshes.remove(old_data)
        

            # Move source to nearest point on target, projecting down
            target_object_data = bpy.data.meshes.new_from_object(target_obj.evaluated_get(context.evaluated_depsgraph_get()))
            bm = bmesh.new()
            bm.from_mesh(target_object_data)
            bvh = BVH.FromBMesh(bm)

            # get down vector for source object.
            down_vec = Vector((0,0,-1))
            down_vec.rotate(source_obj.rotation_euler)

            # ray cast this to the target object.
            target_matrix = target_obj.matrix_world

            local_highest = Vector((0,0, max([v.co.z for v in source_obj.data.vertices])))
            local_lowest = Vector((0,0, min([v.co.z for v in source_obj.data.vertices])))
            local_origin = Vector((0,0,0))

            ray_origin = target_matrix.inverted() @ (source_obj.matrix_world @ local_highest)
            ray_direction = target_matrix.inverted().to_3x3() @ down_vec

            location, normal, face_index, distance = bvh.ray_cast(ray_origin, ray_direction)


            bm.free()
            bpy.data.meshes.remove(target_object_data)

            if not location:
                self.report({'ERROR'}, "The bottom of the source object is not pointing towards the target object.\n See 'Tips and Troubleshooting' at conform-object-docs.readthedocs.io")
                return {'CANCELLED'}

            world_location = target_obj.matrix_world @ location
            source_object_world_offset = ((source_obj.matrix_world @ local_origin) - (source_obj.matrix_world @ local_lowest)).length



            # offset the location by the height of the source object.
            source_object_height = source_obj.dimensions.z
            up_vec = Vector((0,0,1))
            up_vec.rotate(source_obj.rotation_euler)
            original_location = source_obj.location.copy()
            source_obj.location = world_location + (source_object_world_offset *  up_vec )


            source_obj.conform_object.original_location = original_location

            # rotate object to position of normal.
            if self.align_to_face:
                rot_diff = up_vec.rotation_difference((target_obj.rotation_euler.to_matrix() @ normal).to_3d())
                source_obj.rotation_euler.rotate(rot_diff.to_euler())


            context.view_layer.update()


            # make the source object the active object.
            context.view_layer.objects.active = source_obj




            # Add a subdivision modifier if necessay
            if self.add_subsurf_simple:
                if _subd_mod_name not in source_obj.modifiers:
                    mod = source_obj.modifiers.new(_subd_mod_name, 'SUBSURF')
                else:
                    mod = source_obj.modifiers.get(_subd_mod_name)
                mod.subdivision_type = 'SIMPLE'
                mod.levels = self.subsurf_divisions

            # offset the source object from the surface if necessary.
            center_offset = 0 if self.source_object_position == 'LOWEST' else -source_object_world_offset

            source_obj.location = source_obj.location + (self.source_object_offset + center_offset) * up_vec


            context.view_layer.update()

            if self.conform_type == 'GRID':

                conform_grid_obj = self.create_grid(source_obj, collection)
                conform_grid_obj.location = conform_grid_obj.location + ((self.source_object_offset + center_offset) *  -up_vec )

                # Add a Surface Deform modifier to the source object and set the grid as the deform object and bind it.
                if _deform_mod_name not in source_obj.modifiers:
                    mod = source_obj.modifiers.new(_deform_mod_name, 'SURFACE_DEFORM')
                else:
                    mod = source_obj.modifiers.get(_deform_mod_name)
                mod.target = conform_grid_obj
                mod.falloff = self.falloff

               
                if self.place_mod_at_start:
                    bpy.ops.object.modifier_move_to_index(modifier=_deform_mod_name, index=0)

                # if graduated, create the graduated vertex group and assign it to the modifier.False
                if self.is_graduated:

                    group = create_vertex_group(source_obj, _conform_obj_group_name, self.gradient_type, self.gradient_start, self.gradient_end)
                    mod = source_obj.modifiers.get(_deform_mod_name)
                    mod.vertex_group = group.name

            elif self.conform_type == "SHRINKWRAP":

                # add the shrinkwrap modifier and set it to the target object
                if _deform_shrinkwrap_mod_name not in source_obj.modifiers:
                    mod = source_obj.modifiers.new(_deform_shrinkwrap_mod_name, 'SHRINKWRAP')
                else:
                    mod = source_obj.modifiers.get(_deform_shrinkwrap_mod_name)
                
                mod.target = target_obj
                mod.offset = self.source_object_offset

                if self.is_graduated:

                    group = create_vertex_group(source_obj, _conform_obj_group_name, self.gradient_type, self.gradient_start, self.gradient_end)
                    mod = source_obj.modifiers.get(_deform_shrinkwrap_mod_name)
                    mod.vertex_group = group.name

            
            # position the modifier if needed.
            if self.deform_modifier_pos == 'START':
                while source_obj.modifiers.find(mod.name) != 0:
                    bpy.ops.object.modifier_move_up(modifier=mod.name)
            elif self.deform_modifier_pos == 'BEFORE':
                if self.deform_before_mod and self.deform_before_mod != 'NONE':
                    target_mod_name = self.deform_before_mod
                    while source_obj.modifiers.find(target_mod_name) < source_obj.modifiers.find(mod.name):
                        bpy.ops.object.modifier_move_up(modifier=mod.name)


            if self.is_blend_normals:

                source_obj.data.use_auto_smooth = True

                if _transfer_mod_name not in source_obj.modifiers:
                    mod = source_obj.modifiers.new(_transfer_mod_name, 'DATA_TRANSFER')
                else:
                    mod = source_obj.modifiers.get(_transfer_mod_name)
                mod.object = None
                mod.object = target_obj
                mod.use_loop_data = True
                mod.data_types_loops = {'CUSTOM_NORMAL'}

                if not self.is_blend_whole_obj:
                    group = create_vertex_group(source_obj, _blend_obj_group_name, self.blend_gradient_type, self.blend_gradient_start, self.blend_gradient_end)

                    mod.vertex_group = group.name

                source_obj.data.update()

            if self.conform_type == 'GRID':

                # Now add a shrinkwrap modifer to the grid object.
                shrink_mod_name = 'Conformation Shrink Wrap'
                if shrink_mod_name not in conform_grid_obj.modifiers:
                    mod = conform_grid_obj.modifiers.new(shrink_mod_name, 'SHRINKWRAP')
                else:
                    mod = conform_grid_obj.modifiers.get(shrink_mod_name)
                    mod.target = None
                    bpy.ops.object.surfacedeform_bind(modifier=_deform_mod_name)

                bpy.ops.object.surfacedeform_bind(modifier=_deform_mod_name)

                mod.target = target_obj
                mod.wrap_method = 'PROJECT'
                mod.use_negative_direction = True
                mod.use_positive_direction = True

                # hide the grid (optionally)
                conform_grid_obj.hide_set(self.hide_grid) # EYE icon
                conform_grid_obj.hide_viewport = self.hide_grid # MONITOR icon
                conform_grid_obj.hide_render = self.hide_grid # RENDER icon

            
                context.view_layer.update() 
                # make grid child of source object
                if self.parent_grid_to_source:
                    conform_grid_obj.parent = source_obj
                    conform_grid_obj.matrix_parent_inverse = source_obj.matrix_world.inverted()

                conform_grid_obj.conform_object.is_grid_obj = True
                source_obj.conform_object.is_conform_shrinkwrap = False

            elif self.conform_type == 'SHRINKWRAP':
                source_obj.conform_object.is_conform_shrinkwrap = True

            source_obj.conform_object.is_conform_obj = True
                
            


        return {'FINISHED'}

    def create_grid(self, source_obj, collection):
        # create a grid object directly below.
        grid_obj = get_grid_obj(source_obj)
        if grid_obj and grid_obj in source_obj.children:
            conform_grid_obj = grid_obj
            mesh = conform_grid_obj.data
            bm = bmesh.new()
            bm.from_mesh(mesh)
            bm.clear()
        else:
            mesh = bpy.data.meshes.new("Conform Grid Mesh")
            conform_grid_obj = bpy.data.objects.new(source_obj.name + " Conform Grid", mesh)
            collection.objects.link(conform_grid_obj)
            bm = bmesh.new()
            bm.from_mesh(mesh)

        conform_grid_obj.conform_object.is_grid_obj = False

        # get bounds of source object.
        local_verts = [Vector(v[:]) for v in source_obj.bound_box]

        min_x = min(v.x for v in local_verts)
        min_y = min(v.y for v in local_verts)
        min_z = min(v.z for v in local_verts)

        max_x = max(v.x for v in local_verts)
        max_y = max(v.y for v in local_verts)

        # first, create a single face of this size.
        vert0 = bm.verts.new(Vector((   min_x,   min_y,    0)))
        vert1 = bm.verts.new(Vector((   min_x,   max_y,    0)))
        vert2 = bm.verts.new(Vector((   max_x,   max_y,    0)))
        vert3 = bm.verts.new(Vector((   max_x,   min_y,    0)))
        
        face = bm.faces.new([vert0, vert1, vert2, vert3])


        # edge split horizontal and vertical.
        first_loop = face.loops[0]
        horizontal_edges = [first_loop.edge, first_loop.link_loop_next.link_loop_next.edge]
        result = bmesh.ops.subdivide_edges(bm, edges=list(set(horizontal_edges)), cuts=self.vertical_subdivisions, use_grid_fill=True, use_only_quads=True)

        vertical_edges = []
        for f in bm.faces:
            second_loop = f.loops[0].link_loop_next
            vertical_edges.append(second_loop.edge)
            vertical_edges.append(second_loop.link_loop_next.link_loop_next.edge)

        result = bmesh.ops.subdivide_edges(bm, edges=list(set(vertical_edges)), cuts=self.vertical_subdivisions, use_grid_fill=True, use_only_quads=False)


        bm.to_mesh(mesh)
        bm.free()            
        
        lowest_pt = min([v.co.z for v in source_obj.data.vertices])

        local_origin = Vector((0,0,lowest_pt))
        local_origin.x += self.grid_transform_x
        local_origin.y += self.grid_transform_y
        local_origin.z += self.grid_transform_z


        origin = source_obj.matrix_world @ local_origin

        
        conform_grid_obj.location = origin

        conform_grid_obj.rotation_euler = source_obj.rotation_euler
        conform_grid_obj.rotation_euler.rotate_axis("Z", radians(self.grid_rotation))
        conform_grid_obj.scale = source_obj.scale
        conform_grid_obj.scale.x *= self.grid_size_x
        conform_grid_obj.scale.y *= self.grid_size_y

        conform_grid_obj.show_wire = True
        conform_grid_obj.show_all_edges = True
        conform_grid_obj.show_in_front = True
        conform_grid_obj.display_type = 'WIRE'

        return conform_grid_obj


def apply_modifiers(obj):
    ctx = bpy.context.copy()
    ctx['object'] = obj
    for _, m in enumerate(obj.modifiers):
        try:
            ctx['modifier'] = m
            bpy.ops.object.modifier_apply(ctx, modifier=m.name)
        except RuntimeError:
            print(f"Error applying {m.name} to {obj.name}, removing it instead.")
            obj.modifiers.remove(m)

    for m in obj.modifiers:
        obj.modifiers.remove(m)

def apply_modifier(obj, m):
    ctx = bpy.context.copy()
    ctx['object'] = obj
    try:
        ctx['modifier'] = m
        bpy.ops.object.modifier_apply(ctx, modifier=m.name)
    except RuntimeError:
        print(f"Error applying {m.name} to {obj.name}, removing it instead.")
        obj.modifiers.remove(m)



def conform_undo(source_obj, context, remove_grid=True, set_active=True):
    if not source_obj.conform_object.is_conform_obj:
        return

    target_obj = get_target_obj(source_obj)

    #remove subdivision modifier.
    if _subd_mod_name in source_obj.modifiers:
        source_obj.modifiers.remove(source_obj.modifiers[_subd_mod_name])

    #remove the deform modifier.
    grid_object = None
    if _deform_mod_name in source_obj.modifiers:
        mod = source_obj.modifiers[_deform_mod_name]
        grid_object = mod.target
        source_obj.modifiers.remove(mod)

    #remove the transfer modifier.
    if _transfer_mod_name in source_obj.modifiers:
        source_obj.modifiers.remove(source_obj.modifiers[_transfer_mod_name])

    # remove shrinkwrap modifier if preset. 
    if _deform_shrinkwrap_mod_name in source_obj.modifiers:
        source_obj.modifiers.remove(source_obj.modifiers[_deform_shrinkwrap_mod_name])


    # # remove any related vertex groups.
    if _conform_obj_group_name in source_obj.vertex_groups:
        # only perform this is the object has not other data instances.
        result = defaultdict(list)
        for obj in [o for o in bpy.data.objects if o.type == 'MESH']:
            result[obj.data].append(obj)
        if len(result[source_obj.data]) <= 1:
            source_obj.vertex_groups.remove(source_obj.vertex_groups[_conform_obj_group_name])

    #remove grid object.
    if grid_object and remove_grid:
        # check all other objects in the scene to see if this is being used elsewhere.
        found_other_grid = False
        for obj in bpy.data.objects:
            for mod in obj.modifiers:
                if mod.name == _deform_mod_name and mod.target == grid_object:
                    found_other_grid = True
                    break

        if not found_other_grid:
            data_to_remove = grid_object.data
            bpy.data.objects.remove(grid_object)
            bpy.data.meshes.remove(data_to_remove)

    if set_active and target_obj and target_obj.name in bpy.data.objects:
        try:
            context.view_layer.objects.active = target_obj
        except RuntimeError:
            pass

    # reset to original location
    # source_obj.location = source_obj.conform_object.original_location

    source_obj.conform_object.is_conform_obj = False

def conform_apply(source_obj, context):
    if not source_obj.conform_object.is_conform_obj:
        return

    source_obj.conform_object.is_conform_obj = False

    #apply subdivision modifier.
    if _subd_mod_name in source_obj.modifiers:
        apply_modifier(source_obj, source_obj.modifiers[_subd_mod_name])

    #apply the deform modifier.
    grid_object = get_grid_obj(source_obj)
    if _deform_mod_name in source_obj.modifiers:
        mod = source_obj.modifiers[_deform_mod_name]
        apply_modifier(source_obj, mod)

    #apply the transfer modifier.
    if _transfer_mod_name in source_obj.modifiers:
        apply_modifier(source_obj, source_obj.modifiers[_transfer_mod_name])

    # apply shrinkwrap modifier if preset. 
    if _deform_shrinkwrap_mod_name in source_obj.modifiers:
        apply_modifier(source_obj, source_obj.modifiers[_deform_shrinkwrap_mod_name])

    # remove any related vertex groups.
    if _conform_obj_group_name in source_obj.vertex_groups:
        source_obj.vertex_groups.remove(source_obj.vertex_groups[_conform_obj_group_name])

    # remove any related vertex groups.
    if _blend_obj_group_name in source_obj.vertex_groups:
        source_obj.vertex_groups.remove(source_obj.vertex_groups[_blend_obj_group_name])

    #remove grid object.
    if grid_object:
        # check all other objects in the scene to see if this is being used elsewhere.
        try:
            data_to_remove = grid_object.data
            bpy.data.objects.remove(grid_object)
            bpy.data.meshes.remove(data_to_remove)
        except ReferenceError:
            pass
    



class CONFORMOBJECT_OT_ConformUndo(bpy.types.Operator):
    """Conform Object"""
    bl_idname = "conform_object.conform_undo"
    bl_label = "Undo Conform Object"

    bl_options = {'REGISTER', 'UNDO'}

    @classmethod
    def poll(cls, context):
        return context.selected_objects and len([o for o in context.selected_objects if o.conform_object.is_conform_obj])


    def execute(self, context):
        source_objs = [o for o in context.selected_objects if o.conform_object.is_conform_obj]
        for source_obj in source_objs:
            conform_undo(source_obj, context)
            

        return {'FINISHED'}

class CONFORMOBJECT_OT_ConformApply(bpy.types.Operator):
    """Conform Object"""
    bl_idname = "conform_object.conform_apply"
    bl_label = "Apply Conform Object"

    bl_options = {'REGISTER', 'UNDO'}

    @classmethod
    def poll(cls, context):
        return context.selected_objects and len([o for o in context.selected_objects if o.conform_object.is_conform_obj])


    def execute(self, context):
        source_objs = [o for o in context.selected_objects if o.conform_object.is_conform_obj]
        for source_obj in source_objs:
            conform_apply(source_obj, context)
            
        self.report({'INFO'}, "Conform modifiers have been applied to the object.")
        return {'FINISHED'}



class OBJECT_MT_conform_object(bpy.types.Menu):
    bl_idname = 'OBJECT_MT_conform_object'
    bl_label = 'Conform Object'

    def draw(self, context):
        layout = self.layout
        layout.operator(CONFORMOBJECT_OT_Conform.bl_idname, icon='GP_MULTIFRAME_EDITING')
        layout.operator(CONFORMOBJECT_OT_ConformUndo.bl_idname, icon='MOD_INSTANCE')
        layout.operator(CONFORMOBJECT_OT_ConformApply.bl_idname, icon='MOD_THICKNESS')
        layout.separator()
        layout.operator(CONFORMOBJECT_OT_ToggleGridSnap.bl_idname, icon='SNAP_FACE')
        
        # layout.operator(CONFORMOBJECT_OT_Dig.bl_idname)






classes = [
    CONFORMOBJECT_OT_Conform,
    CONFORMOBJECT_OT_ConformUndo,
    CONFORMOBJECT_OT_ConformApply,
    CONFORMOBJECT_OT_ToggleGridSnap,
    CONFORMOBJECT_OT_Dig,
    OBJECT_MT_conform_object]



def menu_func(self, context):
    self.layout.menu(OBJECT_MT_conform_object.bl_idname)

def register():
    for cls in classes:
        register_class(cls)

    bpy.types.VIEW3D_MT_object.append(menu_func)
    bpy.types.VIEW3D_MT_object_context_menu.append(menu_func)
    


def unregister():
    bpy.types.VIEW3D_MT_object_context_menu.remove(menu_func)
    bpy.types.VIEW3D_MT_object.remove(menu_func)

    for cls in classes:
        unregister_class(cls)
