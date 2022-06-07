import bpy
from bpy.props import StringProperty, EnumProperty

from .modals.adjust_bevel import HOPS_OT_AdjustBevelOperator
from .modals.st3_array import HOPS_OT_ST3_Array
from ..operators.booleans.bool_modal import HOPS_OT_BoolModal


class HOPS_OT_POPOVER(bpy.types.Operator):
    bl_idname = "hops.popover_data"
    bl_label = "HopsPopOverData"
    bl_description = "Popover Data"
    bl_options = {"INTERNAL"}

    calling_ops: StringProperty(default="")

    str_1: StringProperty(default="")


    def execute(self, context):
        
        if self.calling_ops == 'BEVEL_ADJUST':
            HOPS_OT_AdjustBevelOperator.mod_selected = self.str_1
        
        elif self.calling_ops == 'ARRAY_V2':
            HOPS_OT_ST3_Array.mod_selected = self.str_1

        elif self.calling_ops == 'BOOL_MODAL':
            HOPS_OT_BoolModal.selected_operation = self.str_1

        return {'FINISHED'}