
# 88     88  dP""b8 888888 88b 88 .dP"Y8 888888
# 88     88 dP   `" 88__   88Yb88 `Ybo." 88__
# 88  .o 88 Yb      88""   88 Y88 o.`Y8b 88""
# 88ood8 88  YboodP 888888 88  Y8 8bodP' 888888


########## - Script License

# All scripts of this plugin have the same this license:
#
# "Scatter5" plugin for Blender 3d
# Copyright (C) 2021 'BD3D DIGITAL DESIGN, SLU'
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

########## - Digital Content License

# External content used by this plugin are NOT under GPL licensing. 
# They are under Royalty free License and therefore CANNOT be redistributed witouth the author agreement. 
# 'External content' are content such as .blend files or image files for example.
# please read the license .txt for more information. 

########## - Contact

# Join BD3D on the blendermarket
# https://www.blendermarket.com/creators/bd3d-store



# 8888b.     db    888888    db        8b    d8    db    88b 88    db     dP""b8 888888 8b    d8 888888 88b 88 888888
#  8I  Yb   dPYb     88     dPYb       88b  d88   dPYb   88Yb88   dPYb   dP   `" 88__   88b  d88 88__   88Yb88   88
#  8I  dY  dP__Yb    88    dP__Yb      88YbdP88  dP__Yb  88 Y88  dP__Yb  Yb  "88 88""   88YbdP88 88""   88 Y88   88
# 8888Y"  dP""""Yb   88   dP""""Yb     88 YY 88 dP""""Yb 88  Y8 dP""""Yb  YboodP 888888 88 YY 88 888888 88  Y8   88    https://asciiflow.com/

# <<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<
# >>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>> User Interaction <<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<
# >>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
#
#
# ┌──────────────────┐  ┌──────────────┐  ┌───────────────┐  ┌─────────────────────────┐
# │tweaking a setting│-►│update factory│-►│update function│-►│changing geonode nodetree│-► blender do it's thing, change instance
# └──────────────────┘  └──────────────┘  └───────────────┘  └─────────────────────────┘
#
# <<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<
# >>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>> How Presets Are handled <<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<
# >>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
#
#                                    ┌────────┐
#                                    │  Json  │ 
#                                    └───▲────┘   
#                                        │ 
#                                    ┌───▼────┐ settings<>dict<>json done in presetting.py -> /!\ Data Loss from settings to dict
#                                    │  Dict  │
#                                    └───▲────┘
#                                        ├──────────────────────────┐
#  ------------------------              │  update_factory.py       │
#  |    copy/paste buffer |    ┌─────────▼───────────────┐          │
#  |  synchronize settings|◄--►│ scatter5.particlesystems│          │
#  |updatefactory features|    │  particle_settings.py   │          │
#  ------------------------    └─────────┬───────────────┘          │
#                                        │                          │ texture_datablock.py
#                                ┌───────▼──────────┐       ┌───────▼───────────┐
#                                │ Geonode NodeTree ◄───────┤ NodeTree.scatter5 │ #special nodegroup dedicated to procedural textures
#                                └───────┬──────────┘       └───────────────────┘
#                                        ▼                  
#                                  BlenderInstancing                           
#                                
#   ┌───────────────────────────────────────────────────────────────────────────────────────────────────────────────────┐ 
#   │ >>>> Implementating a new feature into the procedural workflow Work-Steps:                                        │                                                                                
#   │ ───────────────────────────────────────────────────────────────────────────────────────────────────────────────── │                                                                                        
#   │  > Prototype the feature in Geonode then implement in "resouces/blends/data.blend" color-coded and correcly named │                                                                                                                          
#   │  > Tweaking support:                                                                                              │                             
#   │      > Set up properties in "particle_settings.py" with correct values & same name as in nodetree                 │                                                                                                          
#   │      > Dress up settings in GUI "ui_tweaking.py"                                                                  │                                                          
#   │      > Bridge settings to nodetree from update factory in "update_factory.py"                                     │                                                                                                                                
#   │  > Header menu features & buffers/synch:                                                                          │                                 
#   │      > Implement new category type_s_ in "gui_settings.py" and in "properties.__init__.py"                        │ #-> category API needed because we can't pass string object directly in menu ptr ctxt    
#   │      > Lock/unlock -> implement _locked boolean in "particle_settings.py"                                         │     same settings category concept also used for sync, copy/paste & lock                                                        
#   │      > Synchronize settings: update properties and gui in "synchronize.py"                                        │     
#   │  > Preset support:                                                                                                │                           
#   │      > Update "presetting.py" data management                                                                     │      
#   │      > Update SCATTER5_PT_settings category preset paste support from ui_menu.py                                  |
#   └───────────────────────────────────────────────────────────────────────────────────────────────────────────────────┘
#
# <<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<
# >>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>> Inheritence Structure <<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<
# >>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
#
#
#    ┌─────────────────────┐
#    │Emitter Target Object│ scat_scene = bpy.context.scene.scatter5
#    └──────────┬──┬───────┘ emitter = scat_scene.emitter
#               │  │   ┌────────────────┐
#               │  └───►Masks Collection│ emitter.scatter5.mask_systems
#               │      └────────────────┘ (== per object property)
#    ┌──────────▼──────────┐
#    │Particles Collection │ psys = emitter.scatter5.particle_systems
#    └─┬──┬──┬──┬──┬──┬──┬─┘ (== per object property)
#     .. .. .│ .. .. .. ..
#            │
#    ┌───────▼───────┐
#    │Particle System│ psy = psys["Foo"]
#    └─────┬────┬────┘                                      
#          │    │ ┌────────┐ 
#          │    └─►Settings│-> update factory -> update function -> NodegroupChange
#          │      └────────┘   
#    ┌─────▼─────────────────────────────┐
#    │ScatterObj/Modifier/UniqueNodegroup│
#    └───────────────────────────────────┘  
#      scatter_obj = psy.scatter_obj
#      used either for: 
#          -take data from emitter with object info node
#          -use the scatter_object data vertices for manual point distribution
#       Note that scatter_obj can switch mesh-data to store multiple manual point distribution method.
#



bl_info = {
    "name"        : "Scatter5",
    "author"      : "BD3D, Carbon2",
    "description" : "Scatter5 Release Candidate for blender 3.0",
    "blender"     : (2, 93, 0),
    "version"     : (5, 0),
    "wiki_url"    : "", #TODO create new website google doc
    "tracker_url" : "https://www.blendermarket.com/creators/bd3d-store",
    "support"     : "COMMUNITY",
    "category"    : "", #No Categories = To the top! 
}


import bpy

#from . import cpp #cpp functions only for baking for now 
from . import resources
from . import manual 
from . import properties
from . import scattering
from . import procedural_vg
from . import graph_remap
from . import utils
from . import terrain
from . import handlers
#from . import baking #not used for now prolly for 5.1
from . import ui
from . import external


main_modules = [ 
    #cpp, #cpp functions only for baking for now 
    resources,
    manual,
    properties,
    scattering,
    procedural_vg, 
    graph_remap,
    utils,
    terrain,
    handlers,
    #baking, #not used for now prolly for 5.1
    ui, 
    external,
    ]


def cleanse_modules():
    """remove all plugin modules from sys.modules, will load them again, creating an effective hit-reload soluton
    Not sure why blender is no doing this already whe disabling a plugin..."""
    #https://devtalk.blender.org/t/plugin-hot-reload-by-cleaning-sys-modules/20040

    import sys
    all_modules = sys.modules 
    all_modules = dict(sorted(all_modules.items(),key= lambda x:x[0])) #sort them
    
    for k,v in all_modules.items():
        if k.startswith(__name__):
            del sys.modules[k]

    return None 

def register():

    for m in main_modules:
        m.register()
    
    # NOTE: populate collection property of shortcuts from defaults. i can't call it directly, because at this stage bpy.context is not `real`, i am not happy with it, but i don't see a way to have CollectionProperty filled with data at registration time..
    from .manual.config import first_run
    bpy.app.timers.register(first_run, first_interval=1, )
    
    return None

def unregister():

    for m in reversed(main_modules):
        m.unregister()

    #final step, remove modules from sys.modules 
    cleanse_modules()

    return None



#if __name__ == "__main__":
#    register()