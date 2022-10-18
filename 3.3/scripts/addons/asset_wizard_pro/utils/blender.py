# Copyright (C) 2022 Thomas Hoppe (h0bB1T). All rights reserved.
#
# Unauthorized copying of this file via any medium is strictly prohibited.
# Proprietary and confidential.

import bpy, addon_utils

from dataclasses import dataclass
from itertools import chain
from typing import Dict, List, Tuple, Union

from bpy_extras import view3d_utils
from mathutils import Vector
import mathutils

from .io import os_path


def asset_wizard_pro_enabled() -> bool:
    return addon_utils.check('asset_wizard_pro')[1]


def shader_node_wizard_enabled() -> bool:
    return addon_utils.check('shader_node_wizard')[1]


def material_wizard_enabled() -> bool:
    return addon_utils.check('material_wizard')[1]


def is_file_saved() -> bool:
    """
    Check if the current .blend is saved (and has a name)
    """
    return bpy.data.is_saved and not bpy.data.is_dirty   


def find_or_load_image(filepath: str, reload: bool = False) -> bpy.types.Image:
    # If image exists, return it, otherwise load new.
    for img in bpy.data.images:
        if not img.name.startswith('__') and \
            os_path(filepath) == os_path(img.filepath):
            if reload:
                img.reload()
            return img
    return bpy.data.images.load(filepath)


@dataclass
class IntersectInfo:
    obj: bpy.types.Object
    local_location: Tuple[float, float, float]
    world_location: Tuple[float, float, float]
    local_normal: Tuple[float, float, float]
    world_normal: Tuple[float, float, float]
    face_index: int


def intersection_at_2d(
    #context: bpy.context,
    region: bpy.types.Region,
    region_data: bpy.types.RegionView3D,
    pos: Tuple[float, float],
    objects: List[bpy.types.Object]
    ) -> List[IntersectInfo]:
    # https://blender.stackexchange.com/questions/271349/select-other-object-while-in-edit-mode

    # Get ray in world coords.
    view_vector = view3d_utils.region_2d_to_vector_3d(region, region_data, pos)
    ray_origin = view3d_utils.region_2d_to_origin_3d(region, region_data, pos)
    #bpy.context.workspace.status_text_set(text=f'{view_vector} -- {ray_origin}')
    ray_target = ray_origin + view_vector

    # Collect hitted objects.
    result_objects = [] # type: List[IntersectInfo]

    # Check all objects.
    for obj in objects:
        if obj.type == 'MESH':
            # Convert ray to object space.
            mtx = obj.matrix_world.copy().inverted()
            ray_origin_obj = mtx @ ray_origin
            ray_target_obj = mtx @ ray_target
            ray_direction_obj = ray_target_obj - ray_origin_obj

            # Do ray cast.
            success, location, normal, face_index = obj.ray_cast(ray_origin_obj, ray_direction_obj)
            if success:
                world_location = obj.matrix_world @ location
                tmp = normal.to_4d()
                tmp.w = 0
                world_normal = (obj.matrix_world @ tmp).to_3d()
                result_objects.append(IntersectInfo(obj, location, world_location, normal, world_normal, face_index))

    # Sort by best hit.
    result_objects = sorted(result_objects, key=lambda o: (o.world_location - ray_origin).length_squared)

    # Place cursor to intersect point.
    #if result_objects:        
    #    bpy.context.scene.cursor.location = result_objects[0].world_location

    return result_objects


def intersection_at_2d_plane(
    region: bpy.types.Region,
    region_data: bpy.types.RegionView3D,
    location: Tuple[float, float],  
    plane_pos: Vector = Vector((0, 0, 0)),
    plane_normal: Vector = Vector((0, 0, 1))
    ) -> Union[IntersectInfo, None]:
    """
    Finds the intersection point under mouse cursor with the given (infinite) plane, default is ground plane.
    """
    view_vector = view3d_utils.region_2d_to_vector_3d(region, region_data, location)
    ray_origin = view3d_utils.region_2d_to_origin_3d(region, region_data, location)
    location = mathutils.geometry.intersect_line_plane(ray_origin, ray_origin + view_vector, plane_pos, plane_normal)
    if location:
        return IntersectInfo(None, location, location, (0, 0, 1), (0, 0, 1), 0)


def all_spaces(type: str) -> List[bpy.types.Area]:
    """
    Search specific area in all screens of all workspaces.
    """
    scs = list(chain.from_iterable([ [ s for s in w.screens ] for w in bpy.data.workspaces ]))
    ars = list(chain.from_iterable([ [ a for a in s.areas ] for s in scs ]))
    return [ a for a in ars if a.type == type ]


def area_under_cursor(x_global: float, y_global: float) -> Tuple[float, float, Union[bpy.types.Area, None]]:
    """
    Find the area the is currently under the mouse cursor. Cursor coordinates
    must be in global space (event.mouse_region_x + context.area.x, event.mouse_region_y + context.area.y).
    Returns x, y in this area and the area. area in None if no area found.
    """
    for area in bpy.context.screen.areas:
        x_in_range = x_global >= area.x and x_global <= area.x + area.width
        y_in_range = y_global >= area.y and y_global <= area.y + area.height
        if x_in_range and y_in_range:
            return (x_global - area.x, y_global - area.y, area)
    return (0, 0, None)


def region_of_area(area: bpy.types.Area, type: str) -> Union[bpy.types.Region, None]:
    """
    Find specific region of area, return it or None of not found.
    """
    for r in area.regions:
        if r.type == type:
            return r
    return None


def set_active_object(obj: bpy.types.Object):
    """
    At it is a little bit unusual, do it here.
    """
    bpy.context.view_layer.objects.active = obj


class SelectionHelper:
    """
    Store currently selected objects (by name for safety)
    and is able to restore selection set later.
    Offers some other related tools too.
    Does all by name, in case an object is removed, the pointer may
    fail.
    """    
    def __init__(self, track_current_object: bool = True):
        self.__selected_object_names = [ o.name for o in bpy.context.selected_objects ]
        self.__active_object = None
        if track_current_object and bpy.context.active_object:
            self.__active_object = bpy.context.active_object.name


    def deselect_all(self):
        [ o.select_set(False) for o in bpy.context.selectable_objects ]


    def select_all(self):
        [ o.select_set(True) for o in bpy.context.selectable_objects ]


    def select_only(self, object: bpy.types.Object):
        [ o.select_set(o == object) for o in bpy.context.selectable_objects ]
        set_active_object(object)


    def restore(self):
        """
        (Try to) restore previous state.
        """
        active = None
        for o in bpy.context.selectable_objects:
            o.select_set(o.name in self.__selected_object_names)
            if o.name == self.__active_object:
                active = o

        if active:
            set_active_object(active)


    def __enter__(self):
        return self


    def __exit__(self, type, value, tb):
        self.restore()


def object_by_name(name: str) -> Union[bpy.types.Object, None]:
    """
    If name and object with this name exists, return it. None otherwise.
    """
    if name and name in bpy.data.objects:
        return bpy.data.objects[name]


def duplicate_object(obj: bpy.types.Object, linked: bool, select_too: bool = False) -> bpy.types.Object:
    """
    Duplicates an object and return reference to it.
    """
    # Store for later reselect.
    selected_objs = bpy.context.selected_objects
    [ o.select_set(False) for o in selected_objs ]

    # Select requested for copy.
    obj.select_set(True)
    bpy.ops.object.duplicate(linked=linked, mode='DUMMY')
    new_object = bpy.context.object

    # Restore selection state.
    [ o.select_set(True) for o in selected_objs ]
    new_object.select_set(select_too)

    return new_object


class DropNodeOperator:
    """
    Base class for all operators that drop a node into the shader editor.
    """
    @staticmethod
    def store_mouse_cursor(context, event):
        space = context.space_data
        tree = space.edit_tree

        # convert mouse position to the View2D for later node placement
        if context.region.type == 'WINDOW':
            # convert mouse position to the View2D for later node placement
            space.cursor_location_from_region(
                event.mouse_region_x, event.mouse_region_y)
        else:
            space.cursor_location = tree.view_center


    # Default invoke stores the mouse position to place the node correctly
    # and optionally invokes the transform operator
    def invoke(self, context, event):
        self.store_mouse_cursor(context, event)
        result = self.execute(context)
        bpy.ops.node.translate_attach_remove_on_cancel('INVOKE_DEFAULT')
        return result        
            
    

def drop_node(ng: bpy.types.NodeGroup):
    bpy.ops.node.add_node(
        type='ShaderNodeGroup', 
        use_transform=True, 
        settings=[{
            'name': 'node_tree', 
            'value': 'bpy.data.node_groups["%s"]' % ng.name
        }]
    )
    return{'FINISHED'}


def drop_std_node(name: str, settings: List[Dict[str, str]] = None):
    if settings:
        bpy.ops.node.add_node(
            type=f'ShaderNode{name}', 
            use_transform=True,
            settings=settings
        )
    else:
        bpy.ops.node.add_node(
            type=f'ShaderNode{name}', 
            use_transform=True,
        )
    return{'FINISHED'}


def is_valid_node_space(context: bpy.context, tree_types: List[str]) -> bool:
    """
    Check if node space, has valid tree and tree type matches gives types.
    """
    return context.space_data.type == 'NODE_EDITOR' and \
            context.space_data.node_tree is not None and \
            context.space_data.tree_type in tree_types

    
    