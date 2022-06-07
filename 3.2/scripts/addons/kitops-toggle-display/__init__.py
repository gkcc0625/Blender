bl_info = {
    "name": "KIT OPS Toggle VP Display",
    "author": "Chipp Walters, Martynas Žiemys",
    "version": (1, 3, 22),
    "blender": (2, 80, 0),
    "location": "View3D - ctrl + alt + shift + z",
    "description": "Toggles display mode of selected objects, Align verts in Viewport and UV Editor- Use CTRL+ALT+ X,Y or C(not Y)",
    "warning": "",
    "wiki_url": "",
    "category": "3D View",
}

import bpy

# SCALE X IN UV EDITOR
class OBJECT_OT_scale_xuv(bpy.types.Operator):
    """scales VERTS to x=0"""
    bl_idname = "object.vertscale_xuv"
    bl_label = "Scale UV selected verts to X=0"

    @classmethod
    def poll(cls, context):
        # Checks to see if there's any active mesh object (selected or in edit mode)
        active_object = context.active_object
        return active_object is not None and active_object.type == 'MESH' and context.mode == 'EDIT_MESH'

    def execute(self, context):
        
        bpy.ops.transform.resize(value=(0, 1, 1), orient_type='VIEW', orient_matrix=((1, 0, 0), (0, 1, 0), (0, 0, 1)), 
            orient_matrix_type='VIEW', constraint_axis=(True, False, False), 
            mirror=True, use_proportional_edit=False, proportional_edit_falloff='SMOOTH', 
            proportional_size=1, use_proportional_connected=False, use_proportional_projected=False)
        
        return {'FINISHED'}

# SCALE Y IN UV EDITOR
class OBJECT_OT_scale_yuv(bpy.types.Operator):
    """scales VERTS to y=0"""
    bl_idname = "object.vertscale_yuv"
    bl_label = "Scale UV selected verts to Y=0"

    @classmethod
    def poll(cls, context):
        # Checks to see if there's any active mesh object (selected or in edit mode)
        active_object = context.active_object
        return active_object is not None and active_object.type == 'MESH' and context.mode == 'EDIT_MESH'

    def execute(self, context):
        
        bpy.ops.transform.resize(value=(1, 0, 1), orient_type='VIEW', orient_matrix=((1, 0, 0), (0, 1, 0), (0, 0, 1)), 
            orient_matrix_type='VIEW', constraint_axis=(True, False, False), 
            mirror=True, use_proportional_edit=False, proportional_edit_falloff='SMOOTH', 
            proportional_size=1, use_proportional_connected=False, use_proportional_projected=False)
        
        return {'FINISHED'}


## SCALE X
class OBJECT_OT_scale_x(bpy.types.Operator):
    """scales VERTS to x=0"""
    bl_idname = "object.vertscale_x"
    bl_label = "Scale selected verts to X=0"

    @classmethod
    def poll(cls, context):
        # Checks to see if there's any active mesh object (selected or in edit mode)
        active_object = context.active_object
        return active_object is not None and active_object.type == 'MESH' and context.mode == 'EDIT_MESH'

    def execute(self, context):
        
        bpy.ops.transform.resize(value=(0, 1, 1), orient_type='GLOBAL', orient_matrix=((1, 0, 0), (0, 1, 0), (0, 0, 1)), 
            orient_matrix_type='GLOBAL', constraint_axis=(True, False, False), mirror=True, use_proportional_edit=False, 
            proportional_edit_falloff='SMOOTH', proportional_size=1, use_proportional_connected=False, use_proportional_projected=False)
        
        return {'FINISHED'}

## SCALE Y
class OBJECT_OT_scale_y(bpy.types.Operator):
    """scales VERTS to z=0"""
    bl_idname = "object.vertscale_y"
    bl_label = "Scale selected verts to Y=0"

    @classmethod
    def poll(cls, context):
        # Checks to see if there's any active mesh object (selected or in edit mode)
        active_object = context.active_object
        return active_object is not None and active_object.type == 'MESH' and context.mode == 'EDIT_MESH'

    def execute(self, context):
        
        bpy.ops.transform.resize(value=(1, 0, 1), orient_type='GLOBAL', orient_matrix=((1, 0, 0), (0, 1, 0), (0, 0, 1)), orient_matrix_type='GLOBAL', constraint_axis=(True, False, False), mirror=True, use_proportional_edit=False, proportional_edit_falloff='SMOOTH', proportional_size=1, use_proportional_connected=False, use_proportional_projected=False)
        
        return {'FINISHED'}

## SCALE Z
class OBJECT_OT_scale_z(bpy.types.Operator):
    """scales VERTS to z=0"""
    bl_idname = "object.vertscale_z"
    bl_label = "Scale selected verts to Z=0"

    @classmethod
    def poll(cls, context):
        # Checks to see if there's any active mesh object (selected or in edit mode)
        active_object = context.active_object
        return active_object is not None and active_object.type == 'MESH' and context.mode == 'EDIT_MESH'

    def execute(self, context):
        
        bpy.ops.transform.resize(value=(1, 1, 0), orient_type='GLOBAL', orient_matrix=((1, 0, 0), (0, 1, 0), (0, 0, 1)), orient_matrix_type='GLOBAL', constraint_axis=(True, False, False), mirror=True, use_proportional_edit=False, proportional_edit_falloff='SMOOTH', proportional_size=1, use_proportional_connected=False, use_proportional_projected=False)
        
        return {'FINISHED'}


class OBJECT_OT_wire_toggle(bpy.types.Operator):
    """Toggles display mode of selected objects between Wire and Textured"""
    bl_idname = "object.wire_toggle"
    bl_label = "Display as Wire Toggle"

    @classmethod
    def poll(cls, context):
        return context.object is not None

    def execute(self, context):
        if context.object.display_type == 'WIRE':
            display_type = 'BOUNDS'
            usage_type = 'EXCLUDE'
            #bpy.context.object.ObjectLineArt.usage = 'EXCLUDE'


            
        elif context.object.display_type == 'BOUNDS':
            display_type = 'TEXTURED'
            usage_type = 'INCLUDE'
#        elif context.object.display_type == 'TEXTURED':
#            display_type = 'SOLID'
        else:
            display_type = 'WIRE' 
            usage_type = 'INCLUDE'      
        for obj in context.selected_objects: 
            obj.display_type = display_type
            try:
                obj.lineart.usage = usage_type
            except:
                print("Blender version does not support LINE ART USAGE")
        
       # if context.object.usage == 'INHERIT':
            #print("Inherit")
        
        return {'FINISHED'}


addon_keymaps = []
def registerKeymaps():
    wm = bpy.context.window_manager
    if wm.keyconfigs.addon:
        # KEY SHORTCUTS FOR SPACE TYPE VIEW_3D
        km = wm.keyconfigs.addon.keymaps.new(name='3D View Generic', space_type='VIEW_3D')
        
        ## SET KEY BINDING BELOW
        ## OBJECT WIRE TOGGLE
        kmi = km.keymap_items.new('object.wire_toggle', 'Z', 'PRESS', shift=True, alt=True,ctrl=True)
        addon_keymaps.append((km, kmi))
                
        ## SCALE VERTS X
        kmi = km.keymap_items.new('object.vertscale_x', 'X', 'PRESS', alt=True,ctrl=True)
        addon_keymaps.append((km, kmi))

        ## SCALE VERTS Y
        kmi = km.keymap_items.new('object.vertscale_y', 'C', 'PRESS', alt=True,ctrl=True)
        addon_keymaps.append((km, kmi))

        ## SCALE VERTS Z
        kmi2 = km.keymap_items.new('object.vertscale_z', 'Z', 'PRESS', alt=True,ctrl=True)
        addon_keymaps.append((km, kmi))
        
        
        # KEY SHORTCUTS FOR SPACE TYPE VIEW_3D
        km_uv = wm.keyconfigs.addon.keymaps.new(name='Image', space_type='IMAGE_EDITOR')
        
        ## SCALE UV VERTS X
        km_uv_i = km_uv.keymap_items.new('object.vertscale_xuv', 'X', 'PRESS', alt=True,ctrl=True)
        addon_keymaps.append((km_uv, km_uv_i))

        ## SCALE UV VERTS Y
        km_uv_i = km_uv.keymap_items.new('object.vertscale_yuv', 'C', 'PRESS', alt=True,ctrl=True)
        addon_keymaps.append((km_uv, km_uv_i))


def unregisterKeymaps():
    for km, kmi in addon_keymaps:
        km.keymap_items.remove(kmi)
    addon_keymaps.clear()


classes = (
    OBJECT_OT_wire_toggle,
    OBJECT_OT_scale_x,
    OBJECT_OT_scale_y,
    OBJECT_OT_scale_z,
    OBJECT_OT_scale_xuv,
    OBJECT_OT_scale_yuv
)

def register():
    from bpy.utils import register_class
    for cls in classes:
        register_class(cls)
    registerKeymaps()

def unregister():
    unregisterKeymaps()
    from bpy.utils import unregister_class
    for cls in reversed(classes):
        unregister_class(cls)

if __name__ == "__main__":
    register()