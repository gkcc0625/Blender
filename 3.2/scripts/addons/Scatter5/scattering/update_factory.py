
#####################################################################################################
#  oooooooooooo                         .
#  `888'     `8                       .o8
#   888          .oooo.    .ooooo.  .o888oo  .ooooo.  oooo d8b oooo    ooo
#   888oooo8    `P  )88b  d88' `"Y8   888   d88' `88b `888""8P  `88.  .8'
#   888    "     .oP"888  888         888   888   888  888       `88..8'
#   888         d8(  888  888   .o8   888 . 888   888  888        `888'
#  o888o        `Y888""8o `Y8bod8P'   "888" `Y8bod8P' d888b        .8'
#                                                              .o..P'
#                                                              `Y8P'
#####################################################################################################


import bpy 
import random

from .. resources.translate import translate

from .. utils.extra_utils import dprint
from .. utils.extra_utils import is_rendered_view
from .. utils.event_utils import get_event 

from . synchronize import get_sync_siblings


#####################################################################################################


#Update factory:
#Every settings of per particle systems need updates to take action in the Geonode engine or do else
#In order to keep everything in track, I created this update factory that will return a function. 
#Because we use such data-flow we can implement cool features such as refresh method, alt support, settings synchronization ect..
#it's also really handy to organize all actions in a single place. 

#What's heppening in here?
#Settings in particle_settings.py -> update_fct=factory() -> option add delay to fct -> exec adequate update fct -> add synchronize/batch support 


# oooooo   oooooo     oooo
#  `888.    `888.     .8'
#   `888.   .8888.   .8'   oooo d8b  .oooo.   oo.ooooo.  oo.ooooo.   .ooooo.  oooo d8b
#    `888  .8'`888. .8'    `888""8P `P  )88b   888' `88b  888' `88b d88' `88b `888""8P
#     `888.8'  `888.8'      888      .oP"888   888   888  888   888 888ooo888  888
#      `888'    `888'       888     d8(  888   888   888  888   888 888    .o  888
#       `8'      `8'       d888b    `Y888""8o  888bod8P'  888bod8P' `Y8bod8P' d888b
#                                              888        888
#                                             o888o      o888o


def factory(prop_name, is_delayed=False, alt_support=True, synchronize=True,): #argument to have precise control over update factory behavior per property
    """wrapper of update function, will also search for according function inthe update_factory all UPDTASK automatically"""

    def fct(self,context):

        #Real Time Update? 
        if (bpy.context.scene.scatter5.factory_delay_allow==False) or (is_delayed==False):
            
            #dprint("factory(update_realtime) ->"+prop_name)
            update_dispatcher(self, prop_name, alt_support=alt_support, synchronize=synchronize,)
            return None 

        #Delayed update? 
        if (bpy.context.scene.scatter5.factory_update_method=="update_delayed"): 
            
            if (bpy.context.scene.scatter5.factory_update_delay==0):
                
                #dprint("factory(update_delayed==0) ->"+prop_name)
                update_dispatcher(self, prop_name, alt_support=alt_support, synchronize=synchronize,)
                return None

            #dprint("factory update_delayed->"+prop_name)
            add_delay_to_function(
                interval=bpy.context.scene.scatter5.factory_update_delay,
                function=update_dispatcher, 
                arg=[self, prop_name,], 
                kwarg={"alt_support":alt_support, "synchronize":synchronize,} 
                )
            return None 

        #On mouse release Update? 
        if (bpy.context.scene.scatter5.factory_update_method=="update_on_release"):

            #dprint("factory(update_on_release) ->"+prop_name)
            exec_funtion_on_mouse_release(
                function=update_dispatcher, 
                arg=[self, prop_name,],
                kwarg={"alt_support":alt_support, "synchronize":synchronize,} 
                )
            return None

    return fct


#Note update delay can by avoid by turning the global switch "bpy.context.scene.scatter5.factory_delay_allow" to False


IsTime = True
def add_delay_to_function(interval=0, function=None, arg=[], kwarg={},):
    """add delay to function execution"""

    #already on timer, skip
    global IsTime
    if not IsTime:
        return None 

    def delay_timer():

        old_factory_delay_allow = bpy.context.scene.scatter5.factory_delay_allow
        bpy.context.scene.scatter5.factory_delay_allow = False
        function(*arg,**kwarg)
        bpy.context.scene.scatter5.factory_delay_allow = old_factory_delay_allow

        global IsTime
        IsTime = True

        return None 

    #launching timer 
    bpy.app.timers.register(delay_timer, first_interval=interval)
    IsTime = False

    return None 


IsWaiting = False
Event = None 
def exec_funtion_on_mouse_release(function=None, arg=[], kwarg={},):
    """if "LEFTMOUSE PRESS" loop until no more pressed"""

    #if is waiting already, skip
    global IsWaiting
    if IsWaiting:
        return None 

    event = get_event()
    
    #if user is hitting enter, update directly
    if (event.type=="RET"):

        old_factory_delay_allow = bpy.context.scene.scatter5.factory_delay_allow
        bpy.context.scene.scatter5.factory_delay_allow = False
        function(*arg,**kwarg)
        bpy.context.scene.scatter5.factory_delay_allow = old_factory_delay_allow

        return None 
        
    def wait_for_mouse_release():

        dprint("PROP_FCT >>> wait_for_mouse_release")

        if (event.value!="PRESS"):


            old_factory_delay_allow = bpy.context.scene.scatter5.factory_delay_allow
            bpy.context.scene.scatter5.factory_delay_allow = False
            function(*arg,**kwarg)
            bpy.context.scene.scatter5.factory_delay_allow = old_factory_delay_allow

            global IsWaiting
            IsWaiting = False

            return None 

        return 0.1

    #if user is tweaking with left mouse click hold, launch timer to detect when he is done
    if (event.value=="PRESS"):

        dprint("PROP_FCT >>> LAUNCHING wait_for_mouse_release")
        IsWaiting = True
        bpy.app.timers.register(wait_for_mouse_release)
    
    return None 


#
# oooooooooo.    o8o                                    .             oooo
# `888'   `Y8b   `"'                                  .o8             `888
#  888      888 oooo   .oooo.o oo.ooooo.   .oooo.   .o888oo  .ooooo.   888 .oo.   
#  888      888 `888  d88(  "8  888' `88b `P  )88b    888   d88' `"Y8  888P"Y88b  
#  888      888  888  `"Y88b.   888   888  .oP"888    888   888        888   888  
#  888     d88'  888  o.  )88b  888   888 d8(  888    888 . 888   .o8  888   888  
# o888bood8P'   o888o 8""888P'  888bod8P' `Y888""8o   "888" `Y8bod8P' o888o o888o
#                               888
#                              o888o
#

# Normally all nodegraph tweaking is done here
# except for texture related data (transforms) as this is considered per texture data block
# see the scattering.texture_datablock module

def update_dispatcher(self, prop_name, alt_support=True, synchronize=True,):
    """update nodegroup dispatch, will """

    #self is 'psy', self.id_name is 'emitter'
    
    dprint(f"PROP_FCT: tweaking update : {self.name} -> {prop_name}")
    
    #get prop value
    value = getattr(self,prop_name)

    #get keyboard event 
    event = get_event() #TODO is this causing slow downs (launching a ope) ???? will need to check once optimization is at focus.

    #fetch update function from dict and execute the correct funtion depending on prop_name
    UPDTASK_fct(self, prop_name, value, event=event)

    #Alt Feature
    if (alt_support) and (bpy.context.scene.scatter5.factory_alt_allow) and (event.alt):
        update_alt(self, prop_name, value,)

    #Synchronize Feature
    if synchronize and (bpy.context.scene.scatter5.factory_synchronization_allow):
        update_sync(self, prop_name, value,)

    return None

def update_alt(self, prop_name, value,):
    """sync all selected psy"""

    dprint(f"     >>> event.alt")

    #turn off alt behavior to avoid feedback loop when batch changing selection settings
    #event will return None if factory_event_listening_allow is set to False
    bpy.context.scene.scatter5.factory_event_listening_allow = False

    psys_sel = self.id_data.scatter5.get_psys_selected() if (bpy.context.scene.scatter5.factory_alt_selection_method=="active") else [p  for o in bpy.data.objects for p in o.scatter5.particle_systems if p.sel]

    #copy active settings for all selected systems
    for p in psys_sel:
        if (p!=self) and (not p.is_locked(prop_name)):
            if getattr(p, prop_name) != value:
                setattr(p, prop_name, value,)

    #restore alt behavior
    bpy.context.scene.scatter5.factory_event_listening_allow = True

    return None 

def update_sync(self, prop_name, value,):
    """sync all settings while updating, settings get synced in the update factory"""

    #check if channels exists at first place
    if len(bpy.context.scene.scatter5.sync_channels)==0:
        return 

    #check if there's some stuff to synch with
    #if yes find dict of psy with prop category
    psy     = self
    emitter = self.id_data
    siblings = get_sync_siblings(self.id_data , self.name,)
    if len(siblings)==0:
        return 

    #is_random_seed function not supported by sync, will cause feedback loop
    if prop_name.endswith("_is_random_seed"):
        return 

    #need to disable some bahavior to avoid feedback loop
    old_factory_delay_allow , old_factory_event_listening_allow = bpy.context.scene.scatter5.factory_delay_allow , bpy.context.scene.scatter5.factory_event_listening_allow
    bpy.context.scene.scatter5.factory_delay_allow = bpy.context.scene.scatter5.factory_event_listening_allow = False
    
    dprint(f"     >>> synchronize")

    #synchronisz all syblings with given value
    for ch in siblings:
        
        #check if propn category is supported by channel options
        if len([c for c in ch["categories"] if prop_name.startswith(c)])==0:
            break

        #batch change properties if not set to sync value
        for p in ch["psys"]:
            if getattr(p, prop_name)!=value: #rget/rset not needed, synchronization not supported for nested featuremask
                if not p.is_locked(prop_name):
                    setattr(p, prop_name, value,)

    #restore prop bahavior
    bpy.context.scene.scatter5.factory_delay_allow , bpy.context.scene.scatter5.factory_event_listening_allow = old_factory_delay_allow , old_factory_event_listening_allow

    return 


# ooooo     ooo                  .o8                .                  oooooooooooo               .
# `888'     `8'                 "888              .o8                  `888'     `8             .o8
#  888       8  oo.ooooo.   .oooo888   .oooo.   .o888oo  .ooooo.        888          .ooooo.  .o888oo
#  888       8   888' `88b d88' `888  `P  )88b    888   d88' `88b       888oooo8    d88' `"Y8   888
#  888       8   888   888 888   888   .oP"888    888   888ooo888       888    "    888         888
#  `88.    .8'   888   888 888   888  d8(  888    888 . 888    .o       888         888   .o8   888 .
#    `YbodP'     888bod8P' `Y8bod88P" `Y888""8o   "888" `Y8bod8P'      o888o        `Y8bod8P'   "888"
#                888
#               o888o


def generate_umask_UPTDTASKS(name=""):
    """code generation, automatize the creation of the UPDTASK function for the universal mask system"""

    d = {}

    def _generated_mask_ptr(self, prop_name, value, event=None, bypass=False,):
        named_attribute(self,prop_name,value)

    def _generated_mask_reverse(self, prop_name, value, event=None, bypass=False,):
        node_value(self, f"umask {name}", value, entry="input", i=6)

    def _generated_mask_method(self, prop_name, value, event=None, bypass=False,):
        node_value(self, f"umask {name}", get_enum_idx(self, prop_name, value,), entry="input", i=7)

    def _generated_mask_color_sample_method(self, prop_name, value, event=None, bypass=False,):
        node_value(self, f"umask {name}", get_enum_idx(self, prop_name, value,), entry="input", i=8)

    def _generated_mask_id_color_ptr(self, prop_name, value, event=None, bypass=False,):
        node_value(self, f"umask {name}", list_to_color(value), entry="input", i=9)

    def _generated_mask_noise_scale(self, prop_name, value, event=None, bypass=False,):
        node_value(self, f"umask {name}", value, entry="input", i=11)

    def _generated_mask_noise_brightness(self, prop_name, value, event=None, bypass=False,):
        node_value(self, f"umask {name}", value, entry="input", i=12)

    def _generated_mask_noise_contrast(self, prop_name, value, event=None, bypass=False,):
        node_value(self, f"umask {name}", value, entry="input", i=13)
    
    d[f"UPDTASK_{name}_mask_ptr"] = _generated_mask_ptr
    d[f"UPDTASK_{name}_mask_reverse"] = _generated_mask_reverse
    d[f"UPDTASK_{name}_mask_method"] = _generated_mask_method
    d[f"UPDTASK_{name}_mask_color_sample_method"] = _generated_mask_color_sample_method
    d[f"UPDTASK_{name}_mask_id_color_ptr"] = _generated_mask_id_color_ptr
    d[f"UPDTASK_{name}_mask_noise_scale"] = _generated_mask_noise_scale
    d[f"UPDTASK_{name}_mask_noise_brightness"] = _generated_mask_noise_brightness
    d[f"UPDTASK_{name}_mask_noise_contrast"] = _generated_mask_noise_contrast

    return d 

#  dP""b8  dP"Yb  88      dP"Yb  88""Yb
# dP   `" dP   Yb 88     dP   Yb 88__dP
# Yb      Yb   dP 88  .o Yb   dP 88"Yb
#  YboodP  YbodP  88ood8  YbodP  88  Yb


def UPDTASK_s_color(self, prop_name, value, event=None, bypass=False,):
        self.scatter_obj.color = list(value)+[1]


# 8888b.  88 .dP"Y8 888888 88""Yb 88 88""Yb 88   88 888888 88  dP"Yb  88b 88
#  8I  Yb 88 `Ybo."   88   88__dP 88 88__dP 88   88   88   88 dP   Yb 88Yb88
#  8I  dY 88 o.`Y8b   88   88"Yb  88 88""Yb Y8   8P   88   88 Yb   dP 88 Y88
# 8888Y"  88 8bodP'   88   88  Yb 88 88oodP `YbodP'   88   88  YbodP  88  Y8


def UPDTASK_s_distribution_method(self, prop_name, value, event=None, bypass=False,):

        node_link(self, prop_name, value,)
        node_link(self, prop_name+"_N", value+"_N",)
        
        node_value(self, "is_manual", value=="manual_all", entry="boolean")
        node_value(self, "is_clump", value=="clumping", entry="boolean")

        #manual mode only compatible with local space
        if (value=="manual_all"):
            self.s_distribution_space_bis = self.s_distribution_space
            self.s_distribution_space="local"
        else:
            if self.s_distribution_space_bis!="":
                self.s_distribution_space = self.s_distribution_space_bis
                self.s_distribution_space_bis = ""

def UPDTASK_s_distribution_space(self, prop_name, value, event=None, bypass=False,):

        node_value(self, "is_local", value=="local", entry="boolean")

        mod = self.scatter_obj.modifiers["Scatter5 Geonode Engine MKI"]
        nodes = mod.node_group.nodes
        nodes["s_emitter"].transform_space = "RELATIVE" if (value=="global") else "ORIGINAL"

#Random Distribution 

def UPDTASK_s_distribution_density(self, prop_name, value, event=None, bypass=False,):
        node_value(self, "s_distribution_random", value, entry="input", i=1)

def UPDTASK_s_distribution_limit_distance_allow(self, prop_name, value, event=None, bypass=False,):
        node_value(self, "s_distribution_random", value, entry="input", i=3)

def UPDTASK_s_distribution_limit_distance(self, prop_name, value, event=None, bypass=False,):
        node_value(self, "s_distribution_random", value, entry="input", i=4)

def UPDTASK_s_distribution_seed(self, prop_name, value, event=None, bypass=False,):
        node_value(self, "s_distribution_random", value, entry="input", i=2)

def UPDTASK_s_distribution_is_random_seed(self, prop_name, value, event=None, bypass=False,):
        random_seed(self, event, api_is_random=prop_name, api_seed="s_distribution_seed", )

#Clump Distribution

def UPDTASK_s_distribution_clump_density(self, prop_name, value, event=None, bypass=False,):
        node_value(self, "s_distribution_clump", value, entry="input", i=1)

def UPDTASK_s_distribution_clump_limit_distance_allow(self, prop_name, value, event=None, bypass=False,):
        node_value(self, "s_distribution_clump", value, entry="input", i=2)

def UPDTASK_s_distribution_clump_limit_distance(self, prop_name, value, event=None, bypass=False,):
        node_value(self, "s_distribution_clump", value, entry="input", i=3)

def UPDTASK_s_distribution_clump_seed(self, prop_name, value, event=None, bypass=False,):
        node_value(self, "s_distribution_clump", value, entry="input", i=4)

def UPDTASK_s_distribution_clump_is_random_seed(self, prop_name, value, event=None, bypass=False,):
        random_seed(self, event, api_is_random=prop_name, api_seed="s_distribution_clump_seed")

def UPDTASK_s_distribution_clump_max_distance(self, prop_name, value, event=None, bypass=False,):
        node_value(self, "s_distribution_clump", value, entry="input", i=5)

def UPDTASK_s_distribution_clump_falloff(self, prop_name, value, event=None, bypass=False,):
        node_value(self, "s_distribution_clump", value, entry="input", i=6)

def UPDTASK_s_distribution_clump_random_factor(self, prop_name, value, event=None, bypass=False,):
        node_value(self, "s_distribution_clump", value, entry="input", i=7)

#Child 

def UPDTASK_s_distribution_clump_children_density(self, prop_name, value, event=None, bypass=False,):
        node_value(self, "s_distribution_clump", value, entry="input", i=8)

def UPDTASK_s_distribution_clump_children_limit_distance_allow(self, prop_name, value, event=None, bypass=False,):
        node_value(self, "s_distribution_clump", value, entry="input", i=9)

def UPDTASK_s_distribution_clump_children_limit_distance(self, prop_name, value, event=None, bypass=False,):
        node_value(self, "s_distribution_clump", value, entry="input", i=10)

def UPDTASK_s_distribution_clump_children_seed(self, prop_name, value, event=None, bypass=False,):
        node_value(self, "s_distribution_clump", value, entry="input", i=11)

def UPDTASK_s_distribution_clump_children_is_random_seed(self, prop_name, value, event=None, bypass=False,):
        random_seed(self, event, api_is_random=prop_name, api_seed="s_distribution_clump_children_seed")


# 8888b.  888888 88b 88 .dP"Y8 88 888888 Yb  dP     8b    d8    db    .dP"Y8 88  dP .dP"Y8
#  8I  Yb 88__   88Yb88 `Ybo." 88   88    YbdP      88b  d88   dPYb   `Ybo." 88odP  `Ybo."
#  8I  dY 88""   88 Y88 o.`Y8b 88   88     8P       88YbdP88  dP__Yb  o.`Y8b 88"Yb  o.`Y8b
# 8888Y"  888888 88  Y8 8bodP' 88   88    dP        88 YY 88 dP""""Yb 8bodP' 88  Yb 8bodP'


########## ########## Vgroups #happen with mask

def UPDTASK_s_mask_vg_allow(self, prop_name, value, event=None, bypass=False,):
        mute_node(self,"Vgroup Mask", mute=not value, frame=True)
    
def UPDTASK_s_mask_vg_ptr(self, prop_name, value, event=None, bypass=False,):
        named_attribute(self,prop_name,value)

def UPDTASK_s_mask_vg_revert(self, prop_name, value, event=None, bypass=False,):
        node_value(self, prop_name, value, entry="boolean",)

########## ########## VColors #happen with mask

def UPDTASK_s_mask_vcol_allow(self, prop_name, value, event=None, bypass=False,):
        mute_node(self,"Vcol Mask", mute=not value, frame=True)
    
def UPDTASK_s_mask_vcol_ptr(self, prop_name, value, event=None, bypass=False,):
        named_attribute(self,prop_name,value)
    
def UPDTASK_s_mask_vcol_revert(self, prop_name, value, event=None, bypass=False,):
        node_value(self, prop_name, value, entry="boolean",)
    
def UPDTASK_s_mask_vcol_color_sample_method(self, prop_name, value, event=None, bypass=False,):
        node_value(self, "s_mask_vcol_color_sample_method", get_enum_idx(self, prop_name, value,), entry="input", i=1)
    
def UPDTASK_s_mask_vcol_id_color_ptr(self, prop_name, value, event=None, bypass=False,):
        node_value(self, "s_mask_vcol_color_sample_method", list_to_color(value), entry="input", i=2)

########## ########## Bitmap 

def UPDTASK_s_mask_bitmap_allow(self, prop_name, value, event=None, bypass=False,):
        mute_color(self, "Bitmap Mask", mute=not value,)
        node_link(self, f"RR_GEO s_mask_bitmap Receptor", f"RR_GEO s_mask_bitmap {value}",)
        self.s_mask_bitmap_uv_ptr = self.s_mask_bitmap_uv_ptr

def UPDTASK_s_mask_bitmap_uv_ptr(self, prop_name, value, event=None, bypass=False,):
        named_attribute(self,prop_name,value)
    
def UPDTASK_s_mask_bitmap_ptr(self, prop_name, value, event=None, bypass=False,):
        node_value(self, prop_name, bpy.data.images.get(value), entry="input", i=0)
    
def UPDTASK_s_mask_bitmap_revert(self, prop_name, value, event=None, bypass=False,):
        node_value(self, prop_name, not value, entry="boolean",)
    
def UPDTASK_s_mask_bitmap_color_sample_method(self, prop_name, value, event=None, bypass=False,):
        node_value(self, "s_mask_bitmap_color_sample_method", get_enum_idx(self, prop_name, value,), entry="input", i=1)
    
def UPDTASK_s_mask_bitmap_id_color_ptr(self, prop_name, value, event=None, bypass=False,):
        node_value(self, "s_mask_bitmap_color_sample_method", list_to_color(value), entry="input", i=2)

########## ########## Curves

def UPDTASK_s_mask_curve_allow(self, prop_name, value, event=None, bypass=False,):
        mute_color(self, "Bitmap Mask", mute=not value,)
        node_link(self, f"RR_GEO s_mask_curve Receptor", f"RR_GEO s_mask_curve {value}",)    

def UPDTASK_s_mask_curve_ptr(self, prop_name, value, event=None, bypass=False,):
        node_value(self, "s_mask_curve", value, entry="input", i=1)
    
def UPDTASK_s_mask_curve_revert(self, prop_name, value, event=None, bypass=False,):
        node_value(self, "s_mask_curve", value, entry="input", i=2)

########## ########## Upward Obstruction

def UPDTASK_s_mask_upward_allow(self, prop_name, value, event=None, bypass=False,):
        mute_color(self, "Bitmap Mask", mute=not value,)
        node_link(self, f"RR_GEO s_mask_upward Receptor", f"RR_GEO s_mask_upward {value}",)

def UPDTASK_s_mask_upward_coll_ptr(self, prop_name, value, event=None, bypass=False,):
        node_value(self, "s_mask_upward", value, entry="input", i=1)
    
def UPDTASK_s_mask_upward_revert(self, prop_name, value, event=None, bypass=False,):
        node_value(self, "s_mask_upward", value, entry="input", i=2)

########## ########## Material #happen with masks

def UPDTASK_s_mask_material_allow(self, prop_name, value, event=None, bypass=False,):
        mute_node(self,"Material Mask", mute=not value, frame=True) 
        self.s_mask_material_ptr = self.s_mask_material_ptr

def UPDTASK_s_mask_material_ptr(self, prop_name, value, event=None, bypass=False,):
        materials = self.id_data.data.materials
        matlen = len(materials)
        idx = -1
        for i,m in enumerate(materials):
            if m is None: 
                continue
            if (m.name == value):
                idx = i 
                break 
        node_value(self, prop_name, idx, entry="integer")
    
def UPDTASK_s_mask_material_revert(self, prop_name, value, event=None, bypass=False,):
        node_value(self, prop_name, value, entry="boolean",)


# 88""Yb  dP"Yb  888888    db    888888 88  dP"Yb  88b 88
# 88__dP dP   Yb   88     dPYb     88   88 dP   Yb 88Yb88
# 88"Yb  Yb   dP   88    dP__Yb    88   88 Yb   dP 88 Y88
# 88  Yb  YbodP    88   dP""""Yb   88   88  YbodP  88  Y8

#Align Z

def UPDTASK_s_rot_align_z_allow(self, prop_name, value, event=None, bypass=False,):
        mute_node(self,"Normal Alignment", mute=not value, frame=True)
        self.s_rot_align_z_clump_allow = self.s_rot_align_z_clump_allow

def UPDTASK_s_rot_align_z_method(self, prop_name, value, event=None, bypass=False,):
        node_value(self, "s_rot_align_z", get_enum_idx(self, prop_name, value,), entry="input", i=2)

def UPDTASK_s_rot_align_z_revert(self, prop_name, value, event=None, bypass=False,):
        node_value(self, "s_rot_align_z", value, entry="input", i=3)

def UPDTASK_s_rot_align_z_influence_allow(self, prop_name, value, event=None, bypass=False,):
        node_value(self, "s_rot_align_z", value, entry="input", i=4)

def UPDTASK_s_rot_align_z_influence_value(self, prop_name, value, event=None, bypass=False,):
        node_value(self, "s_rot_align_z", value, entry="input", i=5)

def UPDTASK_s_rot_align_z_object(self, prop_name, value, event=None, bypass=False,):
        node_value(self, "s_rot_align_z", value, entry="input", i=6)

def UPDTASK_s_rot_align_z_clump_allow(self, prop_name, value, event=None, bypass=False,): 
        if not self.s_rot_align_z_allow: 
              mute_node(self, "Clump Normal Alignment", mute=True, frame=True,)
        else: mute_node(self, "Clump Normal Alignment", mute=not value, frame=True,)

def UPDTASK_s_rot_align_z_clump_value(self, prop_name, value, event=None, bypass=False,):
        node_value(self, prop_name, value,)

#Align Y

def UPDTASK_s_rot_align_y_allow(self, prop_name, value, event=None, bypass=False,):
        mute_node(self,"Tangent Alignment", mute=not value, frame=True)

def UPDTASK_s_rot_align_y_method(self, prop_name, value, event=None, bypass=False,):
        node_value(self, "s_rot_align_y", get_enum_idx(self, prop_name, value,), entry="input", i=2)

def UPDTASK_s_rot_align_y_revert(self, prop_name, value, event=None, bypass=False,):
        node_value(self, "s_rot_align_y", value, entry="input", i=3)

def UPDTASK_s_rot_align_y_object(self, prop_name, value, event=None, bypass=False,):
        node_value(self, "s_rot_align_y", value, entry="input", i=4)

def UPDTASK_s_rot_align_y_random_seed(self, prop_name, value, event=None, bypass=False,):
        node_value(self, "s_rot_align_y", value, entry="input", i=6)

def UPDTASK_s_rot_align_y_is_random_seed(self, prop_name, value, event=None, bypass=False,):
        random_seed(self, event, api_is_random=prop_name, api_seed="s_rot_align_y_random_seed")

def UPDTASK_s_rot_align_y_flow_method(self, prop_name, value, event=None, bypass=False,): 
        node_value(self, "s_rot_align_y_is_vcol", value=="flow_vcol", entry="boolean",)

def UPDTASK_s_rot_align_y_flow_direction(self, prop_name, value, event=None, bypass=False,): 
        node_value(self, prop_name, value,)

def UPDTASK_s_rot_align_y_texture_ptr(self, prop_name, value, event=None, bypass=False,): 
        ng_name = value if value.startswith(".TEXTURE ") else f".TEXTURE {value}"
        ng = bpy.data.node_groups.get(value)
        if (ng is not None):
            mod = self.scatter_obj.modifiers["Scatter5 Geonode Engine MKI"]
            if (mod.node_group.nodes["TEXTURE_NODE s_rot_align_y"].node_tree != ng):
                mod.node_group.nodes["TEXTURE_NODE s_rot_align_y"].node_tree = ng

def UPDTASK_s_rot_align_y_vcol_ptr(self, prop_name, value, event=None, bypass=False,): 
        named_attribute(self,prop_name,value)   

#Tilt 

def UPDTASK_s_rot_tilt_allow(self, prop_name, value, event=None, bypass=False,):
        mute_color(self, "Tilt", mute=not value,)
        node_link(self, f"RR_VEC s_rot_tilt Receptor", f"RR_VEC s_rot_tilt {value}",)

def UPDTASK_s_rot_tilt_method(self, prop_name, value, event=None, bypass=False,):
        node_value(self, "s_rot_tilt_is_vcol", value=="tilt_vcol", entry="boolean",)

def UPDTASK_s_rot_tilt_force(self, prop_name, value, event=None, bypass=False,):
        node_value(self, prop_name, value,)

def UPDTASK_s_rot_tilt_direction(self, prop_name, value, event=None, bypass=False,):
        node_value(self, prop_name, value,)

def UPDTASK_s_rot_tilt_blue_is_strength(self, prop_name, value, event=None, bypass=False,):
        node_value(self, prop_name, value, entry="boolean",)

def UPDTASK_s_rot_tilt_texture_ptr(self, prop_name, value, event=None, bypass=False,):
        ng_name = value if value.startswith(".TEXTURE ") else f".TEXTURE {value}"
        ng = bpy.data.node_groups.get(value)
        if (ng is not None):
            mod = self.scatter_obj.modifiers["Scatter5 Geonode Engine MKI"]
            if (mod.node_group.nodes["TEXTURE_NODE s_rot_tilt"].node_tree != ng):
                mod.node_group.nodes["TEXTURE_NODE s_rot_tilt"].node_tree = ng

def UPDTASK_s_rot_tilt_vcol_ptr(self, prop_name, value, event=None, bypass=False,):
        named_attribute(self,prop_name,value)   

locals().update(generate_umask_UPTDTASKS(name="s_rot_tilt"))

#Rot Random 

def UPDTASK_s_rot_random_allow(self, prop_name, value, event=None, bypass=False,):
        mute_color(self, "Random Rotation", mute=not value,)
        node_link(self, f"RR_VEC s_rot_random Receptor", f"RR_VEC s_rot_random {value}",)

def UPDTASK_s_rot_random_tilt_value(self, prop_name, value, event=None, bypass=False,):
        node_value(self, "s_rot_random", value, entry="input", i=0)

def UPDTASK_s_rot_random_yaw_value(self, prop_name, value, event=None, bypass=False,):
        node_value(self, "s_rot_random", value, entry="input", i=1)

def UPDTASK_s_rot_random_seed(self, prop_name, value, event=None, bypass=False,):
        node_value(self, "s_rot_random", value, entry="input", i=2)

def UPDTASK_s_rot_random_is_random_seed(self, prop_name, value, event=None, bypass=False,):
        random_seed(self, event, api_is_random=prop_name, api_seed="s_rot_random_seed")

locals().update(generate_umask_UPTDTASKS(name="s_rot_random"))

#Rot Add

def UPDTASK_s_rot_add_allow(self, prop_name, value, event=None, bypass=False,):
        mute_color(self, "Rotate", mute=not value,)
        node_link(self, f"RR_VEC s_rot_add Receptor", f"RR_VEC s_rot_add {value}",)

def UPDTASK_s_rot_add_default(self, prop_name, value, event=None, bypass=False,):
        node_value(self, "s_rot_add", value, entry="input", i=0)

def UPDTASK_s_rot_add_random(self, prop_name, value, event=None, bypass=False,):
        node_value(self, "s_rot_add", value, entry="input", i=1)

def UPDTASK_s_rot_add_seed(self, prop_name, value, event=None, bypass=False,):
        node_value(self, "s_rot_add", value, entry="input", i=2)

def UPDTASK_s_rot_add_is_random_seed(self, prop_name, value, event=None, bypass=False,):
        random_seed(self, event, api_is_random=prop_name, api_seed="s_rot_add_seed")

def UPDTASK_s_rot_add_snap(self, prop_name, value, event=None, bypass=False,):
        node_value(self, "s_rot_add", value, entry="input", i=3)

locals().update(generate_umask_UPTDTASKS(name="s_rot_add"))


# .dP"Y8  dP""b8    db    88     888888
# `Ybo." dP   `"   dPYb   88     88__
# o.`Y8b Yb       dP__Yb  88  .o 88""
# 8bodP'  YboodP dP""""Yb 88ood8 888888


#Default 

def UPDTASK_s_scale_default_allow(self, prop_name, value, event=None, bypass=False,):
        mute_color(self, "Default Scale", mute=not value,)
        node_link(self, f"RR_VEC s_scale_default Receptor", f"RR_VEC s_scale_default {value}",)

def UPDTASK_s_scale_default_space(self, prop_name, value, event=None, bypass=False,):
        node_value(self, "s_scale_default_is_local", value=="local_scale", entry="boolean")

def UPDTASK_s_scale_default_value(self, prop_name, value, event=None, bypass=False,):
        node_value(self, prop_name, value, entry="vector")

#Random

def UPDTASK_s_scale_random_allow(self, prop_name, value, event=None, bypass=False,):
        mute_color(self, "Random Scale", mute=not value,)
        node_link(self, f"RR_VEC s_scale_random Receptor", f"RR_VEC s_scale_random {value}",)

def UPDTASK_s_scale_random_method(self, prop_name, value, event=None, bypass=False,):
        node_value(self, "s_scale_random", value=="random_uniform", entry="input", i=0)

def UPDTASK_s_scale_random_factor(self, prop_name, value, event=None, bypass=False,):
        node_value(self, "s_scale_random", value, entry="input", i=1)

def UPDTASK_s_scale_random_probability(self, prop_name, value, event=None, bypass=False,):
        node_value(self, "s_scale_random", value/100, entry="input", i=2)

def UPDTASK_s_scale_random_seed(self, prop_name, value, event=None, bypass=False,):
        node_value(self, "s_scale_random", value, entry="input", i=3)

def UPDTASK_s_scale_random_is_random_seed(self, prop_name, value, event=None, bypass=False,):
        random_seed(self, event, api_is_random=prop_name, api_seed="s_scale_random_seed")

locals().update(generate_umask_UPTDTASKS(name="s_scale_random"))

#Shrink 

def UPDTASK_s_scale_shrink_allow(self, prop_name, value, event=None, bypass=False,):
        mute_color(self, "Shrink", mute=not value,)
        node_link(self, f"RR_VEC s_scale_shrink Receptor", f"RR_VEC s_scale_shrink {value}",)

def UPDTASK_s_scale_shrink_factor(self, prop_name, value, event=None, bypass=False,):
        node_value(self, prop_name, value,entry="vector")

locals().update(generate_umask_UPTDTASKS(name="s_scale_shrink"))

#Grow

def UPDTASK_s_scale_grow_allow(self, prop_name, value, event=None, bypass=False,):
        mute_color(self, "Grow", mute=not value,)
        node_link(self, f"RR_VEC s_scale_grow Receptor", f"RR_VEC s_scale_grow {value}",)

def UPDTASK_s_scale_grow_factor(self, prop_name, value, event=None, bypass=False,):
        node_value(self, prop_name, value,entry="vector")

locals().update(generate_umask_UPTDTASKS(name="s_scale_grow"))

#Mirror

def UPDTASK_s_scale_mirror_allow(self, prop_name, value, event=None, bypass=False,):
        mute_color(self, "Random Mirror", mute=not value,)
        node_link(self, f"RR_VEC s_scale_mirror Receptor", f"RR_VEC s_scale_mirror {value}",)

def UPDTASK_s_scale_mirror_is_x(self, prop_name, value, event=None, bypass=False,):
        node_value(self, "s_scale_mirror", value, entry="input", i=0)

def UPDTASK_s_scale_mirror_is_y(self, prop_name, value, event=None, bypass=False,):
        node_value(self, "s_scale_mirror", value, entry="input", i=1)

def UPDTASK_s_scale_mirror_is_z(self, prop_name, value, event=None, bypass=False,):
        node_value(self, "s_scale_mirror", value, entry="input", i=2)

def UPDTASK_s_scale_mirror_seed(self, prop_name, value, event=None, bypass=False,):
        node_value(self, "s_scale_mirror", value, entry="input", i=3)

def UPDTASK_s_scale_mirror_is_random_seed(self, prop_name, value, event=None, bypass=False,):
        random_seed(self, event, api_is_random=prop_name, api_seed="s_scale_mirror_seed")

locals().update(generate_umask_UPTDTASKS(name="s_scale_mirror"))

#Minimum 

def UPDTASK_s_scale_min_allow(self, prop_name, value, event=None, bypass=False,):
        mute_color(self, "Minimal Scale", mute=not value,)
        node_link(self, f"RR_VEC s_scale_min Receptor", f"RR_VEC s_scale_min {value}",)
        node_link(self, f"RR_GEO s_scale_min Receptor", f"RR_GEO s_scale_min {value}",)

def UPDTASK_s_scale_min_method(self, prop_name, value, event=None, bypass=False,):
         node_value(self, "s_scale_min", (value=="s_scale_min_remove"), entry="input", i=2)

def UPDTASK_s_scale_min_value(self, prop_name, value, event=None, bypass=False,):
         node_value(self, "s_scale_min", value, entry="input", i=3)

#Clump Distribution Special 

def UPDTASK_s_scale_clump_allow(self, prop_name, value, event=None, bypass=False,):
        mute_color(self, "Clump Scale", mute=not value,)
        node_link(self, f"RR_VEC s_scale_clump Receptor", f"RR_VEC s_scale_clump {value}",)

def UPDTASK_s_scale_clump_value(self, prop_name, value, event=None, bypass=False,):
        node_value(self, prop_name, value,)


# 88""Yb    db    888888 888888 888888 88""Yb 88b 88
# 88__dP   dPYb     88     88   88__   88__dP 88Yb88
# 88"""   dP__Yb    88     88   88""   88"Yb  88 Y88
# 88     dP""""Yb   88     88   888888 88  Yb 88  Y8


def UPDTASKi02_s_patternX_allow(self, prop_name, value, event=None, bypass=False,):
        idx = int(prop_name[9])
        mute_color(self, f"Pattern{idx}", mute=not value,)
        node_link(self, f"RR_VEC s_pattern{idx} Receptor", f"RR_VEC s_pattern{idx} {value}",)
        node_link(self, f"RR_GEO s_pattern{idx} Receptor", f"RR_GEO s_pattern{idx} {value}",)

def UPDTASKi02_s_patternX_texture_ptr(self, prop_name, value, event=None, bypass=False,):
        ng_name = value if value.startswith(".TEXTURE ") else f".TEXTURE {value}"
        ng = bpy.data.node_groups.get(value)
        if (ng is not None):
            idx = int(prop_name[9])
            mod = self.scatter_obj.modifiers["Scatter5 Geonode Engine MKI"]
            if (mod.node_group.nodes[f"TEXTURE_NODE s_pattern{idx}"].node_tree != ng):
                mod.node_group.nodes[f"TEXTURE_NODE s_pattern{idx}"].node_tree = ng

def UPDTASKi02_s_patternX_dist_influence(self, prop_name, value, event=None, bypass=False,):
        idx = int(prop_name[9])
        node_value(self, f"s_pattern{idx}_infl", value/100, entry="input", i=2)

def UPDTASKi02_s_patternX_dist_revert(self, prop_name, value, event=None, bypass=False,):
        idx = int(prop_name[9])
        node_value(self, f"s_pattern{idx}_infl", value, entry="input", i=3)

def UPDTASKi02_s_patternX_scale_influence(self, prop_name, value, event=None, bypass=False,):
        idx = int(prop_name[9])
        node_value(self, f"s_pattern{idx}_infl", value/100, entry="input", i=4)

def UPDTASKi02_s_patternX_scale_revert(self, prop_name, value, event=None, bypass=False,):
        idx = int(prop_name[9])
        node_value(self, f"s_pattern{idx}_infl", value, entry="input", i=5)

def UPDTASKi02_s_patternX_color_sample_method(self, prop_name, value, event=None, bypass=False,):
        idx = int(prop_name[9])
        node_value(self, f"s_pattern{idx}_color_sample_method", get_enum_idx(self, prop_name, value,), entry="input", i=1)

def UPDTASKi02_s_patternX_id_color_ptr(self, prop_name, value, event=None, bypass=False,):
        idx = int(prop_name[9])
        node_value(self, f"s_pattern{idx}_color_sample_method", list_to_color(value), entry="input", i=2)

def UPDTASKi02_s_patternX_id_color_tolerence(self, prop_name, value, event=None, bypass=False,):
        idx = int(prop_name[9])
        node_value(self, f"s_pattern{idx}_color_sample_method", value, entry="input", i=3)

locals().update(generate_umask_UPTDTASKS(name="s_pattern1"))
locals().update(generate_umask_UPTDTASKS(name="s_pattern2"))


#    db    88""Yb 88  dP"Yb  888888 88  dP""b8
#   dPYb   88__dP 88 dP   Yb   88   88 dP   `"
#  dP__Yb  88""Yb 88 Yb   dP   88   88 Yb
# dP""""Yb 88oodP 88  YbodP    88   88  YboodP


#Elevation

def UPDTASK_s_abiotic_elev_allow(self, prop_name, value, event=None, bypass=False,):
        mute_color(self, f"Abiotic Elev", mute=not value,)
        node_link(self, f"RR_VEC s_abiotic_elev Receptor", f"RR_VEC s_abiotic_elev {value}",)
        node_link(self, f"RR_GEO s_abiotic_elev Receptor", f"RR_GEO s_abiotic_elev {value}",)

def UPDTASK_s_abiotic_elev_space(self, prop_name, value, event=None, bypass=False,):
        node_value(self, f"s_abiotic_elev", get_enum_idx(self, prop_name, value,), entry="input", i=1)
        setattr(self, f"s_abiotic_elev_min_value_{value}", getattr(self, f"s_abiotic_elev_min_value_{value}"),)
        setattr(self, f"s_abiotic_elev_min_falloff_{value}", getattr(self, f"s_abiotic_elev_min_falloff_{value}"),)
        setattr(self, f"s_abiotic_elev_max_value_{value}", getattr(self, f"s_abiotic_elev_max_value_{value}"),)
        setattr(self, f"s_abiotic_elev_max_falloff_{value}", getattr(self, f"s_abiotic_elev_max_falloff_{value}"),)

def UPDTASK_s_abiotic_elev_min_value_local(self, prop_name, value, event=None, bypass=False,):
        node_value(self, f"s_abiotic_elev", value/100, entry="input", i=2)

def UPDTASK_s_abiotic_elev_min_falloff_local(self, prop_name, value, event=None, bypass=False,):
        node_value(self, f"s_abiotic_elev", value/100, entry="input", i=3)

def UPDTASK_s_abiotic_elev_max_value_local(self, prop_name, value, event=None, bypass=False,):
        node_value(self, f"s_abiotic_elev", value/100, entry="input", i=4)

def UPDTASK_s_abiotic_elev_max_falloff_local(self, prop_name, value, event=None, bypass=False,):
        node_value(self, f"s_abiotic_elev", value/100, entry="input", i=5)

def UPDTASK_s_abiotic_elev_min_value_global(self, prop_name, value, event=None, bypass=False,):
        node_value(self, f"s_abiotic_elev", value, entry="input", i=2)

def UPDTASK_s_abiotic_elev_min_falloff_global(self, prop_name, value, event=None, bypass=False,):
        node_value(self, f"s_abiotic_elev", value, entry="input", i=3)

def UPDTASK_s_abiotic_elev_max_value_global(self, prop_name, value, event=None, bypass=False,):
        node_value(self, f"s_abiotic_elev", value, entry="input", i=4)

def UPDTASK_s_abiotic_elev_max_falloff_global(self, prop_name, value, event=None, bypass=False,):
        node_value(self, f"s_abiotic_elev", value, entry="input", i=5)

def UPDTASK_s_abiotic_elev_dist_influence(self, prop_name, value, event=None, bypass=False,):
        node_value(self, f"s_abiotic_elev_infl", value/100, entry="input", i=2)

def UPDTASK_s_abiotic_elev_dist_revert(self, prop_name, value, event=None, bypass=False,):
        node_value(self, f"s_abiotic_elev_infl", value, entry="input", i=3)

def UPDTASK_s_abiotic_elev_scale_influence(self, prop_name, value, event=None, bypass=False,):
        node_value(self, f"s_abiotic_elev_infl", value/100, entry="input", i=4)

def UPDTASK_s_abiotic_elev_scale_revert(self, prop_name, value, event=None, bypass=False,):
        node_value(self, f"s_abiotic_elev_infl", value, entry="input", i=5)

locals().update(generate_umask_UPTDTASKS(name="s_abiotic_elev"))

#Slope

def UPDTASK_s_abiotic_slope_allow(self, prop_name, value, event=None, bypass=False,):
        mute_color(self, f"Abiotic Slope", mute=not value,)
        node_link(self, f"RR_VEC s_abiotic_slope Receptor", f"RR_VEC s_abiotic_slope {value}",)
        node_link(self, f"RR_GEO s_abiotic_slope Receptor", f"RR_GEO s_abiotic_slope {value}",)

def UPDTASK_s_abiotic_slope_space(self, prop_name, value, event=None, bypass=False,):
        node_value(self, f"s_abiotic_slope", get_enum_idx(self, prop_name, value,), entry="input", i=0)

def UPDTASK_s_abiotic_slope_absolute(self, prop_name, value, event=None, bypass=False,):
        node_value(self, f"s_abiotic_slope", value, entry="input", i=5)

def UPDTASK_s_abiotic_slope_min_value(self, prop_name, value, event=None, bypass=False,):
        node_value(self, f"s_abiotic_slope", value, entry="input", i=1)

def UPDTASK_s_abiotic_slope_min_falloff(self, prop_name, value, event=None, bypass=False,):
        node_value(self, f"s_abiotic_slope", value, entry="input", i=2)

def UPDTASK_s_abiotic_slope_max_value(self, prop_name, value, event=None, bypass=False,):
        node_value(self, f"s_abiotic_slope", value, entry="input", i=3)

def UPDTASK_s_abiotic_slope_max_falloff(self, prop_name, value, event=None, bypass=False,):
        node_value(self, f"s_abiotic_slope", value, entry="input", i=4)

def UPDTASK_s_abiotic_slope_dist_influence(self, prop_name, value, event=None, bypass=False,):
        node_value(self, f"s_abiotic_slope_infl", value/100, entry="input", i=2)

def UPDTASK_s_abiotic_slope_dist_revert(self, prop_name, value, event=None, bypass=False,):
        node_value(self, f"s_abiotic_slope_infl", value, entry="input", i=3)

def UPDTASK_s_abiotic_slope_scale_influence(self, prop_name, value, event=None, bypass=False,):
        node_value(self, f"s_abiotic_slope_infl", value/100, entry="input", i=4)

def UPDTASK_s_abiotic_slope_scale_revert(self, prop_name, value, event=None, bypass=False,):
        node_value(self, f"s_abiotic_slope_infl", value, entry="input", i=5)

locals().update(generate_umask_UPTDTASKS(name="s_abiotic_slope"))

#Direction

def UPDTASK_s_abiotic_dir_allow(self, prop_name, value, event=None, bypass=False,):
        mute_color(self, f"Abiotic Orientation", mute=not value,)
        node_link(self, f"RR_VEC s_abiotic_dir Receptor", f"RR_VEC s_abiotic_dir {value}",)
        node_link(self, f"RR_GEO s_abiotic_dir Receptor", f"RR_GEO s_abiotic_dir {value}",)

def UPDTASK_s_abiotic_dir_space(self, prop_name, value, event=None, bypass=False,):
        node_value(self, f"s_abiotic_dir", get_enum_idx(self, prop_name, value,), entry="input", i=0) 

def UPDTASK_s_abiotic_dir_direction(self, prop_name, value, event=None, bypass=False,):
        node_value(self, f"s_abiotic_dir", value, entry="input", i=1)

def UPDTASK_s_abiotic_dir_max(self, prop_name, value, event=None, bypass=False,):
        node_value(self, f"s_abiotic_dir", value, entry="input", i=2)

def UPDTASK_s_abiotic_dir_treshold(self, prop_name, value, event=None, bypass=False,):
        node_value(self, f"s_abiotic_dir", value, entry="input", i=3)
        
def UPDTASK_s_abiotic_dir_dist_influence(self, prop_name, value, event=None, bypass=False,):
        node_value(self, f"s_abiotic_dir_infl", value/100, entry="input", i=2)

def UPDTASK_s_abiotic_dir_dist_revert(self, prop_name, value, event=None, bypass=False,):
        node_value(self, f"s_abiotic_dir_infl", value, entry="input", i=3)

def UPDTASK_s_abiotic_dir_scale_influence(self, prop_name, value, event=None, bypass=False,):
        node_value(self, f"s_abiotic_dir_infl", value/100, entry="input", i=4)

def UPDTASK_s_abiotic_dir_scale_revert(self, prop_name, value, event=None, bypass=False,):
        node_value(self, f"s_abiotic_dir_infl", value, entry="input", i=5) 

locals().update(generate_umask_UPTDTASKS(name="s_abiotic_dir"))

#Curvature 

def UPDTASK_s_abiotic_cur_allow(self, prop_name, value, event=None, bypass=False,):
        mute_color(self, f"Abiotic Curvature", mute=not value,)
        node_link(self, f"RR_VEC s_abiotic_cur Receptor", f"RR_VEC s_abiotic_cur {value}",)
        node_link(self, f"RR_GEO s_abiotic_cur Receptor", f"RR_GEO s_abiotic_cur {value}",)
        if value:
            generate_edge_curvature_attr(self.id_data)

def UPDTASK_s_abiotic_cur_type(self, prop_name, value, event=None, bypass=False,):
        node_value(self, f"s_abiotic_cur", get_enum_idx(self, prop_name, value,), entry="input", i=0)
        self.s_abiotic_cur_max = self.s_abiotic_cur_max

def UPDTASK_s_abiotic_cur_max(self, prop_name, value, event=None, bypass=False,):
        val = (1-(value/100)) if (self.s_abiotic_cur_type=="concave") else (value/100)
        node_value(self, f"s_abiotic_cur", val, entry="input", i=2)

def UPDTASK_s_abiotic_cur_treshold(self, prop_name, value, event=None, bypass=False,):
        node_value(self, f"s_abiotic_cur", value/100, entry="input", i=3)

def UPDTASK_s_abiotic_cur_dist_influence(self, prop_name, value, event=None, bypass=False,):
        node_value(self, f"s_abiotic_cur_infl", value/100, entry="input", i=2)

def UPDTASK_s_abiotic_cur_dist_revert(self, prop_name, value, event=None, bypass=False,):
        node_value(self, f"s_abiotic_cur_infl", value, entry="input", i=3)

def UPDTASK_s_abiotic_cur_scale_influence(self, prop_name, value, event=None, bypass=False,):
        node_value(self, f"s_abiotic_cur_infl", value/100, entry="input", i=4)

def UPDTASK_s_abiotic_cur_scale_revert(self, prop_name, value, event=None, bypass=False,):
        node_value(self, f"s_abiotic_cur_infl", value, entry="input", i=5)

locals().update(generate_umask_UPTDTASKS(name="s_abiotic_cur"))

#Border

def UPDTASK_s_abiotic_border_allow(self, prop_name, value, event=None, bypass=False,):
        mute_color(self, f"Abiotic Border", mute=not value,)
        node_link(self, f"RR_VEC s_abiotic_border Receptor", f"RR_VEC s_abiotic_border {value}",)
        node_link(self, f"RR_GEO s_abiotic_border Receptor", f"RR_GEO s_abiotic_border {value}",)
        if value:
            generate_edge_border_attr(self.id_data)

def UPDTASK_s_abiotic_border_max(self, prop_name, value, event=None, bypass=False,):
        node_value(self, f"s_abiotic_border", value, entry="input", i=2)

def UPDTASK_s_abiotic_border_treshold(self, prop_name, value, event=None, bypass=False,):
        node_value(self, f"s_abiotic_border", value, entry="input", i=3)

def UPDTASK_s_abiotic_border_dist_influence(self, prop_name, value, event=None, bypass=False,):
        node_value(self, f"s_abiotic_border_infl", value/100, entry="input", i=2)

def UPDTASK_s_abiotic_border_dist_revert(self, prop_name, value, event=None, bypass=False,):
        node_value(self, f"s_abiotic_border_infl", value, entry="input", i=3)

def UPDTASK_s_abiotic_border_scale_influence(self, prop_name, value, event=None, bypass=False,):
        node_value(self, f"s_abiotic_border_infl", value/100, entry="input", i=4)

def UPDTASK_s_abiotic_border_scale_revert(self, prop_name, value, event=None, bypass=False,):
        node_value(self, f"s_abiotic_border_infl", value, entry="input", i=5)

locals().update(generate_umask_UPTDTASKS(name="s_abiotic_border"))
    

# 88""Yb 88""Yb  dP"Yb  Yb  dP 88 8b    d8 88 888888 Yb  dP
# 88__dP 88__dP dP   Yb  YbdP  88 88b  d88 88   88    YbdP
# 88"""  88"Yb  Yb   dP  dPYb  88 88YbdP88 88   88     8P
# 88     88  Yb  YbodP  dP  Yb 88 88 YY 88 88   88    dP

#Remove Near

def UPDTASK_s_proximity_removenear_allow(self, prop_name, value, event=None, bypass=False,):
        mute_color(self, f"Remove Near", mute=not value,)
        node_link(self, f"RR_VEC s_proximity_removenear Receptor", f"RR_VEC s_proximity_removenear {value}",)
        node_link(self, f"RR_GEO s_proximity_removenear Receptor", f"RR_GEO s_proximity_removenear {value}",)
        if value:
            generate_edge_border_attr(self.id_data)

def UPDTASK_s_proximity_removenear_coll_ptr(self, prop_name, value, event=None, bypass=False,):
        node_value(self, f"s_proximity_removenear", value, entry="input", i=1)

def UPDTASK_s_proximity_removenear_type(self, prop_name, value, event=None, bypass=False,):
        node_value(self, f"s_proximity_removenear", get_enum_idx(self, prop_name, value,), entry="input", i=2)

def UPDTASK_s_proximity_removenear_max(self, prop_name, value, event=None, bypass=False,):
        node_value(self, f"s_proximity_removenear", value, entry="input", i=3)

def UPDTASK_s_proximity_removenear_treshold(self, prop_name, value, event=None, bypass=False,):
        node_value(self, f"s_proximity_removenear", value, entry="input", i=4)

def UPDTASK_s_proximity_removenear_dist_influence(self, prop_name, value, event=None, bypass=False,):
        node_value(self, f"s_proximity_removenear_infl", value/100, entry="input", i=2)

def UPDTASK_s_proximity_removenear_dist_revert(self, prop_name, value, event=None, bypass=False,):
        node_value(self, f"s_proximity_removenear_infl", not value, entry="input", i=3)

def UPDTASK_s_proximity_removenear_scale_influence(self, prop_name, value, event=None, bypass=False,):
        node_value(self, f"s_proximity_removenear_infl", value/100, entry="input", i=4)

def UPDTASK_s_proximity_removenear_scale_revert(self, prop_name, value, event=None, bypass=False,):
        node_value(self, f"s_proximity_removenear_infl", not value, entry="input", i=5) #reverse needed here

locals().update(generate_umask_UPTDTASKS(name="s_proximity_removenear"))

#Lean Over

def UPDTASK_s_proximity_leanover_allow(self, prop_name, value, event=None, bypass=False,):
        mute_color(self, f"Lean Over", mute=not value,)
        node_link(self, f"RR_VEC1 s_proximity_leanover Receptor", f"RR_VEC1 s_proximity_leanover {value}",)
        node_link(self, f"RR_VEC2 s_proximity_leanover Receptor", f"RR_VEC2 s_proximity_leanover {value}",)
        node_link(self, f"RR_GEO s_proximity_leanover Receptor", f"RR_GEO s_proximity_leanover {value}",)

def UPDTASK_s_proximity_leanover_coll_ptr(self, prop_name, value, event=None, bypass=False,):
        node_value(self, f"s_proximity_leanover", value, entry="input", i=1)

def UPDTASK_s_proximity_leanover_type(self, prop_name, value, event=None, bypass=False,):
        node_value(self, f"s_proximity_leanover", get_enum_idx(self, prop_name, value,), entry="input", i=2)

def UPDTASK_s_proximity_leanover_max(self, prop_name, value, event=None, bypass=False,):
        node_value(self, f"s_proximity_leanover", value, entry="input", i=3)

def UPDTASK_s_proximity_leanover_treshold(self, prop_name, value, event=None, bypass=False,):
        node_value(self, f"s_proximity_leanover", value, entry="input", i=4)

def UPDTASK_s_proximity_leanover_scale_influence(self, prop_name, value, event=None, bypass=False,):
        node_value(self, f"s_proximity_leanover_infl", value/100, entry="input", i=4)

def UPDTASK_s_proximity_leanover_tilt_influence(self, prop_name, value, event=None, bypass=False,):
        node_value(self, f"s_proximity_leanover_infl", value, entry="input", i=5)

locals().update(generate_umask_UPTDTASKS(name="s_proximity_leanover"))

#Outskirt

def UPDTASK_s_proximity_outskirt_allow(self, prop_name, value, event=None, bypass=False,):
        mute_color(self, f"Outskirt", mute=not value,)
        node_link(self, f"RR_VEC1 s_proximity_outskirt Receptor", f"RR_VEC1 s_proximity_outskirt {value}",)
        node_link(self, f"RR_VEC2 s_proximity_outskirt Receptor", f"RR_VEC2 s_proximity_outskirt {value}",)
        node_link(self, f"RR_GEO s_proximity_outskirt Receptor", f"RR_GEO s_proximity_outskirt {value}",)

def UPDTASK_s_proximity_outskirt_limit(self, prop_name, value, event=None, bypass=False,):
        node_value(self, f"s_proximity_outskirt", value, entry="input", i=2)

def UPDTASK_s_proximity_outskirt_treshold(self, prop_name, value, event=None, bypass=False,):
        node_value(self, f"s_proximity_outskirt_infl", value, entry="input", i=5)

def UPDTASK_s_proximity_outskirt_scale_influence(self, prop_name, value, event=None, bypass=False,):
        node_value(self, f"s_proximity_outskirt_infl", value/100, entry="input", i=6)

def UPDTASK_s_proximity_outskirt_tilt_influence(self, prop_name, value, event=None, bypass=False,):
        node_value(self, f"s_proximity_outskirt_infl", -value, entry="input", i=7)

locals().update(generate_umask_UPTDTASKS(name="s_proximity_outskirt"))

# 888888  dP""b8  dP"Yb  .dP"Y8 Yb  dP .dP"Y8 888888 888888 8b    d8
# 88__   dP   `" dP   Yb `Ybo."  YbdP  `Ybo."   88   88__   88b  d88
# 88""   Yb      Yb   dP o.`Y8b   8P   o.`Y8b   88   88""   88YbdP88
# 888888  YboodP  YbodP  8bodP'  dP    8bodP'   88   888888 88 YY 88

#Affinity

def UPDTASK_s_ecosystem_affinity_allow(self, prop_name, value, event=None, bypass=False,):
        mute_color(self, f"Eco Affinity", mute=not value,)
        node_link(self, f"RR_VEC s_ecosystem_affinity Receptor", f"RR_VEC s_ecosystem_affinity {value}",)
        node_link(self, f"RR_GEO s_ecosystem_affinity Receptor", f"RR_GEO s_ecosystem_affinity {value}",)

def UPDTASKi02_s_ecosystem_affinity_XX_ptr(self, prop_name, value, event=None, bypass=False,):
        idx = int(prop_name[22])
        obj = bpy.data.objects.get(f"scatter_obj : {value}")
        node_value(self, f"s_ecosystem_affinity_{idx:02}", obj, entry="input", i=2)
        mute_node(self, f"s_ecosystem_affinity_{idx:02}",mute= obj is None)

def UPDTASKi02_s_ecosystem_affinity_XX_type(self, prop_name, value, event=None, bypass=False,):
        idx = int(prop_name[22])
        node_value(self, f"s_ecosystem_affinity_{idx:02}", get_enum_idx(self, prop_name, value,), entry="input", i=3)

def UPDTASKi02_s_ecosystem_affinity_XX_max_value(self, prop_name, value, event=None, bypass=False,):
        idx = int(prop_name[22])
        node_value(self, f"s_ecosystem_affinity_{idx:02}", value, entry="input", i=4)

def UPDTASKi02_s_ecosystem_affinity_XX_max_falloff(self, prop_name, value, event=None, bypass=False,):
        idx = int(prop_name[22])
        node_value(self, f"s_ecosystem_affinity_{idx:02}", value, entry="input", i=5)

def UPDTASKi02_s_ecosystem_affinity_XX_limit_distance(self, prop_name, value, event=None, bypass=False,):
        idx = int(prop_name[22])
        node_value(self, f"s_ecosystem_affinity_{idx:02}", value, entry="input", i=6)

def UPDTASK_s_ecosystem_affinity_dist_influence(self, prop_name, value, event=None, bypass=False,):
        node_value(self, f"s_ecosystem_affinity_infl", value/100, entry="input", i=2)

def UPDTASK_s_ecosystem_affinity_scale_influence(self, prop_name, value, event=None, bypass=False,):
        node_value(self, f"s_ecosystem_affinity_infl", value/100, entry="input", i=4)

locals().update(generate_umask_UPTDTASKS(name="s_ecosystem_affinity"))

#Repulsion

def UPDTASK_s_ecosystem_repulsion_allow(self, prop_name, value, event=None, bypass=False,):
        mute_color(self, f"Eco Repulsion", mute=not value,)
        node_link(self, f"RR_VEC s_ecosystem_repulsion Receptor", f"RR_VEC s_ecosystem_repulsion {value}",)
        node_link(self, f"RR_GEO s_ecosystem_repulsion Receptor", f"RR_GEO s_ecosystem_repulsion {value}",)

def UPDTASKi02_s_ecosystem_repulsion_XX_ptr(self, prop_name, value, event=None, bypass=False,):
        idx = int(prop_name[23])
        obj = bpy.data.objects.get(f"scatter_obj : {value}")
        node_value(self, f"s_ecosystem_repulsion_{idx:02}", obj, entry="input", i=2)
        mute_node(self, f"s_ecosystem_repulsion_{idx:02}",mute= obj is None)

def UPDTASKi02_s_ecosystem_repulsion_XX_type(self, prop_name, value, event=None, bypass=False,):
        idx = int(prop_name[23])
        node_value(self, f"s_ecosystem_repulsion_{idx:02}", get_enum_idx(self, prop_name, value,), entry="input", i=3)

def UPDTASKi02_s_ecosystem_repulsion_XX_max_value(self, prop_name, value, event=None, bypass=False,):
        idx = int(prop_name[23])
        node_value(self, f"s_ecosystem_repulsion_{idx:02}", value, entry="input", i=4)

def UPDTASKi02_s_ecosystem_repulsion_XX_max_falloff(self, prop_name, value, event=None, bypass=False,):
        idx = int(prop_name[23])
        node_value(self, f"s_ecosystem_repulsion_{idx:02}", value, entry="input", i=5)

def UPDTASK_s_ecosystem_repulsion_dist_influence(self, prop_name, value, event=None, bypass=False,):
        node_value(self, f"s_ecosystem_repulsion_infl", value/100, entry="input", i=2)

def UPDTASK_s_ecosystem_repulsion_scale_influence(self, prop_name, value, event=None, bypass=False,):
        node_value(self, f"s_ecosystem_repulsion_infl", value/100, entry="input", i=4)

locals().update(generate_umask_UPTDTASKS(name="s_ecosystem_repulsion"))

# 88""Yb 88   88 .dP"Y8 88  88
# 88__dP 88   88 `Ybo." 88  88
# 88"""  Y8   8P o.`Y8b 888888
# 88     `YbodP' 8bodP' 88  88

#Push Offset

def UPDTASK_s_push_offset_allow(self, prop_name, value, event=None, bypass=False,):
        mute_color(self, f"Push Offset", mute=not value,)
        node_link(self, f"RR_GEO s_push_offset Receptor", f"RR_GEO s_push_offset {value}",)

def UPDTASK_s_push_offset_add_value(self, prop_name, value, event=None, bypass=False,):
        node_value(self, f"s_push_offset", value, entry="input", i=2)

def UPDTASK_s_push_offset_add_random(self, prop_name, value, event=None, bypass=False,):
        node_value(self, f"s_push_offset", value, entry="input", i=3)

def UPDTASK_s_push_offset_scale_value(self, prop_name, value, event=None, bypass=False,):
        node_value(self, f"s_push_offset", value, entry="input", i=0)

def UPDTASK_s_push_offset_scale_random(self, prop_name, value, event=None, bypass=False,):
        node_value(self, f"s_push_offset", value, entry="input", i=1)

locals().update(generate_umask_UPTDTASKS(name="s_push_offset"))

#Push Direction 

def UPDTASK_s_push_dir_allow(self, prop_name, value, event=None, bypass=False,):
        mute_color(self, f"Push Direction", mute=not value,)
        node_link(self, f"RR_GEO s_push_dir Receptor", f"RR_GEO s_push_dir {value}",)

def UPDTASK_s_push_dir_method(self, prop_name, value, event=None, bypass=False,):
        node_value(self, f"s_push_dir", get_enum_idx(self, prop_name, value,), entry="input", i=2)

def UPDTASK_s_push_dir_add_value(self, prop_name, value, event=None, bypass=False,):
        node_value(self, f"s_push_dir", value, entry="input", i=3)

def UPDTASK_s_push_dir_add_random(self, prop_name, value, event=None, bypass=False,):
        node_value(self, f"s_push_dir", value, entry="input", i=4)

locals().update(generate_umask_UPTDTASKS(name="s_push_dir"))

#Push Noise 

def UPDTASK_s_push_noise_allow(self, prop_name, value, event=None, bypass=False,):
        mute_color(self, f"Push Noise", mute=not value,)
        node_link(self, f"RR_GEO s_push_noise Receptor", f"RR_GEO s_push_noise {value}",)

def UPDTASK_s_push_noise_vector(self, prop_name, value, event=None, bypass=False,):
        node_value(self, f"s_push_noise", value, entry="input", i=0)

def UPDTASK_s_push_noise_speed(self, prop_name, value, event=None, bypass=False,):
        node_value(self, f"s_push_noise", value, entry="input", i=1)

locals().update(generate_umask_UPTDTASKS(name="s_push_noise"))

#Fall

def UPDTASK_s_push_fall_allow(self, prop_name, value, event=None, bypass=False,):
        mute_color(self, f"Push Fall", mute=not value,)
        node_link(self, f"RR_VEC s_push_fall Receptor", f"RR_VEC s_push_fall {value}",)
        node_link(self, f"RR_GEO s_push_fall Receptor", f"RR_GEO s_push_fall {value}",)

def UPDTASK_s_push_fall_height(self, prop_name, value, event=None, bypass=False,):
        node_value(self, f"s_push_fall", value, entry="input", i=0)

def UPDTASK_s_push_fall_key1_pos(self, prop_name, value, event=None, bypass=False,):
        node_value(self, f"s_push_fall", value, entry="input", i=1)

def UPDTASK_s_push_fall_key2_pos(self, prop_name, value, event=None, bypass=False,):
        node_value(self, f"s_push_fall", value, entry="input", i=2)

def UPDTASK_s_push_fall_key1_height(self, prop_name, value, event=None, bypass=False,):
        node_value(self, f"s_push_fall", value, entry="input", i=3)

def UPDTASK_s_push_fall_key2_height(self, prop_name, value, event=None, bypass=False,):
        node_value(self, f"s_push_fall", value, entry="input", i=4)

def UPDTASK_s_push_fall_stop_when_initial_z(self, prop_name, value, event=None, bypass=False,):
        node_value(self, f"s_push_fall", value, entry="input", i=5)

def UPDTASK_s_push_fall_turbulence_allow(self, prop_name, value, event=None, bypass=False,):
        node_value(self, f"s_push_fall", value, entry="input", i=6)

def UPDTASK_s_push_fall_turbulence_spread(self, prop_name, value, event=None, bypass=False,):
        node_value(self, f"s_push_fall", value, entry="input", i=7)

def UPDTASK_s_push_fall_turbulence_speed(self, prop_name, value, event=None, bypass=False,):
        node_value(self, f"s_push_fall", value, entry="input", i=8)

def UPDTASK_s_push_fall_turbulence_rot_vector(self, prop_name, value, event=None, bypass=False,):
        node_value(self, f"s_push_fall", value, entry="input", i=9)

def UPDTASK_s_push_fall_turbulence_rot_factor(self, prop_name, value, event=None, bypass=False,):
        node_value(self, f"s_push_fall", value, entry="input", i=10)

locals().update(generate_umask_UPTDTASKS(name="s_push_fall"))

# Yb        dP 88 88b 88 8888b.  
#  Yb  db  dP  88 88Yb88  8I  Yb 
#   YbdPYbdP   88 88 Y88  8I  dY 
#    YP  YP    88 88  Y8 8888Y"  

#Wind Wave

def UPDTASK_s_wind_wave_allow(self, prop_name, value, event=None, bypass=False,):
        mute_color(self, f"Wind Wave", mute=not value,)
        node_link(self, f"RR_VEC s_wind_wave Receptor", f"RR_VEC s_wind_wave {value}",)

def UPDTASK_s_wind_wave_speed(self, prop_name, value, event=None, bypass=False,):
        node_value(self, f"s_wind_wave", value, entry="input", i=1)

def UPDTASK_s_wind_wave_direction(self, prop_name, value, event=None, bypass=False,):
        node_value(self, f"s_wind_wave", value, entry="input", i=2)

def UPDTASK_s_wind_wave_force(self, prop_name, value, event=None, bypass=False,):
        node_value(self, f"s_wind_wave", value, entry="input", i=3)

def UPDTASK_s_wind_wave_swinging(self, prop_name, value, event=None, bypass=False,):
        node_value(self, f"s_wind_wave", value, entry="input", i=4)

def UPDTASK_s_wind_wave_scale_influence(self, prop_name, value, event=None, bypass=False,):
        node_value(self, f"s_wind_wave", value, entry="input", i=5)

def UPDTASK_s_wind_wave_texture_scale(self, prop_name, value, event=None, bypass=False,):
        node_value(self, f"s_wind_wave", value, entry="input", i=6)

def UPDTASK_s_wind_wave_texture_turbulence(self, prop_name, value, event=None, bypass=False,):
        node_value(self, f"s_wind_wave", value, entry="input", i=7)

def UPDTASK_s_wind_wave_texture_brightness(self, prop_name, value, event=None, bypass=False,):
        node_value(self, f"s_wind_wave", value, entry="input", i=8)

def UPDTASK_s_wind_wave_texture_contrast(self, prop_name, value, event=None, bypass=False,):
        node_value(self, f"s_wind_wave", value, entry="input", i=9)

def UPDTASK_s_wind_wave_dir_method(self, prop_name, value, event=None, bypass=False,):
        node_value(self, f"s_wind_wave", get_enum_idx(self, prop_name, value), entry="input", i=10)

def UPDTASK_s_wind_wave_flowmap_ptr(self, prop_name, value, event=None, bypass=False,):
        named_attribute(self,prop_name,value)   

locals().update(generate_umask_UPTDTASKS(name="s_wind_wave"))

#Wind Noise

def UPDTASK_s_wind_noise_allow(self, prop_name, value, event=None, bypass=False,):
        mute_color(self, f"Wind Noise", mute=not value,)
        node_link(self, f"RR_VEC s_wind_noise Receptor", f"RR_VEC s_wind_noise {value}",)

def UPDTASK_s_wind_noise_force(self, prop_name, value, event=None, bypass=False,):
        node_value(self, f"s_wind_noise", value, entry="input", i=0)

def UPDTASK_s_wind_noise_speed(self, prop_name, value, event=None, bypass=False,):
        node_value(self, f"s_wind_noise", value, entry="input", i=1)

locals().update(generate_umask_UPTDTASKS(name="s_wind_noise"))
        
# 88 88b 88 .dP"Y8 888888    db    88b 88  dP""b8 88 88b 88  dP""b8
# 88 88Yb88 `Ybo."   88     dPYb   88Yb88 dP   `" 88 88Yb88 dP   `"
# 88 88 Y88 o.`Y8b   88    dP__Yb  88 Y88 Yb      88 88 Y88 Yb  "88
# 88 88  Y8 8bodP'   88   dP""""Yb 88  Y8  YboodP 88 88  Y8  YboodP

def UPDTASK_s_instances_method(self, prop_name, value, event=None, bypass=False,):
        node_link(self, prop_name, value)

def UPDTASK_s_instances_coll_ptr(self, prop_name, value, event=None, bypass=False,):
        node_value(self, prop_name, value, entry="input")

def UPDTASK_s_instances_pick_method(self, prop_name, value, event=None, bypass=False,):
        node_link(self, prop_name, value)
        node_link(self, prop_name+" PICK", value+" PICK")
        mute_node(self, "s_instances_pick_scale", mute=(value!="pick_scale"))

def UPDTASK_s_instances_seed(self, prop_name, value, event=None, bypass=False,):
        node_value(self, prop_name, value, entry="integer")

def UPDTASK_s_instances_is_random_seed(self, prop_name, value, event=None, bypass=False,):
        random_seed(self, event, api_is_random=prop_name, api_seed="s_instances_seed")

def UPDTASKi20_s_instances_id_XX_rate(self, prop_name, value, event=None, bypass=False,):
        idx = int(prop_name[15:17])
        node_value(self, "s_instances_pick_rate", value/100, entry="input", i=idx)

def UPDTASK_s_instances_id_scale_method(self, prop_name, value, event=None, bypass=False,):
        node_value(self,"s_instances_is_dynamic_scale", value=="dynamic_scale", entry="boolean")

def UPDTASKi10_s_instances_id_XX_scale_min(self, prop_name, value, event=None, bypass=False,):
        idx = int(prop_name[15:17])
        idx *=2 
        idx -=1
        node_value(self, "s_instances_pick_scale", value, entry="input", i=idx)

def UPDTASKi10_s_instances_id_XX_scale_max(self, prop_name, value, event=None, bypass=False,):
        idx = int(prop_name[15:17])
        idx *=2 
        node_value(self, "s_instances_pick_scale", value, entry="input", i=idx)

def UPDTASK_s_instances_pick_cluster_projection_method(self, prop_name, value, event=None, bypass=False,):
        node_value(self, "s_instances_pick_cluster", get_enum_idx(self, prop_name, value), entry="input", i=0)

def UPDTASK_s_instances_pick_cluster_scale(self, prop_name, value, event=None, bypass=False,):
        node_value(self, "s_instances_pick_cluster", value, entry="input", i=1)

def UPDTASK_s_instances_pick_cluster_blur(self, prop_name, value, event=None, bypass=False,):
        node_value(self, "s_instances_pick_cluster", value, entry="input", i=2)

def UPDTASK_s_instances_pick_clump(self, prop_name, value, event=None, bypass=False,):
        node_value(self, prop_name, value, entry="boolean") 

def UPDTASKi20_s_instances_id_XX_color(self, prop_name, value, event=None, bypass=False,):
        idx = int(prop_name[15:17])
        node_value(self, "s_instances_pick_color", list_to_color(value), entry="input", i=idx)

def UPDTASK_s_instances_id_color_tolerence(self, prop_name, value, event=None, bypass=False,):
        node_value(self, prop_name, value,) 

def UPDTASK_s_instances_id_color_sample_method(self, prop_name, value, event=None, bypass=False,):
        node_value(self, "s_instances_is_vcol", value=="vcol", entry="boolean")

def UPDTASK_s_instances_texture_ptr(self, prop_name, value, event=None, bypass=False,):
        ng_name = value if value.startswith(".TEXTURE ") else f".TEXTURE {value}"
        ng = bpy.data.node_groups.get(value)
        if (ng is not None):
            mod = self.scatter_obj.modifiers["Scatter5 Geonode Engine MKI"]
            if (mod.node_group.nodes["TEXTURE_NODE s_instances"].node_tree != ng):
                mod.node_group.nodes["TEXTURE_NODE s_instances"].node_tree = ng

def UPDTASK_s_instances_vcol_ptr(self, prop_name, value, event=None, bypass=False,):
        named_attribute(self, prop_name, value,)   

def UPDTASK_s_instances_volume_density(self, prop_name, value, event=None, bypass=False,): #unused 
        node_value(self, prop_name, value,)

def UPDTASK_s_instances_volume_voxel_ammount(self, prop_name, value, event=None, bypass=False,): #unused 
        node_value(self, prop_name, value,)

# Yb    dP 88 .dP"Y8 88 88""Yb 88 88     88 888888 Yb  dP
#  Yb  dP  88 `Ybo." 88 88__dP 88 88     88   88    YbdP
#   YbdP   88 o.`Y8b 88 88""Yb 88 88  .o 88   88     8P
#    YP    88 8bodP' 88 88oodP 88 88ood8 88   88    dP

def UPDTASK_s_visibility_view_allow(self, prop_name, value, event=None, bypass=False,):
        mute_node(self,"% Optimization", mute=not value, frame=True) 

def UPDTASK_s_visibility_view_percentage(self, prop_name, value, event=None, bypass=False,):
        node_value(self, prop_name, 1-(value/100),)
    
def UPDTASK_s_visibility_view_viewport_method(self, prop_name, value, event=None, bypass=False,):
        node_value(self, prop_name, (value=="viewport_only"), entry="input", i=0)
        node_value(self, prop_name, (value=="except_rendered"), entry="input", i=1)

#Camera Optimization 

def UPDTASK_s_visibility_cam_allow(self, prop_name, value, event=None, bypass=False,):
        mute_color(self,"Camera Optimization", mute=not value,) 
        node_link(self, f"RR_GEO s_visibility_cam Receptor", f"RR_GEO s_visibility_cam {value}",)
        if (value==True):
            update_active_camera_nodegroup(force_update=True)

def UPDTASK_s_visibility_camclip_allow(self, prop_name, value, event=None, bypass=False,):
        node_value(self, "s_visibility_cam", value, entry="input", i=1)
        if (value==True):
            update_active_camera_nodegroup(force_update=True)

def UPDTASK_s_visibility_camclip_dir_crop_x(self, prop_name, value, event=None, bypass=False,):
        node_value(self, "s_visibility_cam", value, entry="input", i=2)

def UPDTASK_s_visibility_camclip_dir_crop_y(self, prop_name, value, event=None, bypass=False,):
        node_value(self, "s_visibility_cam", value, entry="input", i=3)

def UPDTASK_s_visibility_camclip_dir_shift_x(self, prop_name, value, event=None, bypass=False,):
        node_value(self, "s_visibility_cam", value, entry="input", i=4)

def UPDTASK_s_visibility_camclip_dir_shift_y(self, prop_name, value, event=None, bypass=False,):
        node_value(self, "s_visibility_cam", value, entry="input", i=5)

def UPDTASK_s_visibility_camclip_proximity(self, prop_name, value, event=None, bypass=False,):
        node_value(self, "s_visibility_cam", value, entry="input", i=6) 
        
def UPDTASK_s_visibility_camdist_allow(self, prop_name, value, event=None, bypass=False,):
        node_value(self, "s_visibility_cam", value, entry="input", i=7)
        if (value==True):
            update_active_camera_nodegroup(force_update=True)

def UPDTASK_s_visibility_camdist_min(self, prop_name, value, event=None, bypass=False,):
        node_value(self, "s_visibility_cam", value, entry="input", i=8)

def UPDTASK_s_visibility_camdist_max(self, prop_name, value, event=None, bypass=False,):
        node_value(self, "s_visibility_cam", value, entry="input", i=9)

def UPDTASK_s_visibility_cam_viewport_method(self, prop_name, value, event=None, bypass=False,):
        node_value(self, prop_name, (value=="viewport_only"), entry="input", i=0)
        node_value(self, prop_name, (value=="except_rendered"), entry="input", i=1)

# 8888b.  88 .dP"Y8 88""Yb 88        db    Yb  dP
#  8I  Yb 88 `Ybo." 88__dP 88       dPYb    YbdP
#  8I  dY 88 o.`Y8b 88"""  88  .o  dP__Yb    8P
# 8888Y"  88 8bodP' 88     88ood8 dP""""Yb  dP

def UPDTASK_s_display_allow(self, prop_name, value, event=None, bypass=False,):
        node_value(self, prop_name, value, entry="boolean")
        mute_color(self, "Display", mute=not value)
        mute_color(self, "Display Features", mute=not value)
        if (value==True):
            update_is_rendered_view_nodegroup()

def UPDTASK_s_display_method(self, prop_name, value, event=None, bypass=False,):
        node_link(self, prop_name, value,)
        node_value(self, "is_not_point_display", (value!="point"), entry="boolean")
        mute_node(self,"display_mute_if_not_placeholder", mute=(value not in ("placeholder","placeholder_custom")),)

def UPDTASK_s_display_placeholder_type(self, prop_name, value, event=None, bypass=False,):
        node_value(self, prop_name, bpy.data.objects[value], entry="input")

def UPDTASK_s_display_custom_placeholder_ptr(self, prop_name, value, event=None, bypass=False,):
        node_value(self, prop_name, value, entry="input")

def UPDTASK_s_display_placeholder_scale(self, prop_name, value, event=None, bypass=False,):
        node_value(self, prop_name, value, entry="vector")

def UPDTASK_s_display_point_radius(self, prop_name, value, event=None, bypass=False,):
        node_value(self, prop_name, value,)

def UPDTASK_s_display_camdist_allow(self, prop_name, value, event=None, bypass=False,):
        node_value(self, prop_name, value, entry="boolean")
        mute_color(self, "Closeby Optimization1", mute=not value)
        mute_color(self, "Closeby Optimization2", mute=not value)
        mute_node(self, "s_display_camdist", mute=not value)
        if (value==True):
            update_active_camera_nodegroup(force_update=True)

def UPDTASK_s_display_camdist_distance(self, prop_name, value, event=None, bypass=False,):
        node_value(self, "s_display_camdist", value, entry="input", i=0)

def UPDTASK_s_display_viewport_method(self, prop_name, value, event=None, bypass=False,):
        node_value(self, prop_name, (value=="viewport_only"), entry="input", i=0)
        node_value(self, prop_name, (value=="except_rendered"), entry="input", i=1)
    

# oooooooooooo               .        oooooooooo.    o8o                .          .oooooo.
# `888'     `8             .o8        `888'   `Y8b   `"'              .o8         d8P'  `Y8b
#  888          .ooooo.  .o888oo       888      888 oooo   .ooooo.  .o888oo      888            .ooooo.  ooo. .oo.
#  888oooo8    d88' `"Y8   888         888      888 `888  d88' `"Y8   888        888           d88' `88b `888P"Y88b
#  888    "    888         888         888      888  888  888         888        888     ooooo 888ooo888  888   888
#  888         888   .o8   888 .       888     d88'  888  888   .o8   888 .      `88.    .88'  888    .o  888   888
# o888o        `Y8bod8P'   "888"      o888bood8P'   o888o `Y8bod8P'   "888"       `Y8bood8P'   `Y8bod8P' o888o o888o


#Example of function to dict
#https://stackoverflow.com/questions/9168340/using-a-dictionary-to-select-function-to-execute/9168387#9168387

"""
#technique using decorator?
UpdateTasks = {}
task = lambda f: UpdateTasks.setdefault(f.__name__, f)
"""
#In the end i used Retrospection: check fct that startswith 'UPDTASK' within this file + collect them in dictionary


UpdateTasks = {}

for k,v in locals().copy().items():
    
    #check if is function and if an update task via naming system
    if callable(v) and k.startswith("UPDTASK"):

        #naming system, fct need to be UPDTASK_propname if is update fct for property and UPDTASKi09_propnameXX if property has multiple indexes
        #simple task?             idx: 012345678                                     idx: 0123456789
        if k[7]!="i":
            prop_name = k[8:]
            UpdateTasks[prop_name]=v
            continue 

        #or  multitask? some properties are repeated multiple time with an index, but have the same update fct
        idx = int(k[8:10])
        for i in range(1,idx+1):
            if "XX" in k:
                prop_name = k[11:].replace("XX",f"{i:02}")
                UpdateTasks[prop_name]=v
            elif "X" in k:
                prop_name = k[11:].replace("X",f"{i}")
                UpdateTasks[prop_name]=v
            else:
                raise Exception(f"Dorian, you did BS with the naming system")

        continue
    continue


def UPDTASK_fct(self, prop_name, value, event=None, bypass=False,):

    global UpdateTasks
    UPD_fct = UpdateTasks.get(prop_name)

    if UPD_fct is not None:
        UPD_fct(self, prop_name, value, event=event, bypass=bypass)
        return True

    return False


#   .oooooo.                                              o8o                 oooooooooooo               .
#  d8P'  `Y8b                                             `"'                 `888'     `8             .o8
# 888            .ooooo.  ooo. .oo.    .ooooo.  oooo d8b oooo   .ooooo.        888          .ooooo.  .o888oo
# 888           d88' `88b `888P"Y88b  d88' `88b `888""8P `888  d88' `"Y8       888oooo8    d88' `"Y8   888
# 888     ooooo 888ooo888  888   888  888ooo888  888      888  888             888    "    888         888
# `88.    .88'  888    .o  888   888  888    .o  888      888  888   .o8       888         888   .o8   888 .
#  `Y8bood8P'   `Y8bod8P' o888o o888o `Y8bod8P' d888b    o888o `Y8bod8P'      o888o        `Y8bod8P'   "888"


def named_attribute(self,prop_name,value):
    """because of dumb named attribute design we are forced to interact with our attribute outside of the modifier interface"""
    
    equivalences = {
        "s_rot_add_mask_ptr" : "Input_17_attribute_name",
        "s_rot_random_mask_ptr" : "Input_18_attribute_name",
        "s_rot_tilt_mask_ptr" : "Input_22_attribute_name",
        "s_scale_random_mask_ptr" : "Input_23_attribute_name",
        "s_scale_shrink_mask_ptr" : "Input_26_attribute_name",
        "s_scale_grow_mask_ptr" : "Input_24_attribute_name",
        "s_scale_mirror_mask_ptr" : "Input_25_attribute_name",
        "s_pattern1_mask_ptr" : "Input_27_attribute_name",
        "s_pattern2_mask_ptr" : "Input_28_attribute_name",
        "s_abiotic_elev_mask_ptr" : "Input_29_attribute_name",
        "s_abiotic_slope_mask_ptr" : "Input_30_attribute_name",
        "s_abiotic_dir_mask_ptr" : "Input_31_attribute_name",
        "s_abiotic_cur_mask_ptr" : "Input_32_attribute_name",
        "s_abiotic_border_mask_ptr" : "Input_33_attribute_name",
        "s_proximity_removenear_mask_ptr" : "Input_34_attribute_name",
        "s_proximity_leanover_mask_ptr" : "Input_35_attribute_name",
        "s_proximity_outskirt_mask_ptr" : "Input_37_attribute_name",
        "s_ecosystem_affinity_mask_ptr" : "Input_36_attribute_name",
        "s_ecosystem_repulsion_mask_ptr" : "Input_48_attribute_name",
        "s_wind_wave_mask_ptr" : "Input_38_attribute_name",
        "s_wind_noise_mask_ptr" : "Input_39_attribute_name",
        "s_push_offset_mask_ptr" : "Input_40_attribute_name",
        "s_push_dir_mask_ptr" : "Input_41_attribute_name",
        "s_push_noise_mask_ptr" : "Input_42_attribute_name",
        "s_push_fall_mask_ptr" : "Input_43_attribute_name",
        "s_rot_tilt_vcol_ptr" : "Input_45_attribute_name",
        "s_rot_align_y_vcol_ptr" : "Input_47_attribute_name",
        "s_wind_wave_flowmap_ptr" : "Input_49_attribute_name",
        "s_instances_vcol_ptr" : "Input_51_attribute_name",
        "s_mask_vg_ptr" : "Input_52_attribute_name",
        "s_mask_vcol_ptr" : "Input_53_attribute_name",
        "s_mask_bitmap_uv_ptr" : "Input_55_attribute_name",
        }

    mod = self.scatter_obj.modifiers["Scatter5 Geonode Engine MKI"]
    mod[equivalences[prop_name]] = value
    mod.show_in_editmode = not mod.show_in_editmode
    mod.show_in_editmode = not mod.show_in_editmode

    return None 

def get_enum_idx(self, prop_name, value,):

    return self.bl_rna.properties[prop_name].enum_items[value].value

def list_to_color(value):

    if len(value)==3:
        return [*value, 1]
    else:
        return [0,0,0,0]

def node_value(self, node_name, value, entry="output", i=0,):

    mod = self.scatter_obj.modifiers["Scatter5 Geonode Engine MKI"]
    nodes = mod.node_group.nodes

    node = nodes.get(node_name)
    if node is None:
        print("S5: '",node_name,"' not found")
        return None 

    if entry=="output": 
        if node.outputs[i].default_value != value:
            node.outputs[i].default_value = value 

    elif entry=="input":
        if node.inputs[i].default_value != value:
            node.inputs[i].default_value = value

    elif entry=="vector":
        if node.vector != value:
            node.vector = value

    elif entry=="integer":
        node.integer = value

    elif entry=="boolean":
        node.boolean = value

    elif entry=="string":
        if node.string != value:
            node.string = value

    elif entry=="texture":
        if node.inputs[1].default_value != value:
            node.inputs[1].default_value = value

    return None

def mute_color(self, node_name, mute=True,):

    mod = self.scatter_obj.modifiers["Scatter5 Geonode Engine MKI"]
    nodes = mod.node_group.nodes

    node = nodes.get(node_name)
    if node is None:
        print("S5: '",node_name,"' not found")
        return None 

    node.use_custom_color = not mute

    return None 

def mute_node(self, node_name, mute=True, frame=False,):

    mod = self.scatter_obj.modifiers["Scatter5 Geonode Engine MKI"]   
    nodes = mod.node_group.nodes

    did_mute = False

    node = nodes.get(node_name)
    if node is None:
        print("S5: '",node_name,"' not found")
        return None 

    #individual node mute

    if (frame == False):
        if node.mute != mute :
            node.mute = mute
            did_mute = True
        return did_mute

    #mute all nodes in frame

    if (node.mute != mute):

        for n in [n for n in nodes if (n.parent==node)]:
            node.mute = mute
            mute_node(self, n.name, mute=mute, frame=False)
            mute_color(self, node_name, mute=mute)
            continue 

        did_mute = True

    return did_mute

def node_link(self, input_name, output_name, input_i=0, output_i=0, create=True,):

    mod = self.scatter_obj.modifiers["Scatter5 Geonode Engine MKI"]
    nodes = mod.node_group.nodes

    if (input_name not in nodes):
        print("S5: '",input_name,"' not found")
        return None 

    if (output_name not in nodes):
        print("S5: '",output_name,"' not found")
        return None 

    _input  = nodes[input_name].inputs[input_i]
    _output = nodes[output_name].outputs[output_i]

    #Could perhaps gain perfs by checking if linked alread?
    if create:
        mod.node_group.links.new(_input, _output)

    return None 

def random_seed(self, event, api_is_random="", api_seed="",):

    #This random seed system is crap, i need to find a more elegant solution. I should not rely on eval() exec() this will prolly cause trouble down the line?

    # This fake BooleanProperty is acting as a function (will always be False)
    if eval(f"self.{api_is_random} == False"):
          return None
    else: exec(f"self.{api_is_random} = False")

    scat_scene = bpy.context.scene.scatter5
    emitter = self.id_data

    #Real update will happend when changing the seed api, so to avoid feedback loops we need to disable the update factory feature
    old_factory_delay_allow , old_factory_event_listening_allow = scat_scene.factory_delay_allow , scat_scene.factory_event_listening_allow
    scat_scene.factory_delay_allow = scat_scene.factory_event_listening_allow = False

    if (event.alt) and (scat_scene.factory_alt_allow):
        psys_sel = emitter.scatter5.get_psys_selected() if (scat_scene.factory_alt_selection_method=="active") else [p  for o in bpy.data.objects for p in o.scatter5.particle_systems if p.sel]
        for p in psys_sel:
            exec(f"p.{api_seed} = random.randint(0,9999)")
    else:
        exec(f"self.{api_seed} = random.randint(0,9999)")

    #restore update factory features
    scat_scene.factory_delay_allow , scat_scene.factory_event_listening_allow = old_factory_delay_allow , old_factory_event_listening_allow
    return None


# ooooo     ooo                  .o8                .                  oooooooooo.                 .
# `888'     `8'                 "888              .o8                  `888'   `Y8b              .o8
#  888       8  oo.ooooo.   .oooo888   .oooo.   .o888oo  .ooooo.        888      888  .oooo.   .o888oo  .oooo.
#  888       8   888' `88b d88' `888  `P  )88b    888   d88' `88b       888      888 `P  )88b    888   `P  )88b
#  888       8   888   888 888   888   .oP"888    888   888ooo888       888      888  .oP"888    888    .oP"888
#  `88.    .8'   888   888 888   888  d8(  888    888 . 888    .o       888     d88' d8(  888    888 . d8(  888
#    `YbodP'     888bod8P' `Y8bod88P" `Y888""8o   "888" `Y8bod8P'      o888bood8P'   `Y888""8o   "888" `Y888""8o
#                888
#               o888o


cam_loc = None
cam_rot_euler = None
cam_still_running = False 
cam_still_sum = 0

def update_active_camera_nodegroup(force_update=False):
    """update active camera node pointer"""

    #active camera found?
    
    scene = bpy.context.scene
    active_cam = scene.camera 
    if active_cam is None: 
        return None

    #active camera detect changes? 

    global cam_loc,cam_rot_euler
    if (active_cam.location==cam_loc and active_cam.rotation_euler==cam_rot_euler):
        if not force_update:
            return None 

    #special update methods

    if (scene.scatter5.factory_cam_update_method!="auto") and not force_update:

        if (scene.scatter5.factory_cam_update_method=="toggle"): 
            return None

        elif (scene.scatter5.factory_cam_update_method=="limit"): 

            global cam_still_running
            if cam_still_running:
                return None 

            def cam_still_delay():
                """update only when cam is still"""
                global cam_still_sum, cam_still_running
                new_sum = sum(active_cam.location) + sum(active_cam.rotation_euler)
                if new_sum != cam_still_sum: 
                    cam_still_running = True 
                    cam_still_sum = new_sum
                    return 0.45
                cam_still_running = False 
                update_active_camera_nodegroup(force_update=True)
                return None

            bpy.app.timers.register(cam_still_delay)
            return None 

    dprint("HANDLER: 'update_active_camera_nodegroup'",depsgraph=True,)
    
    #change value in nodegroup

    for ng in bpy.data.node_groups:
        if ng.name.startswith(".S Handler Active Camera"):

            ng.nodes["location"].vector = active_cam.location
            ng.nodes["rotation"].vector = active_cam.rotation_euler

            # maybe later..

            # if (ng.nodes["angle"].outputs[0].default_value != active_cam.data.angle):
            #     ng.nodes["angle"].outputs[0].default_value = active_cam.data.angle
            
            # if (ng.nodes["shift_x"].outputs[0].default_value != active_cam.data.shift_x):
            #     ng.nodes["shift_x"].outputs[0].default_value = active_cam.data.shift_x
            # if (ng.nodes["shift_y"].outputs[0].default_value != active_cam.data.shift_y):
            #     ng.nodes["shift_y"].outputs[0].default_value = active_cam.data.shift_y

            # if (ng.nodes["resolution_x"].outputs[0].default_value != scene.render.resolution_x):
            #     ng.nodes["resolution_x"].outputs[0].default_value = scene.render.resolution_x
            # if (ng.nodes["resolution_y"].outputs[0].default_value != scene.render.resolution_y):
            #     ng.nodes["resolution_y"].outputs[0].default_value = scene.render.resolution_y

    #save changed values in global 

    cam_loc, cam_rot_euler = active_cam.location.copy(), active_cam.rotation_euler.copy()

    return None

def update_is_rendered_view_nodegroup(value=None,):
    """update active camera node pointer"""

    dprint("HANDLER: 'update_is_rendered_view_nodegroup'",depsgraph=True)

    #check needed? perhaps we already have the information
    if value is None: 
        value = is_rendered_view()

    #change value in nodegroup
    for ng in bpy.data.node_groups:
        if ng.name.startswith(".S Handler is rendered"):
            ng.nodes["boolean"].boolean = value

    return None


def generate_edge_curvature_attr(o, eval_modifiers=True,):

    #get or create attribute
    attr = o.data.attributes.get("edge_curvature")
    if attr is None:
         attr = o.data.attributes.new("edge_curvature", "FLOAT", "EDGE")

    if eval_modifiers and ("SUBSURF" not in [m.type for m in o.modifiers]):
          depsgraph = bpy.context.evaluated_depsgraph_get()
          eo = o.evaluated_get(depsgraph)
          ob = eo.to_mesh(preserve_all_data_layers=True, depsgraph=depsgraph)
    else: ob = o.data

    #start bmesh
    import bmesh
    bm = bmesh.new()
    bm.from_mesh(ob)
    bm.edges.ensure_lookup_table()
    
    #loop over all bm edges (slow?) and fill attr with value
    for e in bm.edges:
        attr.data[e.index].value = e.calc_face_angle_signed(0.0)
    
    #free bmesh & update
    bm.free()
    attr.data.update()

    return None

def generate_edge_border_attr(o, eval_modifiers=True,):

    #get or create attribute
    attr = o.data.attributes.get("edge_border")
    if attr is None:
         attr = o.data.attributes.new("edge_border", "BOOLEAN", "EDGE")

    if eval_modifiers and ("SUBSURF" not in [m.type for m in o.modifiers]):
          depsgraph = bpy.context.evaluated_depsgraph_get()
          eo = o.evaluated_get(depsgraph)
          ob = eo.to_mesh(preserve_all_data_layers=True, depsgraph=depsgraph)
    else: ob = o.data

    #start bmesh
    import bmesh
    bm = bmesh.new()
    bm.from_mesh(ob)
    bm.edges.ensure_lookup_table()
    
    #loop over all bm edges (slow?) and fill attr with value
    for e in bm.edges:
        attr.data[e.index].value = e.is_boundary
    
    #free bmesh & update
    bm.free()
    attr.data.update()

    return None

#   .oooooo.                                               .
#  d8P'  `Y8b                                            .o8
# 888      888 oo.ooooo.   .ooooo.  oooo d8b  .oooo.   .o888oo  .ooooo.  oooo d8b
# 888      888  888' `88b d88' `88b `888""8P `P  )88b    888   d88' `88b `888""8P
# 888      888  888   888 888ooo888  888      .oP"888    888   888   888  888
# `88b    d88'  888   888 888    .o  888     d8(  888    888 . 888   888  888
#  `Y8bood8P'   888bod8P' `Y8bod8P' d888b    `Y888""8o   "888" `Y8bod8P' d888b
#               888
#              o888o


class SCATTER5_OT_density_coef_calculation(bpy.types.Operator):

    bl_idname = "scatter5.density_coef_calculation"
    bl_label = "Coef Calculation"
    bl_description = translate("Multiply/ Divide/ Add/ Substract your density by a given coefitient. hold [ALT] do the mathematical operation for every selected particle-systems by using the active system coefitient")
    bl_options     = {'INTERNAL','UNDO'}

    operation : bpy.props.StringProperty() # ADD/SUBSTRACT/MULTIPLY/DIVIDE

    def execute(self, context):

        scat_scene = bpy.context.scene.scatter5
        emitter    = scat_scene.emitter
        psys       = emitter.scatter5.particle_systems
        psy_active = emitter.scatter5.get_psy_active()

        def calculate(density, coef, operation):
            if (operation=="+"):
                return density + coef
            elif (operation=="-"):
                return density - coef
            elif (operation=="*"):
                return density * coef
            elif (operation=="/"): 
                if coef==0: return density
                return density / coef

        event = get_event()
        coef  = psy_active.s_distribution_coef

        #need to disable some bahavior to avoid feedback loop
        old_factory_delay_allow , old_factory_event_listening_allow = scat_scene.factory_delay_allow , scat_scene.factory_event_listening_allow
        scat_scene.factory_delay_allow = scat_scene.factory_event_listening_allow = False

        if (event.alt) and (scat_scene.factory_alt_allow):
            psys_sel = emitter.scatter5.get_psys_selected() if (scat_scene.factory_alt_selection_method=="active") else [p  for o in bpy.data.objects for p in o.scatter5.particle_systems if p.sel]
            for p in psys_sel:
                p.s_distribution_density = calculate(p.s_distribution_density, coef, self.operation)
        else:
            psy_active.s_distribution_density = calculate(psy_active.s_distribution_density, coef, self.operation)

        #Then restore
        scat_scene.factory_delay_allow , scat_scene.factory_event_listening_allow = old_factory_delay_allow , old_factory_event_listening_allow

        return {'FINISHED'}




classes = [

    SCATTER5_OT_density_coef_calculation,

    ]