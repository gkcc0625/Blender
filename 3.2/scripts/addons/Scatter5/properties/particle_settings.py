
#####################################################################################################
#
# ooooooooooooo                                      oooo         o8o
# 8'   888   `8                                      `888         `"'
#      888      oooo oooo    ooo  .ooooo.   .oooo.    888  oooo  oooo  ooo. .oo.    .oooooooo
#      888       `88. `88.  .8'  d88' `88b `P  )88b   888 .8P'   `888  `888P"Y88b  888' `88b
#      888        `88..]88..8'   888ooo888  .oP"888   888888.     888   888   888  888   888
#      888         `888'`888'    888    .o d8(  888   888 `88b.   888   888   888  `88bod8P'
#     o888o         `8'  `8'     `Y8bod8P' `Y888""8o o888o o888o o888o o888o o888o `8oooooo.
#                                                                                  d"     YD
#                                                                                  "Y88888P'
#####################################################################################################


import bpy

from .. import scattering
from .. resources.translate import translate


#generate code of feature mask properties 

def generate_featuremask_properties(name="name"):
    """this fun goal is to generate the redudant the properies declaration of featuremasks, 
    as the props are all declared in local space, they are stored internally in python in __annotations__""" 

    d = {}

    prop_name = f"{name}_mask_ptr"
    d[prop_name] = bpy.props.StringProperty(
        default="",
        update=scattering.update_factory.factory(prop_name, synchronize=True,),
        )

    prop_name = f"{name}_mask_reverse"
    d[prop_name] = bpy.props.BoolProperty(
        name=translate("Reverse"),
        default=False,
        update=scattering.update_factory.factory(prop_name, synchronize=False,),
        )

    prop_name = f"{name}_mask_method"
    d[prop_name] = bpy.props.EnumProperty(
        name=translate("Mask Method"), 
        description=translate("Universal Feature Masking System Method, choose how you'd like to mask the context feature. Masking will create a linear interpolation with default values."),
        default="none", 
        items=[ ("none",translate("None"),"","",0),
                ("mask_vg",translate("Vertex-Group"),"","",1),
                ("mask_vcol",translate("Vertex-Color"),"","",2),
                #("mask_img",translate("Image"),"","",3), #maybe for Scatter5.1 don't feel like implementing 5496854 UV Pointers in modifiers right now 
                ("mask_noise",translate("Noise"),"","",4),
              ],
        update=scattering.update_factory.factory(prop_name, is_delayed=False, synchronize=True),
        )

    prop_name = f"{name}_mask_color_sample_method"
    d[prop_name] = bpy.props.EnumProperty(
        name=translate("Sample Color"), 
        description=translate("Choose how you'd like to sample this color to a black/white normalized array of values."),
        default="id_greyscale", 
        items=[ ("id_greyscale",translate("Greyscale"),"",0),
                ("id_red",translate("Red"),"",1),
                ("id_green",translate("Green"),"",2),
                ("id_blue",translate("Blue"),"",3),
                ("id_black",translate("Black"),"",4),
                ("id_white",translate("White"),"",5),
                ("id_picker",translate("Picker"),"",6),
                #("id_hue",translate("hue"),"",7),
                ("id_saturation",translate("Saturation"),"",8),
                ("id_value",translate("Value"),"",9),
                #("id_aplha",translate("aplha"),"",10),
              ],
        update=scattering.update_factory.factory(prop_name, is_delayed=False, synchronize=False),
        )

    prop_name = f"{name}_mask_id_color_ptr"
    d[prop_name] = bpy.props.FloatVectorProperty(
        name=translate("ID Value"),
        subtype="COLOR",
        min=0, max=1,
        default=(1,0,0), 
        update=scattering.update_factory.factory(prop_name, is_delayed=True,  synchronize=False),
        )

    prop_name = f"{name}_mask_uv_ptr" #not currently use, for 5.1 because right now named attribute workflow is a mess
    d[prop_name] = bpy.props.StringProperty(
        default="UVMap",
        name=translate("This is the Uvmap attribute that your image will be projected upon"),
        update=scattering.update_factory.factory(prop_name, is_delayed=False, synchronize=False,),
        )

    prop_name = f"{name}_mask_noise_scale"
    d[prop_name] = bpy.props.FloatProperty(
        name=translate("Scale"),
        default=0.2,
        min=0,
        update=scattering.update_factory.factory(prop_name, is_delayed=False, synchronize=True,),
        )
    prop_name = f"{name}_mask_noise_brightness"
    d[prop_name] = bpy.props.FloatProperty(
        name=translate("Brightness"),
        default=1,
        min=0,
        soft_max=2,
        update=scattering.update_factory.factory(prop_name, is_delayed=False, synchronize=True,),
        )
    prop_name = f"{name}_mask_noise_contrast"
    d[prop_name] = bpy.props.FloatProperty(
        name=translate("Contrast"),
        default=3,
        min=0,
        soft_max=5,
        update=scattering.update_factory.factory(prop_name, is_delayed=False, synchronize=True,),
        )

    return d

def batch_generate_properties( name="XX", nbr=20, items={}, property_type=None, is_delayed=False, synchronize=False):
    """this fun goal is to generate the redudant the properies declaration"""

    d = {}

    for i in range(nbr):

        #starting from 1
        i+=1

        itm = items.copy()
        prop_name = name.replace("XX",f"{i:02}")
        itm["update"] = scattering.update_factory.factory(prop_name, is_delayed=is_delayed,  synchronize=synchronize)
        d[prop_name] = property_type(**itm)

    return d 


#few update fct, most are in the update factory  

def upd_hide_viewport(self,context):

    self.scatter_obj.hide_viewport = self.hide_viewport

    return None

def upd_hide_render(self,context): 

    self.scatter_obj.hide_render = self.hide_render

    return None

def upd_lock(self, context):

    if self.lock==True:
        self.lock = False
        v = not self.is_all_locked()
        
        for k in self.bl_rna.properties.keys():
            if k.endswith("_locked"):
                setattr(self,k,v)
            continue

    return None 

def upd_euler_to_direction_prop(self_name, prop_name,):
        
    def _self_euler_to_dir(self,context):

        from mathutils import Euler,Vector
        
        e = getattr(self, self_name)
        v = Vector((0.0, 0.0, 1.0))
        v.rotate(e)
    
        setattr(self, prop_name, v)
        return None

    return _self_euler_to_dir

def poll_closed_curve_type(self, object):

    return (object.type == "CURVE") and (object.data.splines[0].use_cyclic_u == True)


class SCATTER5_PROP_particle_systems(bpy.types.PropertyGroup): 
    """bpy.context.object.scatter5.particle_systems, will be stored on emitter"""

    # 88   88 888888 88 88     88 888888 Yb  dP
    # 88   88   88   88 88     88   88    YbdP
    # Y8   8P   88   88 88  .o 88   88     8P
    # `YbodP'   88   88 88ood8 88   88    dP

    scatter_obj : bpy.props.PointerProperty(
        type=bpy.types.Object, 
        description="Empty object with a Geonode modifier where the scattered points are generated on the given surface/emitter information. Note that manual mode will write vertices on this object.",
        )
    active : bpy.props.BoolProperty( #is autimatically updated when user change the ui list intproperty index
        default=False,               #is a ready-only property, please don't change this prop in other places than from the particle_systems_idx update fct
        )
    sel : bpy.props.BoolProperty(
        default=False,
        )

    # 88""Yb 888888 8b    d8  dP"Yb  Yb    dP 888888
    # 88__dP 88__   88b  d88 dP   Yb  Yb  dP  88__
    # 88"Yb  88""   88YbdP88 Yb   dP   YbdP   88""
    # 88  Yb 888888 88 YY 88  YbodP     YP    888888

    def remove_psy(self): #best to use bpy.ops.scatter5.remove_system()

        emitter = self.id_data

        #save selection 
        save_sel = [p.name for p in emitter.scatter5.particle_systems if p.sel]

        #remove scatter object 
        if (self.scatter_obj is not None): 
            bpy.data.meshes.remove(self.scatter_obj.data)

        #remove scatter geonode_coll collection
        geonode_coll = bpy.data.collections.get(f"psy : {self.name}")
        if geonode_coll is not None:
            bpy.data.collections.remove(geonode_coll)

        #remove scatter instance_coll (if not used by another psy)
        instance_coll = bpy.data.collections.get(f"ins_col : {self.name}")
        if instance_coll is not None:
            if self.s_instances_coll_ptr == instance_coll:

                from .. scattering.instances import collection_users

                if len(collection_users(instance_coll))==1:
                    bpy.data.collections.remove(instance_coll)

        #if we deleted an active system, then we will need to reset particle system ui list index
        was_active = None

        #find id from name in order to remove
        for i,p in enumerate(emitter.scatter5.particle_systems):
            if (p.name==self.name):
                was_active = i
                emitter.scatter5.particle_systems.remove(i)
                break
        
        if was_active is not None:

            if len(emitter.scatter5.particle_systems)==0:
                emitter.scatter5.particle_systems_idx = -1
            if was_active==0:
                emitter.scatter5.particle_systems_idx = 0
            else:
                emitter.scatter5.particle_systems_idx = was_active -1

        #restore selection needed, when we change active index, default behavior == reset selection and select active
        for p in save_sel:
            if p in emitter.scatter5.particle_systems:
                emitter.scatter5.particle_systems[p].sel = True

        return None

    # .dP"Y8 88  88  dP"Yb  Yb        dP     88  88 88 8888b.  888888
    # `Ybo." 88  88 dP   Yb  Yb  db  dP      88  88 88  8I  Yb 88__
    # o.`Y8b 888888 Yb   dP   YbdPYbdP       888888 88  8I  dY 88""
    # 8bodP' 88  88  YbodP     YP  YP        88  88 88 8888Y"  888888

    hide_viewport : bpy.props.BoolProperty(
        default=False, 
        description=translate("Hide this particle system in viewport"),
        update=upd_hide_viewport,
        )
        
    hide_render : bpy.props.BoolProperty(
        default=False, 
        description=translate("Hide this particle system in final render"),
        update=upd_hide_render,
        )

    # 88""Yb    db    88""Yb 888888 88  dP""b8 88     888888      dP""b8  dP"Yb  88   88 88b 88 888888
    # 88__dP   dPYb   88__dP   88   88 dP   `" 88     88__       dP   `" dP   Yb 88   88 88Yb88   88
    # 88"""   dP__Yb  88"Yb    88   88 Yb      88  .o 88""       Yb      Yb   dP Y8   8P 88 Y88   88
    # 88     dP""""Yb 88  Yb   88   88  YboodP 88ood8 888888      YboodP  YbodP  `YbodP' 88  Y8   88

    estimated_particlecount : bpy.props.FloatProperty(default=-1) #used in statistics

    def get_estimated_particle_count(self, state="RENDER",):
        """evaluate the psy particle count (will unhide psy if it was hidden) -- CARREFUL MIGHT BE SLOW -- DO NOT RUN IN REAL TIME""" 
        #if have multiple psy to get particle count, might be faster to run evaluated_depsgraph_get() once for all psys at once. see -> "scatter5.estimate"

        if (state=="RENDER") and (not self.hide_render):
            is_hidding = self.hide_viewport 
            if is_hidding:
                self.hide_viewport = False

        count = len([o for o in bpy.context.evaluated_depsgraph_get().object_instances if o.is_instance and o.parent.original == self.scatter_obj])

        if (state=="RENDER") and (not self.hide_render):
            if is_hidding:
                self.hide_viewport = True

        if self.s_visibility_view_allow:
            count = (self.estimated_particlecount/(100-self.s_visibility_view_percentage))*100
                
        self.estimated_particlecount = count
        return count

    def get_estimated_density(self, recalculate_square_area=True):
        """evaluate psy density /m², will remove masks and optimizations temporarily -- CARREFUL MIGHT BE SLOW -- DO NOT RUN IN REAL TIME"""

        emitter = self.id_data

        #Will need to disable all this, 
        #They Have an Impact on Density Estimation

        to_disable = [
            "s_mask_vcol_allow",
            "s_mask_bitmap_allow",
            "s_mask_curve_allow",
            "s_mask_vg_allow",
            "s_proximity_removenear_allow",
            "s_proximity_outskirt_allow",
            "s_ecosystem_affinity_allow",
            "s_ecosystem_repulsion_allow",
            "s_visibility_view_allow",
            "s_visibility_cam_allow",
            "s_display_allow",
            ]

        storage={}
        for prp in to_disable:
            value=getattr(self,prp)
            storage[prp]=value
            if value==True:
                setattr(self,prp,False)

        #get square area 
        if recalculate_square_area:
              square_area = emitter.scatter5.get_estimated_square_area()
        else: square_area = emitter.scatter5.estimated_square_area

        #get density 
        density = round( self.get_estimated_particle_count() / square_area ,4)

        #then restore
        for prp in to_disable:
            value=getattr(self,prp)
            if value!=storage[prp]:
                setattr(self,prp,storage[prp])

        return density

    # 88      dP"Yb   dP""b8 88  dP     .dP"Y8 Yb  dP .dP"Y8 888888 888888 8b    d8
    # 88     dP   Yb dP   `" 88odP      `Ybo."  YbdP  `Ybo."   88   88__   88b  d88
    # 88  .o Yb   dP Yb      88"Yb      o.`Y8b   8P   o.`Y8b   88   88""   88YbdP88
    # 88ood8  YbodP   YboodP 88  Yb     8bodP'  dP    8bodP'   88   888888 88 YY 88

    def is_locked(self,propname):
        """check if given keys, can be full propname or category name, is supposedly in  locked category"""

        _locked_api = "None"
        for cat in ["s_distribution","s_rot","s_scale","s_pattern","s_abiotic","s_proximity","s_ecosystem","s_push","s_wind","s_visibility","s_instances","s_display",]:
            if cat in propname:
                _locked_api = cat + "_locked"
                break
        _locked_api = self.get(_locked_api)
        return False if _locked_api is None else _locked_api

    def is_all_locked(self,):
        """check if all categories are locked, mainly used to display lock icon in GUI"""

        _locks = [self.get(k) for k,v in self.bl_rna.properties.items() if k.endswith("_locked")]
        return all(_locks)     

    lock : bpy.props.BoolProperty(
        default=False, 
        description=translate("Lock this particle-system scattering & clustering settings"),
        update=upd_lock,
        )

    s_distribution_locked : bpy.props.BoolProperty(description=translate("Lock/Unlock Settings"),)
    s_scale_locked        : bpy.props.BoolProperty(description=translate("Lock/Unlock Settings"),)
    s_rot_locked          : bpy.props.BoolProperty(description=translate("Lock/Unlock Settings"),)
    s_pattern_locked      : bpy.props.BoolProperty(description=translate("Lock/Unlock Settings"),)
    s_abiotic_locked      : bpy.props.BoolProperty(description=translate("Lock/Unlock Settings"),)
    s_proximity_locked    : bpy.props.BoolProperty(description=translate("Lock/Unlock Settings"),)
    s_ecosystem_locked    : bpy.props.BoolProperty(description=translate("Lock/Unlock Settings"),)
    s_push_locked         : bpy.props.BoolProperty(description=translate("Lock/Unlock Settings"),)
    s_wind_locked         : bpy.props.BoolProperty(description=translate("Lock/Unlock Settings"),)
    s_visibility_locked   : bpy.props.BoolProperty(description=translate("Lock/Unlock Settings"),)
    s_instances_locked    : bpy.props.BoolProperty(description=translate("Lock/Unlock Settings"),)
    s_display_locked      : bpy.props.BoolProperty(description=translate("Lock/Unlock Settings"),)

    # .dP"Y8 888888 888888 888888 88 88b 88  dP""b8 .dP"Y8
    # `Ybo." 88__     88     88   88 88Yb88 dP   `" `Ybo."
    # o.`Y8b 88""     88     88   88 88 Y88 Yb  "88 o.`Y8b
    # 8bodP' 888888   88     88   88 88  Y8  YboodP 8bodP'
    
    name : bpy.props.StringProperty(
        default="",
        update=scattering.rename.rename_particle,
        )
    
    name_bis : bpy.props.StringProperty( #important for renaming function
        default="",
        )

    s_color : bpy.props.FloatVectorProperty(
        subtype="COLOR",
        min=0, max=1,
        update=scattering.update_factory.factory("s_color", is_delayed=False,),
        )
    
    # .dP"Y8 888888 888888 888888 88 88b 88  dP""b8 .dP"Y8     88""Yb Yb  dP 88""Yb    db    .dP"Y8 .dP"Y8
    # `Ybo." 88__     88     88   88 88Yb88 dP   `" `Ybo."     88__dP  YbdP  88__dP   dPYb   `Ybo." `Ybo."
    # o.`Y8b 88""     88     88   88 88 Y88 Yb  "88 o.`Y8b     88""Yb   8P   88"""   dP__Yb  o.`Y8b o.`Y8b
    # 8bodP' 888888   88     88   88 88  Y8  YboodP 8bodP'     88oodP  dP    88     dP""""Yb 8bodP' 8bodP'
    
    def property_update_bypass(self, prop_name, value,):
        """directly run the property update function (== changing nodetree) witouth changing any property value"""
        return scattering.update_factory.UPDTASK_fct(self, prop_name, value, bypass=True,)

    # 8888b.  88 .dP"Y8 888888 88""Yb 88 88""Yb 88   88 888888 88  dP"Yb  88b 88
    #  8I  Yb 88 `Ybo."   88   88__dP 88 88__dP 88   88   88   88 dP   Yb 88Yb88
    #  8I  dY 88 o.`Y8b   88   88"Yb  88 88""Yb Y8   8P   88   88 Yb   dP 88 Y88
    # 8888Y"  88 8bodP'   88   88  Yb 88 88oodP `YbodP'   88   88  YbodP  88  Y8

    s_distribution_method : bpy.props.EnumProperty(
        name=translate("Method"),
        description=translate("Choose your distribution algorithm"),
        default= "random", 
        items= [ ("random",     translate("Random"), translate(""), "STICKY_UVS_DISABLE",1),
                 ("clumping",   translate("Clump"), translate(""), "STICKY_UVS_LOC",2),
                 ("verts",      translate("per Vertex"), translate(""), "VERTEXSEL",3),
                 ("faces",      translate("per Face"), translate(""), "SNAP_FACE_CENTER",4),
                 # ("edges",      translate("Edges Distribution"), translate(""), "EDGESEL",4), #TODO 5.1
                 # ("clean",      translate("Clean Distribution"), translate(""), "CON_PIVOT",5), #TODO 5.1
                 # ("curve",      translate("Curve-Based"), translate(""), "PARTICLE_POINT",6), #TODO 5.1
                 # ("pixel",      translate("Pixel-Based"), translate(""), "LIGHTPROBE_GRID",7), #TODO 5.1
                 ("manual_all", translate("Manual"), translate(""), "BRUSHES_ALL",8),
               ],
        update=scattering.update_factory.factory("s_distribution_method"),
        )
    s_distribution_space : bpy.props.EnumProperty(
        name=translate("Space"),
        default= "local", 
        items= [ ("local", translate("Local"), translate(""), "ORIENTATION_LOCAL",1 ),
                 ("global", translate("Global"), translate(""), "WORLD",2 ),
               ],
        update=scattering.update_factory.factory("s_distribution_space"),
        )
    s_distribution_space_bis : bpy.props.StringProperty() #Needed for manual mode, because it will override space, always local in this mode
    
    s_distribution_density : bpy.props.FloatProperty(
        name=translate("Particles/m²"), 
        default=0, 
        min=0, 
        update=scattering.update_factory.factory("s_distribution_density", is_delayed=True),
        )
    s_distribution_seed : bpy.props.IntProperty(
        name=translate("Seed"),
        default=0,
        min=0, 
        update=scattering.update_factory.factory("s_distribution_seed", is_delayed=True),
        )
    s_distribution_is_random_seed : bpy.props.BoolProperty( #= value of the property is of no importance, only the update signal matter
        name=translate("Radomize Seed"),
        default=False,
        update=scattering.update_factory.factory("s_distribution_is_random_seed", alt_support=False, ),
        )
    s_distribution_limit_distance_allow : bpy.props.BoolProperty(
        name=translate("Enable Limit Collision"),
        description=translate("Use the poisson disk algorithm to remove points too close by each other. Be warned this feature slows down performance"),
        default=False, 
        update=scattering.update_factory.factory("s_distribution_limit_distance_allow",),
        )
    s_distribution_limit_distance : bpy.props.FloatProperty(
        name=translate("Limit Collision"),
        description=translate("Use the poisson disk algorithm to remove points too close by each other. Be warned this feature slows down performance"),
        subtype="DISTANCE",
        default=0.2,
        min=0, 
        update=scattering.update_factory.factory("s_distribution_limit_distance", is_delayed=True),
        )

    s_distribution_coef : bpy.props.FloatProperty( #Not supported by Preset
        name=translate("Operation Coefficient"),
        default=2,
        min=0,
        update=scattering.update_factory.factory("s_distribution_coef", ),
        )

    ########## ########## Clumps 

    s_distribution_clump_density : bpy.props.FloatProperty(
        name=translate("Clump /m²"), 
        default=0.15,
        min=0.001, 
        update=scattering.update_factory.factory("s_distribution_clump_density", is_delayed=True),
        )
    s_distribution_clump_limit_distance_allow : bpy.props.BoolProperty(
        name=translate("Enable Limit Collision"),
        description=translate("Use the poisson disk algorithm to remove points too close by each other. Be warned this feature slows down performance"),
        default=False, 
        update=scattering.update_factory.factory("s_distribution_clump_limit_distance_allow",),
        )
    s_distribution_clump_limit_distance : bpy.props.FloatProperty(
        name=translate("Limit Collision"),
        description=translate("Use the poisson disk algorithm to remove points too close by each other. Be warned this feature slows down performance"),
        subtype="DISTANCE",
        default=0,
        min=0, 
        update=scattering.update_factory.factory("s_distribution_clump_limit_distance", is_delayed=True),
        )
    s_distribution_clump_seed : bpy.props.IntProperty(
        name=translate("Seed"),
        default=0,
        min=0, 
        update=scattering.update_factory.factory("s_distribution_clump_seed", is_delayed=True),
        )
    s_distribution_clump_is_random_seed : bpy.props.BoolProperty(
        name=translate("Radomize Seed"),
        default=False,
        update=scattering.update_factory.factory("s_distribution_clump_is_random_seed", alt_support=False, ),
        )

    s_distribution_clump_max_distance : bpy.props.FloatProperty(
        name=translate("Reach Distance"),
        subtype="DISTANCE",
        default=0.7, 
        min=0, 
        update=scattering.update_factory.factory("s_distribution_clump_max_distance", is_delayed=True),
        )
    s_distribution_clump_falloff : bpy.props.FloatProperty(
        name=translate("Falloff Distance"),
        subtype="DISTANCE",
        default=0.5,
        min=0, 
        update=scattering.update_factory.factory("s_distribution_clump_falloff", is_delayed=True),
        )
    s_distribution_clump_random_factor : bpy.props.FloatProperty(
        name=translate("Random Factor"),
        default=1, 
        min=0, 
        soft_max=10,
        update=scattering.update_factory.factory("s_distribution_clump_random_factor", is_delayed=True),
        )

    s_distribution_clump_children_density : bpy.props.FloatProperty(
        name=translate("Children /m²"), 
        default=15,
        min=0, 
        update=scattering.update_factory.factory("s_distribution_clump_children_density", is_delayed=True),
        )
    s_distribution_clump_children_limit_distance_allow : bpy.props.BoolProperty(
        name=translate("Enable Limit Collision"),
        description=translate("Use the poisson disk algorithm to remove points too close by each other. Be warned this feature slows down performance"),
        default=False, 
        update=scattering.update_factory.factory("s_distribution_clump_children_limit_distance_allow",),
        )
    s_distribution_clump_children_limit_distance : bpy.props.FloatProperty(
        name=translate("Limit Collision"),
        description=translate("Use the poisson disk algorithm to remove points too close by each other. Be warned this feature slows down performance"),
        subtype="DISTANCE",
        default=0.2, 
        min=0, 
        update=scattering.update_factory.factory("s_distribution_clump_children_limit_distance", is_delayed=True),
        )
    s_distribution_clump_children_seed : bpy.props.IntProperty(
        name=translate("Seed"),
        default=0,
        min=0, 
        update=scattering.update_factory.factory("s_distribution_clump_children_seed", is_delayed=True),
        )
    s_distribution_clump_children_is_random_seed : bpy.props.BoolProperty(
        name=translate("Radomize Seed"),
        default=False,
        update=scattering.update_factory.factory("s_distribution_clump_children_is_random_seed", alt_support=False, ),
        )


    # 8888b.  888888 88b 88 .dP"Y8 88 888888 Yb  dP     8b    d8    db    .dP"Y8 88  dP .dP"Y8
    #  8I  Yb 88__   88Yb88 `Ybo." 88   88    YbdP      88b  d88   dPYb   `Ybo." 88odP  `Ybo."
    #  8I  dY 88""   88 Y88 o.`Y8b 88   88     8P       88YbdP88  dP__Yb  o.`Y8b 88"Yb  o.`Y8b
    # 8888Y"  888888 88  Y8 8bodP' 88   88    dP        88 YY 88 dP""""Yb 8bodP' 88  Yb 8bodP'

    #Not supported by Preset

    ########## ########## Vgroups

    s_mask_vg_allow : bpy.props.BoolProperty( 
        name=translate("Vertex-Group Mask"), 
        default=False, 
        update=scattering.update_factory.factory("s_mask_vg_allow",synchronize=False),
        )
    s_mask_vg_ptr : bpy.props.StringProperty(
        update=scattering.update_factory.factory("s_mask_vg_ptr", synchronize=False,),
        )
    s_mask_vg_revert : bpy.props.BoolProperty(
        name=translate("Reverse"),
        update=scattering.update_factory.factory("s_mask_vg_revert", synchronize=False,),
        )

    ########## ########## VColors
    
    s_mask_vcol_allow : bpy.props.BoolProperty( 
        name=translate("Vertex-Color Mask"), 
        default=False, 
        update=scattering.update_factory.factory("s_mask_vcol_allow", synchronize=False,),
        )
    s_mask_vcol_ptr : bpy.props.StringProperty(
        update=scattering.update_factory.factory("s_mask_vcol_ptr", synchronize=False,),
        )
    s_mask_vcol_revert : bpy.props.BoolProperty(
        name=translate("Reverse"),
        update=scattering.update_factory.factory("s_mask_vcol_revert", synchronize=False,),
        )
    s_mask_vcol_color_sample_method : bpy.props.EnumProperty(
        name=translate("Sample Color"),
        description=translate("Choose how you'd like to sample this color to a black/white normalized array of values."),
        default="id_greyscale", 
        items=[ ("id_greyscale",translate("Greyscale"),"",0),
                ("id_red",translate("Red"),"",1),
                ("id_green",translate("Green"),"",2),
                ("id_blue",translate("Blue"),"",3),
                ("id_black",translate("Black"),"",4),
                ("id_white",translate("White"),"",5),
                ("id_picker",translate("Picker"),"",6),
                #("id_hue",translate("hue"),"",7),
                ("id_saturation",translate("Saturation"),"",8),
                ("id_value",translate("Value"),"",9),
                #("id_aplha",translate("aplha"),"",10),
              ],
        update=scattering.update_factory.factory("s_mask_vcol_color_sample_method"),
        )
    s_mask_vcol_id_color_ptr : bpy.props.FloatVectorProperty(
        name=translate("ID Value"),
        subtype="COLOR",
        min=0, max=1,
        default=(1,0,0), 
        update=scattering.update_factory.factory("s_mask_vcol_id_color_ptr", is_delayed=True, synchronize=False,),
        ) 

    ########## ########## Bitmap 

    s_mask_bitmap_allow : bpy.props.BoolProperty( 
        name=translate("Image Mask"), 
        default=False, 
        update=scattering.update_factory.factory("s_mask_bitmap_allow",synchronize=False),
        )
    s_mask_bitmap_uv_ptr : bpy.props.StringProperty(
        default="UVMap",
        name=translate("This is the Uvmap attribute that your image will be projected upon"),
        update=scattering.update_factory.factory("s_mask_bitmap_uv_ptr", synchronize=False,),
        )
    s_mask_bitmap_ptr : bpy.props.StringProperty(
        update=scattering.update_factory.factory("s_mask_bitmap_ptr", synchronize=False,),
        )
    s_mask_bitmap_revert : bpy.props.BoolProperty(
        name=translate("Reverse"),
        update=scattering.update_factory.factory("s_mask_bitmap_revert", synchronize=False,),
        )
    s_mask_bitmap_color_sample_method : bpy.props.EnumProperty(
        name=translate("Sample Color"),
        description=translate("Choose how you'd like to sample this color to a black/white normalized array of values."),
        default="id_greyscale", 
        items=[ ("id_greyscale",translate("Greyscale"),"",0),
                ("id_red",translate("Red"),"",1),
                ("id_green",translate("Green"),"",2),
                ("id_blue",translate("Blue"),"",3),
                ("id_black",translate("Black"),"",4),
                ("id_white",translate("White"),"",5),
                ("id_picker",translate("Picker"),"",6),
                #("id_hue",translate("hue"),"",7),
                ("id_saturation",translate("Saturation"),"",8),
                ("id_value",translate("Value"),"",9),
                #("id_aplha",translate("aplha"),"",10),
              ],
        update=scattering.update_factory.factory("s_mask_bitmap_color_sample_method"),
        )
    s_mask_bitmap_id_color_ptr : bpy.props.FloatVectorProperty(
        name=translate("ID Value"),
        subtype="COLOR",
        min=0, max=1,
        default=(1,0,0), 
        update=scattering.update_factory.factory("s_mask_bitmap_id_color_ptr", is_delayed=True, synchronize=False,),
        ) 

    ########## ########## Curves

    s_mask_curve_allow : bpy.props.BoolProperty( 
        name=translate("Bezier-Area Mask"), 
        default=False, 
        update=scattering.update_factory.factory("s_mask_curve_allow",synchronize=False),
        )
    s_mask_curve_ptr : bpy.props.PointerProperty(
        type=bpy.types.Object, 
        poll=poll_closed_curve_type,
        update=scattering.update_factory.factory("s_mask_curve_ptr",synchronize=False),
        )
    s_mask_curve_revert : bpy.props.BoolProperty(
        name=translate("Reverse"),
        update=scattering.update_factory.factory("s_mask_curve_revert", synchronize=False,),
        )

    ########## ########## Upward Obstruction

    s_mask_upward_allow : bpy.props.BoolProperty( 
        name=translate("Upward-Obstruction Mask"), 
        default=False, 
        update=scattering.update_factory.factory("s_mask_upward_allow",synchronize=False),
        )
    s_mask_upward_coll_ptr : bpy.props.PointerProperty(
        type=bpy.types.Collection,
        update=scattering.update_factory.factory("s_mask_upward_coll_ptr"),
        )
    s_mask_upward_revert : bpy.props.BoolProperty(
        name=translate("Reverse"),
        update=scattering.update_factory.factory("s_mask_upward_revert", synchronize=False,),
        )

    ########## ########## Material

    s_mask_material_allow : bpy.props.BoolProperty( 
        name=translate("Material ID Mask"), 
        default=False, 
        update=scattering.update_factory.factory("s_mask_material_allow", synchronize=False),
        )
    s_mask_material_ptr : bpy.props.StringProperty(
        update=scattering.update_factory.factory("s_mask_material_ptr", synchronize=False,),
        )
    s_mask_material_revert : bpy.props.BoolProperty(
        name=translate("Reverse"),
        update=scattering.update_factory.factory("s_mask_material_revert", synchronize=False,),
        )

    # .dP"Y8  dP""b8    db    88     888888
    # `Ybo." dP   `"   dPYb   88     88__
    # o.`Y8b Yb       dP__Yb  88  .o 88""
    # 8bodP'  YboodP dP""""Yb 88ood8 888888

    ########## ########## Default 

    s_scale_default_allow : bpy.props.BoolProperty(
        name=translate("Default Scale"), 
        default=False, 
        update=scattering.update_factory.factory("s_scale_default_allow"),
        )
    s_scale_default_space : bpy.props.EnumProperty(
        name=translate("Reference"),
        default="local_scale", 
        items= [ ("local_scale", translate("Local"),"",  "ORIENTATION_LOCAL",1 ),
                 ("global_scale", translate("Global"), "", "WORLD",2 ),
               ],
        update=scattering.update_factory.factory("s_scale_default_space",),
        )
    s_scale_default_value : bpy.props.FloatVectorProperty(
        name=translate("Factor"),
        subtype="XYZ", 
        default=(1,1,1), 
        update=scattering.update_factory.factory("s_scale_default_value", is_delayed=True),
        )

    ########## ########## Random

    s_scale_random_allow : bpy.props.BoolProperty(
        name=translate("Random Scale"), 
        default=False, 
        update=scattering.update_factory.factory("s_scale_random_allow"),
        )
    s_scale_random_factor  : bpy.props.FloatVectorProperty(
        name=translate("Random Factor"),
        subtype="XYZ", 
        default=(0.33,0.33,0.33), 
        soft_min=0,
        soft_max=2,
        update=scattering.update_factory.factory("s_scale_random_factor", is_delayed=True),
        )
    s_scale_random_probability : bpy.props.FloatProperty(
        name=translate("Probability"),
        subtype="PERCENTAGE",
        default=50, min=0, max=99, 
        update=scattering.update_factory.factory("s_scale_random_probability", is_delayed=True),
        )
    s_scale_random_method : bpy.props.EnumProperty(
        name=translate("Randomization Method"),
        default="random_uniform", 
        items= [ ("random_uniform", translate("Uniform"), "", 1 ),
                 ("random_vectorial",  translate("Vectorial"), "", 2 ),
               ],
        update=scattering.update_factory.factory("s_scale_random_method",),
        )
    s_scale_random_seed : bpy.props.IntProperty(
        name=translate("Seed"),
        default=0,
        min=0, 
        update=scattering.update_factory.factory("s_scale_random_seed", is_delayed=True),
        )
    s_scale_random_is_random_seed : bpy.props.BoolProperty( #= value of the property is of no importance, only the update signal matter
        name=translate("Radomize Seed"),
        default=False,
        update=scattering.update_factory.factory("s_scale_random_is_random_seed", alt_support=False, ),
        )
    #Feature Mask
    __annotations__.update(generate_featuremask_properties(name="s_scale_random",))

    ########## ########## Shrink

    s_scale_shrink_allow : bpy.props.BoolProperty(
        name=translate("Enable Shrink Mask"), 
        default=False, 
        update=scattering.update_factory.factory("s_scale_shrink_allow"),
        )
    s_scale_shrink_factor : bpy.props.FloatVectorProperty(
        name=translate("Shrink Factor"),
        subtype="XYZ",
        default=(0.1,0.1,0.1),
        soft_min=0,soft_max=1,
        update=scattering.update_factory.factory("s_scale_shrink_factor", is_delayed=True),
        )
    #Feature Mask
    __annotations__.update(generate_featuremask_properties(name="s_scale_shrink",))

    ########## ########## Grow

    s_scale_grow_allow : bpy.props.BoolProperty(
        name=translate("Enable Grow Mask"), 
        default=False, 
        update=scattering.update_factory.factory("s_scale_grow_allow"),
        )
    s_scale_grow_factor : bpy.props.FloatVectorProperty(
        name=translate("Growth Factor"),
        subtype="XYZ",
        default=(3,3,3),
        soft_min=1,soft_max=5,
        update=scattering.update_factory.factory("s_scale_grow_factor", is_delayed=True),
        )
    #Feature Mask
    __annotations__.update(generate_featuremask_properties(name="s_scale_grow",))

    ########## ########## Mirrorring 

    s_scale_mirror_allow : bpy.props.BoolProperty(
        name=translate("Hide Repetition with Random Mirrorring (by doing a scale by -1 on x or y axis)"),
        default=False,
        update=scattering.update_factory.factory("s_scale_mirror_allow", ),
        )
    s_scale_mirror_is_x : bpy.props.BoolProperty(
        default=True,
        update=scattering.update_factory.factory("s_scale_mirror_is_x", ),
        )
    s_scale_mirror_is_y : bpy.props.BoolProperty(
        default=True,
        update=scattering.update_factory.factory("s_scale_mirror_is_y", ),
        )
    s_scale_mirror_is_z : bpy.props.BoolProperty(
        default=False,
        update=scattering.update_factory.factory("s_scale_mirror_is_z", ),
        ) 
    
    s_scale_mirror_seed : bpy.props.IntProperty(
        name=translate("Seed"),
        default=0,
        update=scattering.update_factory.factory("s_scale_mirror_seed", is_delayed=True),
        )
    s_scale_mirror_is_random_seed : bpy.props.BoolProperty( #= value of the property is of no importance, only the update signal matter
        name=translate("Radomize Seed"),
        default=False,
        update=scattering.update_factory.factory("s_scale_mirror_is_random_seed", alt_support=False, ),
        )
    #Feature Mask
    __annotations__.update(generate_featuremask_properties(name="s_scale_mirror",))

########## ########## Minimal 

    s_scale_min_allow : bpy.props.BoolProperty(
        name=translate("Minimal Value"),
        default=False,
        update=scattering.update_factory.factory("s_scale_min_allow", ),
        )
    s_scale_min_method : bpy.props.EnumProperty(
        name=translate("Minimal Filter Method"),
        default="s_scale_min_lock",
        items      = [("s_scale_min_lock"  ,translate("Adjusting")  ,translate("Set minimal scale value to given value") ),
                      ("s_scale_min_remove",translate("Removing") ,translate("Remove instance if scale goes below given value") ),],
        update=scattering.update_factory.factory("s_scale_min_method"),
        )
    s_scale_min_value : bpy.props.FloatProperty(
        name=translate("Value"),
        default=0.05,
        soft_min=0, soft_max=10, 
        update=scattering.update_factory.factory("s_scale_min_value", is_delayed=True),
        )

    ########## ########## Clump Special  

    s_scale_clump_allow : bpy.props.BoolProperty(
        name=translate("Enable Children Scale Influence, Scale down when away from the clump center"), 
        default=True, 
        update=scattering.update_factory.factory("s_scale_clump_allow"),
        )
    s_scale_clump_value : bpy.props.FloatProperty(
        name=translate("Factor"), 
        default=0.3, min=0, max=1,  
        update=scattering.update_factory.factory("s_scale_clump_value", is_delayed=True),
        )

    # 88""Yb  dP"Yb  888888    db    888888 88  dP"Yb  88b 88
    # 88__dP dP   Yb   88     dPYb     88   88 dP   Yb 88Yb88
    # 88"Yb  Yb   dP   88    dP__Yb    88   88 Yb   dP 88 Y88
    # 88  Yb  YbodP    88   dP""""Yb   88   88  YbodP  88  Y8

    ########## ########## Align Z

    s_rot_align_z_allow : bpy.props.BoolProperty(
        name=translate("Particle Normal Alignment"), 
        description=translate("Define your particle normal (also called particle +Z axis or particle upward direction) by aligning toward a chosen axis"),
        default=False, 
        update=scattering.update_factory.factory("s_rot_align_z_allow"),
        )
    s_rot_align_z_method : bpy.props.EnumProperty(
        name=translate("Normal Axis"), 
        description=translate("Define your particle normal (also called particle +Z axis or particle upward direction) by aligning toward a chosen axis"),
        default= "meth_align_z_normal",
        items= [ ("meth_align_z_normal",  translate("Surface Normal"),     translate(""),"NORMALS_FACE",0),
                 ("meth_align_z_local",   translate("Local Z"),    translate(""),"ORIENTATION_LOCAL",1),
                 ("meth_align_z_global",  translate("Global Z"),   translate(""),"WORLD",2),
                #("meth_align_z_origin",  translate("Emitter Origin"),     translate(""),"PIVOT_BOUNDBOX",3),
                 ("meth_align_z_object",  translate("Object Origin"), translate(""),"EYEDROPPER",4),
                 #("meth_align_z_random",  translate("Random"),     translate(""),"ORIENTATION_GIMBAL",5),
               ],
        update=scattering.update_factory.factory("s_rot_align_z_method"),
        )
    s_rot_align_z_revert : bpy.props.BoolProperty(
        name=translate("Reverse"),
        description=translate("Reverse alignment axis"),
        default=False, 
        update=scattering.update_factory.factory("s_rot_align_z_revert"),
        )
    s_rot_align_z_random_seed : bpy.props.IntProperty(
        name=translate("Seed"),
        default=0,
        min=0, 
        update=scattering.update_factory.factory("s_rot_align_z_random_seed", is_delayed=True),
        )
    s_rot_align_z_is_random_seed : bpy.props.BoolProperty( #= value of the property is of no importance, only the update signal matter
        name=translate("Radomize Seed"),
        default=False,
        update=scattering.update_factory.factory("s_rot_align_z_is_random_seed", alt_support=False, ),
        )
    s_rot_align_z_influence_allow : bpy.props.BoolProperty(
        name=translate("Vertical Influence"), 
        description=translate("This feature will mix your chosen alignment method with global or local Z alignment depending on your distribution space."),
        default=False, 
        update=scattering.update_factory.factory("s_rot_align_z_influence_allow"),
        )
    s_rot_align_z_influence_value : bpy.props.FloatProperty( #was 's_rot_align_z_method_mix' in beta, now legacy property 
        name=translate("Direction"), 
        description=translate("-1.0 means a complete alignment with -Z, +1.0 for +Z. Values in between represents the alignment strength. A Value of 0.0 represents no influences at all."),
        default=0.7, min=-1, max=1,
        precision=3,
        update=scattering.update_factory.factory("s_rot_align_z_influence_value", is_delayed=True),
        )

    s_rot_align_z_object  : bpy.props.PointerProperty(
        name=translate("Object"),
        type=bpy.types.Object, 
        update=scattering.update_factory.factory("s_rot_align_z_object"),
        )

    s_rot_align_z_clump_allow : bpy.props.BoolProperty(
        name=translate("Align children normal to clump center"), 
        default=False, 
        update=scattering.update_factory.factory("s_rot_align_z_clump_allow"),
        )
    s_rot_align_z_clump_value : bpy.props.FloatProperty(
        name=translate("Direction"), 
        default=-0.5, soft_min=-2, soft_max=2,  
        update=scattering.update_factory.factory("s_rot_align_z_clump_value", is_delayed=True),
        )

    ########## ########## Align Y

    s_rot_align_y_allow : bpy.props.BoolProperty(
        name=translate("Particle Tangent Alignment"), 
        description=translate("Define your particle tangent (also called particle +Y axis or particle forward direction) by aligning toward a chosen axis"),
        default=False, 
        update=scattering.update_factory.factory("s_rot_align_y_allow"),
        )
    s_rot_align_y_method : bpy.props.EnumProperty(
        name=translate("Tangent Axis"), 
        description=translate("Define your particle tangent (also called particle +Y axis or particle forward direction) by aligning toward a chosen axis"),
        default= "meth_align_y_local",
        items= [ ("meth_align_y_downslope", translate("Downslope"), translate(""), "SORT_ASC",0),
                 ("meth_align_y_local", translate("Local Y"), translate(""), "ORIENTATION_LOCAL",1),
                 ("meth_align_y_global", translate("Global Y"), translate(""), "WORLD",2),
                #("meth_align_y_origin", translate("Emitter Origin"), translate(""), "PIVOT_BOUNDBOX",3),
                 ("meth_align_y_object", translate("Object Origin"), translate(""), "EYEDROPPER",4),
                 ("meth_align_y_flow", translate("Flowmap"), translate(""), "ANIM",5),
                 ("meth_align_y_random", translate("Random"), translate(""), "ORIENTATION_GIMBAL",6),
               ],
        update=scattering.update_factory.factory("s_rot_align_y_method"),
        )
    s_rot_align_y_revert : bpy.props.BoolProperty(
        name=translate("Reverse"),
        description=translate("Reverse alignment axis"),
        default=False, 
        update=scattering.update_factory.factory("s_rot_align_y_revert"),
        )
    s_rot_align_y_random_seed : bpy.props.IntProperty(
        name=translate("Seed"),
        default=0,
        min=0, 
        update=scattering.update_factory.factory("s_rot_align_y_random_seed", is_delayed=True),
        )
    s_rot_align_y_is_random_seed : bpy.props.BoolProperty( #= value of the property is of no importance, only the update signal matter
        name=translate("Radomize Seed"),
        default=False,
        update=scattering.update_factory.factory("s_rot_align_y_is_random_seed", alt_support=False, ),
        )

    s_rot_align_y_object : bpy.props.PointerProperty(
        name=translate("Object"),
        type=bpy.types.Object, 
        update=scattering.update_factory.factory("s_rot_align_y_object"),
        )

    s_rot_align_y_flow_method : bpy.props.EnumProperty(
        name= translate("Flowmap Method"),  
        default= "flow_vcol",
        items= [ ("flow_vcol", translate("Vertex Colors"), translate(""), "VPAINT_HLT",1),
                 ("flow_text", translate("Texture Data"),  translate(""), "NODE_TEXTURE",2),
               ],
        update=scattering.update_factory.factory("s_rot_align_y_flow_method"),
        )
    s_rot_align_y_flow_direction : bpy.props.FloatProperty(
        name=translate("Direction"),  
        subtype="ANGLE",
        default=0, 
        precision=3,
        update=scattering.update_factory.factory("s_rot_align_y_flow_direction"),
        )
    s_rot_align_y_texture_ptr : bpy.props.StringProperty(
        description="Internal property that will update a TEXTURE_NODE node tree from given nodetree name, used for presets and most importantly copy/paste or synchronization",
        update=scattering.update_factory.factory("s_rot_align_y_texture_ptr",),
        )
    s_rot_align_y_vcol_ptr : bpy.props.StringProperty(
        default="",
        update=scattering.update_factory.factory("s_rot_align_y_vcol_ptr", synchronize=False,),
        )

    ########## ########## Random Rotation 

    s_rot_random_allow : bpy.props.BoolProperty(
        name=translate("Random Rotation"), 
        default=False, 
        update=scattering.update_factory.factory("s_rot_random_allow"),
        )
    s_rot_random_tilt_value : bpy.props.FloatProperty(
        name=translate("Tilt"), 
        subtype="ANGLE",
        default=0.3490659,
        update=scattering.update_factory.factory("s_rot_random_tilt_value", is_delayed=True),
        )
    s_rot_random_yaw_value : bpy.props.FloatProperty(
        name=translate("Yaw"), 
        subtype="ANGLE",
        default=6.28,
        update=scattering.update_factory.factory("s_rot_random_yaw_value", is_delayed=True),
        )
    s_rot_random_seed : bpy.props.IntProperty(
        name=translate("Seed"),
        default=0,
        min=0, 
        update=scattering.update_factory.factory("s_rot_random_seed", is_delayed=True),
        )
    s_rot_random_is_random_seed : bpy.props.BoolProperty( #= value of the property is of no importance, only the update signal matter
        name=translate("Radomize Seed"),
        default=False,
        update=scattering.update_factory.factory("s_rot_random_is_random_seed", alt_support=False, ),
        )
    #Feature Mask
    __annotations__.update(generate_featuremask_properties(name="s_rot_random",))

    ########## ########## Added Rotation

    s_rot_add_allow : bpy.props.BoolProperty(
        name=translate("Default Rotation Values"),
        default=False, 
        update=scattering.update_factory.factory("s_rot_add_allow"),
        )
    s_rot_add_default : bpy.props.FloatVectorProperty(
        name=translate("Add Angle"),
        subtype="EULER",
        default=(0,0,0), 
        update=scattering.update_factory.factory("s_rot_add_default", is_delayed=True),
        )
    s_rot_add_random : bpy.props.FloatVectorProperty(
        name=translate("Add Random Angle"),
        subtype="EULER",
        default=(0,0,0), 
        update=scattering.update_factory.factory("s_rot_add_random", is_delayed=True),
        )
    s_rot_add_seed : bpy.props.IntProperty(
        name=translate("Seed"),
        default=0,
        min=0, 
        update=scattering.update_factory.factory("s_rot_add_seed", is_delayed=True),
        )
    s_rot_add_is_random_seed : bpy.props.BoolProperty( #= value of the property is of no importance, only the update signal matter
        name=translate("Radomize Seed"),
        default=False,
        update=scattering.update_factory.factory("s_rot_add_is_random_seed", alt_support=False, ),
        )
    s_rot_add_snap : bpy.props.FloatProperty(
        default=0,
        name=translate("Snap"), 
        subtype="ANGLE",
        min=0,
        soft_max=6.283185, #=360d
        update=scattering.update_factory.factory("s_rot_add_snap", is_delayed=True),
        )
    #Feature Mask
    __annotations__.update(generate_featuremask_properties(name="s_rot_add",))

    ########## ########## Tilt

    s_rot_tilt_allow : bpy.props.BoolProperty(
        name=translate("Allow Tilting Control via Flowmap"), 
        default=False, 
        update=scattering.update_factory.factory("s_rot_tilt_allow"),
        )
    s_rot_tilt_method : bpy.props.EnumProperty(
        name= translate("Flowmap Method"),  
        default= "tilt_vcol",
        items= [ ("tilt_vcol", translate("Vertex Colors"), translate(""), "VPAINT_HLT",1),
                 ("tilt_text", translate("Texture Data"),  translate(""), "NODE_TEXTURE",2),
               ],
        update=scattering.update_factory.factory("s_rot_tilt_method"),
        )
    s_rot_tilt_force : bpy.props.FloatProperty(
        name=translate("Strength"), 
        default=0.7,
        soft_min=-1,
        soft_max=1,
        update=scattering.update_factory.factory("s_rot_tilt_force"),
        )
    s_rot_tilt_direction : bpy.props.FloatProperty(
        name=translate("Direction"),  
        subtype="ANGLE",
        default=0,
        precision=3,
        update=scattering.update_factory.factory("s_rot_tilt_direction"),
        )
    s_rot_tilt_blue_is_strength : bpy.props.BoolProperty(
        name=translate("Blue Channel as Strength"), 
        default=False, 
        update=scattering.update_factory.factory("s_rot_tilt_blue_is_strength"),
        )
    s_rot_tilt_texture_ptr : bpy.props.StringProperty(
        description="Internal property that will update a TEXTURE_NODE node tree from given nodetree name, used for presets and most importantly copy/paste or synchronization",
        update=scattering.update_factory.factory("s_rot_tilt_texture_ptr",),
        )
    s_rot_tilt_vcol_ptr : bpy.props.StringProperty(
        default="",
        update=scattering.update_factory.factory("s_rot_tilt_vcol_ptr", synchronize=False,),
        )
    #Feature Mask
    __annotations__.update(generate_featuremask_properties(name="s_rot_tilt",))

    # 88""Yb    db    888888 888888 888888 88""Yb 88b 88 .dP"Y8
    # 88__dP   dPYb     88     88   88__   88__dP 88Yb88 `Ybo."
    # 88"""   dP__Yb    88     88   88""   88"Yb  88 Y88 o.`Y8b
    # 88     dP""""Yb   88     88   888888 88  Yb 88  Y8 8bodP'

    #These are per particle pattern settings,
    #other params are stored per texture data block!

    ########## ########## Pattern Slot 1

    s_pattern1_allow : bpy.props.BoolProperty(
        default=False,
        name=translate("Enable Pattern"),
        update=scattering.update_factory.factory("s_pattern1_allow",),
        )
    s_pattern1_texture_ptr : bpy.props.StringProperty(
        description="Internal property that will update a TEXTURE_NODE node tree from given nodetree name, used for presets and most importantly copy/paste or synchronization",
        update=scattering.update_factory.factory("s_pattern1_texture_ptr",),
        )
    #->Distribution Influence
    s_pattern1_dist_influence : bpy.props.FloatProperty(
        name=translate("Density"),
        default=100, subtype="PERCENTAGE", min=0, max=100, precision=1,
        update=scattering.update_factory.factory("s_pattern1_dist_influence", is_delayed=True),
        )
    s_pattern1_dist_revert : bpy.props.BoolProperty(
        name=translate("Reverse Influence"),
        update=scattering.update_factory.factory("s_pattern1_dist_revert",),
        )
    #->Scale Influence
    s_pattern1_scale_influence: bpy.props.FloatProperty(
        name=translate("Scale"),
        default=70, subtype="PERCENTAGE", min=0, max=100, precision=1,
        update=scattering.update_factory.factory("s_pattern1_scale_influence", is_delayed=True),
        )
    s_pattern1_scale_revert : bpy.props.BoolProperty(
        name=translate("Reverse Influence"),
        update=scattering.update_factory.factory("s_pattern1_scale_revert",),
        )
    #->ID Methods
    s_pattern1_color_sample_method : bpy.props.EnumProperty(
        name=translate("Sample Color"),
        description=translate("Filter the color by given ID method"),
        default="id_greyscale", 
        items=[ ("id_greyscale",translate("Greyscale"),"",0),
                ("id_red",translate("Red"),"",1),
                ("id_green",translate("Green"),"",2),
                ("id_blue",translate("Blue"),"",3),
                ("id_black",translate("Black"),"",4),
                ("id_white",translate("White"),"",5),
                ("id_picker",translate("Picker"),"",6),
                #("id_hue",translate("hue"),"",7),
                ("id_saturation",translate("Saturation"),"",8),
                ("id_value",translate("Value"),"",9),
                #("id_aplha",translate("aplha"),"",10),
              ],
        update=scattering.update_factory.factory("s_pattern1_color_sample_method"),
        )
    s_pattern1_id_color_ptr : bpy.props.FloatVectorProperty(
        name=translate("ID Value"),
        subtype="COLOR",
        min=0, max=1,
        default=(1,0,0), 
        update=scattering.update_factory.factory("s_pattern1_id_color_ptr", is_delayed=True),
        )
    s_pattern1_id_color_tolerence: bpy.props.FloatProperty(
        name=translate("Tolerence"),
        default=0.15, soft_min=0, soft_max=1,
        update=scattering.update_factory.factory("s_pattern1_id_color_tolerence", is_delayed=True),
        )
    #Feature Mask
    __annotations__.update(generate_featuremask_properties(name="s_pattern1",))

    ########## ########## Pattern Slot 2

    s_pattern2_allow : bpy.props.BoolProperty(
        default=False,
        name=translate("Enable Pattern"),
        update=scattering.update_factory.factory("s_pattern2_allow",),
        )
    s_pattern2_texture_ptr : bpy.props.StringProperty(
        description="Internal property that will update a TEXTURE_NODE node tree from given nodetree name, used for presets and most importantly copy/paste or synchronization",
        update=scattering.update_factory.factory("s_pattern2_texture_ptr",),
        )
    #->Distribution Influence
    s_pattern2_dist_influence: bpy.props.FloatProperty(
        name=translate("Density"),
        default=100, subtype="PERCENTAGE", min=0, max=100, precision=1,
        update=scattering.update_factory.factory("s_pattern2_dist_influence", is_delayed=True),
        )
    s_pattern2_dist_revert : bpy.props.BoolProperty(
        name=translate("Reverse Influence"),
        update=scattering.update_factory.factory("s_pattern2_dist_revert",),
        )
    #->Scale Influence
    s_pattern2_scale_influence : bpy.props.FloatProperty(
        name=translate("Scale"),
        default=70, subtype="PERCENTAGE", min=0, max=100, precision=1,
        update=scattering.update_factory.factory("s_pattern2_scale_influence", is_delayed=True),
        )
    s_pattern2_scale_revert : bpy.props.BoolProperty(
        name=translate("Reverse Influence"),
        update=scattering.update_factory.factory("s_pattern2_scale_revert",),
        )
    #->ID Methods
    s_pattern2_color_sample_method : bpy.props.EnumProperty(
        name=translate("Sample Color"),
        description=translate("Filter the color by given ID method"),
        default="id_greyscale", 
        items=[ ("id_greyscale",translate("Greyscale"),"",0),
                ("id_red",translate("Red"),"",1),
                ("id_green",translate("Green"),"",2),
                ("id_blue",translate("Blue"),"",3),
                ("id_black",translate("Black"),"",4),
                ("id_white",translate("White"),"",5),
                ("id_picker",translate("Picker"),"",6),
                #("id_hue",translate("hue"),"",7),
                ("id_saturation",translate("Saturation"),"",8),
                ("id_value",translate("Value"),"",9),
                #("id_aplha",translate("aplha"),"",10),
              ],
        update=scattering.update_factory.factory("s_pattern2_color_sample_method"),
        )
    s_pattern2_id_color_ptr : bpy.props.FloatVectorProperty(
        name=translate("ID Value"),
        subtype="COLOR",
        min=0, max=1,
        default=(1,0,0), 
        update=scattering.update_factory.factory("s_pattern2_id_color_ptr", is_delayed=True),
        )
    s_pattern2_id_color_tolerence: bpy.props.FloatProperty(
        name=translate("Tolerence"),
        default=0.15, soft_min=0, soft_max=1,
        update=scattering.update_factory.factory("s_pattern2_id_color_tolerence", is_delayed=True),
        )
    #Feature Mask
    __annotations__.update(generate_featuremask_properties(name="s_pattern2",))

    #    db    88""Yb 88  dP"Yb  888888 88  dP""b8
    #   dPYb   88__dP 88 dP   Yb   88   88 dP   `"
    #  dP__Yb  88""Yb 88 Yb   dP   88   88 Yb
    # dP""""Yb 88oodP 88  YbodP    88   88  YboodP

    ########## ########## Elevation

    s_abiotic_elev_allow : bpy.props.BoolProperty(
        default=False,
        update=scattering.update_factory.factory("s_abiotic_elev_allow",),
        )
    s_abiotic_elev_space : bpy.props.EnumProperty(   
        name=translate("Space"),
        default="local", 
        items= [ ("local", translate("Local"),"",  "ORIENTATION_LOCAL",0 ),
                 ("global", translate("Global"), "", "WORLD",1 ),
               ],
        update=scattering.update_factory.factory("s_abiotic_elev_space",),
        )
    #local parameters
    s_abiotic_elev_min_value_local : bpy.props.FloatProperty(
        name=translate("Min"),
        subtype="PERCENTAGE",
        default=0,
        min=0, 
        max=100,  
        precision=1,
        update=scattering.update_factory.factory("s_abiotic_elev_min_value_local", is_delayed=True),
        )
    s_abiotic_elev_min_falloff_local : bpy.props.FloatProperty(
        name=translate("Transition"),
        subtype="PERCENTAGE",
        default=0,
        min=0, 
        max=100, 
        soft_max=30, 
        precision=1,
        update=scattering.update_factory.factory("s_abiotic_elev_min_falloff_local", is_delayed=True),
        ) 
    s_abiotic_elev_max_value_local : bpy.props.FloatProperty(
        name=translate("Max"),
        subtype="PERCENTAGE",
        default=75,
        min=0, 
        max=100, 
        precision=1,
        update=scattering.update_factory.factory("s_abiotic_elev_max_value_local", is_delayed=True),
        ) 
    s_abiotic_elev_max_falloff_local : bpy.props.FloatProperty(
        name=translate("Transition"),
        subtype="PERCENTAGE",
        default=5,
        min=0, 
        max=100, 
        soft_max=30, 
        precision=1,
        update=scattering.update_factory.factory("s_abiotic_elev_max_falloff_local", is_delayed=True),
        )
    #global parameters
    s_abiotic_elev_min_value_global : bpy.props.FloatProperty(
        name=translate("Min"),
        subtype="DISTANCE",
        default=0,
        precision=1,
        update=scattering.update_factory.factory("s_abiotic_elev_min_value_global", is_delayed=True),
        )
    s_abiotic_elev_min_falloff_global : bpy.props.FloatProperty(
        name=translate("Transition"),
        subtype="DISTANCE",
        default=0,
        min=0, 
        precision=1,
        update=scattering.update_factory.factory("s_abiotic_elev_min_falloff_global", is_delayed=True),
        ) 
    s_abiotic_elev_max_value_global : bpy.props.FloatProperty(
        name=translate("Maximal"),
        subtype="DISTANCE",
        default=10,
        precision=1,
        update=scattering.update_factory.factory("s_abiotic_elev_max_value_global", is_delayed=True),
        ) 
    s_abiotic_elev_max_falloff_global : bpy.props.FloatProperty(
        name=translate("Transition"),
        subtype="DISTANCE",
        default=0,
        min=0, 
        precision=1,
        update=scattering.update_factory.factory("s_abiotic_elev_max_falloff_global", is_delayed=True),
        ) 
    #Particle Influence
    s_abiotic_elev_dist_influence: bpy.props.FloatProperty(
        name=translate("Density"),
        default=100, 
        subtype="PERCENTAGE", 
        min=0, 
        max=100, 
        precision=1,
        update=scattering.update_factory.factory("s_abiotic_elev_dist_influence", is_delayed=True),
        )
    s_abiotic_elev_dist_revert : bpy.props.BoolProperty(
        name=translate("Reverse Influence"),
        update=scattering.update_factory.factory("s_abiotic_elev_dist_revert",),
        )
    s_abiotic_elev_scale_influence: bpy.props.FloatProperty(
        name=translate("Scale"),
        default=0, 
        subtype="PERCENTAGE", 
        min=0, 
        max=100, 
        precision=1,
        update=scattering.update_factory.factory("s_abiotic_elev_scale_influence", is_delayed=True),
        )
    s_abiotic_elev_scale_revert : bpy.props.BoolProperty(
        name=translate("Reverse Influence"),
        update=scattering.update_factory.factory("s_abiotic_elev_scale_revert",),
        )
    #Feature Mask
    __annotations__.update(generate_featuremask_properties(name="s_abiotic_elev",))

    ########## ########## Slope

    s_abiotic_slope_allow : bpy.props.BoolProperty(
        default=False,
        update=scattering.update_factory.factory("s_abiotic_slope_allow",),
        )
    s_abiotic_slope_space : bpy.props.EnumProperty(   
        name=translate("Space"),
        default="local", 
        items= [ ("local", translate("Local"),"",  "ORIENTATION_LOCAL",0 ),
                 ("global", translate("Global"), "", "WORLD",1 ),
               ],
        update=scattering.update_factory.factory("s_abiotic_slope_space",),
        )
    s_abiotic_slope_absolute : bpy.props.BoolProperty(
        default=True,
        name=translate("Use Absolute Values"),
        update=scattering.update_factory.factory("s_abiotic_slope_absolute"),
        )
    #parameters
    s_abiotic_slope_min_value : bpy.props.FloatProperty(
        name=translate("Min"),
        subtype="ANGLE",
        default=0,
        min=0, 
        max=1.5708,
        precision=1,
        update=scattering.update_factory.factory("s_abiotic_slope_min_value", is_delayed=True),
        )
    s_abiotic_slope_min_falloff : bpy.props.FloatProperty(
        name=translate("Transition"),
        subtype="ANGLE",
        default=0,
        min=0, 
        max=1.5708, 
        soft_max=0.08726646, 
        precision=3,
        update=scattering.update_factory.factory("s_abiotic_slope_min_falloff", is_delayed=True),
        ) 
    s_abiotic_slope_max_value : bpy.props.FloatProperty(
        name=translate("Max"),
        subtype="ANGLE",
        default=0.2617994, #15 degrees
        min=0, 
        max=1.5708,
        precision=1,
        update=scattering.update_factory.factory("s_abiotic_slope_max_value", is_delayed=True),
        ) 
    s_abiotic_slope_max_falloff : bpy.props.FloatProperty(
        name=translate("Transition"),
        subtype="ANGLE",
        default=0,
        min=0, 
        max=1.5708, 
        soft_max=0.08726646, 
        precision=3,
        update=scattering.update_factory.factory("s_abiotic_slope_max_falloff", is_delayed=True),
        ) 
    #Particle Influence
    s_abiotic_slope_dist_influence: bpy.props.FloatProperty(
        name=translate("Density"),
        default=100,
        subtype="PERCENTAGE",
        min=0,
        max=100, 
        precision=1,
        update=scattering.update_factory.factory("s_abiotic_slope_dist_influence", is_delayed=True),
        )
    s_abiotic_slope_dist_revert : bpy.props.BoolProperty(
        name=translate("Reverse Influence"),
        update=scattering.update_factory.factory("s_abiotic_slope_dist_revert",),
        )
    s_abiotic_slope_scale_influence: bpy.props.FloatProperty(
        name=translate("Scale"),
        default=0,
        subtype="PERCENTAGE",
        min=0,
        max=100, 
        precision=1,
        update=scattering.update_factory.factory("s_abiotic_slope_scale_influence", is_delayed=True),
        )
    s_abiotic_slope_scale_revert : bpy.props.BoolProperty(
        name=translate("Reverse Influence"),
        update=scattering.update_factory.factory("s_abiotic_slope_scale_revert",),
        )
    #Feature Mask
    __annotations__.update(generate_featuremask_properties(name="s_abiotic_slope",))

    ########## ########## Direction

    s_abiotic_dir_allow : bpy.props.BoolProperty(
        default=False,
        update=scattering.update_factory.factory("s_abiotic_dir_allow",),
        )
    s_abiotic_dir_space : bpy.props.EnumProperty(   
        name=translate("Space"),
        default="local", 
        items= [ ("local", translate("Local"),"",  "ORIENTATION_LOCAL",0 ),
                 ("global", translate("Global"), "", "WORLD",1 ),
               ],
        update=scattering.update_factory.factory("s_abiotic_dir_space",),
        )
    s_abiotic_dir_direction : bpy.props.FloatVectorProperty(
        default=(0.701299, 0.493506, 0.514423),
        subtype="DIRECTION",
        update=scattering.update_factory.factory("s_abiotic_dir_direction", is_delayed=True),
        )
    s_abiotic_dir_direction_euler : bpy.props.FloatVectorProperty( 
        subtype="EULER",
        update=upd_euler_to_direction_prop("s_abiotic_dir_direction_euler", "s_abiotic_dir_direction",),
        )

    s_abiotic_dir_max : bpy.props.FloatProperty(
        name=translate("Max"),
        subtype="ANGLE",
        default=0.261799,
        soft_min=0, 
        soft_max=1, 
        precision=3,
        update=scattering.update_factory.factory("s_abiotic_dir_max", is_delayed=True),
        ) 
    s_abiotic_dir_treshold : bpy.props.FloatProperty(
        name=translate("Transition"),
        subtype="ANGLE",
        default=0.0872665,
        soft_min=0,
        soft_max=1,
        precision=3,
        update=scattering.update_factory.factory("s_abiotic_dir_treshold", is_delayed=True),
        ) 
    #Particle Influence
    s_abiotic_dir_dist_influence: bpy.props.FloatProperty(
        name=translate("Density"),
        default=100,
        subtype="PERCENTAGE",
        min=0,
        max=100,
        precision=1,
        update=scattering.update_factory.factory("s_abiotic_dir_dist_influence", is_delayed=True),
        )
    s_abiotic_dir_dist_revert : bpy.props.BoolProperty(
        name=translate("Reverse Influence"),
        update=scattering.update_factory.factory("s_abiotic_dir_dist_revert",),
        )
    s_abiotic_dir_scale_influence: bpy.props.FloatProperty(
        name=translate("Scale"),
        default=0,
        subtype="PERCENTAGE",
        min=0,
        max=100,
        precision=1,
        update=scattering.update_factory.factory("s_abiotic_dir_scale_influence", is_delayed=True),
        )
    s_abiotic_dir_scale_revert : bpy.props.BoolProperty(
        name=translate("Reverse Influence"),
        update=scattering.update_factory.factory("s_abiotic_dir_scale_revert",),
        )
    #Feature Mask
    __annotations__.update(generate_featuremask_properties(name="s_abiotic_dir",))

    ########## ########## Edge Curvature

    s_abiotic_cur_allow : bpy.props.BoolProperty(
        default=False,
        update=scattering.update_factory.factory("s_abiotic_cur_allow",),
        )
    s_abiotic_cur_type : bpy.props.EnumProperty(   
        name=translate("Type"),
        default="convex", 
        items= [ ("convex", translate("Convex"),"",  "SPHERECURVE",0 ),
                 ("concave", translate("Concave"), "", "SHARPCURVE",1 ),
               ],
        update=scattering.update_factory.factory("s_abiotic_cur_type",),
        )
    s_abiotic_cur_max: bpy.props.FloatProperty(
        name=translate("Max"),
        default=55,
        subtype="PERCENTAGE",
        min=0,
        max=100,
        precision=1,
        update=scattering.update_factory.factory("s_abiotic_cur_max", is_delayed=True),
        )
    s_abiotic_cur_treshold: bpy.props.FloatProperty(
        name=translate("Transition"),
        default=0,
        subtype="PERCENTAGE",
        min=0,
        max=100,
        precision=1,
        update=scattering.update_factory.factory("s_abiotic_cur_treshold", is_delayed=True),
        )
    #Particle Influence
    s_abiotic_cur_dist_influence: bpy.props.FloatProperty(
        name=translate("Density"),
        default=100,
        subtype="PERCENTAGE",
        min=0,
        max=100,
        precision=1,
        update=scattering.update_factory.factory("s_abiotic_cur_dist_influence", is_delayed=True),
        )
    s_abiotic_cur_dist_revert : bpy.props.BoolProperty(
        name=translate("Reverse Influence"),
        update=scattering.update_factory.factory("s_abiotic_cur_dist_revert",),
        )
    s_abiotic_cur_scale_influence: bpy.props.FloatProperty(
        name=translate("Scale"),
        default=0,
        subtype="PERCENTAGE",
        min=0,
        max=100,
        precision=1,
        update=scattering.update_factory.factory("s_abiotic_cur_scale_influence", is_delayed=True),
        )
    s_abiotic_cur_scale_revert : bpy.props.BoolProperty(
        name=translate("Reverse Influence"),
        update=scattering.update_factory.factory("s_abiotic_cur_scale_revert",),
        )
    #Feature Mask
    __annotations__.update(generate_featuremask_properties(name="s_abiotic_cur",))

    ########## ########## Edge Border

    s_abiotic_border_allow : bpy.props.BoolProperty(
        default=False,
        update=scattering.update_factory.factory("s_abiotic_border_allow",),
        )
    s_abiotic_border_max : bpy.props.FloatProperty(
        name=translate("Max"),
        default=1,
        min=0,
        subtype="DISTANCE",
        update=scattering.update_factory.factory("s_abiotic_border_max", is_delayed=True),
        )
    s_abiotic_border_treshold : bpy.props.FloatProperty(
        name=translate("Transition"),
        default=0.5,
        min=0,
        subtype="DISTANCE",
        update=scattering.update_factory.factory("s_abiotic_border_treshold", is_delayed=True),
        )
    #Particle Influence
    s_abiotic_border_dist_influence: bpy.props.FloatProperty(
        name=translate("Density"),
        default=100,
        subtype="PERCENTAGE",
        min=0,
        max=100,
        precision=1,
        update=scattering.update_factory.factory("s_abiotic_border_dist_influence", is_delayed=True),
        )
    s_abiotic_border_dist_revert : bpy.props.BoolProperty(
        name=translate("Reverse Influence"),
        update=scattering.update_factory.factory("s_abiotic_border_dist_revert",),
        )
    s_abiotic_border_scale_influence: bpy.props.FloatProperty(
        name=translate("Scale"),
        default=0,
        subtype="PERCENTAGE",
        min=0,
        max=100,
        precision=1,
        update=scattering.update_factory.factory("s_abiotic_border_scale_influence", is_delayed=True),
        )
    s_abiotic_border_scale_revert : bpy.props.BoolProperty(
        name=translate("Reverse Influence"),
        update=scattering.update_factory.factory("s_abiotic_border_scale_revert",),
        )
    #Feature Mask
    __annotations__.update(generate_featuremask_properties(name="s_abiotic_border",))

    #Edge Watershed Later? 

    #Edge Data Later ? 
    
    # 88""Yb 88""Yb  dP"Yb  Yb  dP 88 8b    d8 88 888888 Yb  dP
    # 88__dP 88__dP dP   Yb  YbdP  88 88b  d88 88   88    YbdP
    # 88"""  88"Yb  Yb   dP  dPYb  88 88YbdP88 88   88     8P
    # 88     88  Yb  YbodP  dP  Yb 88 88 YY 88 88   88    dP

    ########## ########## Meshes 

    s_proximity_removenear_allow : bpy.props.BoolProperty( 
        name=translate("Remove Near Object"), 
        default=False, 
        update=scattering.update_factory.factory("s_proximity_removenear_allow",),
        )
    #treshold
    s_proximity_removenear_coll_ptr : bpy.props.PointerProperty(
        type=bpy.types.Collection,
        update=scattering.update_factory.factory("s_proximity_removenear_coll_ptr"),
        )
    s_proximity_removenear_type : bpy.props.EnumProperty(   
        name=translate("Proximity Contact"),
        default="mesh", 
        items= [ ("origin", translate("Origin Points"),translate("Evaluate only the location of given instances"),  "ORIENTATION_VIEW",0 ),
                 ("mesh", translate("Meshes Faces"), translate("Evaluate the mesh of the instance, be warned, this can be performance intensive"), "MESH_DATA",1 ),
                 ("convexhull", translate("Meshes Convex-Hull"), translate("Evaluate the convex-hull mesh of the instance, be warned, this can be performance intensive"), "CON_PIVOT",2 )
               ],
        update=scattering.update_factory.factory("s_proximity_removenear_type",),
        )
    s_proximity_removenear_max : bpy.props.FloatProperty(
        name=translate("Max Distance"),
        default=0.75,
        min=0,
        subtype="DISTANCE",
        update=scattering.update_factory.factory("s_proximity_removenear_max", is_delayed=True),
        )
    s_proximity_removenear_treshold : bpy.props.FloatProperty(
        name=translate("Transition"),
        default=0.25,
        min=0,
        subtype="DISTANCE",
        update=scattering.update_factory.factory("s_proximity_removenear_treshold", is_delayed=True),
        )
    #Particle Influence
    s_proximity_removenear_dist_influence: bpy.props.FloatProperty(
        name=translate("Density"),
        default=100,
        subtype="PERCENTAGE",
        min=0,
        max=100,
        precision=1,
        update=scattering.update_factory.factory("s_proximity_removenear_dist_influence", is_delayed=True),
        )
    s_proximity_removenear_dist_revert : bpy.props.BoolProperty(
        name=translate("Reverse Influence"),
        update=scattering.update_factory.factory("s_proximity_removenear_dist_revert",),
        )
    s_proximity_removenear_scale_influence: bpy.props.FloatProperty(
        name=translate("Scale"),
        default=0,
        subtype="PERCENTAGE",
        min=0,
        max=100,
        precision=1,
        update=scattering.update_factory.factory("s_proximity_removenear_scale_influence", is_delayed=True),
        )
    s_proximity_removenear_scale_revert : bpy.props.BoolProperty(
        name=translate("Reverse Influence"),
        update=scattering.update_factory.factory("s_proximity_removenear_scale_revert",),
        )
    #Feature Mask
    __annotations__.update(generate_featuremask_properties(name="s_proximity_removenear",))

    ########## ########## Lean Over

    s_proximity_leanover_allow : bpy.props.BoolProperty( 
        name=translate("Tilt Near Object"), 
        default=False, 
        update=scattering.update_factory.factory("s_proximity_leanover_allow",),
        )
    #treshold
    s_proximity_leanover_coll_ptr : bpy.props.PointerProperty(
        type=bpy.types.Collection,
        update=scattering.update_factory.factory("s_proximity_leanover_coll_ptr"),
        )
    s_proximity_leanover_type : bpy.props.EnumProperty(   
        name=translate("Proximity Contact"),
        default="mesh", 
        items= [ ("origin", translate("Origin Points"),translate("Evaluate only the location of given instances"),  "ORIENTATION_VIEW",0 ),
                 ("mesh", translate("Meshes Faces"), translate("Evaluate the mesh of the instance, be warned, this can be performance intensive"), "MESH_DATA",1 ),
                 ("convexhull", translate("Meshes Convex-Hull"), translate("Evaluate the convex-hull mesh of the instance, be warned, this can be performance intensive"), "CON_PIVOT",2 )
               ],
        update=scattering.update_factory.factory("s_proximity_leanover_type",),
        )
    s_proximity_leanover_max : bpy.props.FloatProperty(
        name=translate("Max Distance"),
        default=0.4,
        min=0,
        subtype="DISTANCE",
        update=scattering.update_factory.factory("s_proximity_leanover_max", is_delayed=True),
        )
    s_proximity_leanover_treshold : bpy.props.FloatProperty(
        name=translate("Transition"),
        default=0.8,
        min=0,
        subtype="DISTANCE",
        update=scattering.update_factory.factory("s_proximity_leanover_treshold", is_delayed=True),
        )
    #Particle Influence
    s_proximity_leanover_scale_influence : bpy.props.FloatProperty(
        name=translate("Scale"),
        default=60,
        subtype="PERCENTAGE",
        min=0,
        max=100,
        precision=1,
        update=scattering.update_factory.factory("s_proximity_leanover_scale_influence", is_delayed=True),
        )
    s_proximity_leanover_tilt_influence : bpy.props.FloatProperty(
        name=translate("Tilt"),
        default=1,
        min=0,
        max=2,
        soft_max=1,
        precision=1,
        update=scattering.update_factory.factory("s_proximity_leanover_tilt_influence", is_delayed=True),
        )
    #Turbulence  #for 5.1 add new helicopter hovering feature "Hover Turbulence"
    # s_proximity_leanover_turbulence_allow : bpy.props.BoolProperty( 
    #     name=translate("Turbulence Effect"), 
    #     default=False, 
    #     update=scattering.update_factory.factory("s_proximity_leanover_turbulence_allow",),
    #     )
    # s_proximity_leanover_turbulence_scale : bpy.props.FloatProperty(
    #     name=translate("Scale"),
    #     default=0.2,
    #     precision=1,
    #     update=scattering.update_factory.factory("s_proximity_leanover_turbulence_scale", is_delayed=True),
    #     )
    # s_proximity_leanover_turbulence_detail : bpy.props.FloatProperty(
    #     name=translate("Detail"),
    #     default=1,
    #     precision=1,
    #     update=scattering.update_factory.factory("s_proximity_leanover_turbulence_detail", is_delayed=True),
    #     )
    # s_proximity_leanover_turbulence_speed : bpy.props.FloatProperty(
    #     name=translate("Speed"),
    #     default=1,
    #     precision=1,
    #     update=scattering.update_factory.factory("s_proximity_leanover_turbulence_speed", is_delayed=True),
    #     )

    #Feature Mask
    __annotations__.update(generate_featuremask_properties(name="s_proximity_leanover",))

    ########## ########## Outskirt 

    s_proximity_outskirt_allow : bpy.props.BoolProperty(
        name=translate("Outskirt Transition"), 
        description=translate("Procedurally add scale and rotation at outskirts  of a particle system. Warning this feature might be slow"),
        default=False, 
        update=scattering.update_factory.factory("s_proximity_outskirt_allow",),
        )
    #Treshold
    s_proximity_outskirt_treshold : bpy.props.FloatProperty(
        name=translate("Transition"),
        default=2,
        min=0,
        subtype="DISTANCE",
        update=scattering.update_factory.factory("s_proximity_outskirt_treshold", is_delayed=True),
        )
    s_proximity_outskirt_limit : bpy.props.FloatProperty(
        name=translate("Treshold"),
        default=1,
        min=0,
        subtype="DISTANCE",
        update=scattering.update_factory.factory("s_proximity_outskirt_limit", is_delayed=True),
        )
    #Particle Influence
    s_proximity_outskirt_scale_influence : bpy.props.FloatProperty(
        name=translate("Scale"),
        default=70,
        subtype="PERCENTAGE",
        min=0,
        max=100,
        precision=1,
        update=scattering.update_factory.factory("s_proximity_outskirt_scale_influence", is_delayed=True),
        )
    s_proximity_outskirt_tilt_influence : bpy.props.FloatProperty(
        name=translate("Tilt"),
        default=0.5,
        min=-2,
        max=2,
        soft_min=-1,
        soft_max=1,
        precision=1,
        update=scattering.update_factory.factory("s_proximity_outskirt_tilt_influence", is_delayed=True),
        )

    #Feature Mask
    __annotations__.update(generate_featuremask_properties(name="s_proximity_outskirt",))

    #Curves for 5.1?

    # s_proximity_curve_allow : bpy.props.BoolProperty( 
    #     name=translate("Proximity by Bezier-Curve"), 
    #     default=False, 
    #     update=scattering.update_factory.factory("s_proximity_curve_allow",),
    #     )

    # 888888  dP""b8  dP"Yb  .dP"Y8 Yb  dP .dP"Y8 888888 888888 8b    d8
    # 88__   dP   `" dP   Yb `Ybo."  YbdP  `Ybo."   88   88__   88b  d88
    # 88""   Yb      Yb   dP o.`Y8b   8P   o.`Y8b   88   88""   88YbdP88
    # 888888  YboodP  YbodP  8bodP'  dP    8bodP'   88   888888 88 YY 88

    ########## ########## Affinity

    s_ecosystem_affinity_allow : bpy.props.BoolProperty(
        name=translate("Ecosystem Affinity"), 
        default=False, 
        update=scattering.update_factory.factory("s_ecosystem_affinity_allow",),
        )
    s_ecosystem_affinity_ui_max_slot : bpy.props.IntProperty(default=1,max=3)
    #tresholds
    __annotations__.update( batch_generate_properties(name="s_ecosystem_affinity_XX_ptr", nbr=3, items={"name":translate("Particle System"),}, property_type=bpy.props.StringProperty, is_delayed=False),)
    __annotations__.update( batch_generate_properties(name="s_ecosystem_affinity_XX_type", nbr=3, items={"name":translate("Proximity Contact"),"default":"origin","items":[ ("origin", translate("Origin Points"),translate("Evaluate only the location of given instances"),  "ORIENTATION_VIEW",0 ),("mesh", translate("Meshes Faces"), translate("Evaluate the mesh of the instance, be warned, this can be performance intensive"), "MESH_DATA",1 ),("convexhull", translate("Meshes Convex-Hull"), translate("Evaluate the convex-hull mesh of the instance, be warned, this can be performance intensive"), "CON_PIVOT",2 ),],}, property_type=bpy.props.EnumProperty, is_delayed=False),)
    __annotations__.update( batch_generate_properties(name="s_ecosystem_affinity_XX_max_value", nbr=3, items={"name":translate("Max Distance"),"default":0.5,"min":0,"subtype":"DISTANCE",}, property_type=bpy.props.FloatProperty, is_delayed=True),)
    __annotations__.update( batch_generate_properties(name="s_ecosystem_affinity_XX_max_falloff", nbr=3, items={"name":translate("Transition"),"default":0.5,"min":0,"subtype":"DISTANCE",}, property_type=bpy.props.FloatProperty, is_delayed=True),)
    __annotations__.update( batch_generate_properties(name="s_ecosystem_affinity_XX_limit_distance", nbr=3, items={"name":translate("Limit Collision"),"default":0,"min":0,"subtype":"DISTANCE",}, property_type=bpy.props.FloatProperty, is_delayed=True),)

    #Particle Influence
    s_ecosystem_affinity_dist_influence: bpy.props.FloatProperty(
        name=translate("Density"),
        default=100,
        subtype="PERCENTAGE",
        min=0,
        max=100,
        precision=1,
        update=scattering.update_factory.factory("s_ecosystem_affinity_dist_influence", is_delayed=True),
        )
    s_ecosystem_affinity_scale_influence: bpy.props.FloatProperty(
        name=translate("Scale"),
        default=50,
        subtype="PERCENTAGE",
        min=0,
        max=100,
        precision=1,
        update=scattering.update_factory.factory("s_ecosystem_affinity_scale_influence", is_delayed=True),
        )

    #Feature Mask
    __annotations__.update(generate_featuremask_properties(name="s_ecosystem_affinity",))

    ########## ########## Repulsion

    s_ecosystem_repulsion_allow : bpy.props.BoolProperty(
        name=translate("Ecosystem Repulsion"), 
        default=False, 
        update=scattering.update_factory.factory("s_ecosystem_repulsion_allow",),
        )
    s_ecosystem_repulsion_ui_max_slot : bpy.props.IntProperty(default=1,max=3)
    #tresholds
    __annotations__.update( batch_generate_properties(name="s_ecosystem_repulsion_XX_ptr", nbr=3, items={"name":translate("Particle System"),}, property_type=bpy.props.StringProperty, is_delayed=False),)
    __annotations__.update( batch_generate_properties(name="s_ecosystem_repulsion_XX_type", nbr=3, items={"name":translate("Proximity Contact"),"default":"origin","items":[ ("origin", translate("Origin Points"),translate("Evaluate only the location of given instances"),  "ORIENTATION_VIEW",0 ),("mesh", translate("Meshes Faces"), translate("Evaluate the mesh of the instance, be warned, this can be performance intensive"), "MESH_DATA",1 ),("convexhull", translate("Meshes Convex-Hull"), translate("Evaluate the convex-hull mesh of the instance, be warned, this can be performance intensive"), "CON_PIVOT",2 ),],}, property_type=bpy.props.EnumProperty, is_delayed=False),)
    __annotations__.update( batch_generate_properties(name="s_ecosystem_repulsion_XX_max_value", nbr=3, items={"name":translate("Max Distance"),"default":0.5,"min":0,"subtype":"DISTANCE",}, property_type=bpy.props.FloatProperty, is_delayed=True),)
    __annotations__.update( batch_generate_properties(name="s_ecosystem_repulsion_XX_max_falloff", nbr=3, items={"name":translate("Transition"),"default":0.5,"min":0,"subtype":"DISTANCE",}, property_type=bpy.props.FloatProperty, is_delayed=True),)

    #Particle Influence
    s_ecosystem_repulsion_dist_influence: bpy.props.FloatProperty(
        name=translate("Density"),
        default=100,
        subtype="PERCENTAGE",
        min=0,
        max=100,
        precision=1,
        update=scattering.update_factory.factory("s_ecosystem_repulsion_dist_influence", is_delayed=True),
        )
    s_ecosystem_repulsion_scale_influence: bpy.props.FloatProperty(
        name=translate("Scale"),
        default=50,
        subtype="PERCENTAGE",
        min=0,
        max=100,
        precision=1,
        update=scattering.update_factory.factory("s_ecosystem_repulsion_scale_influence", is_delayed=True),
        )

    #Feature Mask
    __annotations__.update(generate_featuremask_properties(name="s_ecosystem_repulsion",))

    # 88""Yb 88   88 .dP"Y8 88  88
    # 88__dP 88   88 `Ybo." 88  88
    # 88"""  Y8   8P o.`Y8b 888888
    # 88     `YbodP' 8bodP' 88  88

    ########## ########## Push Offset

    s_push_offset_allow : bpy.props.BoolProperty(
        default=False,
        update=scattering.update_factory.factory("s_push_offset_allow",),
        )
    s_push_offset_add_value : bpy.props.FloatVectorProperty(
        name=translate("Offset"),
        default=(0,0,0),
        subtype="XYZ",
        unit="LENGTH",
        update=scattering.update_factory.factory("s_push_offset_add_value",),
        )
    s_push_offset_add_random : bpy.props.FloatVectorProperty(
        name=translate("Random"),
        default=(0,0,0),
        subtype="XYZ",
        unit="LENGTH",
        update=scattering.update_factory.factory("s_push_offset_add_random",),
        )
    s_push_offset_scale_value : bpy.props.FloatVectorProperty(
        name=translate("Scale"),
        default=(1,1,1),
        subtype="XYZ",
        update=scattering.update_factory.factory("s_push_offset_scale_value",),
        )
    s_push_offset_scale_random : bpy.props.FloatVectorProperty(
        name=translate("Random"),
        default=(0,0,0),
        subtype="XYZ",
        update=scattering.update_factory.factory("s_push_offset_scale_random",),
        )
    #Feature Mask
    __annotations__.update(generate_featuremask_properties(name="s_push_offset",))

    ########## ########## Push Direction

    s_push_dir_allow : bpy.props.BoolProperty(
        default=False,
        update=scattering.update_factory.factory("s_push_dir_allow",),
        )
    s_push_dir_method : bpy.props.EnumProperty(
         name=translate("Axis"),
         default= "push_normal", 
         items= [ ("push_normal", translate("Surface Normal"), "", "NORMALS_FACE", 0),
                  ("push_point",  translate("Rotation"), "", "SNAP_NORMAL", 1),
                  ("push_local",  translate("Local Z"), "", "ORIENTATION_LOCAL", 2),
                  ("push_global", translate("Global Z"), "", "WORLD", 3),
                  # more for 5.1?
                  #("push_origin", translate("Emitter Origin"),   "", "PIVOT_BOUNDBOX",4),
                  #("push_object", translate("Object"), "", "EYEDROPPER", 5),
                  #("push_custom", translate("Direction"), "", "TRANSFORM_ORIGINS", 7),
                ],
         update=scattering.update_factory.factory("s_push_dir_method"),
         )
    s_push_dir_add_value : bpy.props.FloatProperty(
        name=translate("Distance"),
        default=1,
        subtype="DISTANCE",
        update=scattering.update_factory.factory("s_push_dir_add_value", is_delayed=True),
        )
    s_push_dir_add_random : bpy.props.FloatProperty(
        name=translate("Random Distance"),
        default=0,
        subtype="DISTANCE",
        update=scattering.update_factory.factory("s_push_dir_add_random", is_delayed=True),
        )
    #Feature Mask
    __annotations__.update(generate_featuremask_properties(name="s_push_dir",))

    #more method for 5.1 ?

    # s_push_dir_object_ptr  : bpy.props.PointerProperty(
    #     name=translate("Object"),
    #     type=bpy.types.Object, 
    #     update=scattering.update_factory.factory("s_push_dir_object_ptr"),
    #     )
    # s_push_dir_normalize : bpy.props.BoolProperty(
    #     name=translate("Vector Normalization"),
    #     default=True,
    #     update=scattering.update_factory.factory("s_push_dir_normalize"),
    #     )
    # s_push_dir_custom_direction : bpy.props.FloatVectorProperty(
    #     default=(0,0,1),
    #     subtype="DIRECTION",
    #     update=scattering.update_factory.factory("s_push_dir_custom_direction", is_delayed=True),
    #     )

    ########## ########## Push Noise 

    s_push_noise_allow : bpy.props.BoolProperty(
        default=False,
        name=translate("Add Random Animated Noise after every other effects"),
        update=scattering.update_factory.factory("s_push_noise_allow"),
        )
    s_push_noise_vector : bpy.props.FloatVectorProperty(
        name=translate("Spread"),
        default=(1,1,1),
        subtype="XYZ_LENGTH",
        update=scattering.update_factory.factory("s_push_noise_vector", is_delayed=True),
        )
    s_push_noise_speed : bpy.props.FloatProperty(
        name=translate("Speed"),
        default=1,
        soft_min=0,
        soft_max=5,
        update=scattering.update_factory.factory("s_push_noise_speed", is_delayed=True),
        )
    #Feature Mask
    __annotations__.update(generate_featuremask_properties(name="s_push_noise",))

    ########## ########## Fall Effect

    s_push_fall_allow : bpy.props.BoolProperty(
        name=translate("Create Animated leave falling effect"),
        default=False,
        update=scattering.update_factory.factory("s_push_fall_allow"),
        )
    s_push_fall_height : bpy.props.FloatProperty(
        name=translate("Fall Distance"),
        default=20,
        subtype="DISTANCE",
        update=scattering.update_factory.factory("s_push_fall_height", is_delayed=True),
        )
    s_push_fall_key1_pos : bpy.props.IntProperty(
        name=translate("Frame"),
        default=0,
        update=scattering.update_factory.factory("s_push_fall_key1_pos", is_delayed=True),
        )
    s_push_fall_key1_height : bpy.props.FloatProperty(
        name=translate("Height"),
        default=5,
        subtype="DISTANCE",
        update=scattering.update_factory.factory("s_push_fall_key1_height", is_delayed=True),
        )
    s_push_fall_key2_pos : bpy.props.IntProperty(
        name=translate("Frame"),
        default=100,
        update=scattering.update_factory.factory("s_push_fall_key2_pos", is_delayed=True),
        )
    s_push_fall_key2_height : bpy.props.FloatProperty(
        name=translate("Height"),
        default=-5,
        subtype="DISTANCE",
        update=scattering.update_factory.factory("s_push_fall_key2_height", is_delayed=True),
        )
    s_push_fall_stop_when_initial_z : bpy.props.BoolProperty(
        default=True,
        update=scattering.update_factory.factory("s_push_fall_stop_when_initial_z"),
        )
    s_push_fall_turbulence_allow : bpy.props.BoolProperty(
        default=False,
        update=scattering.update_factory.factory("s_push_fall_turbulence_allow"),
        )
    s_push_fall_turbulence_spread : bpy.props.FloatVectorProperty(
        name=translate("Spread"),
        default=(1.0,1.0,0.5),
        subtype="XYZ_LENGTH",
        update=scattering.update_factory.factory("s_push_fall_turbulence_spread", is_delayed=True),
        )
    s_push_fall_turbulence_speed : bpy.props.FloatProperty(
        name=translate("Speed"),
        default=1,
        min=0,
        soft_max=4,
        update=scattering.update_factory.factory("s_push_fall_turbulence_speed", is_delayed=True),
        )
    s_push_fall_turbulence_rot_vector : bpy.props.FloatVectorProperty(
        name=translate("Rotation"),
        default=(0.5,0.5,0.5),
        subtype="EULER",
        update=scattering.update_factory.factory("s_push_fall_turbulence_rot_vector", is_delayed=True),
        )
    s_push_fall_turbulence_rot_factor : bpy.props.FloatProperty(
        name=translate("Rotation Factor"),
        default=1,
        soft_min=0,
        soft_max=1,
        update=scattering.update_factory.factory("s_push_fall_turbulence_rot_factor", is_delayed=True),
        )
    #Feature Mask
    __annotations__.update(generate_featuremask_properties(name="s_push_fall",))

    # Yb        dP 88 88b 88 8888b.  
    #  Yb  db  dP  88 88Yb88  8I  Yb 
    #   YbdPYbdP   88 88 Y88  8I  dY 
    #    YP  YP    88 88  Y8 8888Y"  

    ########## ########## Wind Wave

    s_wind_wave_allow : bpy.props.BoolProperty(
        default=False,
        update=scattering.update_factory.factory("s_wind_wave_allow",),
        )
    s_wind_wave_speed : bpy.props.FloatProperty(
        name=translate("Speed"), 
        default=1.0, 
        soft_min=0.001, 
        soft_max=5, 
        precision=3,
        update=scattering.update_factory.factory("s_wind_wave_speed", is_delayed=True),
        )
    s_wind_wave_force : bpy.props.FloatProperty(
        name=translate("Strength"), 
        default=1, 
        soft_min=0, 
        soft_max=3, 
        precision=3,
        update=scattering.update_factory.factory("s_wind_wave_force", is_delayed=True),
        )
    s_wind_wave_swinging : bpy.props.BoolProperty(
        default=False,
        update=scattering.update_factory.factory("s_wind_wave_swinging",),
        description=translate("The wind effect will swing particle back and forth instead of an unilaterally inclining them"),
        )
    s_wind_wave_scale_influence : bpy.props.BoolProperty(
        default=False,
        update=scattering.update_factory.factory("s_wind_wave_scale_influence",),
        description=translate("Smaller/taller instances are less/more affected by the wind force"),
        )
    s_wind_wave_texture_scale : bpy.props.FloatProperty(
        name=translate("Scale"),
        default=0.1,
        update=scattering.update_factory.factory("s_wind_wave_texture_scale", is_delayed=True),
        )
    s_wind_wave_texture_turbulence : bpy.props.FloatProperty(
        name=translate("Turbulence"),
        default=0,
        soft_min=0,
        soft_max=10,
        update=scattering.update_factory.factory("s_wind_wave_texture_turbulence", is_delayed=True),
        )
    s_wind_wave_texture_brightness : bpy.props.FloatProperty(
        name=translate("Brightness"),
        default=1,
        min=0, 
        soft_max=2,
        update=scattering.update_factory.factory("s_wind_wave_texture_brightness", is_delayed=True),
        )
    s_wind_wave_texture_contrast : bpy.props.FloatProperty(
        name=translate("Contrast"),
        default=1.5,
        min=0, 
        soft_max=5,
        update=scattering.update_factory.factory("s_wind_wave_texture_contrast", is_delayed=True),
        )

    s_wind_wave_dir_method : bpy.props.EnumProperty(
         name=translate("Wind Direction"),
         default= "fixed", 
         items= [ ("fixed", translate("Fixed Direction"), "", "CURVE_PATH", 0),
                  ("vcol",  translate("Vertex-Color Flowmap"), "", "GROUP_VCOL", 1),
                ],
         update=scattering.update_factory.factory("s_wind_wave_dir_method"),
         )
    s_wind_wave_direction : bpy.props.FloatProperty(
        name=translate("Direction"), 
        subtype="ANGLE",
        default=0.87266, 
        soft_min=-6.283185, 
        soft_max=6.283185, #=360d
        precision=3,
        update=scattering.update_factory.factory("s_wind_wave_direction", is_delayed=True),
        )
    s_wind_wave_flowmap_ptr : bpy.props.StringProperty(
        default="",
        update=scattering.update_factory.factory("s_wind_wave_flowmap_ptr", synchronize=False,),
        )
    #Feature Mask
    __annotations__.update(generate_featuremask_properties(name="s_wind_wave",))

    ########## ########## Wind Noise

    s_wind_noise_allow : bpy.props.BoolProperty(
        default=False,
        update=scattering.update_factory.factory("s_wind_noise_allow",),
        description=translate("Add random turbulence noise movement"),
        )
    s_wind_noise_force : bpy.props.FloatProperty(
        name=translate("Strength"), 
        default=0.5, 
        soft_min=0, 
        soft_max=3, 
        precision=3,
        update=scattering.update_factory.factory("s_wind_noise_force", is_delayed=True),
        )
    s_wind_noise_speed : bpy.props.FloatProperty(
        name=translate("Speed"), 
        default=1, 
        soft_min=0.001, 
        soft_max=10, 
        precision=3,
        update=scattering.update_factory.factory("s_wind_noise_speed", is_delayed=True),
        )
    #Feature Mask
    __annotations__.update(generate_featuremask_properties(name="s_wind_noise",))

    # 88 88b 88 .dP"Y8 888888    db    88b 88  dP""b8 88 88b 88  dP""b8
    # 88 88Yb88 `Ybo."   88     dPYb   88Yb88 dP   `" 88 88Yb88 dP   `"
    # 88 88 Y88 o.`Y8b   88    dP__Yb  88 Y88 Yb      88 88 Y88 Yb  "88
    # 88 88  Y8 8bodP'   88   dP""""Yb 88  Y8  YboodP 88 88  Y8  YboodP

    def get_instances_obj(self):
        """get all objects used by this particle instancing method"""
            
        instances = [] 

        if (self.s_instances_method=="ins_collection"):
            if self.s_instances_coll_ptr:
                for o in self.s_instances_coll_ptr.objects:
                    if o not in instances:
                        instances.append(o)

        return instances 

    #Not supported by Preset

    s_instances_method : bpy.props.EnumProperty( #partially ignored
        name=translate("Instance Method"),
        default= "ins_collection", 
        items= [ ("ins_collection", translate("Collection"), translate("Use the scattered points to instances items contained in a collection"), "OUTLINER_COLLECTION", 0,),
                 ("ins_volume", translate("Volume"), translate("Use the scattered points to generate volumes"), "VOLUME_DATA", 1,),
                 ("ins_point", translate("Points"), translate("Use the scattered points directly"), "STICKY_UVS_DISABLE", 2,),
               ],
        update=scattering.update_factory.factory("s_instances_method"),
        ) 
    s_instances_coll_ptr : bpy.props.PointerProperty(
        type=bpy.types.Collection,
        update=scattering.update_factory.factory("s_instances_coll_ptr"),
        )
    s_instances_list_idx : bpy.props.IntProperty()
    #only for ins_collection
    s_instances_pick_method : bpy.props.EnumProperty(
        name=translate("Pick Method"),
        default= "pick_random", 
        items= [ ("pick_random", translate("Random"), translate("Randomly pick items"), "OBJECT_DATA", 0,),
                 ("pick_rate", translate("Probability"), translate("Assign items based on a spawn rate probability."), "MOD_HUE_SATURATION", 1,),
                 ("pick_scale", translate("Scale"), translate("Assign items based on scattered points minimal/maximal scale range"), "OBJECT_ORIGIN", 2,),
                 ("pick_color", translate("Sample Color"), translate("Assign items to scattered points based on a given color attributer (vertex-color or texture)"), "COLOR", 3,),
                 ("pick_idx", translate("Manual Index"), translate("Assign items with the Instance Index panting brush"), "LINENUMBERS_ON", 4,),
                 ("pick_cluster", translate("Clusters"), translate("Automatically pack instance in clusters pattern"), "CON_OBJECTSOLVER", 5,),
               ],
        update=scattering.update_factory.factory("s_instances_pick_method"),
        )
    #for pick_random & pick_rate
    s_instances_seed : bpy.props.IntProperty(
        name=translate("Seed"),
        default=0,
        min=0, 
        update=scattering.update_factory.factory("s_instances_seed", is_delayed=True),
        )
    s_instances_is_random_seed : bpy.props.BoolProperty( #= value of the property is of no importance, only the update signal matter
        name=translate("Radomize Seed"),
        default=False,
        update=scattering.update_factory.factory("s_instances_is_random_seed", alt_support=False, ),
        )
    #for pick_rate
    __annotations__.update( batch_generate_properties(name="s_instances_id_XX_rate", nbr=20, items={"default":0,"min":0,"max":100,"subtype":"PERCENTAGE","name":translate("Probability"),"description":translate("Set this object spawn rate, objects above will over-shadow those located below in an alphabetically sorted list")}, property_type=bpy.props.IntProperty, is_delayed=True),)
    #for pick_scale
    __annotations__.update( batch_generate_properties(name="s_instances_id_XX_scale_min", nbr=20, items={"default":0,"soft_min":0,"soft_max":3,"name":translate("Scale Range Min"),"description":translate("Assign instance to scattered points fitting the given range, objects above will over-shadow those located below in an alphabetically sorted list")}, property_type=bpy.props.FloatProperty, is_delayed=True),)
    __annotations__.update( batch_generate_properties(name="s_instances_id_XX_scale_max", nbr=20, items={"default":0,"soft_min":0,"soft_max":3,"name":translate("Scale Range Max"),"description":translate("Assign instance to scattered points fitting the given range, objects above will over-shadow those located below in an alphabetically sorted list")}, property_type=bpy.props.FloatProperty, is_delayed=True),)
    s_instances_id_scale_method : bpy.props.EnumProperty(
        name=translate("Scale Method"),
        default= "dynamic_scale",
        items= [ ("fixed_scale", translate("Frozen Scale"), translate("Reset all instances scale to 1"),"FREEZE",0),
                 ("dynamic_scale", translate("Dynamic Scale"), translate("Rescale Items Dynamically depending on the given range"),"LIGHT_DATA",1),
               ],
        update=scattering.update_factory.factory("s_instances_id_scale_method"),
        )
    #for pick color
    __annotations__.update( batch_generate_properties(name="s_instances_id_XX_color", nbr=20, items={"default":(1,0,0),"subtype":"COLOR","min":0,"max":1,"name":translate("Color"),"description":translate("Assign this instance to the corresponding color sampled")}, property_type=bpy.props.FloatVectorProperty, is_delayed=True),)
    #for pick_cluster
    s_instances_pick_cluster_projection_method : bpy.props.EnumProperty(
        name=translate("Projection Method"),
        default= "local", 
        items= [ ("local", translate("Local"), translate(""), "ORIENTATION_LOCAL",0 ),
                 ("global", translate("Global"), translate(""), "WORLD",1 ),
               ],
        update=scattering.update_factory.factory("s_instances_pick_cluster_projection_method"),
        )
    s_instances_pick_cluster_scale : bpy.props.FloatProperty(
        name=translate("Scale"),
        default=0.3,
        min=0,
        update=scattering.update_factory.factory("s_instances_pick_cluster_scale"),
        )
    s_instances_pick_cluster_blur : bpy.props.FloatProperty(
        name=translate("Jitter"),
        default=0.5,
        min=0, max=3,
        update=scattering.update_factory.factory("s_instances_pick_cluster_blur"),
        )
    s_instances_pick_clump : bpy.props.BoolProperty(
        default=False, 
        name=translate("Use Clumps as Clusters"),
        description=translate("This option appear if you are using clump distribution method, it will allow you to assing each instance to individual clumps"),
        update=scattering.update_factory.factory("s_instances_pick_clump"),
        )

    s_instances_id_color_tolerence : bpy.props.FloatProperty(
        name=translate("Tolerence"),
        default=0.3, min=0, soft_max=3,
        update=scattering.update_factory.factory("s_instances_id_color_tolerence"), 
        )

    s_instances_id_color_sample_method : bpy.props.EnumProperty(
        name=translate("Color Source"),
        default= "vcol", 
        items= [ ("vcol", translate("Vertex Colors"), "", "VPAINT_HLT", 1,),
                 ("text", translate("Texture Data"), "", "NODE_TEXTURE",   2,),
               ],
        update=scattering.update_factory.factory("s_instances_id_color_sample_method"),
        ) 
    s_instances_texture_ptr : bpy.props.StringProperty(
        description="Internal property that will update a TEXTURE_NODE node tree from given nodetree name, used for presets and most importantly copy/paste or synchronization",
        update=scattering.update_factory.factory("s_instances_texture_ptr",),
        )
    s_instances_vcol_ptr : bpy.props.StringProperty(
        default="",
        update=scattering.update_factory.factory("s_instances_vcol_ptr", synchronize=False,),
        )

    #only for ins_volume
    s_instances_volume_density : bpy.props.FloatProperty( #unused 
        name=translate("Density"),
        default=1,
        min=0,
        update=scattering.update_factory.factory("s_instances_volume_density"),
        )
    s_instances_volume_voxel_ammount : bpy.props.FloatProperty( #unused 
        name=translate("Voxel Ammount"),
        default=64,
        min=0,
        update=scattering.update_factory.factory("s_instances_volume_voxel_ammount"),
        )

    # Yb    dP 88 .dP"Y8 88 88""Yb 88 88     88 888888 Yb  dP
    #  Yb  dP  88 `Ybo." 88 88__dP 88 88     88   88    YbdP
    #   YbdP   88 o.`Y8b 88 88""Yb 88 88  .o 88   88     8P
    #    YP    88 8bodP' 88 88oodP 88 88ood8 88   88    dP

    #Not Supported by Presets

    s_visibility_view_allow : bpy.props.BoolProperty( 
        default=False,
        update=scattering.update_factory.factory("s_visibility_view_allow"),
        )
    s_visibility_view_percentage : bpy.props.FloatProperty(
        name=translate("Removal"),
        default=80,
        subtype="PERCENTAGE",
        min=0,
        max=100, 
        precision=1,
        update=scattering.update_factory.factory("s_visibility_view_percentage", is_delayed=True),
        )
    s_visibility_view_viewport_method : bpy.props.EnumProperty(
        name=translate("Visibility Method"),
        default="except_rendered",
        items= [ ("viewport_only", translate("Viewport Only"),translate("This functionality will be active only in the viewport"),),
                 ("except_rendered", translate("Viewport Except Rendered"),translate("This functionality will be active only in the viewport, except if rendered view is activated"),),
                 ("viewport_and_render", translate("Viewport & Render"), translate("This functionality will be active both in viewport and final render"),),
               ],
        update=scattering.update_factory.factory("s_visibility_view_viewport_method"),
        )

    ########## ########## Camera Optimization

    s_visibility_cam_allow : bpy.props.BoolProperty( 
        default=False,
        name=translate("Camera Optimizations"),
        update=scattering.update_factory.factory("s_visibility_cam_allow"),
        )
    s_visibility_camclip_allow : bpy.props.BoolProperty(
        default=True,
        name=translate("Frustrum Culling"),
        description=translate("Only show particles inside the active-camera frustrum volume"),
        update=scattering.update_factory.factory("s_visibility_camclip_allow"),
        )
    s_visibility_camclip_proximity : bpy.props.FloatProperty(
        name=translate("Near-Camera"),
        default=0,
        subtype="DISTANCE",
        min=0,
        soft_max=20, 
        update=scattering.update_factory.factory("s_visibility_camclip_proximity", is_delayed=True),
        )
    s_visibility_camclip_dir_crop_x  : bpy.props.FloatProperty(
        name=translate("Fov X"),
        default=0.450,
        min=0, max=1, soft_max=0.6, precision=3,
        update=scattering.update_factory.factory("s_visibility_camclip_dir_crop_x", is_delayed=True),
        )
    s_visibility_camclip_dir_crop_y  : bpy.props.FloatProperty(
        name=translate("Fov Y"),
        default=0.250,
        min=0, max=1, soft_max=0.6, precision=3,
        update=scattering.update_factory.factory("s_visibility_camclip_dir_crop_y", is_delayed=True),
        )
    s_visibility_camclip_dir_shift_x : bpy.props.FloatProperty(
        name=translate("Shift X"),
        default=0,
        soft_min=-0.5, soft_max=0.5, precision=3,
        update=scattering.update_factory.factory("s_visibility_camclip_dir_shift_x", is_delayed=True),
        )
    s_visibility_camclip_dir_shift_y : bpy.props.FloatProperty(
        name=translate("Shift Y"),
        default=0,
        soft_min=-0.5, soft_max=0.5, precision=3,
        update=scattering.update_factory.factory("s_visibility_camclip_dir_shift_y", is_delayed=True),
        )
    s_visibility_camdist_allow: bpy.props.BoolProperty(
        default=False,
        name=translate("Distance Culling"),
        description=translate("Only show close to the camera"),
        update=scattering.update_factory.factory("s_visibility_camdist_allow"),
        )
    s_visibility_camdist_min : bpy.props.FloatProperty(
        name=translate("Falloff Min"),
        default=10,
        subtype="DISTANCE",
        min=0,
        soft_max=200, 
        update=scattering.update_factory.factory("s_visibility_camdist_min", is_delayed=True),
        )
    s_visibility_camdist_max : bpy.props.FloatProperty(
        name=translate("Falloff Max"),
        default=40,
        subtype="DISTANCE",
        min=0,
        soft_max=200, 
        update=scattering.update_factory.factory("s_visibility_camdist_max", is_delayed=True),
        )
    s_visibility_cam_viewport_method : bpy.props.EnumProperty(
        name=translate("Visibility Method"),
        default="viewport_only",
        items= [ ("viewport_only", translate("Viewport Only"),translate("This functionality will be active only in the viewport"),),
                 ("except_rendered", translate("Viewport Except Rendered"),translate("This functionality will be active only in the viewport, except if rendered view is activated"),),
                 ("viewport_and_render", translate("Viewport & Render"), translate("This functionality will be active both in viewport and final render"),),
               ],
        update=scattering.update_factory.factory("s_visibility_cam_viewport_method"),
        )

    # 8888b.  88 .dP"Y8 88""Yb 88        db    Yb  dP
    #  8I  Yb 88 `Ybo." 88__dP 88       dPYb    YbdP
    #  8I  dY 88 o.`Y8b 88"""  88  .o  dP__Yb    8P
    # 8888Y"  88 8bodP' 88     88ood8 dP""""Yb  dP

    #Not Supported by Presets

    s_display_allow : bpy.props.BoolProperty( 
        default=False,
        update=scattering.update_factory.factory("s_display_allow",),
        )
    s_display_method : bpy.props.EnumProperty(
        name=translate("Display as"),
        default= "placeholder", 
        items= [ ("bb", translate("Bounding-Box"), translate(""), "CUBE",1 ),
                 ("convexhull", translate("Convex-Hull"), translate(""), "CON_PIVOT",2 ),
                 ("placeholder", translate("Placeholder"), translate(""), "MOD_CLOTH",3 ),
                 ("placeholder_custom", translate("Custom Placeholder"), translate(""), "MOD_CLOTH",4 ),
                 ("point", translate("Point"), translate(""), "STICKY_UVS_DISABLE",5 ),
                 #("cloud", translate("Point-Cloud"), translate(""), "POINTCLOUD_DATA",7 ), #TODO Carbon! 
               ],
        update=scattering.update_factory.factory("s_display_method"),
        )
    s_display_placeholder_type : bpy.props.EnumProperty(
        name=translate("Placeholder Type"),
        default= "SCATTER5_placeholder_pyramidal_square",
        items= [("SCATTER5_placeholder_extruded_triangle",     translate("Extruded Triangle") ,""     ,"MESH_CUBE", 1 ),
                ("SCATTER5_placeholder_extruded_square",       translate("Extruded Square") ,""       ,"MESH_CUBE", 2 ),
                ("SCATTER5_placeholder_extruded_pentagon",     translate("Extruded Pentagon") ,""     ,"MESH_CUBE", 3 ),
                ("SCATTER5_placeholder_extruded_hexagon",      translate("Extruded Hexagon") ,""      ,"MESH_CUBE", 4 ),
                ("SCATTER5_placeholder_extruded_decagon",      translate("Extruded Decagon") ,""      ,"MESH_CUBE", 5 ),
                ("SCATTER5_placeholder_pyramidal_triangle",    translate("Pyramidal Triangle") ,""    ,"MESH_CONE", 6 ),
                ("SCATTER5_placeholder_pyramidal_square",      translate("Pyramidal Square") ,""      ,"MESH_CONE", 7 ),
                ("SCATTER5_placeholder_pyramidal_pentagon",    translate("Pyramidal Pentagon") ,""    ,"MESH_CONE", 8 ),
                ("SCATTER5_placeholder_pyramidal_hexagon",     translate("Pyramidal Hexagon") ,""     ,"MESH_CONE", 9 ),
                ("SCATTER5_placeholder_pyramidal_decagon",     translate("Pyramidal Decagon") ,""     ,"MESH_CONE", 10 ),
                ("SCATTER5_placeholder_flat_triangle",         translate("Flat Triangle") ,""         ,"SNAP_FACE", 11 ),
                ("SCATTER5_placeholder_flat_square",           translate("Flat Square") ,""           ,"SNAP_FACE", 12 ),
                ("SCATTER5_placeholder_flat_pentagon",         translate("Flat Pentagon") ,""         ,"SNAP_FACE", 13 ),
                ("SCATTER5_placeholder_flat_hexagon",          translate("Flat Hexagon") ,""          ,"SNAP_FACE", 14 ),
                ("SCATTER5_placeholder_flat_decagon",          translate("Flat Decagon") ,""          ,"SNAP_FACE", 15 ),
                ("SCATTER5_placeholder_card_triangle",         translate("Card Triangle") ,""         ,"MESH_PLANE", 16 ),
                ("SCATTER5_placeholder_card_square",           translate("Card Square") ,""           ,"MESH_PLANE", 17 ),
                ("SCATTER5_placeholder_card_pentagon",         translate("Card Pentagon") ,""         ,"MESH_PLANE", 18 ),
                ("SCATTER5_placeholder_hemisphere_01",         translate("Hemisphere 01") ,""         ,"MESH_ICOSPHERE", 19 ),
                ("SCATTER5_placeholder_hemisphere_02",         translate("Hemisphere 02") ,""         ,"MESH_ICOSPHERE", 20 ),
                ("SCATTER5_placeholder_hemisphere_03",         translate("Hemisphere 03") ,""         ,"MESH_ICOSPHERE", 21 ),
                ("SCATTER5_placeholder_hemisphere_04",         translate("Hemisphere 04") ,""         ,"MESH_ICOSPHERE", 22 ),
                ("SCATTER5_placeholder_lowpoly_pine_01",       translate("Lowpoly Pine 01") ,""       ,"LIGHT_POINT", 23 ),
                ("SCATTER5_placeholder_lowpoly_pine_02",       translate("Lowpoly Pine 02") ,""       ,"LIGHT_POINT", 24 ),
                ("SCATTER5_placeholder_lowpoly_coniferous_01", translate("Lowpoly Coniferous 01") ,"" ,"LIGHT_POINT", 25 ),
                ("SCATTER5_placeholder_lowpoly_coniferous_02", translate("Lowpoly Coniferous 02") ,"" ,"LIGHT_POINT", 26 ),
                ("SCATTER5_placeholder_lowpoly_coniferous_03", translate("Lowpoly Coniferous 03") ,"" ,"LIGHT_POINT", 27 ),
                ("SCATTER5_placeholder_lowpoly_coniferous_04", translate("Lowpoly Coniferous 04") ,"" ,"LIGHT_POINT", 28 ),
                ("SCATTER5_placeholder_lowpoly_sapling_01",    translate("Lowpoly Sapling 01"),""     ,"LIGHT_POINT", 29 ),
                ("SCATTER5_placeholder_lowpoly_sapling_02",    translate("Lowpoly Sapling 02"),""     ,"LIGHT_POINT", 30 ),
                ("SCATTER5_placeholder_lowpoly_cluster_01",    translate("Lowpoly Cluster 01") ,""    ,"STICKY_UVS_LOC", 31 ),
                ("SCATTER5_placeholder_lowpoly_cluster_02",    translate("Lowpoly Cluster 02") ,""    ,"STICKY_UVS_LOC", 32 ),
                ("SCATTER5_placeholder_lowpoly_cluster_03",    translate("Lowpoly Cluster 03") ,""    ,"STICKY_UVS_LOC", 33 ),
                ("SCATTER5_placeholder_lowpoly_cluster_04",    translate("Lowpoly Cluster 04") ,""    ,"STICKY_UVS_LOC", 34 ),
                ("SCATTER5_placeholder_lowpoly_plant_01",      translate("Lowpoly Plant 01") ,""      ,"OUTLINER_OB_HAIR", 35 ),
                ("SCATTER5_placeholder_lowpoly_plant_02",      translate("Lowpoly Plant 02") ,""      ,"OUTLINER_OB_HAIR", 36 ),
                ("SCATTER5_placeholder_lowpoly_plant_03",      translate("Lowpoly Plant 03") ,""      ,"OUTLINER_OB_HAIR", 38 ),
                ("SCATTER5_placeholder_lowpoly_flower_01",     translate("Lowpoly Flower 01"),""      ,"OUTLINER_OB_HAIR", 39 ),
                ("SCATTER5_placeholder_lowpoly_flower_02",     translate("Lowpoly Flower 02"),""      ,"OUTLINER_OB_HAIR", 40 ),
                ("SCATTER5_placeholder_helper_empty_stick",    translate("Helper Empty Stick") ,""    ,"EMPTY_ARROWS", 41 ),
                ("SCATTER5_placeholder_helper_empty_arrow",    translate("Helper Empty Arrow") ,""    ,"EMPTY_ARROWS", 42 ),
                ("SCATTER5_placeholder_helper_empty_axis",     translate("Helper Empty Axis") ,""     ,"EMPTY_ARROWS", 43 ),
                ("SCATTER5_placeholder_helper_colored_axis",   translate("Helper Colored Axis") ,""   ,"EMPTY_ARROWS", 44 ),
                ("SCATTER5_placeholder_helper_colored_cube",   translate("Helper Colored Cube") ,""   ,"EMPTY_ARROWS", 45 ),
                ("SCATTER5_placeholder_helper_y_arrow",        translate("Helper Tangent Arrow") ,""  ,"EMPTY_ARROWS", 46 ),
               ],
        update=scattering.update_factory.factory("s_display_placeholder_type"),
        )
    s_display_custom_placeholder_ptr : bpy.props.PointerProperty(
        type=bpy.types.Object, 
        update=scattering.update_factory.factory("s_display_custom_placeholder_ptr",),
        )
    s_display_placeholder_scale : bpy.props.FloatVectorProperty(
        name=translate("Scale Factor"),
        subtype="XYZ", 
        default=(0.3,0.3,0.3), 
        update=scattering.update_factory.factory("s_display_placeholder_scale", is_delayed=True),
        )
    s_display_point_radius : bpy.props.FloatProperty(
        name=translate("Scale Factor"),
        default=0.3,
        min=0,
        update=scattering.update_factory.factory("s_display_point_radius"),
        )
    s_display_camdist_allow: bpy.props.BoolProperty(
        default=False,
        name=translate("Reveal Near Instance Camera"),
        description=translate("Disable the particle display method for points closed to the camera"),
        update=scattering.update_factory.factory("s_display_camdist_allow"),
        )
    s_display_camdist_distance : bpy.props.FloatProperty(
        name=translate("Distance"),
        default=5,
        subtype="DISTANCE",
        min=0,
        soft_max=200, 
        update=scattering.update_factory.factory("s_display_camdist_distance", is_delayed=True),
        )
    s_display_viewport_method : bpy.props.EnumProperty(
        name=translate("Visibility Method"),
        default="except_rendered",
        items= [ ("viewport_only", translate("Viewport Only"),translate("This functionality will be active only in the viewport"),),
                 ("except_rendered", translate("Viewport Except Rendered"),translate("This functionality will be active only in the viewport, except if rendered view is activated"),),
                 ("viewport_and_render", translate("Viewport & Render"), translate("This functionality will be active both in viewport and final render"),),
               ],
        update=scattering.update_factory.factory("s_display_viewport_method"),
        )