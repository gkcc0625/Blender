
#   .oooooo.                                         ooo        ooooo
#  d8P'  `Y8b                                        `88.       .888'
# 888      888 oo.ooooo.   .ooooo.  ooo. .oo.         888b     d'888   .oooo.   ooo. .oo.    .oooo.    .oooooooo  .ooooo.  oooo d8b
# 888      888  888' `88b d88' `88b `888P"Y88b        8 Y88. .P  888  `P  )88b  `888P"Y88b  `P  )88b  888' `88b  d88' `88b `888""8P
# 888      888  888   888 888ooo888  888   888        8  `888'   888   .oP"888   888   888   .oP"888  888   888  888ooo888  888
# `88b    d88'  888   888 888    .o  888   888        8    Y     888  d8(  888   888   888  d8(  888  `88bod8P'  888    .o  888
#  `Y8bood8P'   888bod8P' `Y8bod8P' o888o o888o      o8o        o888o `Y888""8o o888o o888o `Y888""8o `8oooooo.  `Y8bod8P' d888b
#               888                                                                                   d"     YD
#              o888o                                                                                  "Y88888P'


import bpy, platform, os, ctypes



class SCATTER5_OT_open_manager(bpy.types.Operator):

    bl_idname      = "scatter5.open_manager"
    bl_label       = ""
    bl_description = ""

    manager_category : bpy.props.StringProperty()

    def execute(self, context):

        addon_prefs = bpy.context.preferences.addons["Scatter5"].preferences
            
        #save current 3dview area 
        old_context = bpy.context.area 
        old_area = bpy.context.area.ui_type

        #change current 3d view to new type 
        addon_prefs.manager_category = self.manager_category
        bpy.context.area.ui_type = 'PREFERENCES'
        bpy.context.preferences.active_section= 'ADDONS'
        bpy.context.window_manager.addon_support = {'COMMUNITY'}
        bpy.context.window_manager.addon_search='Scatter5'

        #then dupplicate into new windows 
        bpy.ops.screen.area_dupli('INVOKE_DEFAULT')

        #if Window, use ctypes put on top & change size
        if platform.system() == 'Windows':
            ctypes.windll.user32.MoveWindow(
                ctypes.windll.user32.GetActiveWindow(), 
                int(addon_prefs.win_pop_location[0]), 
                int(addon_prefs.win_pop_location[1]), 
                int(addon_prefs.win_pop_size[0]), 
                int(addon_prefs.win_pop_size[1]), 
                )

        #restore viewport with old area
        old_context.ui_type = old_area

        #Register Impostors
        bpy.ops.scatter5.impost_addonprefs(state=True)

        return {'FINISHED'}




classes = [

    SCATTER5_OT_open_manager,    

    ]