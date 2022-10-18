# Copyright (C) 2022 Thomas Hoppe (h0bB1T). All rights reserved.
#
# Unauthorized copying of this file via any medium is strictly prohibited.
# Proprietary and confidential.

import math
import bpy

from bpy.types import PropertyGroup, WindowManager
from bpy.props import StringProperty, BoolProperty, EnumProperty, CollectionProperty, PointerProperty, FloatProperty

from .registries.resource_lists_registry import ResourceListsRegistry
from .registries.config_registry import ConfigRegistry

class TagProperty(PropertyGroup):
    title: StringProperty()


class PropertySection(PropertyGroup):
    """
    Each panel gets is own instance, so changing a setting in one panel, does not effect another.
    """
    export_library: EnumProperty(
        name='',
        description='Export to this Library',
        items=lambda self, context: [ ( l.path, l.name, l.name ) for l in context.preferences.filepaths.asset_libraries ]
    )

    export_file: EnumProperty(
        name='',
        description='Export to this File',
        items=lambda self, context: ResourceListsRegistry.get().library_files(self.export_library)
    )

    catalog: EnumProperty(
        name='',
        description='Catalog to map this Item to',
        items=lambda self, _: ResourceListsRegistry.get().catalogs(self.export_library)
    )

    tag_select: EnumProperty(
        name='', 
        description='Select Tag previously used',
        items=lambda _, __: ConfigRegistry.get().tags()
    )
    tags: CollectionProperty(name='Tags', type=TagProperty)
    new_tag: StringProperty(name='', description='Enter new Tag Name')

    description: StringProperty(name='', description='Asset Description')

    show_stats: BoolProperty(name='', description='Open Panel with Info about current Library .blend')

    use_render_as_preview: BoolProperty(name='', description='Use the current Render Result as Preview Image, instead of rendering a Preview or use Placeholder Image', default=False)


class Properties(PropertyGroup):
    material_node_section: PointerProperty(type=PropertySection)
    geometry_node_section: PointerProperty(type=PropertySection)
    object_collection_section: PointerProperty(type=PropertySection)

    collection: EnumProperty(
        name='Collection',
        description='Collection to export',
        items=lambda _, __: [ ( c.name, c.name, c.name ) for c in bpy.data.collections ]
    )

    author: StringProperty(name='', description='Author of this Asset')
    auto_place_padding: FloatProperty(name='Padding', description='Padding used in Grid placement', default=0.2)

    shader_tag_select: EnumProperty(
        name='Shader Tag',
        description='Tag to include in Name, so Pie Menu can position it',
        items=lambda _, __: ConfigRegistry.get().shader_tags()
    )

    geometry_tag_select: EnumProperty(
        name='Geometry Tag',
        description='Tag to include in Name, so Pie Menu can position it',
        items=lambda _, __: ConfigRegistry.get().geometry_tags()
    )    

    show_object_cleaners: BoolProperty(name='Object Cleanup', description='Toggle Object Cleanup Options', default=False)
    oc_remove_animation_data: BoolProperty(name='Remove animation Data', description='Remove animation Data from selected Meshes', default=False)
    oc_unparent: BoolProperty(name='Remove parent Empties', description='Remove all Parent Empties, leaving Transformation (Clear animation Data may be necessary)', default=True)
    oc_merge_objects: BoolProperty(name='Merge Objects', description='Merge Meshes in selected Hierarchy', default=False)

    show_mesh_cleaners: BoolProperty(name='Mesh Cleanup', description='Toggle Mesh Cleanup Options', default=False)
    mc_clear_custom_split_normals: BoolProperty(name='Clear custom split Normals', description='Clear these on all selected Meshes', default=True)
    mc_set_auto_smooth: BoolProperty(name='Enabled Auto Smooth', description='Enable Auto Smooth and set Angle', default=True)
    mc_recalculate_normals_outside: BoolProperty(name='Recalculate Normals', description='Recalculate Normals to Outside on all selected Meshes', default=True)
    mc_join_vertices: BoolProperty(name='Join Vertices', description='Join Vertices close together, which isn\'t needed in Blender, but some 3D Formats', default=True)
    mc_limited_dissolve: BoolProperty(name='Limited Dissolve', description='Delete all unnesseary Edges and Vertices to get large N-Gons', default=True)
    
    mc_auto_smooth_angle: FloatProperty(name='Auto Smooth Angle', default=math.radians(30), subtype='ANGLE', precision=2)

    mc_join_vertices_distance: FloatProperty(name='Max Distance', description='Maximum Distance of Vertices when joining', default=0.0001, precision=5)

    replace_mode: BoolProperty(name='Re-Place Mode', description='Replace target Object, copy Transformation', default=False)
    place_quick: BoolProperty(name='Quick Transform', description='Quick place Mode', default=True)
    place_create_copy: BoolProperty(name='Copy before Place', description='Create a Copy before placing', default=False)
    place_linked_copy: BoolProperty(name='Linked Copy', description='Create a linked Copy', default=True)
    place_auto_parent: BoolProperty(name='Auto Parent', description='Automatically set Target Object as Parent', default=False)

    @staticmethod
    def initialize():
        WindowManager.awp_properties = PointerProperty(type=Properties)
        

    @staticmethod
    def get() -> 'Properties':
        return bpy.context.window_manager.awp_properties       


    @staticmethod
    def dispose():
        if WindowManager.awp_properties:
            del(WindowManager.awp_properties)
            