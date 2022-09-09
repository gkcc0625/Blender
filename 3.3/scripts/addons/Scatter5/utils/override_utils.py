
#Some function i use sometimes if context override do not work 

import bpy


def set_active_and_selection(new_active,new_selection):
    """to use if {override} on bpy.ops is failing. not sure why, but on many occasion on certain .ops override is problematic"""
    
    #support if active object has been deleted
    if new_active == None and new_selection == None: 
        return (None,None)
    
    #save return statement
    if bpy.context.object:
          active = bpy.context.object
          selection = bpy.context.selected_objects
    else: active = selection = None
    
    #set active and selection
    for o in bpy.context.scene.objects:
        o.select_set(state=False)
    for o in new_selection:
        o.select_set(state=True)
    bpy.context.view_layer.objects.active = new_active
    new_active.select_set(state=True)
    
    return (active,selection)


def set_mode(mode="OBJECT",active=None, selection=[]):
    """set mode to object + save selection & active then restore"""
    
    #bad blender api design for mode_set, not sure if there's an alternative?  anyway... 
    api_convert = {
        "OBJECT"        : "OBJECT"       , 
        "EDIT_MESH"     : "EDIT"         , 
        "SCULPT"        : "SCULPT"       , 
        "PAINT_VERTEX"  : "VERTEX_PAINT" , 
        "PAINT_WEIGHT"  : "WEIGHT_PAINT" , 
        "PAINT_TEXTURE" : "TEXTURE_PAINT",
        }
        
    #return statement 
    if bpy.context.object:
          ro = bpy.context.object
    else: ro = None 
    rm = bpy.context.mode
    rs = bpy.context.selected_objects
    
    #restore active and selection if arg
    if selection:
        for o in bpy.context.scene.objects:
            o.select_set(state=False)
        for o in selection:
            o.select_set(state=True)
    if active:
        bpy.context.view_layer.objects.active = active
        active.select_set(state=True)

    #change/restore mode
    if mode and rm != mode:
        bpy.ops.object.mode_set(mode=api_convert[mode])
    
    return (rm, ro, rs)
