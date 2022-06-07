import bpy
from bpy.types import Menu
from bpy.app.handlers import persistent

bl_info = {
    "name": "Inactive Shading Style",
    "author": "APEC",
    "version": (1, 0, 2),
    "blender": (2, 81, 0),
    "location": "View3D > Properties",
    "description": "Toggle wire shading style for inactive meshes.",
    "wiki_url": "https://blenderartists.org/t/shading-for-inactive-objects-in-viewport-wireframe/1206498",
    "tracker_url": "",
    "category": "3D View"
}


oldactive = None
oldsel = None


@persistent
def update_shading_style(scene):
    '''
    watch changes in selection or active object
    set display_type accordingly
    '''
    if scene.inactive_shading:
        global oldactive, oldsel

        context = bpy.context

        active = context.active_object if context.active_object else None
        sel = context.selected_objects

        if active != oldactive or sel != oldsel:
            oldactive = active
            oldsel = sel

            for obj in context.visible_objects:
                obj.display_type = 'TEXTURED' if obj in sel else 'WIRE'


def PanelInactiveShading(self, context):
    layout = self.layout
    layout.separator()
    layout.label(text="Inactive Shading")
    layout.prop(context.scene, "inactive_shading", text="Wire")


def register():
    def update_inactive_shading(self, context):
        '''
        reset the display type of all visible objects, when scene.inactive_shading is toggled
        '''

        vis = context.visible_objects

        # enabled - set display style according to 1. object being active or among selection: TEXTURED, 2. object not selected: WIRE
        if context.scene.inactive_shading:
            active = context.active_object if context.active_object else None

            sel = [obj for obj in context.selected_objects if obj != active]

            for obj in vis:
                if obj in sel or obj == active:
                    obj.display_type = 'TEXTURED'

                else:
                    obj.display_type = 'WIRE'

        # disabled - set all visible objects to TEXUTURED
        else:
            for obj in vis:
                obj.display_type = 'TEXTURED'

    bpy.types.Scene.inactive_shading = bpy.props.BoolProperty(name="Inactive Shading", default=False, update=update_inactive_shading)

    bpy.types.VIEW3D_PT_shading_color.append(PanelInactiveShading)

    bpy.app.handlers.depsgraph_update_post.append(update_shading_style)
    bpy.app.handlers.undo_post.append(update_shading_style)
    bpy.app.handlers.redo_post.append(update_shading_style)


def unregister():
    bpy.app.handlers.depsgraph_update_post.remove(update_shading_style)
    bpy.app.handlers.undo_post.remove(update_shading_style)
    bpy.app.handlers.redo_post.remove(update_shading_style)

    bpy.types.VIEW3D_PT_shading_color.remove(PanelInactiveShading)

    del bpy.types.Scene.inactive_shading
    
if __name__ == "__main__":
    register()
