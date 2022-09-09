
#####################################################################################################
#
# oooooooooooo                    o8o      .       .                           ooooooooo.                                   oooo
# `888'     `8                    `"'    .o8     .o8                           `888   `Y88.                                 `888
#  888         ooo. .oo.  .oo.   oooo  .o888oo .o888oo  .ooooo.  oooo d8b       888   .d88'  .oooo.   ooo. .oo.    .ooooo.   888
#  888oooo8    `888P"Y88bP"Y88b  `888    888     888   d88' `88b `888""8P       888ooo88P'  `P  )88b  `888P"Y88b  d88' `88b  888
#  888    "     888   888   888   888    888     888   888ooo888  888           888          .oP"888   888   888  888ooo888  888
#  888       o  888   888   888   888    888 .   888 . 888    .o  888           888         d8(  888   888   888  888    .o  888
# o888ooooood8 o888o o888o o888o o888o   "888"   "888" `Y8bod8P' d888b         o888o        `Y888""8o o888o o888o `Y8bod8P' o888o
#
#####################################################################################################


import bpy

from .. resources.icons import cust_icon
from .. resources.translate import translate

from .. utils.str_utils import word_wrap 

from . import templates

def draw_emit_intro(self,context,):

        layout = self.layout
    
        word_wrap( string=translate("Scatter5 needs an Emitter-Object in order to work. Please Choose one Below."), layout=layout, max_char=41, alignment="CENTER",)                    
        #layout.separator(factor=0.33)
        layout.prop(bpy.context.scene.scatter5,"emitter",text="",icon_value=cust_icon("W_EMITTER"))
        word_wrap( string=translate("You can Swap Emitters at any Moment by Clicking on Panel's Headers."), layout=layout, max_char=41, alignment="CENTER",)
        layout.separator(factor=0.33)



        if context.object is not None:
            
            layout.separator(factor=4)
       
            word_wrap( string=translate("Add more vertices on active mesh ?"), layout=layout, max_char=41, alignment="CENTER",)
            
            layout.separator(factor=0.11)

            button = layout.row(align=True)
            button.scale_y=1.2
            button.enabled = context.object.type=="MESH"
            button.operator("scatter5.grid_bisect", text=translate("Bisect")+f" '{context.object.name}'",)

            # TODO for 5.1 or 6.0

            # layout.separator(factor=3)
       
            # word_wrap( string=translate("Create a wrapped surface that cover multiple objects at once?"), layout=layout, max_char=41, alignment="CENTER",)
            
            # layout.separator(factor=0.33)

            # button = layout.row(align=True)
            # button.scale_y=1.2
            # button.enabled = False
            # button.operator("scatter5.dummy", text=translate("Work in Progress."))

        layout.separator(factor=150)

        return None 


#    .oooooo.   oooo
#   d8P'  `Y8b  `888
#  888           888   .oooo.    .oooo.o  .oooo.o  .ooooo.   .oooo.o
#  888           888  `P  )88b  d88(  "8 d88(  "8 d88' `88b d88(  "8
#  888           888   .oP"888  `"Y88b.  `"Y88b.  888ooo888 `"Y88b.
#  `88b    ooo   888  d8(  888  o.  )88b o.  )88b 888    .o o.  )88b
#   `Y8bood8P'  o888o `Y888""8o 8""888P' 8""888P' `Y8bod8P' 8""888P'



class SCATTER5_PT_choose_emitter_object(bpy.types.Panel):

    bl_idname      = "SCATTER5_PT_choose_emitter_object"
    bl_label       = translate("Scatter5")
    bl_category    = "Scatter5"
    bl_space_type  = "VIEW_3D"
    bl_region_type = "UI"
    bl_context     = "objectmode"
    bl_order       = 0

    @classmethod
    def poll(cls, context, ):
        return context.scene.scatter5.emitter is None

    #def draw_header_preset(self, _context):
    #    templates.main_panel_header(self)

    def draw(self, context):
        draw_emit_intro(self,context,)
        return 

class SCATTER5_PT_choose_emitter_weight(bpy.types.Panel):

    bl_idname      = "SCATTER5_PT_choose_emitter_weight"
    bl_label       = translate("Scatter5")
    bl_category    = "Scatter5"
    bl_space_type  = "VIEW_3D"
    bl_region_type = "UI"
    bl_context     = "weightpaint"
    bl_order       = 0

    @classmethod
    def poll(cls, context, ):
        return context.scene.scatter5.emitter is None

    #def draw_header_preset(self, _context):
    #    templates.main_panel_header(self)

    def draw(self, context):
        draw_emit_intro(self,context,)
        return 

class SCATTER5_PT_choose_emitter_vcolor(bpy.types.Panel):

    bl_idname      = "SCATTER5_PT_choose_emitter_vcolor"
    bl_label       = translate("Scatter5")
    bl_category    = "Scatter5"
    bl_space_type  = "VIEW_3D"
    bl_region_type = "UI"
    bl_context     = "vertexpaint"
    bl_order       = 0

    @classmethod
    def poll(cls, context, ):
        return context.scene.scatter5.emitter is None

    #def draw_header_preset(self, _context):
    #    templates.main_panel_header(self)

    def draw(self, context):
        draw_emit_intro(self,context,)
        return 



classes = [

    SCATTER5_PT_choose_emitter_object,
    SCATTER5_PT_choose_emitter_weight,
    SCATTER5_PT_choose_emitter_vcolor,
    
    ]



#if __name__ == "__main__":
#    register()

