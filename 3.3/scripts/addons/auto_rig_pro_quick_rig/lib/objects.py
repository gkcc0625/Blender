import bpy, os
from .bone_edit import *
from .context import *


def is_object_hidden(obj_to_get):
    if obj_to_get.hide_get() == False and obj_to_get.hide_viewport == False:
        return False
    else:
        return True
        

def get_object(name, view_layer_change=False):
    ob = bpy.data.objects.get(name)
    if ob:
        if view_layer_change:
            found = False
            for v_o in bpy.context.view_layer.objects:
                if v_o == ob:
                    found = True
            if not found:# object not in view layer, add to the base collection
                bpy.context.collection.objects.link(ob)

    return ob


def delete_object(obj):
    bpy.data.objects.remove(obj, do_unlink=True)


def set_active_object(object_name):
     bpy.context.view_layer.objects.active = bpy.data.objects[object_name]
     bpy.data.objects[object_name].select_set(state=True)