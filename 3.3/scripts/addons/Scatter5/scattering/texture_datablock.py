

# ooooooooooooo                           .                                       oooooooooo.                 .            
# 8'   888   `8                         .o8                                       `888'   `Y8b              .o8            
#      888       .ooooo.  oooo    ooo .o888oo oooo  oooo  oooo d8b  .ooooo.        888      888  .oooo.   .o888oo  .oooo.  
#      888      d88' `88b  `88b..8P'    888   `888  `888  `888""8P d88' `88b       888      888 `P  )88b    888   `P  )88b 
#      888      888ooo888    Y888'      888    888   888   888     888ooo888       888      888  .oP"888    888    .oP"888 
#      888      888    .o  .o8"'88b     888 .  888   888   888     888    .o       888     d88' d8(  888    888 . d8(  888 
#     o888o     `Y8bod8P' o88'   888o   "888"  `V88V"V8P' d888b    `Y8bod8P'      o888bood8P'   `Y888""8o   "888" `Y888""8o


import bpy, random, os 

from .. resources.translate import translate
from .. resources.icons import cust_icon
from .. resources import directories

from .. utils.extra_utils import dprint
from .. utils.path_utils import get_subpaths
from .. utils.import_utils import serialization , import_image, import_and_add_geonode
from .. utils.draw_utils import add_font, clear_all_fonts


# ooooooooo.                                                        .    o8o
# `888   `Y88.                                                    .o8    `"'
#  888   .d88' oooo d8b  .ooooo.  oo.ooooo.   .ooooo.  oooo d8b .o888oo oooo   .ooooo.   .oooo.o
#  888ooo88P'  `888""8P d88' `88b  888' `88b d88' `88b `888""8P   888   `888  d88' `88b d88(  "8
#  888          888     888   888  888   888 888ooo888  888       888    888  888ooo888 `"Y88b.
#  888          888     888   888  888   888 888    .o  888       888 .  888  888    .o o.  )88b
# o888o        d888b    `Y8bod8P'  888bod8P' `Y8bod8P' d888b      "888" o888o `Y8bod8P' 8""888P'
#                                  888
#                                 o888o


def user_name_upd(self,context):
    ng = self.id_data
    #same ? 
    if (self.user_name == ng.name.replace(".TEXTURE ","")):
        return None
    #else change both names  
    i=0
    search_name = f".TEXTURE {self.user_name}"
    while search_name in bpy.data.node_groups:
        search_name = f".TEXTURE {self.user_name}.{i:03}"
        i+=1

    self.is_default = (search_name==".TEXTURE *DEFAULT*")

    ng.name = search_name
    self.user_name = search_name.replace(".TEXTURE ","") #only "same ?" check above will save us from feedback loop

def is_default_upd(self,context):
    ng = self.id_data
    ng.nodes["is_default"].boolean = self.is_default

def texture_type_upd(self,context):
    ng = self.id_data
    ng.links.new(ng.nodes[self.texture_type].outputs[0],ng.nodes["texture_type"].inputs[0])

def scale_upd(self,context):
    ng = self.id_data
    ng.nodes["scale"].outputs[0].default_value = self.scale
    
def distorsion_upd(self,context):
    ng = self.id_data
    ng.nodes["distorsion"].outputs[0].default_value = self.distorsion

def detail_upd(self,context):
    ng = self.id_data
    ng.nodes["detail"].outputs[0].default_value = self.detail

def out_type_upd(self,context):
    ng = self.id_data
    ng.nodes["out_type_color"].boolean = self.out_type == "Color"

def brick_offset_upd(self,context):
    ng = self.id_data
    node = ng.nodes["brick_node"]
    node.offset = self.brick_offset

def brick_offset_frequency_upd(self,context):
    ng = self.id_data
    node = ng.nodes["brick_node"]
    node.offset_frequency = self.brick_offset_frequency

def brick_squash_upd(self,context):
    ng = self.id_data
    node = ng.nodes["brick_node"]
    node.squash = self.brick_squash

def brick_squash_frequency_upd(self,context):
    ng = self.id_data
    node = ng.nodes["brick_node"]
    node.squash_frequency = self.brick_squash_frequency

def brick_mortar_size_upd(self, context):
    ng = self.id_data
    node = ng.nodes["brick_node"]
    node.inputs[5].default_value = self.brick_mortar_size

def brick_mortar_smooth_upd(self, context):
    ng = self.id_data
    node = ng.nodes["brick_node"]
    node.inputs[6].default_value = self.brick_mortar_smooth

def brick_bias_upd(self,context):
    ng = self.id_data
    node = ng.nodes["brick_node"]
    node.inputs[7].default_value = self.brick_bias

def brick_width_upd(self,context):
    ng = self.id_data
    node = ng.nodes["brick_node"]
    node.inputs[8].default_value = self.brick_width

def brick_row_height_upd(self,context):
    ng = self.id_data
    node = ng.nodes["brick_node"]
    node.inputs[9].default_value = self.brick_row_height

def image_interpolation_upd(self, context):
    ng = self.id_data
    node = ng.nodes["image_node"]
    node.interpolation = self.image_interpolation

def image_extension_upd(self, context):
    ng = self.id_data
    node = ng.nodes["image_node"]
    node.extension = self.image_extension

def image_ptr_upd(self, context):
    ng = self.id_data
    node = ng.nodes["image_node"]
    node.inputs[0].default_value = self.image_ptr

def image_frame_upd(self, context):
    ng = self.id_data
    node = ng.nodes["image_node"]
    node.inputs[2].default_value = self.image_frame

def magic_turbulence_depth_upd(self,context):
    ng = self.id_data
    node = ng.nodes["magic_node"]
    node.turbulence_depth = self.magic_turbulence_depth

def musgrave_musgrave_type_upd(self,context):
    ng = self.id_data
    node = ng.nodes["musgrave_node"]
    node.musgrave_type = self.musgrave_musgrave_type

def musgrave_offset_upd(self,context):
    ng = self.id_data
    node = ng.nodes["musgrave_node"]
    node.inputs[6].default_value = self.musgrave_offset

def noise_roughness_upd(self,context):
    ng = self.id_data
    node = ng.nodes["noise_node"]
    node.inputs[4].default_value = self.noise_roughness

def voronoi_feature_upd(self,context):
    ng = self.id_data
    node = ng.nodes["voronoi_node"]
    node.feature = self.voronoi_feature

def voronoi_distance_upd(self,context):
    ng = self.id_data
    node = ng.nodes["voronoi_node"]
    node.distance = self.voronoi_distance

def voronoi_exponent_upd(self,context):
    ng = self.id_data
    node = ng.nodes["voronoi_node"]
    node.inputs[4].default_value = self.voronoi_exponent

def voronoi_randomness_upd(self,context):
    ng = self.id_data
    node = ng.nodes["voronoi_node"]
    node.inputs[5].default_value = self.voronoi_randomness

def wave_wave_type_upd(self, context):
    ng = self.id_data
    node = ng.nodes["wave_node"]
    node.wave_type = self.wave_wave_type

def wave_bands_direction_upd(self, context):
    ng = self.id_data
    node = ng.nodes["wave_node"]
    node.bands_direction = self.wave_bands_direction

def wave_wave_profile_upd(self, context):
    ng = self.id_data
    node = ng.nodes["wave_node"]
    node.wave_profile = self.wave_wave_profile

def wave_detail_scale_upd(self, context):
    ng = self.id_data
    node = ng.nodes["wave_node"]
    node.inputs[4].default_value = self.wave_detail_scale

def wave_detail_roughness_upd(self, context):
    ng = self.id_data
    node = ng.nodes["wave_node"]
    node.inputs[5].default_value = self.wave_detail_roughness

def wave_phase_offset_upd(self, context):
    ng = self.id_data
    node = ng.nodes["wave_node"]
    node.inputs[6].default_value = self.wave_phase_offset

def intensity_upd(self,context):
    ng = self.id_data
    ng.nodes["intensity"].outputs[0].default_value = self.intensity

def contrast_upd(self,context):
    ng = self.id_data
    ng.nodes["contrast"].outputs[0].default_value = self.contrast

def saturation_upd(self,context):
    ng = self.id_data
    ng.nodes["saturation"].outputs[0].default_value = self.saturation

def jitter_upd(self,context):
    ng = self.id_data
    ng.nodes["jitter"].outputs[0].default_value = self.jitter

def use_color_ramp_upd(self,context):
    ng = self.id_data
    ng.nodes["use_color_ramp"].boolean = self.use_color_ramp

def mapping_projection_upd(self,context):
    ng = self.id_data
    index = self.bl_rna.properties["mapping_projection"].enum_items[self.mapping_projection].value
    ng.nodes["mapping_projection"].integer = index 

def mapping_uv_ptr_upd(self,context):
    ng = self.id_data

    for o in [o for o in bpy.data.objects if (o.type=="MESH") and (len(o.modifiers)!=0)]:

        m = o.modifiers.get("Scatter5 Geonode Engine MKI")
        if m is not None: 
            
            for node_name,mod_inputs in (("TEXTURE_NODE s_pattern1","Input_15_attribute_name"),
                                         ("TEXTURE_NODE s_pattern2","Input_16_attribute_name"),
                                         ("TEXTURE_NODE s_rot_tilt","Input_44_attribute_name"),
                                         ("TEXTURE_NODE s_rot_align_y","Input_46_attribute_name"),
                                         ("TEXTURE_NODE s_instances","Input_50_attribute_name"),
                                         ):
                node = m.node_group.nodes.get(node_name)
                if (node is not None):
                    if (node.node_tree.name==ng.name):
                        m[mod_inputs] = self.mapping_uv_ptr
                continue
                
            #send update signal 
            m.show_in_editmode = not m.show_in_editmode
            m.show_in_editmode = not m.show_in_editmode

            continue

        m = o.modifiers.get("ScatterVisualizer")
        if (m is not None):
            if (m.node_group.nodes["TEXTURE_NODE visualizer"].node_tree.name==ng.name):
                m["Input_2_attribute_name"] = self.mapping_uv_ptr

            #send update signal 
            m.show_in_editmode = not m.show_in_editmode
            m.show_in_editmode = not m.show_in_editmode

        continue

def mapping_location_upd(self,context):
    ng = self.id_data
    ng.nodes["mapping_location"].vector = self.mapping_location

def mapping_rotation_upd(self,context):
    ng = self.id_data
    ng.nodes["mapping_rotation"].vector = self.mapping_rotation

def mapping_scale_upd(self,context):
    ng = self.id_data
    ng.nodes["mapping_scale"].vector = self.mapping_scale

def mapping_random_loc_upd(self,context):
    if (self.mapping_random_loc == True):
        self.mapping_random_loc = False
        self.mapping_location = [random.uniform(0,999), random.uniform(0,999) , random.uniform(0,999) ]


class SCATTER5_PROP_node_texture(bpy.types.PropertyGroup):
    """bpy.data.node_groups[i].scatter5.texture"""

    user_name : bpy.props.StringProperty(
        default="*DEFAULT*",
        update=user_name_upd,
        )

    is_default : bpy.props.BoolProperty(
        default=False,
        update=is_default_upd,
        )

    texture_type : bpy.props.EnumProperty(
        default="musgrave_",
        items=[("brick_",translate("Brick"),"","MOD_BUILD",0),
               ("checker_",translate("Checker"),"","MESH_GRID",1),
               ("image_",translate("Image"),"","IMAGE_DATA",2),
               ("magic_",translate("Magic"),"","SHADERFX",3),
               ("musgrave_",translate("Musgrave"),"","FORCE_TURBULENCE",4),
               ("noise_",translate("Noise"),"","BOIDS",5),
               ("voronoi_",translate("Voronoi"),"","SYSTEM",6),
               ("wave_",translate("Wave"),"","MOD_OCEAN",7),
               ("white_noise_",translate("White Noise"),"","ALIGN_FLUSH",8),
            ],
        update=texture_type_upd,
        )

    #texture settings 

    #general
    scale : bpy.props.FloatProperty(
        name=translate("Scale"),
        default=1,
        update=scale_upd,
        )
    detail : bpy.props.FloatProperty(
        name=translate("Detail"),
        default=1,
        min=0,
        max=15,
        update=detail_upd,
        )
    distorsion : bpy.props.FloatProperty(
        name=translate("Distorsion"),
        default=0,
        update=distorsion_upd,
        )
    out_type : bpy.props.EnumProperty(
        name=translate("Output"),
        default="Greyscale",
        items=[("Greyscale","Greyscale","","",0),("Color","Colored","","",1),],
        update=out_type_upd,
        )
    #brick 
    brick_offset : bpy.props.FloatProperty(
        name=translate("Offset"),
        default=0.5, 
        min=0,
        max=1,
        update=brick_offset_upd,
        )
    brick_offset_frequency : bpy.props.IntProperty(
        name=translate("Offset Frequency"),
        default=2,
        min=1,
        max=99,
        update=brick_offset_frequency_upd,
        )
    brick_squash : bpy.props.FloatProperty(
        name=translate("Squash"),
        default=1, 
        min=0,
        max=99, 
        update=brick_squash_upd,
        )
    brick_squash_frequency : bpy.props.IntProperty(
        name=translate("Squash Frequency"),
        default=2,
        min=1,
        max=99, 
        update=brick_squash_frequency_upd,
        )
    brick_mortar_size : bpy.props.FloatProperty(
        name=translate("Mortar Size"),
        default=0.02, 
        soft_min=0,
        soft_max=0.125, 
        update=brick_mortar_size_upd,
        )
    brick_mortar_smooth : bpy.props.FloatProperty(
        name=translate("Mortar Smooth"),
        default=0.1, 
        soft_min=0,
        soft_max=0.125,
        update=brick_mortar_smooth_upd,
        )
    brick_bias : bpy.props.FloatProperty(
        name=translate("Bias"),
        default=0, 
        soft_min=-1,
        soft_max=1, 
        update=brick_bias_upd,
        )
    brick_width : bpy.props.FloatProperty(
        name=translate("Width"),
        default=0.5,
        soft_min=0.01,
        soft_max=100,
        update=brick_width_upd,
        )
    brick_row_height : bpy.props.FloatProperty(
        name=translate("Row Height"),
        default=0.25,
        soft_min=0.01,
        soft_max=100,
        update=brick_row_height_upd,
        )
    #image texture
    image_interpolation : bpy.props.EnumProperty(
        name=translate("Interpolation"),
        default="Linear",
        items=[("Linear","Linear",""),("Closest","Closest",""),("Cubic","Cubic","")], 
        update=image_interpolation_upd,
        )
    image_extension : bpy.props.EnumProperty(
        name=translate("Extension"),
        default="REPEAT",
        items=[("REPEAT","Repeat",""),("EXTEND","Extend",""),("CLIP","Clip",""),], 
        update=image_extension_upd,
        )
    image_ptr : bpy.props.PointerProperty(
        type=bpy.types.Image, 
        update=image_ptr_upd,
        )
    image_frame : bpy.props.IntProperty(
        name=translate("Frame"),
        default=0,
        update=image_frame_upd,
        )
    #magic
    magic_turbulence_depth : bpy.props.IntProperty(
        name=translate("Depth"),
        default=0, 
        soft_min=0,
        soft_max=10, 
        update=magic_turbulence_depth_upd,
        )
    #musgrave
    musgrave_musgrave_type : bpy.props.EnumProperty(
        name=translate("Type"),
        default="HYBRID_MULTIFRACTAL", 
        items=[("MULTIFRACTAL","Multifractal",""),("RIDGED_MULTIFRACTAL","Ridged Multifractal",""),("HYBRID_MULTIFRACTAL","Hybrid Multifractal",""),("FBM","Fbm",""),("HETERO_TERRAIN","Hetero Terrain",""),], 
        update=musgrave_musgrave_type_upd,
        )
    musgrave_offset : bpy.props.FloatProperty(
        name=translate("Offset"),
        default=0.2, 
        update=musgrave_offset_upd,
        )
    #noise
    noise_roughness : bpy.props.FloatProperty(
        name=translate("Roughness"),
        default=0, 
        soft_min=0,
        soft_max=1, 
        update=noise_roughness_upd,
        )
    #voronoi
    voronoi_feature : bpy.props.EnumProperty(
        name=translate("Feature"),
        default="F1", 
        items=[("F1","F1",""),("F2","F2",""),], 
        update=voronoi_feature_upd,
        )
    voronoi_distance : bpy.props.EnumProperty(
        name=translate("Distance"),
        default="EUCLIDEAN",
        items=[("EUCLIDEAN","Euclidean",""),("MANHATTAN","Manhattan",""),("CHEBYCHEV","Chebychev",""),("MINKOWSKI","Minkowski",""),], 
        update=voronoi_distance_upd,
        )
    voronoi_exponent : bpy.props.FloatProperty(
        name=translate("Exponent"),
        default=0, 
        soft_min=0,
        soft_max=32,
        update=voronoi_exponent_upd,
        )
    voronoi_randomness : bpy.props.FloatProperty(
        name=translate("Randomness"),
        default=1,
        soft_min=0,
        soft_max=1, 
        update=voronoi_randomness_upd,
        )
    #wave
    wave_wave_type : bpy.props.EnumProperty(
        name=translate("Type"),
        default="BANDS", 
        items=[("BANDS","Bands",""),("RINGS","Rings",""),], 
        update=wave_wave_type_upd,
        )
    wave_bands_direction : bpy.props.EnumProperty(
        name=translate("Bands Direction"),
        default="X", 
        items=[("X","X",""),("Y","Y",""),("Z","Z",""),("DIAGONAL","Diagonal",""),], 
        update=wave_bands_direction_upd,
        )
    wave_wave_profile : bpy.props.EnumProperty(
        name=translate("Wave Profile"),
        default="SIN", 
        items=[("SIN","Sine",""),("SAW","Saw",""),("TRI","Triangle",""),], 
        update=wave_wave_profile_upd,
        )
    wave_detail_scale : bpy.props.FloatProperty(
        name=translate("Detail Scale"),
        default=0, 
        update=wave_detail_scale_upd,
        )
    wave_detail_roughness : bpy.props.FloatProperty(
        name=translate("Detail Roughness"),
         default=0, 
         soft_min=0,
         soft_max=1, 
         update=wave_detail_roughness_upd,
         )
    wave_phase_offset : bpy.props.FloatProperty(
        name=translate("Phase Offset"),
        default=0, 
        update=wave_phase_offset_upd,
        )

    #color adjustments 

    intensity : bpy.props.FloatProperty(
        name=translate("Brightness"),
        default=1,
        min=0,
        soft_max=2,
        update=intensity_upd,
        )
    contrast : bpy.props.FloatProperty(
        name=translate("Contrast"),
        default=1,
        min=0,
        soft_max=5,
        update=contrast_upd,
        )
    saturation : bpy.props.FloatProperty(
        name=translate("Saturation"),
        default=1,
        min=0,
        max=2,
        update=saturation_upd,
        )
    jitter : bpy.props.FloatProperty(
        name=translate("Jitter"),
        default=0,
        min=0,
        max=3,
        update=jitter_upd,
        )

    #color ramp

    use_color_ramp : bpy.props.BoolProperty(
        name=translate("Use Color-Ramp"),
        default=False,
        update=use_color_ramp_upd,
        )
    def get_color_ramp(self):
        return self.id_data.nodes["ColorRamp"].color_ramp

    #mapping 

    mapping_projection : bpy.props.EnumProperty(
        name=translate("Space"),
        default= "local", 
        items= [ ("local", "Local", "", "ORIENTATION_LOCAL", 0),
                 ("global", "Global", "", "WORLD", 1),
                 ("uv", "UV", "", "STICKY_UVS_DISABLE", 2),
               ],
        update=mapping_projection_upd,
        )
    mapping_uv_ptr : bpy.props.StringProperty(
        default="",
        update=mapping_uv_ptr_upd,
        )
    mapping_location : bpy.props.FloatVectorProperty(
        name=translate("Location"),
        default = (0,0,0),
        update=mapping_location_upd,
        )
    mapping_rotation : bpy.props.FloatVectorProperty(
        name=translate("Rotation"),
        default = (0,0,0),
        subtype="EULER",
        update=mapping_rotation_upd,
        )
    mapping_scale : bpy.props.FloatVectorProperty(
        name=translate("Scale"),
        default = (1,1,1),
        update=mapping_scale_upd,
        ) 
    mapping_random_loc : bpy.props.BoolProperty(
        name=translate("Random Location"),
        default = False,
        update=mapping_random_loc_upd,
        )


# ooooooooo.                                             .       .    o8o
# `888   `Y88.                                         .o8     .o8    `"'
#  888   .d88' oooo d8b  .ooooo.   .oooo.o  .ooooo.  .o888oo .o888oo oooo  ooo. .oo.    .oooooooo
#  888ooo88P'  `888""8P d88' `88b d88(  "8 d88' `88b   888     888   `888  `888P"Y88b  888' `88b
#  888          888     888ooo888 `"Y88b.  888ooo888   888     888    888   888   888  888   888
#  888          888     888    .o o.  )88b 888    .o   888 .   888 .  888   888   888  `88bod8P'
# o888o        d888b    `Y8bod8P' 8""888P' `Y8bod8P'   "888"   "888" o888o o888o o888o `8oooooo.
#                                                                                      d"     YD
#                                                                                      "Y88888P'


def export_texture_as_dict(texture_ng, texture_random_loc=False,):
    """return a settings dict from a scatter texture nodegroup"""

    d = {}
    node_props = texture_ng.scatter5.texture

    #Noise settings 

    d["texture_type"] = node_props.texture_type
    d["scale"] = node_props.scale
    d["detail"] = node_props.detail
    d["distorsion"] = node_props.distorsion
    d["out_type"] = node_props.out_type

    if (d["texture_type"]=="brick_"):
        d["brick_offset"] = node_props.brick_offset
        d["brick_offset_frequency"] = node_props.brick_offset_frequency
        d["brick_squash"] = node_props.brick_squash
        d["brick_squash_frequency"] = node_props.brick_squash_frequency
        d["brick_mortar_size"] = node_props.brick_mortar_size
        d["brick_mortar_smooth"] = node_props.brick_mortar_smooth
        d["brick_bias"] = node_props.brick_bias
        d["brick_width"] = node_props.brick_width
        d["brick_row_height"] = node_props.brick_row_height

    elif (d["texture_type"]=="image_"):
        d["image_interpolation"] = node_props.image_interpolation
        d["image_extension"] = node_props.image_extension
        if (node_props.image_ptr is not None):
            d["image_name"] = node_props.image_ptr.name #Special
            d["image_path"] = node_props.image_ptr.filepath.split("\\")[-1] #Special

    elif (d["texture_type"]=="magic_"):
        d["magic_turbulence_depth"] = node_props.magic_turbulence_depth

    elif (d["texture_type"]=="musgrave_"):
        d["musgrave_musgrave_type"] = node_props.musgrave_musgrave_type
        d["musgrave_offset"] = node_props.musgrave_offset

    elif (d["texture_type"]=="noise_"):
        d["noise_roughness"] = node_props.noise_roughness

    elif (d["texture_type"]=="voronoi_"):
        d["voronoi_feature"] = node_props.voronoi_feature
        d["voronoi_distance"] = node_props.voronoi_distance
        d["voronoi_exponent"] = node_props.voronoi_exponent
        d["voronoi_randomness"] = node_props.voronoi_randomness

    elif (d["texture_type"]=="wave_"):
        d["wave_wave_type"] = node_props.wave_wave_type
        d["wave_bands_direction"] = node_props.wave_bands_direction
        d["wave_wave_profile"] = node_props.wave_wave_profile
        d["wave_detail_scale"] = node_props.wave_detail_scale
        d["wave_detail_roughness"] = node_props.wave_detail_roughness
        d["wave_phase_offset"] = node_props.wave_phase_offset

    #Color adjustments

    if node_props.intensity!=1:
        d["intensity"] = node_props.intensity
    if node_props.contrast!=1:
        d["contrast"] = node_props.contrast
    if node_props.saturation!=1:
        d["saturation"] = node_props.saturation
    if node_props.jitter!=0:
        d["jitter"] = node_props.jitter

    #Color ramp 

    d["use_color_ramp"] = node_props.use_color_ramp
    if (d["use_color_ramp"]==True):
        color_ramp =  node_props.get_color_ramp()
        d["color_ramp_interpolation"] = color_ramp.interpolation #Special
        d["color_ramp_elements"] = [(e.position, list(e.color)) for e in color_ramp.elements] #Special

    #Projection 

    d["mapping_projection"] = node_props.mapping_projection
    d["mapping_uv_ptr"] = node_props.mapping_uv_ptr
    d["mapping_location"] = node_props.mapping_location
    d["mapping_rotation"] = node_props.mapping_rotation
    d["mapping_scale"] = node_props.mapping_scale
    d["mapping_random_loc"] = texture_random_loc

    return d 

def paste_dict_to_texture(d, texture_ng, img_directory=directories.lib_library,):
    """apply settings to a scatter texture nodegroup"""

    node_props = texture_ng.scatter5.texture

    for k,v in d.items():
        if k in node_props.bl_rna.properties.keys():
            setattr(node_props,k,v)

    #Image Special 

    if ("image_name" in d):
        
        img = bpy.data.images.get(d["image_name"])
        if img is None: 
            #try to find this img in library
            if (img_directory!="") and (os.path.exists(img_directory)):
                for p in get_subpaths(img_directory):
                    img_name = d["image_path"] if ("\\" not in d["image_path"]) else d["image_path"].split("\\")[-1]
                    if p.endswith( img_name ):
                        img = import_image(p)
                        break
                    continue

        node_props.image_ptr = img

    #ColorRamp Special

    if (d["use_color_ramp"]==True):

        color_ramp =  node_props.get_color_ramp()
        color_ramp.interpolation = d["color_ramp_interpolation"]
        
        #clear all elements, it seems that api of color_ramp is a bit unstable
        for e in color_ramp.elements:
            try: color_ramp.elements.remove(e)
            except: pass

        #get colorramp element from dict &  sort from position, needed as sadly `color_ramp.elements.update()` do not work
        color_ramp_elements = d["color_ramp_elements"]
        color_ramp_elements = sorted(color_ramp_elements, key=lambda x:x[0])

        #change elements value 
        for i, (pos,col) in enumerate(color_ramp_elements):
            if (i > (len(color_ramp.elements)-1)):
                e = color_ramp.elements.new(pos)
                e.color = col
            else:
                color_ramp.elements[i].color = col
                color_ramp.elements[i].position = pos

    return None

def paste_legacy_beta_dict_to_texture(old, texture_ng, img_directory=directories.lib_library,):
    """partially convert legacy texture data information to new texture, scatter5 beta"""

    d = {}

    if ("type" in old):

        if (old["type"]=="IMAGE"):
            d["texture_type"]="image_"
            d["img_name"] = old["s_img_name"]
            d["img_path"] = old["s_img_path"]

        elif (old["type"]=="MAGIC"):
            d["texture_type"]="magic_"

        elif (old["type"]=="VORONOI"):
            d["texture_type"]="voronoi_"

        elif (old["type"]=="CLOUDS"):
            d["texture_type"]="noise_"

            d["noise_roughness"]=1
        elif (old["type"]=="MARBLE"):
            d["texture_type"]="wave_"
            d["wave_bands_direction"] = 'DIAGONAL'
            d["wave_detail_scale"] = 1
            d["wave_detail_roughness"] = 1
            d["distorsion"] = 10
            d["detail"] = 3

        elif (old["type"]=="STUCCI"):
            d["texture_type"] = 'musgrave_'
            d["musgrave_musgrave_type"] = 'MULTIFRACTAL'

        elif (old["type"]=="DISTORTED_NOISE"):
            d["texture_type"]="musgrave_"

        elif (old["type"]=="WOOD"):
            d["texture_type"]="wave_"

    if ("scale" in old):
        d["scale"] = old["distorsion"]
    if ("distorsion" in old):
        d["distorsion"] = old["distorsion"]

    if ("intensity" in old):
        d["intensity"] = old["intensity"]
    if ("contrast" in old):
        d["contrast"] = old["contrast"]
    if ("saturation" in old):
        d["saturation"] = old["saturation"]
        
    if ("use_color_ramp" in old):
        d["use_color_ramp"] = old["use_color_ramp"]
    if ("s_colorramp_interpolation" in old):
        d["color_ramp_interpolation"] = old["s_colorramp_interpolation"]
    if ("s_colorramp_elements" in old):
        d["color_ramp_elements"] = old["s_colorramp_elements"]

    if ("s_texture_projection" in old):
        d["mapping_projection"] = "local" if (old["s_texture_projection"]=="s_point_position") else "uv"
    if ("s_texture_uv_ptr" in old):
        d["mapping_uv_ptr"] = old["s_texture_uv_ptr"]
    if ("s_texture_location" in old):
        d["mapping_location"] = old["s_texture_location"]
    if ("s_texture_rotation" in old):
        d["mapping_rotation"] = old["s_texture_rotation"]
    if ("s_texture_scale" in old):
        d["mapping_scale"] = old["s_texture_scale"]
    if ("s_texture_random_loc" in old):
        d["mapping_random_loc"] = old["s_texture_random_loc"]

    paste_dict_to_texture(d, texture_ng, img_directory=img_directory,)

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


class SCATTER5_OT_scatter_texture_new(bpy.types.Operator):

    bl_idname      = "scatter5.scatter_texture_new"
    bl_label       = ""
    bl_description = translate("Create a new Scatter node texture data")
    bl_options     = {'INTERNAL','UNDO'}

    ptr_name : bpy.props.StringProperty()
    new_name : bpy.props.StringProperty()

    def execute(self, context):

        texture_node = context.PTR_texture_node
        texture_node.node_tree = texture_node.node_tree.copy()
        texture_node.node_tree.scatter5.texture.user_name = self.new_name
        
        #update api
        psy = context.PTR_psy
        setattr(psy,self.ptr_name, texture_node.node_tree.name)

        return {'FINISHED'}


class SCATTER5_OT_scatter_texture_enum(bpy.types.Operator):

    bl_idname      = "scatter5.scatter_texture_enum"
    bl_label       = ""
    bl_description = ""
    bl_options     = {'INTERNAL','UNDO'}

    ptr_name : bpy.props.StringProperty()

    def generate_items(scene, context, ):
        items = []

        for ng in bpy.data.node_groups: 
            if ng.name.startswith(".TEXTURE "):
                if (not ng.name.endswith("*DEFAULT*")) and not (ng.name.endswith("*VISUALIZER*")):
                    items.append((ng.name, ng.name.replace(".TEXTURE ",""),""))

        if (len(items)==0):
            return [("none",translate("Nothing Found"),"")]
        return items 

    enum : bpy.props.EnumProperty(items=generate_items,)

    def execute(self, context):

        if self.enum=="none":
            return {'FINISHED'} 

        ng = bpy.data.node_groups[self.enum]
        if (ng is None):
            print("Nodegroup not found") #should never happend
            return {'FINISHED'} 

        texture_node = context.PTR_texture_node
        texture_node.node_tree = bpy.data.node_groups[self.enum]
        texture_node.node_tree.scatter5.texture.user_name = self.enum.replace(".TEXTURE ","")
            
        #update our UVMap ptr
        texture_node.node_tree.scatter5.texture.mapping_uv_ptr = texture_node.node_tree.scatter5.texture.mapping_uv_ptr

        #update api
        psy = context.PTR_psy
        setattr(psy,self.ptr_name, texture_node.node_tree.name)

        #also update visualizer, if found 
        for o in [o for o in bpy.data.objects if (o.type=="MESH") and (len(o.modifiers)!=0)]:
            m = o.modifiers.get("ScatterVisualizer")
            if (m is not None):
                m.node_group.nodes["TEXTURE_NODE visualizer"].node_tree = ng
                break

        return {'FINISHED'}


class SCATTER5_OT_scatter_texture_duppli(bpy.types.Operator):

    bl_idname      = "scatter5.scatter_texture_duppli"
    bl_label       = ""
    bl_description = ""
    bl_options     = {'INTERNAL','UNDO'}

    ptr_name : bpy.props.StringProperty()

    def execute(self, context):

        texture_node = context.PTR_texture_node
        texture_node.node_tree = texture_node.node_tree.copy()
        texture_node.node_tree.scatter5.texture.user_name = texture_node.node_tree.name.replace(".TEXTURE ","")
        
        #update api
        psy = context.PTR_psy
        setattr(psy,self.ptr_name, texture_node.node_tree.name)

        return {'FINISHED'}


# class SCATTER5_OT_scatter_texture_preset(bpy.types.Operator): #FOR 5.1, but use classic preset system of blender, or implement them per category??? 

#     bl_idname      = "scatter5.scatter_texture_preset"
#     bl_label       = ""
#     bl_description = ""
#     bl_options     = {'INTERNAL','UNDO'}

#     def execute(self, context):

        # PresetsDict = {
        #     "empty_image": ("Image-Data",     "IMAGE_DATA",         {'type':'IMAGE','contrast':1,'factor_blue':1,'factor_green':1,'factor_red':1,'saturation':1,'intensity':1,'use_color_ramp':False,}),
        #     "clouds":      ("Clouds",         "W_DTXT_CLOUD",       {'type':'CLOUDS','noise_basis':'BLENDER_ORIGINAL','noise_type':'SOFT_NOISE','contrast':3,'factor_blue':1,'factor_green':1,'factor_red':1,'intensity':1,'noise_depth':0,'noise_scale':0.1,'saturation':1,'use_clamp':True,'use_color_ramp':False,}),
        #     "wood":        ("Wood",           "W_DTXT_WOOD",        {'type':'WOOD','wood_type':'BANDS','noise_basis':'BLENDER_ORIGINAL','noise_basis_2':'SIN','noise_type':'SOFT_NOISE','contrast':1,'factor_blue':1,'factor_green':1,'factor_red':1,'saturation':1,'turbulence':5,'use_clamp':True,'intensity':1,'noise_scale':0.25,'use_color_ramp':True,'s_colorramp_elements':[(0.21,[0,0,0,1]),(0.82,[0.28,0.28,0.28,1]),(1,[1,1,1,1])],'s_colorramp_interpolation':'LINEAR',}),
        #     "zebra":       ("Zebra",          "W_DTXT_ZEBRA",       {'type':'WOOD','wood_type':'BANDNOISE','noise_type':'SOFT_NOISE','noise_basis':'ORIGINAL_PERLIN','noise_basis_2':'SIN','contrast':3,'factor_blue':1,'factor_green':1,'factor_red':1,'intensity':0.04,'noise_scale':0.9,'saturation':1,'turbulence':15.6,'use_color_ramp':False,}),
        #     "marble" :     ("Marble",         "W_DTXT_RGB_MARBLE",  {'type':'MARBLE','marble_type':'SOFT','noise_basis':'BLENDER_ORIGINAL','noise_basis_2':'SIN','noise_type':'SOFT_NOISE','contrast':1,'turbulence':7,'saturation':1,'factor_blue':1,'factor_green':1,'factor_red':1,'intensity':1,'noise_depth':2,'use_clamp':True,'noise_scale':0.25,'use_color_ramp':False,}),
        #     "voronoi":     ("Voronoi",        "W_DTXT_VORONOI",     {'type':'VORONOI','color_mode':'POSITION','distance_metric':'MINKOVSKY','contrast':0.75,'factor_blue':2,'factor_green':2,'factor_red':2,'intensity':0.2,'minkovsky_exponent':10,'noise_intensity':1.6,'weight_1':1,'weight_2':0,'weight_3':0,'weight_4':0,'noise_scale':0.2,'saturation':0,'use_clamp':True,'use_color_ramp':False,}),
        #     "bubble":      ("Bubble",         "W_DTXT_BUBBLE",      {'type':'VORONOI','color_mode':'INTENSITY','contrast':3.0,'distance_metric':'DISTANCE','factor_blue':1.0,'factor_green':1.0,'factor_red':1.0,'intensity':1.15,'weight_1':1,'weight_2':0,'weight_3':0,'weight_4':0,'saturation':0.0,'use_clamp':True,'use_color_ramp':False,'minkovsky_exponent':2.5,'noise_intensity':1.1,'noise_scale':0.25,'use_preview_alpha':False,}),
        #     "blob":        ("Blob",           "W_DTXT_BLOB",        {'type':'VORONOI','distance_metric':'DISTANCE_SQUARED','color_mode':'INTENSITY','contrast':2.0,'factor_blue':1.0,'factor_green':1.0,'factor_red':1.0,'intensity':1.0,'minkovsky_exponent':2.5,'noise_intensity':1.5,'noise_scale':0.3,'saturation':0.0,'use_clamp':True,'weight_1':1.5,'weight_2':0.15,'weight_3':0.15,'weight_4':0.15,'use_color_ramp':True,'s_colorramp_interpolation':'CONSTANT','s_colorramp_elements':[(0.0,[0.0,0.0,0.0,1]),(0.35,[0.5,0.5,0.5,1]),(0.95,[1.0,1.0,1.0,1])],}),
        #     "musgrave":    ("Musgrave",       "W_DTXT_MUSGRAVE",    {'type':'MUSGRAVE','musgrave_type':'FBM','noise_basis':'ORIGINAL_PERLIN','contrast':1,'dimension_max':0.67,'factor_blue':1,'factor_green':1,'factor_red':1,'gain':1,'intensity':1,'noise_intensity':2,'noise_scale':0.31,'octaves':8,'offset':1,'saturation':1,'use_clamp':True,'use_color_ramp':False,}),
        #     "manhattan":   ("manhattan",      "W_DTXT_MANHATTAN",   {'type':'VORONOI','distance_metric':'MANHATTAN','color_mode':'POSITION','contrast':0.75,'factor_blue':2,'factor_green':2,'factor_red':2,'intensity':0.17,'minkovsky_exponent':10,'noise_intensity':1.6,'saturation':0,'use_clamp':True,'noise_scale':0.25,'weight_1':1,'weight_2':0.1,'weight_3':0,'weight_4':0,'use_color_ramp':False,}),
        #     "rgb_cloud":   ("RGB Cloud",      "W_DTXT_RGB_CLOUD",   {'type':'CLOUDS','noise_type':'SOFT_NOISE','noise_basis':'BLENDER_ORIGINAL','cloud_type':'COLOR','contrast':4.8,'factor_blue':2,'factor_green':2,'factor_red':2,'saturation':2,'intensity':0.25,'use_clamp':True,'noise_depth':2,'noise_scale':0.2,'use_color_ramp':False,}),
        #     "rgb_tiger":   ("RGB Tiger",      "W_DTXT_RGB_TIGER",   {'type':'MUSGRAVE','musgrave_type':'RIDGED_MULTIFRACTAL','noise_basis':'ORIGINAL_PERLIN','contrast':0.5,'dimension_max':1,'factor_blue':1,'factor_green':1,'factor_red':1,'gain':1,'intensity':1,'noise_intensity':1,'saturation':1,'use_clamp':True,'noise_scale':0.2,'octaves':2,'offset':1,'use_color_ramp':True,'s_colorramp_elements':[(0,[0,1,0,1]),(0.4,[0,0,1,1]),(0.7,[1,0,0,1])],'s_colorramp_interpolation':'CONSTANT',}),
        #     "rgb_camo":    ("RGB Camo",       "W_DTXT_RGB_CAMO",    {'type':'STUCCI','noise_basis':'ORIGINAL_PERLIN','stucci_type':'WALL_OUT','noise_type':'SOFT_NOISE','use_clamp':True,'contrast':1,'factor_blue':1,'saturation':1,'turbulence':7,'factor_green':1,'factor_red':1,'intensity':1,'noise_scale':0.1,'use_color_ramp':True,'s_colorramp_interpolation':'CONSTANT','s_colorramp_elements':[(0,[1,0,0,1]),(0.34,[0,1,0,1]),(0.60,[0,0,1,1])],}),
        #     "rgb_magic":   ("RGB Magic",      "W_DTXT_RGB_MAGIC",   {'type':'MAGIC','contrast':1,'factor_blue':1,'factor_green':1,'factor_red':1,'intensity':1,'saturation':1,'turbulence':9,'use_clamp':True,'noise_depth':0,'use_color_ramp':True,'s_colorramp_interpolation':'CONSTANT','s_colorramp_elements':[(0,[0.01,0,1,1]),(0.3985,[1,0,0,1]),(0.5707,[0,0,0,1]),(0.685,[0.008,1,0,1])],}),
        #     "rgb_voronoi": ("RGB Voronoi",    "W_DTXT_RGB_VORONOI", {'type':'VORONOI','color_mode':'POSITION_OUTLINE','distance_metric':'MINKOVSKY','contrast':1,'factor_blue':1,'factor_green':1,'factor_red':1,'intensity':1,'weight_1':1,'weight_2':0,'weight_3':0,'weight_4':0,'saturation':1,'use_clamp':True,'minkovsky_exponent':3,'noise_intensity':1.39,'noise_scale':0.35,'use_color_ramp':True,'s_colorramp_interpolation':'CONSTANT','s_colorramp_elements':[(0.0,[0.01,0,1,1]),(0.37,[0.008,1,0,1]),(0.563,[1,0,0,1]),(0.831,[0,0,0,1])],}),
        #     "rgb_pixel":   ("RGB Pixel",      "W_DTXT_RGB_PIXEL",   {'type':'STUCCI','noise_basis':'CELL_NOISE','noise_type':'SOFT_NOISE','stucci_type':'WALL_OUT','contrast':1,'factor_blue':1,'factor_green':1,'factor_red':1,'saturation':1,'turbulence':7,'use_clamp':True,'intensity':1,'noise_scale':0.2,'use_color_ramp':True,'s_colorramp_elements':[(0.0,[1,0,0,1]),(0.34,[0,1,0,1]),(0.66,[0,0,1,1])],'s_colorramp_interpolation':'CONSTANT',}),
        #     "rgb_curvy":   ("RGB Curvy",      "W_DTXT_RGB_CURVY",   {'type':'MARBLE','noise_type':'SOFT_NOISE','noise_basis':'ORIGINAL_PERLIN','noise_basis_2':'SIN','marble_type':'SHARP','contrast':0.75,'factor_blue':1,'factor_green':1,'factor_red':1,'intensity':0.9,'noise_depth':0,'noise_scale':0.6,'saturation':1,'turbulence':12.25,'use_clamp':True,'use_color_ramp':True,'s_colorramp_interpolation':'CONSTANT','s_colorramp_elements':[(0,[0,1,0,1]),(0.33,[0,0,1,1]),(0.68,[1,0,0,1])],},),
        #     "id_abstract": ("Id Abstract",    "W_DTXT_ID_ABSTRACT", {'type':'DISTORTED_NOISE','noise_basis':'CELL_NOISE','noise_distortion':'ORIGINAL_PERLIN','contrast':0.97,'distortion':1.7,'factor_blue':1,'factor_green':1,'factor_red':1,'intensity':1.3,'noise_scale':0.5,'saturation':1,'use_clamp':True,'use_color_ramp':True,'s_colorramp_elements':[(0,[0.685,0,0.656,1]),(0.038,[0.0,0.748,0.748,1]),(0.175,[1,0.423,0.0,1]),(0.319,[0.0102,0.1399,1,1]),(0.5512,[0.527,0.018,0.0,1]),(0.8564,[0.008,0.559,0.0,1])],'s_colorramp_interpolation':'CONSTANT',}),
        #     "id_lava":     ("Id Lava",        "W_DTXT_ID_LAVA",     {'type':'MUSGRAVE','musgrave_type':'MULTIFRACTAL','noise_basis':'ORIGINAL_PERLIN','contrast':0.91,'dimension_max':1,'factor_blue':1,'factor_green':1,'factor_red':1,'gain':1,'intensity':0.89,'noise_intensity':0.57,'noise_scale':0.26,'octaves':2.56,'offset':1,'saturation':1,'use_clamp':True,'use_color_ramp':True,'s_colorramp_elements':[(0,[0.685,0,0.656,1]),(0.014,[0,0.748,0.748,1]),(0.175,[1,0.423,0,1]),(0.435,[0.010,0.139,1,1]),(0.685,[0.527,0.018,0,1]),(0.955,[0.008,0.559,0,1])],'s_colorramp_interpolation':'CONSTANT',}),
        #     "id_marble":   ("Id Marble",      "W_DTXT_ID_MARBLE",   {'type':'MARBLE','marble_type':'SOFT','noise_basis':'ORIGINAL_PERLIN','noise_basis_2':'SIN','noise_type':'SOFT_NOISE','contrast':1,'factor_blue':1,'factor_green':1,'factor_red':1,'intensity':1,'noise_depth':24,'noise_scale':0.6,'saturation':1,'turbulence':13,'use_clamp':True,'use_color_ramp':True,'s_colorramp_elements':[(0,[0.685,0,0.656,1]),(0.038,[0.0,0.748,0.748,1]),(0.1757,[1,0.4231,0.0,1]),(0.367,[0.0102,0.1399,1,1]),(0.6736,[0.527,0.018,0.0,1]),(0.94,[0.008,0.559,0.0,1])],'s_colorramp_interpolation':'CONSTANT',}),
        #     "flow_lava":   ("Flowmap Lava",   "W_DTXT_FLOW_LAVA",   {'type':'CLOUDS','noise_basis':'BLENDER_ORIGINAL','noise_type':'HARD_NOISE','contrast':1,'saturation':1,'factor_blue':1,'factor_green':1,'factor_red':1,'intensity':1,'noise_depth':0,'noise_scale':0.5,'use_clamp':True,'use_color_ramp':True,'s_colorramp_interpolation':'LINEAR','s_colorramp_elements':[ (0,[1,0,0,1]),(0.310843348,[0,0,0,1]),(0.62,[0,0.5,0.008051,1]),(0.8,[0.8349971,1,0.029547309,1])],}),
        #     "flow_bubble": ("Flowmap Bubble", "W_DTXT_FLOW_BUBBLE", {'type':'CLOUDS','noise_basis':'VORONOI_F1','noise_type':'SOFT_NOISE','contrast':1,'saturation':1,'factor_blue':1,'factor_green':1,'factor_red':1,'intensity':1.13,'noise_depth':0,'noise_scale':0.5,'use_color_ramp':True,'s_colorramp_interpolation':'LINEAR','s_colorramp_elements':[(0,[1,0.21,0.02,1]),(0.26,[1,0,0,1]),(0.61,[0,0,0,1]),(1,[0.06,1,0.015,1.0])],'use_clamp':True,}),
        #     "flow_blue":   ("Flowmap Blue",   "W_DTXT_FLOW_BLUE",   {'type':'VORONOI','distance_metric':'DISTANCE_SQUARED','minkovsky_exponent':2.5,'color_mode':'INTENSITY','noise_scale':0.7,'contrast':1,'factor_blue':1,'factor_green':1,'factor_red':1,'intensity':1,'saturation':1,'noise_intensity':1.3,'use_clamp':True,'use_preview_alpha':False,'weight_1':1,'weight_2':0,'weight_3':0,'weight_4':0,'use_color_ramp':True,'s_colorramp_elements':[(0.09,[0,0,0,1]),(0.16,[0,0,0.59,1]),(0.53,[0,0.5,1,1]),(1,[0.5,1,1,1])],'s_colorramp_interpolation':'LINEAR',}),
        #     }

        # return {'FINISHED'}


class SCATTER5_OT_scatter_texture_transforms(bpy.types.Operator):

    bl_idname      = "scatter5.scatter_texture_transforms"
    bl_label       = ""
    bl_description = translate("Randomize this transform")

    transform : bpy.props.StringProperty() #enum in "loc/rot/sca"
    ng_name : bpy.props.StringProperty()

    def execute(self, context):

        ng = bpy.data.node_groups.get(self.ng_name)
        if ng is None: 
            return {'FINISHED'}

        node_props = ng.scatter5.texture

        if (self.transform == "loc"):
            node_props.mapping_location = [random.uniform(0,999), random.uniform(0,999) , random.uniform(0,999) ]
            return {'FINISHED'}

        elif (self.transform == "rot"):
            node_props.mapping_rotation = [random.uniform(0,6.28), random.uniform(0,6.28), random.uniform(0,6.28) ]
            return {'FINISHED'}

        elif (self.transform == "sca"):
            r = random.uniform(0.05,2)
            node_props.mapping_scale = [r,r,r]
            return {'FINISHED'}

        return {'FINISHED'}


# oooooooooo.                                        o8o
# `888'   `Y8b                                       `"'
#  888      888 oooo d8b  .oooo.   oooo oooo    ooo oooo  ooo. .oo.    .oooooooo
#  888      888 `888""8P `P  )88b   `88. `88.  .8'  `888  `888P"Y88b  888' `88b
#  888      888  888      .oP"888    `88..]88..8'    888   888   888  888   888
#  888     d88'  888     d8(  888     `888'`888'     888   888   888  `88bod8P'
# o888bood8P'   d888b    `Y888""8o     `8'  `8'     o888o o888o o888o `8oooooo.
#                                                                     d"     YD
#                                                                     "Y88888P'


class SCATTER5_PT_scatter_texture(bpy.types.Panel):

    bl_idname      = "SCATTER5_PT_scatter_texture"
    bl_label       = ""
    bl_category    = ""
    bl_space_type  = "VIEW_3D"
    bl_region_type = "HEADER" #Hide this panel? not sure how to hide them...
    #bl_options     = {"DRAW_BOX"}

    def draw(self, context):

        layout = self.layout

        emitter = bpy.context.scene.scatter5.emitter
        ng = context.PTR_ng
        psy = context.PTR_psy
        node_props = ng.scatter5.texture      

        element = layout.column(align=True)
        lbl = element.row(align=True)
        lbl.label(text=translate("Texture-Settings:"),)
        element.prop(node_props, "texture_type",text="")
        element.separator(factor=0.5)

        if (node_props.texture_type=="brick_"):

            props = element.column(align=True)
            props.scale_y = 0.85
            props.prop(node_props, "scale")
            element.separator(factor=0.5)
            props = element.column(align=True)
            props.scale_y = 0.85
            props.prop(node_props, "brick_offset")
            props.prop(node_props, "brick_offset_frequency")
            props.prop(node_props, "brick_squash")
            props.prop(node_props, "brick_squash_frequency")
            element.separator(factor=0.5)
            props = element.column(align=True)
            props.scale_y = 0.85
            props.prop(node_props, "brick_mortar_size")
            props.prop(node_props, "brick_mortar_smooth")
            props.prop(node_props, "brick_bias")
            props.prop(node_props, "brick_width")
            props.prop(node_props, "brick_row_height")

        elif (node_props.texture_type=="checker_"):

            props = element.column(align=True)
            props.scale_y = 0.85
            props.prop(node_props, "scale")

        elif (node_props.texture_type=="image_"):

            props = element.column(align=True)
            props.scale_y = 0.85
            props.prop(node_props, "image_interpolation", text="")
            props.prop(node_props, "image_extension", text="")

            element.separator(factor=0.5)

            props = element.column(align=True)
            props.scale_y = 0.85
            props.template_ID(node_props, "image_ptr", open="image.open")

            element.separator(factor=0.5)

            props = element.column(align=True)
            props.scale_y = 0.85
            img_op = props.row(align=True)    
            op = img_op.operator("scatter5.bitmap_draw_menu", text=translate("Image Library"), icon="ASSET_MANAGER")
            op.ng_name=ng.name
            op = img_op.operator("scatter5.bitmap_skip", text="", icon="TRIA_LEFT", )
            op.ng_name=ng.name
            op.option="left"
            op = img_op.operator("scatter5.bitmap_skip", text="", icon="TRIA_RIGHT", )
            op.ng_name=ng.name
            op.option="right"
            op = img_op.operator("scatter5.bitmap_skip", text="", icon_value=cust_icon("W_DICE"), )
            op.ng_name=ng.name
            op.option="random"

            props = element.column(align=True)
            props.scale_y = 0.85
            props.prop(node_props, "scale")

            #frame needed? 
            #element.separator(factor=0.5)
            #element.prop(node_props, "image_frame")

        elif (node_props.texture_type=="magic_"):

            element.prop(node_props, "out_type",text="")
            element.separator(factor=0.5)
            props = element.column(align=True)
            props.scale_y = 0.85
            props.prop(node_props, "scale")
            props.prop(node_props, "magic_turbulence_depth")
            props.prop(node_props, "distorsion")

        elif (node_props.texture_type=="musgrave_"):

            element.prop(node_props, "musgrave_musgrave_type",text="")
            element.separator(factor=0.5)
            props = element.column(align=True)
            props.scale_y = 0.85
            props.prop(node_props, "scale")
            props.prop(node_props, "detail")
            if node_props.musgrave_musgrave_type!="FBM":
                props.prop(node_props, "musgrave_offset")

        elif (node_props.texture_type=="noise_"):

            element.prop(node_props, "out_type",text="")
            element.separator(factor=0.5)
            props = element.column(align=True)
            props.scale_y = 0.85
            props.prop(node_props, "scale")
            props.prop(node_props, "detail")
            props.prop(node_props, "noise_roughness")
            props.prop(node_props, "distorsion")

        elif (node_props.texture_type=="voronoi_"):

            element.prop(node_props, "voronoi_feature", text="")
            element.prop(node_props, "voronoi_distance", text="")
            element.prop(node_props, "out_type",text="")
            element.separator(factor=0.5)
            props = element.column(align=True)
            props.scale_y = 0.85
            props.prop(node_props, "scale")
            if node_props.voronoi_distance == "MINKOWSKI":
                props.prop(node_props, "voronoi_exponent")
            props.prop(node_props, "voronoi_randomness")

        elif (node_props.texture_type=="wave_"):
            
            element.prop(node_props,"wave_wave_type", text="")
            element.prop(node_props,"wave_bands_direction", text="")
            element.prop(node_props,"wave_wave_profile", text="")
            element.separator(factor=0.5)
            props = element.column(align=True)
            props.scale_y = 0.85
            props.prop(node_props,"scale")
            props.prop(node_props,"detail")
            props.prop(node_props,"distorsion")
            props.separator(factor=0.5)
            props = element.column(align=True)
            props.scale_y = 0.85
            props.prop(node_props,"wave_detail_scale")
            props.prop(node_props,"wave_detail_roughness")
            props.prop(node_props,"wave_phase_offset")

        elif (node_props.texture_type=="white_noise_"):

            element.prop(node_props, "out_type",text="")

        element = layout.column(align=True)
        lbl = element.row(align=True)
        lbl.label(text=translate("Color-Adjustments:"),)

        props = element.column(align=True)
        props.scale_y = 0.85
        props.prop(node_props, "intensity",)
        props.prop(node_props, "contrast",)
        props.prop(node_props, "saturation",)
        props.prop(node_props, "jitter",)

        element = layout.column(align=True)
        lbl = element.row(align=True)
        lbl.scale_y = 0.8
        lbl.label(text=translate("Color-Ramp:"),)

        clramp = element.column(align=True)
        clramp.prop(node_props, "use_color_ramp",icon="SNAP_INCREMENT")
        if node_props.use_color_ramp:
            cr = clramp.column()
            cr.scale_y = 0.7
            cr.separator()
            cr.box().template_color_ramp(ng.nodes["ColorRamp"], "color_ramp", expand=True)
            clramp.separator()

        element = layout.column(align=True)
        lbl = element.row(align=True)
        lbl.label(text="Mapping:")

        element.prop(node_props, "mapping_projection",text="")
        if node_props.mapping_projection=="uv":
            element.prop_search(node_props, "mapping_uv_ptr", emitter.data, "uv_layers", text="")

        element = layout.column(align=True)
        lbl = element.row(align=True)
        lbl.label(text=translate("Location/Rotation/Scale:"),)

        matrix = element.row(align=True)
        matrix.scale_y = 0.85
        matrix1 = matrix.column(align=True)
        matrix1.prop(node_props, "mapping_location", text="")
        op = matrix1.operator("scatter5.scatter_texture_transforms",text="",icon_value=cust_icon("W_DICE"),)
        op.ng_name = ng.name
        op.transform = "loc"
        matrix2 = matrix.column(align=True)
        matrix2.prop(node_props, "mapping_rotation", text="")
        op = matrix2.operator("scatter5.scatter_texture_transforms",text="",icon_value=cust_icon("W_DICE"),)
        op.ng_name = ng.name
        op.transform = "rot"
        matrix3 = matrix.column(align=True)
        matrix3.prop(node_props, "mapping_scale", text="")
        op = matrix3.operator("scatter5.scatter_texture_transforms",text="",icon_value=cust_icon("W_DICE"),)
        op.ng_name = ng.name
        op.transform = "sca"

        element = layout.column(align=True)
        lbl = element.row(align=True)
        lbl.label(text=translate("Visualizer:"),)
        op = element.operator("scatter5.scatter_texture_visualizer",text="Visualize with Vertex-Color", icon="VPAINT_HLT", depress=("ScatterVisualizer" in emitter.modifiers and emitter.modifiers["ScatterVisualizer"].node_group.nodes["TEXTURE_NODE visualizer"].node_tree==ng))
        op.scatter_texture_name = ng.name

        return None 


def draw_texture_datablock(layout, psy=None, ptr_name="", texture_node=None, new_name=""):
    """draw texture datablock"""

    ng = texture_node.node_tree

    tex_column = layout.column(align=True)

    #custom data row 

    data_row = tex_column.row(align=True)

    enum = data_row.row(align=True)
    enum.alignment = "LEFT"
    enum.scale_x = 0.91
    enum.context_pointer_set("PTR_psy",psy)
    enum.context_pointer_set("PTR_texture_node", texture_node) 
    op = enum.operator_menu_enum("SCATTER5_OT_scatter_texture_enum", "enum", text=" ", icon="NODE_TEXTURE")
    op.ptr_name = ptr_name

    #new ? should never use this, it should always be full

    if (ng.name == ".TEXTURE *DEFAULT*"): 
        
        ope = data_row.row(align=True)
        ope.context_pointer_set("PTR_psy",psy)
        ope.context_pointer_set("PTR_texture_node", texture_node)
        op = ope.operator("scatter5.scatter_texture_new", text=translate("New"), icon="ADD")
        op.ptr_name = ptr_name
        op.new_name = new_name
        
        return None 

    #name operator, special behavior that check if name not in double & will change the node_tree name accordingly

    text = data_row.row(align=True)
    text.prop(ng.scatter5.texture,"user_name", text="")

    #copy operator if ng has multiple users? 

    if (ng.users!=1):

        ope = data_row.row(align=True)
        ope.alignment = "RIGHT"
        ope.scale_x = 0.7
        ope.context_pointer_set("PTR_psy",psy)
        ope.context_pointer_set("PTR_texture_node", texture_node)
        op = ope.operator("scatter5.scatter_texture_duppli", text=str(ng.users),)
        op.ptr_name = ptr_name

    #settings panel

    panel = data_row.row(align=True)
    panel.context_pointer_set("PTR_ng",ng)
    panel.context_pointer_set("PTR_psy",psy)
    panel.popover(panel="SCATTER5_PT_scatter_texture",text="", icon="OPTIONS",)

    return 


# oooooo     oooo  o8o                                            oooo   o8o
#  `888.     .8'   `"'                                            `888   `"'
#   `888.   .8'   oooo   .oooo.o oooo  oooo    oooooooo  .oooo.    888  oooo    oooooooo  .ooooo.  oooo d8b
#    `888. .8'    `888  d88(  "8 `888  `888   d'""7d8P  `P  )88b   888  `888   d'""7d8P  d88' `88b `888""8P
#     `888.8'      888  `"Y88b.   888   888     .d8P'    .oP"888   888   888     .d8P'   888ooo888  888
#      `888'       888  o.  )88b  888   888   .d8P'  .P d8(  888   888   888   .d8P'  .P 888    .o  888
#       `8'       o888o 8""888P'  `V88V"V8P' d8888888P  `Y888""8o o888o o888o d8888888P  `Y8bod8P' d888b


class SCATTER5_OT_scatter_texture_visualizer(bpy.types.Operator):

    bl_idname = "scatter5.scatter_texture_visualizer"
    bl_label = ""
    bl_description = translate("Visualize the texture on your mesh vertices with the help of vertex-color")
    bl_options = {'REGISTER'}

    scatter_texture_name : bpy.props.StringProperty()

    def __init__(self):
        self.old_active = ""

    def invoke(self, context, event):

        emitter = bpy.context.scene.scatter5.emitter
        bpy.context.view_layer.objects.active = emitter

        #user is dummy? do not understand what are vertex-colors
        if (len(emitter.data.vertices)<100):
            bpy.ops.scatter5.popup_menu(msgs=translate("This Feature will visualize the points texture via your emitter vertex-colors.\nYou need more vertices in order to visualize the result more clearly."),title=translate("Your emitter does not have enough vertices"),icon="INFO")
            return {'CANCELLED'}

        #user is trying to re-enter mode again? 
        mod = emitter.modifiers.get("ScatterVisualizer")
        if (mod is not None):
            self.cancel(context)

        #add new vertex color 
        if emitter.data.vertex_colors.active:
            self.old_active = emitter.data.vertex_colors.active.name
        if len(emitter.data.vertex_colors)<8:
            emitter.data.vertex_colors.new(name="ScatterVisualizer")
        vcol = emitter.data.vertex_colors[-1] #forced to do this because number of vcol slot is limited
        emitter.data.vertex_colors.active = vcol

        ng = bpy.data.node_groups.get(self.scatter_texture_name)

        #add geonode modifier and set up settings
        mod = import_and_add_geonode( emitter, mod_name="ScatterVisualizer", node_name=".ScatterVisualizer", blend_path=directories.addon_visualizer, copy=False,)
        mod["Input_2_use_attribute"] = True
        mod["Input_2_attribute_name"] = ng.scatter5.texture.mapping_uv_ptr

        mod["Output_3_attribute_name"] = vcol.name
        mod.node_group.nodes["emitter"].inputs[0].default_value = emitter
        mod.node_group.nodes["TEXTURE_NODE visualizer"].node_tree = ng
        self.mod_name = mod.name

        #go in vcol
        bpy.ops.object.mode_set(mode="VERTEX_PAINT")

        #add indication on screen
        add_font(text=translate("Visualizing")+f" '{self.scatter_texture_name.replace('.TEXTURE ','')}'", size=[40,50], position=[20,60], color=[1,1,1,0.9], origin="BOTTOM LEFT", shadow={"blur":3,"color":[0,0,0,0.6],"offset":[2,-2],})
        add_font(text=translate("Quit Vertex-Paint to Stop"), size=[40,50], position=[20,20], color=[1,1,1,0.9], origin="BOTTOM LEFT", shadow={"blur":3,"color":[0,0,0,0.6],"offset":[2,-2],})
        
        #start modal 
        context.window_manager.modal_handler_add(self)  

        return {'RUNNING_MODAL'}

    def modal(self, context, event):

        if (context.mode!="PAINT_VERTEX"):
            self.cancel(context)
            return {'CANCELLED'}

        return {'PASS_THROUGH'}

    def cancel(self, context):

        emitter = bpy.context.scene.scatter5.emitter

        #remove screen indication 
        clear_all_fonts()

        #remove modifier 
        mod = emitter.modifiers.get("ScatterVisualizer")
        if (mod is not None):
            mod.node_group.nodes["TEXTURE_NODE visualizer"].node_tree = None
            emitter.modifiers.remove(mod)

        #remove vertex-color
        vcol = emitter.data.vertex_colors.get("ScatterVisualizer")
        if (vcol is not None):
            emitter.data.vertex_colors.remove(vcol)
        if (self.old_active!=""):
            emitter.data.vertex_colors.active = emitter.data.vertex_colors[self.old_active]

        return None 


# ooooooooo.                         o8o               .
# `888   `Y88.                       `"'             .o8
#  888   .d88'  .ooooo.   .oooooooo oooo   .oooo.o .o888oo  .ooooo.  oooo d8b
#  888ooo88P'  d88' `88b 888' `88b  `888  d88(  "8   888   d88' `88b `888""8P
#  888`88b.    888ooo888 888   888   888  `"Y88b.    888   888ooo888  888
#  888  `88b.  888    .o `88bod8P'   888  o.  )88b   888 . 888    .o  888
# o888o  o888o `Y8bod8P' `8oooooo.  o888o 8""888P'   "888" `Y8bod8P' d888b
#                        d"     YD
#                        "Y88888P'


classes = [
    
    SCATTER5_PT_scatter_texture,

    SCATTER5_OT_scatter_texture_new,
    SCATTER5_OT_scatter_texture_enum,
    SCATTER5_OT_scatter_texture_duppli,
    #SCATTER5_OT_scatter_texture_preset,
    SCATTER5_OT_scatter_texture_transforms,

    SCATTER5_OT_scatter_texture_visualizer,

    ]


def register():

    for cls in classes:
        bpy.utils.register_class(cls)

    return 

def unregister():

    del bpy.types.NodeTree.scatter5
    
    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)

    return 