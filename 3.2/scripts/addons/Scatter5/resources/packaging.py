
# ooooooooo.                       oooo                              o8o
# `888   `Y88.                     `888                              `"'
#  888   .d88'  .oooo.    .ooooo.   888  oooo   .oooo.    .oooooooo oooo  ooo. .oo.    .oooooooo
#  888ooo88P'  `P  )88b  d88' `"Y8  888 .8P'   `P  )88b  888' `88b  `888  `888P"Y88b  888' `88b
#  888          .oP"888  888        888888.     .oP"888  888   888   888   888   888  888   888
#  888         d8(  888  888   .o8  888 `88b.  d8(  888  `88bod8P'   888   888   888  `88bod8P'
# o888o        `Y888""8o `Y8bod8P' o888o o888o `Y888""8o `8oooooo.  o888o o888o o888o `8oooooo.
#                                                        d"     YD                    d"     YD
#                                                        "Y88888P'                    "Y88888P'
 

import bpy, zipfile

from . import directories
from . translate import translate




def unzip_in_location( zip_path, location_path, ):

    with zipfile.ZipFile( zip_path, 'r') as z:
        z.extractall( location_path )

    return 


#                                         .                                  oooo
#                                       .o8                                  `888
#         .oooo.o  .ooooo.   .oooo.   .o888oo oo.ooooo.   .oooo.    .ooooo.   888  oooo
#        d88(  "8 d88' `"Y8 `P  )88b    888    888' `88b `P  )88b  d88' `"Y8  888 .8P'
#        `"Y88b.  888        .oP"888    888    888   888  .oP"888  888        888888.
#  .o.   o.  )88b 888   .o8 d8(  888    888 .  888   888 d8(  888  888   .o8  888 `88b.
#  Y8P   8""888P' `Y8bod8P' `Y888""8o   "888"  888bod8P' `Y888""8o `Y8bod8P' o888o o888o
#                                              888
#                                             o888o



class SCATTER5_OT_install_package(bpy.types.Operator):

    bl_idname      = "scatter5.install_package"
    bl_label       = "install_package"
    bl_description = ""
    bl_options     = {'INTERNAL'}

    filepath : bpy.props.StringProperty(subtype="FILE_PATH")
    popup_menu : bpy.props.BoolProperty(default=True)

    def execute(self, context):
            
        #check if file is .scatpack
        if not self.filepath.endswith(".scatpack"):
            
            print("Scatpack File Incorrect")
            if self.popup_menu:
                bpy.ops.scatter5.popup_menu( msgs=translate("Selected File is not a '.scatpack' format"), )
            self.popup_menu = True
            return {'FINISHED'}    
            
        #check if creator of .scatpack is dummy and can't create the zipfile structure properly 
        with zipfile.ZipFile( self.filepath , 'r') as z:
            IsCorrect = False
            for p in z.namelist():
                if ( p.startswith("_presets_") or p.startswith("_biomes_") or p.startswith("_bitmaps_")):
                    IsCorrect = True 
            if IsCorrect == False:

                print("Unpacking Scatpack Failed") 
                if self.popup_menu:
                    bpy.ops.scatter5.popup_menu( msgs=translate("your '.scatpack' structure is wrong, it doesn't have a '_presets_' nor '_biomes_' folder on first level"), )
                self.popup_menu = True
                return {'FINISHED'}  

        #install .scatpack
        unzip_in_location( self.filepath , directories.lib_library)

        #reload all libs
        bpy.ops.scatter5.reload_biome_library()
        bpy.ops.scatter5.reload_preset_gallery()

        #Great Success!
        if self.popup_menu:
            bpy.ops.scatter5.popup_menu( title="Success!", icon="CHECKMARK", msgs=translate("Installation Successful"), )
        self.popup_menu = True
        return {'FINISHED'}

    def invoke(self, context, event):
        context.window_manager.fileselect_add(self)
        return {'RUNNING_MODAL'}
 



classes = [

    SCATTER5_OT_install_package,

    ]
