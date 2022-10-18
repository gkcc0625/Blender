# Copyright (C) 2022 Thomas Hoppe (h0bB1T). All rights reserved.
#
# Unauthorized copying of this file via any medium is strictly prohibited.
# Proprietary and confidential.

from typing import List, Tuple
import bpy

from bpy.types import Operator, UILayout
from bpy.props import StringProperty

from ..properties import Properties
from ..utils.io import run_blender
from ..registries.config_registry import ConfigRegistry
from ..registries.resource_lists_registry import ResourceListsRegistry
from ..awp.shared import auto_place, bounding_box, remove_duplicate_images
from ..awp.utils import update_asset_browser


class ASSET_OT_multi_purpose(Operator):
    """
    Agree initial notice.
    """
    bl_idname = 'awp.multi_purpose'
    bl_label = ''
    bl_description = ''
    bl_options = {'REGISTER', 'UNDO'}


    mode: StringProperty()
    param0: StringProperty()


    def __selected_meshes(self) -> List[bpy.types.Object]:
        return [ o for o in bpy.context.selected_objects if o.type == 'MESH' ]


    def __restore_selected(self, objs: List[bpy.types.Object]):
        [ o.select_set(o in objs) for o in bpy.context.selectable_objects ]


    def __select_only(self, obj: bpy.types.Object):
        [ o.select_set(False) for o in bpy.context.selectable_objects ]
        obj.select_set(True)
        #bpy.context.view_layer.objects.active = obj


    def __str_to_vec(self, pos: str) -> Tuple[float, float, float]:
        if pos == 'C': return (0, 0, 0)
        if pos == '-X': return (-1, 0, 0)
        if pos == '-Y': return (0, -1, 0)
        if pos == '-Z': return (0, 0, -1)
        if pos == '+X': return (1, 0, 0)
        if pos == '+Y': return (0, 1, 0)
        if pos == '+Z': return (0, 0, 1)


    @classmethod
    def description(cls, context, properties):
        return {
            'agree': 'I hereby agree that I\'ve read and understand this Notice.',
            'auto_place': 'Automatically place all Asset Objects in a Grid',
            'open_asset': f'Open Asset File \'{properties.param0}\' in new Blender Instance',
            'refresh_lib': 'Refresh Assets in Asset Browser',
            'img_cleanup': 'Remove duplicate Images in current Scene',
            'update_res_lists': 'Update Library and Catalog Files',
            'update_origin': f'Set Origin to Object \'{properties.param0}\' of selected Meshes',
            'rotate_90': f'Rotate selected Objects individually by 90° on selected Axis (\'{properties.param0}\')',
            'apply': 'Apply Transform into Mesh Data',
            'library_override_selected': 'Convert selected Object into Library Overrides',
            'library_override': 'Create Library Override to be able to move Object',
        }.get(properties.mode, '??')


    def execute(self, context: bpy.context):
        props = Properties.get()
        if self.mode == 'invoke_place':
            bpy.ops.awp.object_placer(
                'INVOKE_DEFAULT', 
                placemode='place', 
                quick=props.place_quick, 
                create_copy=props.place_create_copy, 
                linked_copy=props.place_linked_copy,
                auto_parent=props.place_auto_parent,
            )
            return {'FINISHED'}
        elif self.mode == 'invoke_replace':
            bpy.ops.awp.object_placer(
                'INVOKE_DEFAULT', 
                placemode='replace', 
                quick=props.place_quick, 
                create_copy=props.place_create_copy, 
                linked_copy=props.place_linked_copy,
                auto_parent=props.place_auto_parent,
            )
            return {'FINISHED'}            
        elif self.mode == 'agree':
            ConfigRegistry.get().agree()
        elif self.mode == 'auto_place':
            auto_place(float(self.param0))
        elif self.mode == 'open_asset':
            run_blender([ self.param0 ])
        elif self.mode == 'refresh_lib':
            update_asset_browser(context)
        elif self.mode == 'img_cleanup':
            remove_duplicate_images(False)
        elif self.mode == 'update_res_lists':
            ResourceListsRegistry.get().update()
            ResourceListsRegistry.get().update_nodes()
        elif self.mode in [ 'update_origin', 'rotate_90', 'apply' ]:
            # Store selected objects info.
            objs = context.selected_objects
            meshes = self.__selected_meshes()

            if objs and meshes:
                context.view_layer.objects.active = objs[0]

                bpy.ops.object.mode_set(mode='OBJECT')
                old = bpy.context.scene.cursor.location[:]

                if self.mode == 'update_origin':
                    for m in meshes:
                        self.__select_only(m)
                        dim, center = bounding_box([m])
                        vec = self.__str_to_vec(self.param0)
                        bpy.context.scene.cursor.location = (
                            center[0] + (dim[0] / 2) * vec[0],
                            center[1] + (dim[1] / 2) * vec[1],
                            center[2] + (dim[2] / 2) * vec[2],
                        )
                        bpy.ops.object.origin_set(type='ORIGIN_CURSOR')
                elif self.mode == 'rotate_90':
                    for m in meshes:
                        self.__select_only(m)
                        bpy.context.scene.cursor.location = bounding_box([m])[1]
                        dir = 1 if self.param0[0] == '-' else -1
                        bpy.ops.transform.rotate(
                            value=3.1415926 / 2 * dir,
                            orient_axis=self.param0[1],
                            orient_type='CURSOR'
                        )
                elif self.mode == 'apply':
                    for m in meshes:
                        self.__select_only(m)
                        bpy.ops.object.transform_apply(
                            location=self.param0 == 'LOCATION', 
                            rotation=self.param0 == 'ROTATION', 
                            scale=self.param0 == 'SCALE'
                        )
                
                bpy.context.scene.cursor.location = old

            self.__restore_selected(objs)
        elif self.mode == 'library_override_selected':
            convertible = list(bpy.context.selectable_objects)
            for o in convertible:
                if o.library:
                    o.override_create(remap_local_usages=True).select_set(True)
        elif self.mode == 'library_override':
            obj = bpy.context.active_object
            if obj:
                context.view_layer.objects.active = obj.override_create(remap_local_usages=True)

        return {'FINISHED'}


    @staticmethod
    def create_ui(l: UILayout, mode: str, text: str, icon: str, param0: str = ''):
        op = l.operator(ASSET_OT_multi_purpose.bl_idname, text=text, icon=icon if icon else 'NONE') # type: ASSET_OT_multi_purpose
        op.mode = mode
        op.param0 = param0
        return op


    @staticmethod
    def create_ui_agree(l: UILayout):
        ASSET_OT_multi_purpose.create_ui(l, 'agree', 'I Agree', 'CHECKMARK')   


    @staticmethod
    def create_ui_auto_place(l: UILayout, distance: float):
        ASSET_OT_multi_purpose.create_ui(l, 'auto_place', '', 'VIEW_ORTHO', str(distance))      


    @staticmethod
    def create_ui_open_asset(l: UILayout, file: str):
        ASSET_OT_multi_purpose.create_ui(l, 'open_asset', '', 'FILE', file)                    


    @staticmethod
    def create_ui_refresh_lib(l: UILayout):
        ASSET_OT_multi_purpose.create_ui(l, 'refresh_lib', '', 'ASSET_MANAGER')  


    @staticmethod
    def create_ui_img_cleanup(l: UILayout):
        ASSET_OT_multi_purpose.create_ui(l, 'img_cleanup', 'Image Cleanup', 'IMAGE_DATA')   

    @staticmethod
    def create_ui_img_update_res_lists(l: UILayout):
        ASSET_OT_multi_purpose.create_ui(l, 'update_res_lists', '', 'FILE_REFRESH')      


    @staticmethod
    def create_ui_update_origin(l: UILayout, mode: str, text: str, icon: str):
        ASSET_OT_multi_purpose.create_ui(l, 'update_origin', text, None, mode)


    @staticmethod
    def create_ui_rotate_90(l: UILayout, mode: str, text: str, icon: str):
        ASSET_OT_multi_purpose.create_ui(l, 'rotate_90', text, None, mode)  


    @staticmethod
    def create_ui_apply(l: UILayout, mode: str, text: str, icon: str):
        ASSET_OT_multi_purpose.create_ui(l, 'apply', text, icon, mode)                  


    @staticmethod
    def create_ui_library_override_selected(l: UILayout):
        ASSET_OT_multi_purpose.create_ui(l, 'library_override_selected', 'Convert selected Objects to Library Overrides', 'DECORATE_LIBRARY_OVERRIDE')


    @staticmethod
    def create_ui_library_override(l: UILayout):
        ASSET_OT_multi_purpose.create_ui(l, 'library_override', 'Make Library Override', 'LIBRARY_DATA_OVERRIDE')

