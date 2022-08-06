
#####################################################################################################
# 
#  ooooo   ooooo                             .o8  oooo
#  `888'   `888'                            "888  `888
#   888     888   .oooo.   ooo. .oo.    .oooo888   888   .ooooo.  oooo d8b
#   888ooooo888  `P  )88b  `888P"Y88b  d88' `888   888  d88' `88b `888""8P
#   888     888   .oP"888   888   888  888   888   888  888ooo888  888
#   888     888  d8(  888   888   888  888   888   888  888    .o  888
#  o888o   o888o `Y888""8o o888o o888o `Y8bod88P" o888o `Y8bod8P' d888b
# 
#####################################################################################################


import bpy
import datetime

from bpy.app.handlers import persistent

from .. utils.extra_utils import dprint
from .. utils.extra_utils import is_rendered_view, all_3d_viewports


# oooooooooo.                                                                          oooo
# `888'   `Y8b                                                                         `888
#  888      888  .ooooo.  oo.ooooo.   .oooo.o  .oooooooo oooo d8b  .oooo.   oo.ooooo.   888 .oo.
#  888      888 d88' `88b  888' `88b d88(  "8 888' `88b  `888""8P `P  )88b   888' `88b  888P"Y88b
#  888      888 888ooo888  888   888 `"Y88b.  888   888   888      .oP"888   888   888  888   888
#  888     d88' 888    .o  888   888 o.  )88b `88bod8P'   888     d8(  888   888   888  888   888
# o888bood8P'   `Y8bod8P'  888bod8P' 8""888P' `8oooooo.  d888b    `Y888""8o  888bod8P' o888o o888o
#                          888                d"     YD                      888
#                         o888o               "Y88888P'                     o888o


from .. scattering.emitter import handler_emitter_check, handler_emitter_if_pinned_mode, handler_scene_emitter_cleanup
from .. scattering.update_factory import update_active_camera_nodegroup

@persistent
def scatter5_depsgraph(scene,desp): 

    #debug print
    dprint("HANDLER: 'scatter5_depsgraph'",depsgraph=True)

    #check on emitter prop
    handler_emitter_check()

    #update emitter pointer if in pin mode
    handler_emitter_if_pinned_mode()

    #delete object properties if user altD/ShiftD an emitter object
    handler_scene_emitter_cleanup()

    #update active camera nodegroup
    update_active_camera_nodegroup()

    return None


# oooooooooooo                                                  
# `888'     `8                                                  
#  888         oooo d8b  .oooo.   ooo. .oo.  .oo.    .ooooo.    
#  888oooo8    `888""8P `P  )88b  `888P"Y88bP"Y88b  d88' `88b   
#  888    "     888      .oP"888   888   888   888  888ooo888   
#  888          888     d8(  888   888   888   888  888    .o   
# o888o        d888b    `Y888""8o o888o o888o o888o `Y8bod8P'   



@persistent
def scatter5_frame_pre(scene,desp): 

    #debug print
    dprint("HANDLER: 'scatter5_frame_pre'",depsgraph=True)

    #update active camera nodegroup
    update_active_camera_nodegroup()

    return None

@persistent
def scatter5_frame_post(scene,desp): 

    scat_scene = bpy.context.scene.scatter5

    #debug print
    dprint("HANDLER: 'scatter5_frame_post'",depsgraph=True)

    #update active camera nodegroup
    update_active_camera_nodegroup()

    return None


# ooooooooo.                               .o8                     
# `888   `Y88.                            "888                     
#  888   .d88'  .ooooo.  ooo. .oo.    .oooo888   .ooooo.  oooo d8b 
#  888ooo88P'  d88' `88b `888P"Y88b  d88' `888  d88' `88b `888""8P 
#  888`88b.    888ooo888  888   888  888   888  888ooo888  888     
#  888  `88b.  888    .o  888   888  888   888  888    .o  888     
# o888o  o888o `Y8bod8P' o888o o888o `Y8bod88P" `Y8bod8P' d888b    


# @persistent
# def scatter5_render_pre(scene,desp): 

#     scat_scene = bpy.context.scene.scatter5

#     #debug print
#     dprint("HANDLER: 'scatter5_render_pre'",depsgraph=True)

#     return None

# @persistent
# def scatter5_render_post(scene,desp): 

#     scat_scene = bpy.context.scene.scatter5

#     #debug print
#     dprint("HANDLER: 'scatter5_render_post'",depsgraph=True)
    
#     return None


# ooooooooo.                               .o8                                     .o8       oooooo     oooo  o8o
# `888   `Y88.                            "888                                    "888        `888.     .8'   `"'
#  888   .d88'  .ooooo.  ooo. .oo.    .oooo888   .ooooo.  oooo d8b  .ooooo.   .oooo888         `888.   .8'   oooo   .ooooo.  oooo oooo    ooo
#  888ooo88P'  d88' `88b `888P"Y88b  d88' `888  d88' `88b `888""8P d88' `88b d88' `888          `888. .8'    `888  d88' `88b  `88. `88.  .8'
#  888`88b.    888ooo888  888   888  888   888  888ooo888  888     888ooo888 888   888           `888.8'      888  888ooo888   `88..]88..8'
#  888  `88b.  888    .o  888   888  888   888  888    .o  888     888    .o 888   888            `888'       888  888    .o    `888'`888'
# o888o  o888o `Y8bod8P' o888o o888o `Y8bod88P" `Y8bod8P' d888b    `Y8bod8P' `Y8bod88P"            `8'       o888o `Y8bod8P'     `8'  `8'


from .. scattering.update_factory import update_is_rendered_view_nodegroup


overlay_to_restore = []
def set_overlay(boolean):
    """will toggle off overlay while in renderede view""" 

    if (boolean==True): #== restore

        global overlay_to_restore
        for space in overlay_to_restore:
            try: space.overlay.show_overlays = True
            except: pass #perhaps space do not exists anymore so we need to be careful 
        overlay_to_restore = []

    elif (boolean==False):

        for space in all_3d_viewports():
            if space.shading.type=="RENDERED":
                if space.overlay.show_overlays: 
                    overlay_to_restore.append(space)
                    space.overlay.show_overlays = False

    return None 


shading_type_owner = object()

def shading_type_callback(*args):
    """message bus rendered view check function""" 

    dprint("MSGBUS: 'S5 View3DShading.type'",depsgraph=True)

    #check for rendered view
    is_rdr = is_rendered_view()

    #set/reset overlay
    if bpy.context.scene.scatter5.update_auto_overlay_rendered:
        set_overlay(not is_rdr)

    #update is rendered view nodegroup
    update_is_rendered_view_nodegroup(value=is_rdr)

    return None 


# oooooooooooo       .o8   o8o      .        ooo        ooooo                 .o8
# `888'     `8      "888   `"'    .o8        `88.       .888'                "888
#  888          .oooo888  oooo  .o888oo       888b     d'888   .ooooo.   .oooo888   .ooooo.
#  888oooo8    d88' `888  `888    888         8 Y88. .P  888  d88' `88b d88' `888  d88' `88b
#  888    "    888   888   888    888         8  `888'   888  888   888 888   888  888ooo888
#  888       o 888   888   888    888 .       8    Y     888  888   888 888   888  888    .o
# o888ooooood8 `Y8bod88P" o888o   "888"      o8o        o888o `Y8bod8P' `Y8bod88P" `Y8bod8P'


edit_mode_owner = object()
was_edit = False

def edit_mode_callback(*args):
    """message bus rendered view check function""" 

    dprint("MSGBUS: 'S5 EditMode'",depsgraph=True)

    emitter = bpy.context.scene.scatter5.emitter
    if (emitter is None):
        return None 
    if (emitter is not bpy.context.object):
        return None 

    global was_edit

    if was_edit and (bpy.context.object.mode == "OBJECT"):
        emitter.scatter5.get_estimated_square_area()

    was_edit = (bpy.context.object.mode == "EDIT")

    return None 


# ooooo                                  .o8       ooooooooo.                          .
# `888'                                 "888       `888   `Y88.                      .o8
#  888          .ooooo.   .oooo.    .oooo888        888   .d88'  .ooooo.   .oooo.o .o888oo
#  888         d88' `88b `P  )88b  d88' `888        888ooo88P'  d88' `88b d88(  "8   888
#  888         888   888  .oP"888  888   888        888         888   888 `"Y88b.    888
#  888       o 888   888 d8(  888  888   888        888         888   888 o.  )88b   888 .
# o888ooooood8 `Y8bod8P' `Y888""8o `Y8bod88P"      o888o        `Y8bod8P' 8""888P'   "888"


def add_msgbusses(): 

    bpy.msgbus.subscribe_rna(
        key=(bpy.types.View3DShading, "type"),
        owner=shading_type_owner,
        notify=shading_type_callback,
        args=(None,),
        options={"PERSISTENT"},
        )

    bpy.msgbus.subscribe_rna(
        key=(bpy.types.Object, "mode"),
        owner=edit_mode_owner,
        notify=edit_mode_callback,
        args=(None,),
        options={"PERSISTENT"},
        )

    return None 


@persistent
def scatter5_load_post(scene,desp): 

    #debug print
    dprint(f"HANDLER: 'scatter5_load_post'", depsgraph=True)

    #need to add message bus on each
    add_msgbusses()

    return None


#   ooooooooo.
#   `888   `Y88.
#    888   .d88'  .ooooo.   .oooooooo
#    888ooo88P'  d88' `88b 888' `88b
#    888`88b.    888ooo888 888   888
#    888  `88b.  888    .o `88bod8P'
#   o888o  o888o `Y8bod8P' `8oooooo.
#                          d"     YD
#                          "Y88888P'


def all_handlers():
    """return a list of handler stored in .blend"""

    return_list = []
    
    for oh in bpy.app.handlers:
        try:
            for h in oh:
                return_list.append(h)
        except: pass
    
    return return_list


def register():

    #msgbus

    add_msgbusses()

    #depsgraph

    if (scatter5_depsgraph not in all_handlers()):
        bpy.app.handlers.depsgraph_update_post.append(scatter5_depsgraph)

    #frame_change

    if (scatter5_frame_pre not in all_handlers()):
        bpy.app.handlers.frame_change_pre.append(scatter5_frame_pre)

    if (scatter5_frame_post not in all_handlers()):
        bpy.app.handlers.frame_change_post.append(scatter5_frame_post)
        
    #render

    # if (scatter5_render_pre not in all_handlers()):
    #     bpy.app.handlers.render_pre.append(scatter5_render_pre)

    # if (scatter5_render_post not in all_handlers()):
    #     bpy.app.handlers.render_post.append(scatter5_render_post)

    #on blend open 

    if (scatter5_load_post not in all_handlers()):
        bpy.app.handlers.load_post.append(scatter5_load_post)


    return


def unregister():

    #msgbus

    bpy.msgbus.clear_by_owner(shading_type_owner)

    bpy.msgbus.clear_by_owner(edit_mode_owner)

    #remove all handlers 

    for h in all_handlers():

        #depsgraph

        if(h.__name__=="scatter5_depsgraph"):
            bpy.app.handlers.depsgraph_update_post.remove(h)

        #frame_change

        if(h.__name__=="scatter5_frame_pre"):
            bpy.app.handlers.frame_change_pre.remove(h)

        if(h.__name__=="scatter5_frame_post"):
            bpy.app.handlers.frame_change_post.remove(h)

        #render 

        # if(h.__name__=="scatter5_render_pre"):
        #     bpy.app.handlers.render_pre.remove(h)

        # if(h.__name__=="scatter5_render_post"):
        #     bpy.app.handlers.render_post.remove(h)

        #on blend open 

        if(h.__name__=="scatter5_load_post"):
            bpy.app.handlers.load_post.remove(h)

    return