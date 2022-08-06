
#extension of the os.path module i guess? 

import bpy, os, subprocess, shlex, platform, glob


def get_direct_folder_paths(main):
    """get all directories paths within given path"""
    for _, dirnames, _ in os.walk(main):
        return [os.path.join(main,d) for d in dirnames]


def get_direct_files_paths(main):
    """get all files paths within given path"""
    for _, _, files in os.walk(main):
        return [os.path.join(main,d) for d in files]


def get_subpaths(main):
    """get all existing subpaths within the given path"""
    return [os.path.join(r,file) for r,d,f in os.walk(main) for file in f] 
    #could use `glob.glob(f"{main}/**/*")` perhaps? not sure need more research 


def search_for_path(main, file, extension, search_first=None):
    """search everywhere for a file, if found, return it's path else return None, there's a search_first option where the search is firstly done from given peth"""

    if not os.path.exists(main):
        raise Exception("The path you gave doesn't exists")

    if not file.endswith(extension):
        file += extension
    
    #search first?
    if (search_first is not None):

        if not os.path.exists(search_first):
            raise Exception("The path you gave doesn't exists (search_first)")

        #search in given specific folder first
        for p in get_subpaths(search_first):
            if (os.path.basename(p)==file):
                return p

        #also try parent folder perhaps?
        for p in get_subpaths(os.path.dirname(search_first)): #double searching... but that's ok
            if (os.path.basename(p)==file):
                return p

        #if not cound will proceed to full search below

    #else search everywhere in main branch
    for p in get_subpaths(main):
        if (os.path.basename(p)==file):
            return p
            
    #nothing found 
    return ""


#   .oooooo.   oooo
#  d8P'  `Y8b  `888
# 888           888   .oooo.    .oooo.o  .oooo.o  .ooooo.   .oooo.o
# 888           888  `P  )88b  d88(  "8 d88(  "8 d88' `88b d88(  "8
# 888           888   .oP"888  `"Y88b.  `"Y88b.  888ooo888 `"Y88b.
# `88b    ooo   888  d8(  888  o.  )88b o.  )88b 888    .o o.  )88b
#  `Y8bood8P'  o888o `Y888""8o 8""888P' 8""888P' `Y8bod8P' 8""888P'


class SCATTER5_OT_open_directory(bpy.types.Operator):

    bl_idname      = "scatter5.open_directory"
    bl_label       = ""
    bl_description = ""

    folder : bpy.props.StringProperty()

    def execute(self, context):

        if not os.path.exists(self.folder):
            raise Exception("The folder you try to open does not exists")
            return {'FINISHED'}             

        if platform.system() == 'Windows':
            os.startfile(self.folder)

        elif platform.system() == 'Linux':
            subprocess.call(['xdg-open', self.folder])

        elif platform.system() == 'Darwin':
            os.system('open {}'.format(shlex.quote(self.folder)))

        return {'FINISHED'} 


classes = [

    SCATTER5_OT_open_directory,

    ]
