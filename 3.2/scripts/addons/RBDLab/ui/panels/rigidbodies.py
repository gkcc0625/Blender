import bpy
from bpy.types import Panel
from ...core.functions import have_rigidbodies_in_target_collection


class RBD_PT_ui(Panel):
    bl_label = "Rigid Bodies"
    bl_idname = "RBD_PT_ui"
    bl_category = "RBDLab"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"

    def draw(self, context):
        layout = self.layout

        layout.use_property_split = True
        layout.use_property_decorate = False
        flow = layout.grid_flow(align=True)
        col = flow.column()

        col.prop(bpy.context.scene.rbdlab_props, "avalidable_mass", text="")

        col = layout.column(align=False, heading="Collision Margin")
        col.use_property_decorate = False
        row = col.row(align=True)
        sub = row.row(align=True)
        sub.prop(bpy.context.scene.rbdlab_props, "use_collision_margin", text='')
        sub = sub.row(align=True)
        sub.active = bpy.context.scene.rbdlab_props.use_collision_margin
        sub.prop(bpy.context.scene.rbdlab_props, "collision_margin", text='')

        col.prop(bpy.context.scene.rbdlab_props, "rb_friction", text="Friction")
        # col.prop(bpy.context.scene.rbdlab_props, "dynamic", text="Dynamic")
        col.prop(bpy.context.scene.rbdlab_props, "deactivation", text="Deactivation")
        col.prop(bpy.context.scene.rbdlab_props, "d_translation", text="Damping Translation")
        col.prop(bpy.context.scene.rbdlab_props, "d_rotation", text="Damping Rotation")

        if not have_rigidbodies_in_target_collection():
            col.operator("rbd.add", text='Add Rigid Body Actives')
        else:
            big_row = col.row()
            big_row.scale_y = 1.5
            big_row.operator("rbd.update", text='Update')
            col.operator("rbd.remove", text='Remove Rigid Bodies')

        col.label(text='Selection to Passive:')
        col.operator("rbd.passive", text='Convert in Passive')
