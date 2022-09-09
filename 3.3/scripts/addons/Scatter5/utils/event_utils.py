
# get_even() Hack to get even from non modal nor invoke

#https://blender.stackexchange.com/questions/211544/detect-user-event-bpy-types-event-anywhere-from-blender/211590#211590

import bpy 


_event = None  

class SCATTER5_OT_get_event(bpy.types.Operator):
    """need to use an operator as bpy.types.Event only accessible from invoke() or modal()"""

    bl_idname  = "scatter5.get_event"
    bl_label   = ""

    def invoke(self, context, event):
        global _event
        _event = event
        return {'FINISHED'}

class NullEvent():
    """empty event class"""

    type=""
    value=""
    shift=False
    ctrl=False
    alt=False

def get_event():
    """get bpy.types.Event via bpy.types.Operator invoke(), if event not allowed, will return NullEvent() custom empty class"""
        
    if (not bpy.context.scene.scatter5.factory_event_listening_allow) or (bpy.context.window is None):
        return NullEvent()

    global _event
    bpy.ops.scatter5.get_event('INVOKE_DEFAULT')
    return _event



classes = [

    SCATTER5_OT_get_event,

    ]