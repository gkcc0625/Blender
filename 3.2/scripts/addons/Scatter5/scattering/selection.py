
#####################################################################################################
#
#  .oooooo..o           oooo                          .    o8o
# d8P'    `Y8           `888                        .o8    `"'
# Y88bo.       .ooooo.   888   .ooooo.   .ooooo.  .o888oo oooo   .ooooo.  ooo. .oo.
#  `"Y8888o.  d88' `88b  888  d88' `88b d88' `"Y8   888   `888  d88' `88b `888P"Y88b
#      `"Y88b 888ooo888  888  888ooo888 888         888    888  888   888  888   888
# oo     .d8P 888    .o  888  888    .o 888   .o8   888 .  888  888   888  888   888
# 8""88888P'  `Y8bod8P' o888o `Y8bod8P' `Y8bod8P'   "888" o888o `Y8bod8P' o888o o888o
#
#####################################################################################################


import bpy 

from .. utils.event_utils import get_event

from .. resources.icons import cust_icon
from .. resources.translate import translate


#####################################################################################################


def set_sel(psys,value):
    """batch set set all psy selection status""" #foreach_set() 'cound'nt access api for some reasons...
    for p in psys:
        p.sel = value
    return None 


def idx_active_update(self,context):
    """function that run when user set a particle system as active, used for shift&alt shortcut, also change selection"""

    scat_scene = bpy.context.scene.scatter5
    emitter = self.id_data
    psys    = emitter.scatter5.particle_systems

    #set psy.active property based from emitter, very useful when browsing api, .active shall be ONLY changed from here, nowhere else!
    for i,p in enumerate(psys):
        p.active = i == self.particle_systems_idx

    psy_active = emitter.scatter5.get_psy_active() #same as self.get_psy_active()
    if psy_active is None:
        return None

    #select scatter_obj?
    if scat_scene.update_auto_set_scatter_obj_active:
        for o in bpy.data.objects:
            if o.name.startswith("scatter_obj"):
                select = (o == psy_active.scatter_obj)
                o.hide_select = not select
                o.select_set(select)

    event = get_event()

    if (not event.shift):
        set_sel(psys,False,)

    psy_active.sel = True

    if (event.alt):
        for p in psys:
            p.hide_viewport = not p.sel

    return None 


class SCATTER5_OT_toggle_selection(bpy.types.Operator):
    """toggle select all"""
    bl_idname      = "scatter5.toggle_selection"
    bl_label       = ""
    bl_description = translate("Select/Deselect everything")

    select   : bpy.props.BoolProperty()
    deselect : bpy.props.BoolProperty()
    emitter  : bpy.props.StringProperty()

    @classmethod
    def poll(cls, context):
        return (bpy.context.scene.scatter5.emitter != None)

    def execute(self, context):

        #find emitter object 
        if self.emitter=="":
              emitter = bpy.context.scene.scatter5.emitter
        else: emitter = bpy.data.objects[self.emitter]
        psys = emitter.scatter5.particle_systems

        #Select All?
        if self.select==True:
            set_sel(psys,True)
        #Deselect All?
        elif self.deselect==True:
            set_sel(psys,False)
        #Then Toggle automatically 
        else:
            if True in [p.sel for p in psys]:
                  set_sel(psys,False)
            else: set_sel(psys,True)

        self.select = self.deselect = False
        return {'FINISHED'}


class SCATTER5_OT_instance_selection(bpy.types.Operator):
    """Select/Deselect particle system(s)"""
    bl_idname      = "scatter5.instance_selection"
    bl_label       = ""
    bl_description = translate("Select/Deselect this object, use [SHIFT] for multi selection, [ALT] to recenter viewport toward object, [ALT-SHIFT] for both")

    obj_name : bpy.props.StringProperty(default="")
    coll_name : bpy.props.StringProperty(default="")

    def invoke(self, context, event):

        #Object do not exists?
        obj = bpy.data.objects.get(self.obj_name)
        if obj is None:
            return {'FINISHED'}

        #Object Not in scene? 
        if (obj.name not in bpy.context.scene.objects):
            bpy.ops.scatter5.popup_menu(msgs=translate("Object is not in scene"),title=translate("Action not Possible"),icon="ERROR",)
            return {'FINISHED'}

        #Object hidden in viewlayer?
        if (obj.name not in bpy.context.view_layer.objects):
            #try to unhide from collection ?
            if self.coll_name:
                obj_name, coll_name = self.obj_name, self.coll_name
                def draw(self, context):
                    nonlocal obj_name, coll_name
                    layout = self.layout
                    layout.operator("scatter5.exec_line",text=translate("Unhide Viewlayer Collection")).api = f"from ..utils.coll_utils import exclude_all_view_layers ; exclude_all_view_layers(bpy.data.collections['{coll_name}'], exclude=False) ; o = bpy.data.objects['{obj_name}'] ; bpy.context.view_layer.objects.active =o ; o.select_set(True)"
                    return 
                context.window_manager.popup_menu(draw, title=translate("Object is in Hidden Viewlayer"))
                return {'FINISHED'}    
            bpy.ops.scatter5.popup_menu(msgs=translate("Object is not in view layer"),title=translate("Action not Possible"),icon="ERROR",)
            return {'FINISHED'}

        def deselect_all():
            for o in bpy.context.selected_objects:
                o.select_set(state=False)

        #event shift+alt click
        if event.shift and event.alt:
            bpy.context.view_layer.objects.active = obj
            obj.select_set(state=True)
            bpy.ops.view3d.view_selected()

        #event shift click
        elif event.shift:
            bpy.context.view_layer.objects.active = obj
            obj.select_set(state=True)

        #event alt click
        elif event.alt:
            deselect_all()
            bpy.context.view_layer.objects.active = obj
            obj.select_set(state=True)
            bpy.ops.view3d.view_selected()

        #event normal
        else:
            deselect_all()
            bpy.context.view_layer.objects.active = obj
            obj.select_set(state=True)

        return {'FINISHED'}



#   .oooooo.   oooo
#  d8P'  `Y8b  `888
# 888           888   .oooo.    .oooo.o  .oooo.o  .ooooo.   .oooo.o
# 888           888  `P  )88b  d88(  "8 d88(  "8 d88' `88b d88(  "8
# 888           888   .oP"888  `"Y88b.  `"Y88b.  888ooo888 `"Y88b.
# `88b    ooo   888  d8(  888  o.  )88b o.  )88b 888    .o o.  )88b
#  `Y8bood8P'  o888o `Y888""8o 8""888P' 8""888P' `Y8bod8P' 8""888P'



classes = [

    SCATTER5_OT_toggle_selection,
    SCATTER5_OT_instance_selection,
    
    ]



#if __name__ == "__main__":
#    register()