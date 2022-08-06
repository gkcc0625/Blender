
#####################################################################################################
#       .                                          oooo                .
#     .o8                                          `888              .o8
#   .o888oo  .ooooo.  ooo. .oo.  .oo.   oo.ooooo.   888   .oooo.   .o888oo  .ooooo.
#     888   d88' `88b `888P"Y88bP"Y88b   888' `88b  888  `P  )88b    888   d88' `88b
#     888   888ooo888  888   888   888   888   888  888   .oP"888    888   888ooo888
#     888 . 888    .o  888   888   888   888   888  888  d8(  888    888 . 888    .o
#     "888" `Y8bod8P' o888o o888o o888o  888bod8P' o888o `Y888""8o   "888" `Y8bod8P'
#                                        888
#                                       o888o
#####################################################################################################


import bpy 
from .. resources.icons import cust_icon
from .. resources.translate import translate


# ooooo   ooooo                           .o8
# `888'   `888'                          "888
#  888     888   .ooooo.   .oooo.    .oooo888   .ooooo.  oooo d8b
#  888ooooo888  d88' `88b `P  )88b  d88' `888  d88' `88b `888""8P
#  888     888  888ooo888  .oP"888  888   888  888ooo888  888
#  888     888  888    .o d8(  888  888   888  888    .o  888
# o888o   o888o `Y8bod8P' `Y888""8o `Y8bod88P" `Y8bod8P' d888b


def main_panel_header(self):
    """draw main panels header"""

    addon_prefs = bpy.context.preferences.addons["Scatter5"].preferences
    scat_scene  = bpy.context.scene.scatter5
    emitter     = scat_scene.emitter
    layout      = self.layout

    if bpy.context.mode == 'PAINT_WEIGHT':
        row = layout.row()

        ope = row.row(align=True)
        ope.alignment = "RIGHT"
        ope.active = False
        op = ope.operator("scatter5.exec_line", text=emitter.name, icon="WPAINT_HLT", emboss=False ,depress=False)
        op.api = "bpy.ops.object.mode_set(mode='OBJECT')"
        op.description = translate("Quit weight painting mode, get back to object mode")

        layout.separator()
        return 

    if bpy.context.mode == 'PAINT_VERTEX':
        row = layout.row()

        ope = row.row(align=True)
        ope.alignment = "RIGHT"
        ope.active = False
        op = ope.operator("scatter5.exec_line", text=emitter.name, icon="VPAINT_HLT", emboss=False ,depress=False)
        op.api = "bpy.ops.object.mode_set(mode='OBJECT')"
        op.description = translate("Quit Vertex painting mode, get back to object mode")

        layout.separator()
        return 

    if (addon_prefs.emitter_method =="remove"):
        row = layout.row(align=False)

        ope = row.row(align=True)
        ope.alignment = "RIGHT"
        ope.active = False
        ope.operator("scatter5.exec_line",text=emitter.name, emboss=False, icon="EYEDROPPER",).api="bpy.context.scene.scatter5.emitter = None"

        layout.separator()
        return 

    elif (addon_prefs.emitter_method =="pin"):
        row = layout.row(align=False)

        ope = row.row(align=True)
        ope.alignment = "RIGHT"
        ope.active = False
        op = ope.operator("scatter5.property_toggle",text=emitter.name, emboss=False, icon="PINNED" if scat_scene.emitter_pinned else "UNPINNED",)
        op.api = "bpy.context.scene.scatter5.emitter_pinned"
        op.description = translate("Pin this target")

        layout.separator()
        return 

    elif (addon_prefs.emitter_method =="set_active"):
        row = layout.row(align=False)

        ope = row.row(align=True)
        ope.alignment = "RIGHT"
        ope.active = False
        ope.operator("scatter5.active_as_emitter",text=emitter.name, emboss=False, icon="RESTRICT_SELECT_OFF",)
            
        layout.separator()
        return 

    return 

# ooo        ooooo            o8o
# `88.       .888'            `"'
#  888b     d'888   .oooo.   oooo  ooo. .oo.
#  8 Y88. .P  888  `P  )88b  `888  `888P"Y88b
#  8  `888'   888   .oP"888   888   888   888
#  8    Y     888  d8(  888   888   888   888
# o8o        o888o `Y888""8o o888o o888o o888o


def main_spacing(layout):
    addon_prefs   = bpy.context.preferences.addons["Scatter5"].preferences
    return layout.separator(factor=addon_prefs.ui_main_when_open)

def main_panel(self,layout,prop_str="",icon="",name="",description="",disable=False):
    """draw main panel opening template"""

    addon_prefs   = bpy.context.preferences.addons["Scatter5"].preferences
    is_open       = eval(f"bpy.context.scene.scatter5.ui.{prop_str}")

    #customize UI from user choice, arrow or icon 
    is_arrow = addon_prefs.ui_use_arrow
    if is_arrow :
          icon = "DOWNARROW_HLT" if is_open else "RIGHTARROW_THIN"
    else: name = f"  {name}"

    #space on left
    row = layout.row(align=True)
    row.scale_y   = addon_prefs.ui_scale_y
    row.alignment = 'LEFT'
    row.separator(factor=0.5)

    #draw opening operator
    header = row.column(align=True)
    header.alignment = 'LEFT'

    #disable? 
    if addon_prefs.ui_use_active:
        header.active = is_open and not disable

    #we may wan't to have it always closed 
    operatr_id  = "scatter5.property_toggle" 
    if disable:
        operatr_id = "scatter5.dummy"
        is_open = False

    #toggle operator with correct arg icon
    if icon.startswith("W_"):
          args = {"text":name,"emboss":False,"icon_value":cust_icon(icon)}
    else: args = {"text":name,"emboss":False,"icon":icon}
    op = header.operator(operatr_id,**args)
    op.api = f"bpy.context.scene.scatter5.ui.{prop_str}"
    op.description = description

    return is_open


#  .oooooo..o              .o8
# d8P'    `Y8             "888
# Y88bo.      oooo  oooo   888oooo.
#  `"Y8888o.  `888  `888   d88' `88b
#      `"Y88b  888   888   888   888
# oo     .d8P  888   888   888   888
# 8""88888P'   `V88V"V8P'  `Y8bod8P'


def sub_spacing(layout):
    addon_prefs = bpy.context.preferences.addons["Scatter5"].preferences
    if addon_prefs.ui_use_dark_box:
          return layout.separator(factor=0.3)
    else: return layout.separator(factor=1.7)

def sub_panel( self,
               layout,
               prop_str="",
               icon="",
               name="",
               description="",
               doc="",
               panel=None,
               panel_icon=None,
               context_pointer_set=None,
               ):

    """draw sub panel opening template, use fct to add own settings""" 

    addon_prefs   = bpy.context.preferences.addons["Scatter5"].preferences
    is_open       = eval(f"bpy.context.scene.scatter5.ui.{prop_str}")
    scat_scene  = bpy.context.scene.scatter5
    emitter     = scat_scene.emitter

    #change layout from user prefs
    if addon_prefs.ui_use_dark_box:
        box = layout.box()
        header = box.box().row()
    else:
        col = layout.column(align=True)
        header = col.box().row()
        if is_open:
              box = col.box()
              box.separator(factor=1.50)
        else: box = None 

    #toggle operator with correct arg icon
    args = {"text":name,"emboss":False,}
    if type(icon) is int:
          args["icon_value"]=icon
    elif icon.startswith("W_"):
          args["icon_value"]=cust_icon(icon)
    else: args["icon"]=icon

    op = header.operator("scatter5.property_toggle",**args)
    op.api = f"bpy.context.scene.scatter5.ui.{prop_str}"
    op.description = description


    if panel: #possibility to add menu/operator in header with custom context ptr 

        m = header.row()
        m.active = False
        m.emboss = "NONE"
        if panel_icon:
            if panel_icon.startswith("W_"): 
                  args = {"text":"", "icon_value":cust_icon(panel_icon)}
            else: args = {"text":"", "icon":panel_icon}
        else:     args = {"text":"", "icon_value":cust_icon("W_PREFERENCES")}

        #transfer arg, this is needed for the graph tweaking panel.. 
        if context_pointer_set is not None:
            for cont in context_pointer_set:
                m.context_pointer_set(cont[0], cont[1]) 

        m.popover(panel=panel,**args)


    #documentation
    #removed the old documentation website, now everything is video-tutorial and texts in dialog boxes
    #header.operator("wm.url_open", text="" ,icon_value=cust_icon("W_QUESTION") ,emboss=False).url = doc
    if doc!="":
        docu = header.row()
        op = docu.operator("scatter5.popup_dialog",emboss=False,icon_value=cust_icon("W_QUESTION"),text="")
        op.msg = doc
        op.no_confirm = True
        
    return box, is_open  


# ooooooooooooo                                 oooo
# 8'   888   `8                                 `888
#      888       .ooooo.   .oooooooo  .oooooooo  888   .ooooo.
#      888      d88' `88b 888' `88b  888' `88b   888  d88' `88b
#      888      888   888 888   888  888   888   888  888ooo888
#      888      888   888 `88bod8P'  `88bod8P'   888  888    .o
#     o888o     `Y8bod8P' `8oooooo.  `8oooooo.  o888o `Y8bod8P'
#                         d"     YD  d"     YD
#                         "Y88888P'  "Y88888P'


def bool_toggle(layout, prop_api=None, prop_str="", label="", icon="", left_space=True, panel_close=True, enabled=True, ): #panel_close not used in the end?

    addon_prefs = bpy.context.preferences.addons["Scatter5"].preferences
    scat_ui     = bpy.context.scene.scatter5.ui
    is_toggled  =  getattr(prop_api,prop_str) == True


    if addon_prefs.ui_bool_use_standard:

        MainCol = layout.column(align=True)
        MainCol.enabled = enabled

        MainRow = MainCol.row()
        if left_space:
            _1tocol = MainRow.column() ; _1tocol.scale_x = 0.01
        _2tocol = MainRow.column() ; _2tocol.scale_x = 1.0

        prop=_2tocol.row()
        prop.scale_y = 1.05
        prop.prop(prop_api,prop_str,text=label)

        MainRow = MainCol.row()
        if left_space:
            _1tocol = MainRow.column() ; _1tocol.scale_x = 0.01
        _2tocol = MainRow.column() ; _2tocol.scale_x = 1.0
        _2tocol = MainRow.column() ; _2tocol.scale_x = 1.0
        _2tocol = MainRow.column() ; _2tocol.scale_x = 1.0
        tocol = MainRow.column() ; tocol.scale_x = 1.0

        return tocol, is_toggled

    else:

        MainRow = layout.row()
        MainRow.enabled = enabled
        if left_space:
            _1tocol = MainRow.column() ; _1tocol.scale_x = 0.01
        _2tocol = MainRow.column() ; _2tocol.scale_x = 1.0
        tocol = MainRow.column() ; tocol.scale_x = 1.0

        #Define Icon
        if addon_prefs.ui_bool_use_panelclose and not is_toggled :
            args = {"text":"", "icon":"PANEL_CLOSE"}
        else:
            if not icon.startswith("W_"): 
                  args = {"text":"", "icon":icon}
            else: args = {"text":"", "icon_value":cust_icon(icon)}

        _2tocol.prop(prop_api,prop_str, **args )
        tocol.label(text=label)

        return tocol, is_toggled