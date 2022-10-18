# Copyright (C) 2022 Thomas Hoppe (h0bB1T). All rights reserved.
#
# Unauthorized copying of this file via any medium is strictly prohibited.
# Proprietary and confidential.

import bpy, math

from bpy.types import AddonPreferences, UILayout
from bpy.props import StringProperty, IntProperty, BoolProperty, EnumProperty, FloatProperty

from typing import List, Tuple

from .properties import Properties
from .registries.key_registry import KeyRegistry
from .registries.config_registry import ConfigRegistry
from .operators.tag_manager import ASSET_OT_tag_manager

class PreferencesPanel(AddonPreferences):
    bl_idname = __package__

    render_engine: EnumProperty(
        name='Preview Renderer', 
        default='CYCLES', 
        items=[
            ( 'CYCLES', 'Cycles', 'Cycles'),
            ( 'BLENDER_EEVEE', 'Eevee', 'Eevee' ),
        ]
    )
    cycles_samples: IntProperty(name='Number of Samples', default=10, min=1, max=1024)
    dimension: IntProperty(name='Preview Render Size', default=128)

    prefer_snw: BoolProperty(
        name='Prefer Shader Node Wizard Pie', 
        description='If you\'ve installed and enabled SNW, Asset Wizard Pro will invoke' + 
            ' SNW\'s Pie Menu in Shader Node Editor. Useful when using the same hotkey (first Addon wins in this case)',
        default=True
    )

    relative_paths: BoolProperty(
        name='Relative Paths',
        description='If enabled, Paths to external data (images, volumes) is relative, not absolute',
        default=True
    )
    auto_place: BoolProperty(name='Autoplace Objects in Grid', default=True)
    author: StringProperty(name='Default Author')

    new_tag: StringProperty()
    new_shader_tag: StringProperty()
    new_geometry_tag: StringProperty()

    oc_remove_animation_data: BoolProperty(name='Remove animation Data', description='Remove animation Data from selected Meshes', default=False)
    oc_unparent: BoolProperty(name='Remove parent Empties', description='Remove all Parent Empties, leaving Transformation (Clear animation Data may be necessary)', default=True)
    oc_merge_objects: BoolProperty(name='Merge Objects', description='Merge Meshes in selected Hierarchy', default=False)

    mc_clear_custom_split_normals: BoolProperty(name='Clear custom split Normals', description='Clear these on all selected Meshes', default=True)
    mc_set_auto_smooth: BoolProperty(name='Enabled Auto Smooth', description='Enable Auto Smooth and set Angle', default=True)
    mc_recalculate_normals_outside: BoolProperty(name='Recalculate Normals', description='Recalculate Normals to Outside on all selected Meshes', default=True)
    mc_join_vertices: BoolProperty(name='Join Vertices', description='Join Vertices close together, which isn\'t needed in Blender, but some 3D Formats', default=True)
    mc_limited_dissolve: BoolProperty(name='Limited Dissolve', description='Delete all unnesseary Edges and Vertices to get large N-Gons', default=True)
    mc_auto_smooth_angle: FloatProperty(name='Auto Smooth Angle', default=math.radians(30), subtype='ANGLE', precision=2)
    mc_join_vertices_distance: FloatProperty(name='Max Distance', description='Maximum Distance of Vertices when joining', default=0.0001, precision=5)

    place_quick: BoolProperty(name='Quick Transform', description='Quick place Mode', default=True)
    place_linked_copy: BoolProperty(name='Linked Copy', description='Create a linked Copy', default=True)
    place_auto_parent: BoolProperty(name='Auto Parend', description='Automatically set Target Object as Parent', default=False)


    def __draw_tag_controls(self, g: UILayout, name: str, tags: List[Tuple[str, str, str]], prp: str, a_mode: str, r_mode: str):
        r = g.column(align=True)
        r.label(text=f'{name}:')
        s = r.row(align=True)
        s.prop(self, prp, text='')
        ASSET_OT_tag_manager.create_ui(s, 'ADD', True, a_mode, '', getattr(self, prp))
        for t, _, __ in tags:
            s = r.row(align=True)
            s.label(text=t)
            ASSET_OT_tag_manager.create_ui(s, 'REMOVE', True, r_mode, '', t)


    def draw(self, context: bpy.context):
        l = self.layout # type: bpy.types.UILayout
        c = l.column(align=False)
        c.use_property_decorate = True
        c.use_property_split = False

        b = c.box().column(align=True)
        b.use_property_split = True
        b.label(text='Preview Render Options:')
        b.separator()
        b.row(align=True).prop(self, 'render_engine', expand=True)
        if self.render_engine == 'CYCLES':
            b.prop(self, 'cycles_samples')
        b.prop(self, 'dimension')

        b = c.box().column(align=True)
        b.use_property_split = True
        b.label(text='Hotkeys and Settings:')
        b.separator()
        KeyRegistry.instance().render_prefs(b)
        b.separator()
        b.prop(self, 'prefer_snw', toggle=True, icon='NODE')

        b = c.box().column(align=True)
        b.use_property_split = True
        b.label(text='Export Options:')
        b.separator()
        b.prop(self, 'relative_paths', icon='OUTLINER', toggle=True)
        b.prop(self, 'auto_place', icon='VIEW_ORTHO', toggle=True)
        b.prop(self, 'author')

        b = c.box().column(align=True)
        b.use_property_split = True
        b.label(text='Preferred Tool Panel Options:')
        b.separator()
        sp = b.split(factor=0.5, align=True)
        lc = sp.column(align=True)

        lc.label(text='Object Cleanup:')
        lc.prop(self, 'oc_remove_animation_data')
        lc.prop(self, 'oc_unparent')
        lc.prop(self, 'oc_merge_objects')

        lc.separator()

        lc.label(text='Place Object:')
        lc.prop(self, 'place_quick')
        lc.prop(self, 'place_linked_copy')
        lc.prop(self, 'place_auto_parent')

        rc = sp.column(align=True)

        rc.label(text='Mesh Cleanup:')
        rc.prop(self, 'mc_clear_custom_split_normals')
        rc.prop(self, 'mc_set_auto_smooth')
        rc.prop(self, 'mc_auto_smooth_angle')
        rc.prop(self, 'mc_recalculate_normals_outside')
        rc.prop(self, 'mc_join_vertices')
        rc.prop(self, 'mc_join_vertices_distance')
        rc.prop(self, 'mc_limited_dissolve')


        #b.separator()
        b = c.box().column(align=True)
        b.label(text='Tags and Node Group Types:')
        b.separator()
        g = b.grid_flow(row_major=True, columns=3, even_columns=True)
        self.__draw_tag_controls(g, 'Asset Tags', ConfigRegistry.get().tags(), 'new_tag', 'ADD_TAG', 'REMOVE_TAG')
        self.__draw_tag_controls(g, 'Shader Types', ConfigRegistry.get().shader_tags(), 'new_shader_tag', 'ADD_SHADER_TAG', 'REMOVE_SHADER_TAG')
        self.__draw_tag_controls(g, 'Geometry Types', ConfigRegistry.get().geometry_tags(), 'new_geometry_tag', 'ADD_GEOMETRY_TAG', 'REMOVE_GEOMETRY_TAG')


    def transfer_defaults(self):
        """
        Copy user default settings to properties.
        """
        p = Properties.get()
        pr = PreferencesPanel.get()
        p.author = pr.author
        p.oc_remove_animation_data = pr.oc_remove_animation_data
        p.oc_unparent = pr.oc_unparent
        p.oc_merge_objects = pr.oc_merge_objects
        p.place_quick = pr.place_quick
        p.place_linked_copy = pr.place_linked_copy
        p.place_auto_parent = pr.place_auto_parent
        p.mc_clear_custom_split_normals = pr.mc_clear_custom_split_normals
        p.mc_set_auto_smooth = pr.mc_set_auto_smooth
        p.mc_auto_smooth_angle = pr.mc_auto_smooth_angle
        p.mc_recalculate_normals_outside = pr.mc_recalculate_normals_outside
        p.mc_join_vertices = pr.mc_join_vertices
        p.mc_join_vertices_distance = pr.mc_join_vertices_distance
        p.mc_limited_dissolve = pr.mc_limited_dissolve


    @staticmethod
    def get() -> 'PreferencesPanel':
        return bpy.context.preferences.addons[__package__].preferences
        