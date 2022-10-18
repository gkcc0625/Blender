# Copyright (C) 2022 Thomas Hoppe (h0bB1T). All rights reserved.
#
# Unauthorized copying of this file via any medium is strictly prohibited.
# Proprietary and confidential.

from ast import operator
import bpy

from typing import List, Tuple

from bpy.types import Operator, UILayout
from bpy.props import StringProperty, BoolProperty, FloatProperty

from ..utils.dev import err
from ..utils.blender import set_active_object
from ..properties import Properties
from ..utils.io import run_blender
from ..registries.config_registry import ConfigRegistry
from ..registries.resource_lists_registry import ResourceListsRegistry
from ..awp.shared import auto_place, bounding_box, remove_duplicate_images
from ..awp.utils import update_asset_browser


class ASSET_OT_import_cleaner(Operator):
    """
    Different batch tasks for object and mesh cleanup.
    """
    bl_idname = 'awp.import_cleaner'
    bl_label = ''
    bl_description = ''
    bl_options = {'REGISTER', 'UNDO'}


    # object or mesh
    mode: StringProperty(options={'HIDDEN'})

    # Object related.
    remove_animation_data: BoolProperty(options={'HIDDEN'})
    unparent: BoolProperty(options={'HIDDEN'})
    merge_objects: BoolProperty(options={'HIDDEN'})

    # Mesh related.
    clear_custom_split_normals: BoolProperty(options={'HIDDEN'})
    set_auto_smooth: BoolProperty(options={'HIDDEN'})
    recalculate_normals_outside: BoolProperty(options={'HIDDEN'})
    limited_dissolve: BoolProperty(options={'HIDDEN'})
    join_vertices: BoolProperty(options={'HIDDEN'})

    auto_smooth_angle: FloatProperty(options={'HIDDEN'})
    join_vertices_distance: FloatProperty(options={'HIDDEN'})


    def __restore_selected(self, objs: List[bpy.types.Object]):
        [ o.select_set(o in objs) for o in bpy.context.selectable_objects ]


    def __select_only(self, obj: bpy.types.Object):
        [ o.select_set(False) for o in bpy.context.selectable_objects ]
        obj.select_set(True)    


    @classmethod
    def description(cls, context, properties):
        return {
            'objects': 'Run selected cleanup Options on selected Objects',
            'meshes': 'Run selected cleanup Options on selected Meshes',
        }.get(properties.mode, '??')


    def execute(self, context: bpy.types.Context):
        # Must be in object mode.
        if context.mode != 'OBJECT':
            bpy.ops.object.mode_set(mode='OBJECT')

        # Store selected objects info.
        objs = list(context.selected_objects) # type: List[bpy.types.Object]
        meshes = [ o for o in objs if o.type == 'MESH' ]

        if objs and meshes:
            # Store cursor location.
            old = bpy.context.scene.cursor.location[:]

            try:
                # Run changes on selected objects.
                if self.mode == 'objects':
                    if self.remove_animation_data:
                        for o in objs:
                            o.animation_data_clear()

                    if self.unparent or self.merge_objects:
                        for m in meshes:
                            self.__select_only(m)
                            if m.parent and m.parent.type == 'EMPTY':
                                bpy.ops.object.parent_clear(type='CLEAR_KEEP_TRANSFORM')


                        # Remove all empties
                        empties = [ o for o in objs if o.type == 'EMPTY' ]
                        # Update for later op.
                        objs = [ o for o in objs if o.type != 'EMPTY' ] 
                        for e in empties:
                            bpy.data.objects.remove(e)

                        set_active_object(objs[0])

                        # In case of merge, do the merge and return, as the obj list is invalid.
                        meshes = [ o for o in objs if o.type == 'MESH' ]
                        if self.merge_objects and meshes:
                            # Required for merging.
                            set_active_object(meshes[0])
                            [ o.select_set(True) for o in meshes ]
                            bpy.ops.object.join()
                            bpy.context.scene.cursor.location = old
                            return {'FINISHED'}

                elif self.mode == 'meshes':
                    for m in meshes:
                        self.__select_only(m)

                        if self.clear_custom_split_normals:
                            bpy.ops.mesh.customdata_custom_splitnormals_clear()
                        if self.set_auto_smooth:
                            m.data.use_auto_smooth = True
                            m.data.auto_smooth_angle = self.auto_smooth_angle


                        bpy.ops.object.mode_set(mode='EDIT')
                        bpy.ops.mesh.select_all(action='SELECT')
                        if self.recalculate_normals_outside:
                            bpy.ops.mesh.normals_make_consistent(inside=False)
                        if self.join_vertices:
                            bpy.ops.mesh.remove_doubles(threshold=self.join_vertices_distance)
                        if self.limited_dissolve:
                            bpy.ops.mesh.dissolve_limited()
                        bpy.ops.mesh.select_all(action='DESELECT')
                        bpy.ops.object.mode_set(mode='OBJECT')

            except:
                err('Operation failed')
                self.report({'ERROR'}, 'Operation failed, see Console')

            # Restore cursor location.
            bpy.context.scene.cursor.location = old

        # Restore selection state.
        if context.mode != 'OBJECT':
            bpy.ops.object.mode_set(mode='OBJECT')
        self.__restore_selected(objs)

        return {'FINISHED'}


    @staticmethod
    def create_ui_objects(
        l: UILayout, 
        text: str, 
        icon: str, 
        remove_animation_data: bool = False, 
        unparent: bool = False, 
        merge_objects: bool = False
        ):
        operator = l.operator(ASSET_OT_import_cleaner.bl_idname, text=text, icon=icon) # type: ASSET_OT_import_cleaner
        operator.mode = 'objects'
        operator.remove_animation_data = remove_animation_data
        operator.unparent = unparent
        operator.merge_objects = merge_objects


    @staticmethod
    def create_ui_meshes(
        l: UILayout, 
        text: str, 
        icon: str, 
        clear_custom_split_normals: bool = False,
        set_auto_smooth: bool = False,
        recalculate_normals_outside: bool = False,
        limited_dissolve: bool = False,
        join_vertices: bool = False,
        auto_smooth_angle: float = 0,
        join_vertices_distance: float = 0,
        ):
        operator = l.operator(ASSET_OT_import_cleaner.bl_idname, text=text, icon=icon) # type: ASSET_OT_import_cleaner
        operator.mode = 'meshes'
        operator.clear_custom_split_normals = clear_custom_split_normals
        operator.set_auto_smooth = set_auto_smooth
        operator.recalculate_normals_outside = recalculate_normals_outside
        operator.limited_dissolve = limited_dissolve
        operator.join_vertices = join_vertices
        operator.auto_smooth_angle = auto_smooth_angle
        operator.join_vertices_distance = join_vertices_distance

