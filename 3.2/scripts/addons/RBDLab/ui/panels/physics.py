import bpy
from bpy.types import Panel

from bl_ui.properties_physics_common import (
    point_cache_ui,
    effector_weights_ui,
)

class PHYSICS_PT_ui(Panel):
    bl_label = "Physics"
    bl_idname = "PHYSICS_PT_ui"
    bl_category = "RBDLab"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"

    def draw(self, context):
        layout = self.layout
        layout.use_property_split = True
        layout.use_property_decorate = False
        flow = layout.grid_flow(align=True)
        col = flow.column()


class PHYSICS_PT_substeps(Panel):
    bl_label = "Rigid Bodies"
    bl_idname = "PHYSICS_PT_substeps"
    bl_category = "RBDLab"
    bl_parent_id = "PHYSICS_PT_ui"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"

    def draw(self, context):
        layout = self.layout
        col = layout.column()

        scene = context.scene
        rbw = scene.rigidbody_world
        if rbw:
            col.prop(rbw, "substeps_per_frame")
            col.prop(rbw, "solver_iterations")
        else:
            col.label(text='No rigid bodies at the moment in the scene')


class PHYSICS_CACHE_PT_ui(Panel):
    bl_label = "Cache"
    bl_idname = "PHYSICS_CACHE_PT_ui"
    bl_category = "RBDLab"
    bl_parent_id = "PHYSICS_PT_ui"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"

    def draw(self, context):
        layout = self.layout

        layout.use_property_split = True
        layout.use_property_decorate = False
        flow = layout.grid_flow(align=True)
        col = flow.column()

        scene = context.scene
        rbw = scene.rigidbody_world
        if rbw:
            point_cache_ui(self, rbw.point_cache, rbw.point_cache.is_baked is False and rbw.enabled, 'RIGID_BODY')
        else:
            col.label(text='No rigid bodies at the moment in the scene')