import bpy
from .. import world as wd
from ..constants import addon_name
from ..ui import library
from bpy.types import PropertyGroup
from bpy.props import (BoolProperty,
                       FloatProperty,
                       FloatVectorProperty,
                       EnumProperty,
                       IntProperty,
                       StringProperty,
                       )

CAMERAS = []

def update_comp_exposure(self,context):
    if self.comp_exposure:
        bpy.ops.photographer.add_exposure_node()
    else:
        bpy.ops.photographer.disable_exposure_node()

def update_active_camera_index(self, context):
	context.scene.photographer.active_camera_index = -1

def camera_items(self,context):
    global CAMERAS
    CAMERAS = []
    camera_objs = [o for o in bpy.context.scene.objects if o.type=='CAMERA']
    for cam in camera_objs:
        CAMERAS.append((cam.name,cam.name,''))
    return CAMERAS

def update_active_scene_camera(self,context):
    if self.active_scene_camera:
        bpy.ops.mastercamera.look_through(camera = self.active_scene_camera)

class SceneSettings(PropertyGroup):
    cam_list_sorting : EnumProperty(
        name = "Sorting options for Camera list",
        items = [('ALPHA','Sort Alphabetically','','CAMERA_DATA',0),
                ('COLLECTION','Group by Collection','','OUTLINER_OB_GROUP_INSTANCE',1)],
        options = {'HIDDEN'},
        # default = bpy.context.preferences.addons[addon_name].preferences.default_cam_list_sorting,
    )
    comp_exposure : BoolProperty(
        name = "Apply at Compositing",
        description = ("Apply Exposure during Compositing. \nExposure won't be "
                        "visible in viewport, but will be applied to EXR files"),
        default = False,
        options = {'HIDDEN'},
        update = update_comp_exposure,
    )
    active_view_layer_index: IntProperty(
        default=-1,
    )
    active_camera_index: IntProperty(
        default=-1,
        update=update_active_camera_index,
    )
    active_scene_camera: bpy.props.EnumProperty(
        name="Scene Camera",
        items = camera_items,
        options = {'HIDDEN'},
        update = update_active_scene_camera,
    )
    cam_filter : StringProperty(
        name="Filter",
        description="Filter by name",
    )
    cam_filter_reverse : BoolProperty(
        name="Reverse Order",
        description="Reverse Sorting order",
        default = False,
    )   

class LightMixerSettings(PropertyGroup):
    solo_active: BoolProperty(
        name="Solo",
        default=False,
        options = {'HIDDEN'},
    )
    world_show_more: BoolProperty(
        name="Expand World settings",
        default=True,
        options = {'HIDDEN'},
    )
    show_active_light : BoolProperty(
        name="Active Light properties",
        default=True,
    )

    hdri_tex: EnumProperty(
        name="HDRI Texture",
        items=wd.enum_previews_hdri_tex,
        update=wd.update_hdri_tex,
    )
    hdri_category: EnumProperty(
        name="HDRI Category",
        items=library.subfolders_return,
        description="HDRI Subfolder category",
        update=wd.update_hdri_tex,
    )
    hdri_rotation: FloatProperty(
        name="Rotation",
        default=0, soft_min=-3.141593, soft_max=3.141593, unit='ROTATION',
        get=wd.get_hdri_rotation,
        set=wd.set_hdri_rotation,
    )
    hdri_use_temperature: BoolProperty(
        name="Use Color Temperature",
        default=True,
        options = {'HIDDEN'},
        update = wd.update_hdri_use_temperature,
    )
    hdri_temperature: FloatProperty(
        name="Temperature",
        default=6500, min=0, soft_min=1100, soft_max=13000,
        get=wd.get_hdri_temperature,
        set=wd.set_hdri_temperature,
    )
    hdri_tint: FloatProperty(
        name="Tint",
        default=0, min=-100, max=100,
        get=wd.get_hdri_tint,
        set=wd.set_hdri_tint,
    )
    hdri_color: FloatVectorProperty(
        name="Color Multiplier",
        subtype='COLOR',
        min=0.0, max=1.0, size=4,
        default=(1.0,1.0,1.0,1.0),
        get=wd.get_hdri_color,
        set=wd.set_hdri_color,
    )
    hdri_blur: FloatProperty(
        name="Blur",
        default=0, min=0, soft_max=1,
        get=wd.get_hdri_blur,
        set=wd.set_hdri_blur,
    )
