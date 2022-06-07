import bpy
import math

from . import bokeh, camera_sensors
from .functions import calc_exposure_value, shutter_speed_to_angle
from .autofocus import stop_playback, focus_continuous
from .white_balance import convert_RBG_to_whitebalance, convert_temperature_to_RGB_table
from .sampling_threshold import update_light_threshold, check_light_threshold
from .ui.library import previews_register,previews_unregister
from .world import get_environment_tex, enum_previews_hdri_tex
from .operators.exposure import get_exposure_node
from .constants import base_ev

# Default variables
min_color_temperature = 1800
max_color_temperature = 14000
default_color_temperature = 6500
min_color_tint = -100
max_color_tint = 100
default_tint = 0
stored_cm_view_transform = 'Filmic'
eevee_soft_shadows = False
stored_lens_shift = 0

#Camera Exposure update functions ##############################################################

def update_settings(self,context):
    if context.scene.camera:
        settings = context.scene.camera.data.photographer

        if bpy.context.scene.render.engine == 'LUXCORE':
            tonemapper = context.scene.camera.data.luxcore.imagepipeline.tonemapper

            if settings.exposure_enabled:
                tonemapper.enabled = True
                tonemapper.type = 'TONEMAP_LINEAR'
                tonemapper.linear_scale = 0.001464 #1/683
                tonemapper.use_autolinear = False

        if settings.exposure_enabled:
            update_aperture(self, context)
            update_shutter_speed(self, context)
            update_shutter_angle(self, context)
            update_falsecolor(self,context)

        elif settings.exposure_enabled == False:
            if context.scene.photographer.comp_exposure:
                exp = get_exposure_node(self,context)
                exp.inputs['Exposure'] = 0
            else:
                context.scene.view_settings.exposure = 0

        if context.scene.camera.data.dof.focus_distance == 0:
            context.scene.camera.data.dof.focus_distance = 3

        if settings.resolution_enabled:
            update_resolution(settings,context)

        if context.scene.view_settings.use_curve_mapping:
            settings.color_temperature = settings.color_temperature
            settings.tint = settings.tint

        if settings.override_world:
            update_world(settings,context)

        if settings.override_frames:
            update_frames(settings,context)

# Update EV
def update_ev(self,context):
    settings = context.scene.camera.data.photographer

    if settings.exposure_enabled:
        EV = calc_exposure_value(self,context,settings)

        bl_exposure = -EV + base_ev

        aces_ue_match = bpy.context.preferences.addons[__package__].preferences.aces_ue_match
        display_device = context.scene.display_settings.display_device
        view_transform = context.scene.view_settings.view_transform
        if aces_ue_match and display_device == 'ACES' and view_transform != 'Raw':
            # Blender ACES is darker than Unreal ACES which has specific modifications. Brighness difference supposedly 1.45.
            bl_exposure += 0.536 # 2^0.536 = 1.45

        bl_exposure -= math.log2(0.78/bpy.context.preferences.addons[__package__].preferences.lens_attenuation)

        if context.scene.photographer.comp_exposure:
            context.scene.view_settings.exposure = 0
            exp = get_exposure_node(self,context)
            exp.inputs['Exposure'].default_value = bl_exposure
        else:
            context.scene.view_settings.exposure = bl_exposure

        # Updating Light Sampling Threshold when Exposure changes if Auto
        if bpy.context.preferences.addons[__package__].preferences.auto_light_threshold:
            update_light_threshold(self,context)

        # Setting Warning Light Threshold
        else:
            if not bpy.context.preferences.addons[__package__].preferences.hide_light_threshold_warning:
                check_light_threshold(self,context)

def get_ev(self):
    default_ev =  base_ev - math.log2(0.78 / bpy.context.preferences.addons[__package__].preferences.lens_attenuation)
    return self.get('ev',  default_ev)

def set_ev(self,value):
    self['ev'] = value
    update_ev(self,bpy.context)
    return None

def get_exposure_compensation(self):
    return self.get('exposure_compensation',  0)

def set_exposure_compensation(self,value):
    self['exposure_compensation'] = value
    update_ev(self,bpy.context)
    return None

def get_ae(self):
    return self.get('ae',  0)

def set_ae(self,value):
    self['ae'] = value
    self.ev = base_ev - value
    update_ev(self,bpy.context)
    return None

# Update Aperture
def update_aperture(self, context):
    settings = context.scene.camera.data.photographer

    use_dof = context.scene.camera.data.dof.use_dof

    if use_dof :
        if not settings.aperture_slider_enable:
            context.scene.camera.data.dof.aperture_fstop = float(settings.aperture_preset) * context.scene.unit_settings.scale_length
        else:
            context.scene.camera.data.dof.aperture_fstop = settings.aperture * context.scene.unit_settings.scale_length

    update_ev(self, context)

def get_aperture(self):
    return self.get('aperture',  2.4)

def set_aperture(self,value):
    self['aperture'] = value
    update_aperture(self,bpy.context)
    return None

def get_aperture_preset(self):
    return self.get('aperture_preset',  6)

def set_aperture_preset(self,value):
    self['aperture_preset'] = value
    update_aperture(self,bpy.context)
    return None

# Update Shutter Speed
def update_shutter_speed(self,context):
    scene = context.scene
    settings = scene.camera.data.photographer

    if settings.shutter_mode == 'SPEED':
        fps = scene.render.fps / scene.render.fps_base

        if settings.motionblur_enabled:
            if scene.render.engine == 'CYCLES':
                scene.render.motion_blur_shutter = shutter_speed_to_angle(self,context,settings) / 360
            elif scene.render.engine == 'BLENDER_EEVEE':
                scene.eevee.motion_blur_shutter = shutter_speed_to_angle(self,context,settings) / 360

    if settings.exposure_mode == 'MANUAL':
        update_ev(self, context)


def get_shutter_speed(self):
    return self.get('shutter_speed', 100)

def set_shutter_speed(self,value):
    self['shutter_speed'] = value
    update_shutter_speed(self,bpy.context)
    return None

def get_shutter_speed_preset(self):
    return self.get('shutter_speed_preset',  35)

def set_shutter_speed_preset(self,value):
    self['shutter_speed_preset'] = value
    update_shutter_speed(self,bpy.context)
    return None

# Update Shutter Angle
def update_shutter_angle(self,context):
    scene = context.scene
    settings = scene.camera.data.photographer

    if settings.shutter_mode == 'ANGLE':
        fps = scene.render.fps / scene.render.fps_base

        if not settings.shutter_speed_slider_enable:
            shutter_angle = float(settings.shutter_angle_preset)
        else:
            shutter_angle = settings.shutter_angle

        if settings.motionblur_enabled:
            if scene.render.engine == 'CYCLES':
                scene.render.motion_blur_shutter = shutter_angle / 360
            elif scene.render.engine == 'BLENDER_EEVEE':
                scene.eevee.motion_blur_shutter = shutter_angle / 360

    if settings.exposure_mode == 'MANUAL':
        update_ev(self, context)

def get_shutter_angle(self):
    return self.get('shutter_angle', 180)

def set_shutter_angle(self,value):
    self['shutter_angle'] = value
    update_shutter_angle(self,bpy.context)
    return None

def get_shutter_angle_preset(self):
    return self.get('shutter_angle_preset',  8)

def set_shutter_angle_preset(self,value):
    self['shutter_angle_preset'] = value
    update_shutter_angle(self,bpy.context)
    return None

# Update Iso
def get_iso(self):
    return self.get('iso', 100)

def set_iso(self,value):
    self['iso'] = value
    update_ev(self,bpy.context)
    return None

def get_iso_preset(self):
    return self.get('iso_preset', 0)

def set_iso_preset(self,value):
    self['iso_preset'] = value
    update_ev(self,bpy.context)
    return None

# Update Motion Blur
def get_motionblur_enabled(self):
    return self.get('motionblur_enabled', False)

def set_motionblur_enabled(self,value):
    self['motionblur_enabled'] = value
    update_settings(self,bpy.context)
    return None

# Update False Color
def update_falsecolor(self,context):
    settings = context.scene.camera.data.photographer

    if context.scene.view_settings.view_transform != 'False Color':
        global stored_cm_view_transform
        stored_cm_view_transform = context.scene.view_settings.view_transform

    if settings.falsecolor_enabled:
        context.scene.view_settings.view_transform = 'False Color'

    else:
        context.scene.view_settings.view_transform = stored_cm_view_transform

# Fisheye Functions
def update_fisheye(self,context):
    camera = self.id_data
    if self.fisheye and context.scene.render.engine == 'CYCLES':
        camera.type = 'PANO'
        camera.cycles.panorama_type == 'FISHEYE_EQUISOLID'
        self.fisheye_focal = camera.lens
    else:
        camera.type = 'PERSP'

    # Disable lens_shift for Fisheye lens (doesn't support lens shift)
    global stored_lens_shift
    if self.fisheye:
        stored_lens_shift = self.lens_shift
        self.lens_shift = 0
    else:
        self.lens_shift = stored_lens_shift

def get_fisheye_focal(self):
    return self.get('fisheye_focal', 50)

def set_fisheye_focal(self, value):
    self['fisheye_focal'] = value
    camera = self.id_data
    camera.cycles.fisheye_lens = value
    camera.lens = value

def get_focal(self):
    return self.id_data.lens
    # return self['focal']

def set_focal(self, value):
    camera = self.id_data
    if self.lens_shift != 0:
        obj = [o for o in bpy.data.objects if o.type == 'CAMERA' and o.data is camera]
        old_rot = obj[0].rotation_euler.x
        old_focal = self.focal
        old_atan = math.atan(self.lens_shift/(old_focal/36))
        rot = old_rot + old_atan
        self['focal'] = value
        atan = math.atan(self.lens_shift/(value/36))
        obj[0].rotation_euler.x = rot - atan
    else:
        self['focal'] = value
    camera.lens = value #+ (camera.dof.focus_distance * self.breathing/10)
    return None

def get_lens_shift(self):
    return self.get('lens_shift', 0)

def set_lens_shift(self, value):
    camera = self.id_data
    obj = [o for o in bpy.data.objects if o.type == 'CAMERA' and o.data is camera]
    old_rot = obj[0].rotation_euler.x
    old_vert_shift = self.lens_shift
    old_atan = math.atan(self.lens_shift/(camera.lens/36))
    rot = old_rot + old_atan
    self['lens_shift'] = value
    atan = math.atan(value/(camera.lens/36))
    camera.shift_y = value
    obj[0].rotation_euler.x = rot - atan

    return None

# def get_breathing(self):
#     return self.get('breathing', 0)
#
# def set_breathing(self, value):
#     camera = self.id_data
#     self['breathing'] = value
#     self.focal = self.focal
#     return None

# Update Resolution
def update_resolution(self,context):
    # resolution_x = 1920
    # resolution_y = 1080

    if self.resolution_mode == 'CUSTOM_RES':
        resolution_x = self.resolution_x
        resolution_y = self.resolution_y

    if self.resolution_mode == 'CUSTOM_RATIO' and self.ratio_x != 0:
        resolution_x = self.resolution_x
        resolution_y = self.resolution_x * (self.ratio_y / self.ratio_x)

    if self.resolution_mode == '11':
        resolution_x = self.longedge
        resolution_y = resolution_x

    if self.resolution_mode == '32':
        resolution_x = self.longedge
        resolution_y = (self.longedge/3)*2

    if self.resolution_mode == '43':
        resolution_x = self.longedge
        resolution_y = (self.longedge/4)*3

    if self.resolution_mode == '67':
        resolution_x = self.longedge
        resolution_y = (self.longedge/7)*6

    if self.resolution_mode == '169':
        resolution_x = self.longedge
        resolution_y = (self.longedge/16)*9

    if self.resolution_mode == '2351':
        resolution_x = self.longedge
        resolution_y = self.longedge/2.35

    if self.resolution_mode == '2391':
        resolution_x = self.longedge
        resolution_y = self.longedge/2.3864

    if self.resolution_rotation == 'LANDSCAPE':
        context.scene.render.resolution_x = resolution_x
        context.scene.render.resolution_y = resolution_y

    if self.resolution_rotation == 'PORTRAIT':
        context.scene.render.resolution_x = resolution_y
        context.scene.render.resolution_y = resolution_x

def update_resolution_enabled(self,context):
    # Get Blender resolution when enabling Photographer resolution
    resolution_x = context.scene.render.resolution_x
    resolution_y = context.scene.render.resolution_y

    if self.resolution_mode == 'CUSTOM_RES':
        if resolution_y >= resolution_x:
            self.resolution_rotation = 'PORTRAIT'
            self.resolution_x = resolution_y
            self.resolution_y = resolution_x
        else:
            self.resolution_rotation = 'LANDSCAPE'
            self.resolution_x = resolution_x
            self.resolution_y = resolution_y

    update_resolution(self,context)

# White Balance Functions
def get_wb_enabled(self):
    return bpy.context.scene.view_settings.use_curve_mapping

def set_wb_enabled(self,value):
    self['wb_enabled'] = value
    bpy.context.scene.view_settings.use_curve_mapping = value
    return None

def get_preview_color_temp(self):
    def_k = convert_temperature_to_RGB_table(default_color_temperature)
    # inverting
    def_k = (def_k[2],def_k[1],def_k[0])

    # Convert Temperature to Color
    white_balance_color = convert_temperature_to_RGB_table(self.color_temperature)
    # Set preview color in the UI - inverting red and blue channels
    self['preview_color_temp'] = (white_balance_color[2],white_balance_color[1],white_balance_color[0])
    return self.get('preview_color_temp', def_k)

def set_preview_color_temp(self,value):
    return None

def get_color_temperature(self):
    return self.get('color_temperature', default_color_temperature)

def set_color_temperature(self, value):
    # Convert Temperature to Color
    self['color_temperature'] = value
    white_balance_color = convert_temperature_to_RGB_table(self.color_temperature)

    # if context.scene.camera == context.view_layer.objects.active:
        # Calculate Curves values from color - ignoring green which is set by the Tint
    red = white_balance_color[0]
    blue = white_balance_color[2]
    average = (red + blue) / 2

    # Apply values to Red and Blue white levels
    bpy.context.scene.view_settings.curve_mapping.white_level[0] = red / average
    bpy.context.scene.view_settings.curve_mapping.white_level[2] = blue / average

    #Little trick to update viewport as Color Management Curves don't update automatically
    exposure = bpy.context.scene.view_settings.exposure
    bpy.context.scene.view_settings.exposure = exposure

    return None

def get_preview_color_tint(self):
    photographer = bpy.context.scene.camera.data.photographer

    # Set preview color in the UI
    self['preview_color_tint'] = convert_tint_to_color_preview(photographer.tint)
    def_tint = convert_tint_to_color_preview(default_tint)
    return self.get('preview_color_tint', def_tint)

def set_preview_color_tint(self,value):
    return None

def get_tint(self):
    return self.get('tint', default_tint)

def set_tint(self, value):
    self['tint'] = value
    if self.tint < 0:
        tint_curve_mult = self.tint / 200 + 1 # Diving by 200 instead of 100 to avoid green level to go lower than 0.5. Gives more precision to the slider.
    else:
        tint_curve_mult = self.tint / 50 + 1  # Diving by 50 to avoid green level to go higher than 3. Gives more precision to the slider.

    # Apply value to Green white level
    bpy.context.scene.view_settings.curve_mapping.white_level[1] = tint_curve_mult

    #Little trick to update viewport as Color Management Curves don't update automatically
    exposure = bpy.context.scene.view_settings.exposure
    bpy.context.scene.view_settings.exposure = exposure
    return None

def convert_tint_to_color_preview(color_tint):
    red = 1.0
    green = 1.0
    blue = 1.0

    if color_tint < 0:
        red = red + color_tint / 150 # Dividing with 150.
        #Not an accurate match to the actual Tint math, purposefully different so the preview color is pleasing
        blue = blue + color_tint / 150

    if color_tint > 0:
        green = green - color_tint / 150

    return red, green, blue

def update_wb_color(self,context):
    picked_color = (self.wb_color[0],self.wb_color[1],self.wb_color[2])
    convert_RBG_to_whitebalance(picked_color, True)

def update_af_continuous(self,context):
    if self.af_continuous_enabled:
        # Disable Focus Plane
        if self.show_focus_plane:
            self.show_focus_plane = False

        if self.id_data.dof.focus_object is not None:
            self.report({'WARNING'}, "There is an object set as focus target which will override the results of the Autofocus.")

        self.id_data.show_limits = True
        bpy.app.timers.register(focus_continuous)
        if self.af_animate:
            bpy.app.handlers.frame_change_pre.append(stop_playback)
    else:
        self.id_data.show_limits = False
        if bpy.app.timers.is_registered(focus_continuous):
            bpy.app.timers.unregister(focus_continuous)

# def update_ae_animated(self,context):
#     settings = context.scene.camera.data.photographer
#     if settings.ae_animated:
#         bpy.app.timers.register(auto_exposure.ae_bake)
#         bpy.app.handlers.frame_change_pre.append(stop_playback)
#     else:
#         if bpy.app.timers.is_registered(auto_exposure.ae_bake):
#             bpy.app.timers.unregister(auto_exposure.ae_bake)

# Update Sensor Size
def update_sensor_type(self,context):
    if self.id_data.sensor_fit == "VERTICAL" and not self.lock_vertical_fov:
        self.id_data.sensor_fit = "AUTO"
    if self.sensor_type != 'Custom':
        width, height = camera_sensors.sensor_types[self.sensor_type]
        self.id_data.sensor_width = width
        self.id_data.sensor_height = height

    # Refresh viewport and render
    self.id_data.sensor_width = self.id_data.sensor_width

def get_sensor_type(self):
    return self.get('sensor_type', 8)

def set_sensor_type(self,value):
    self['sensor_type'] = value
    update_sensor_type(self,bpy.context)
    return None


def lock_camera_button(self, context):
    # Hide AF buttons if the active camera in the scene isn't a camera
    if bpy.context.preferences.addons[__package__].preferences.show_cam_buttons_pref:
        # for area in bpy.context.screen.areas:
        if context.area.type == 'VIEW_3D':
            if context.area.spaces[0].region_3d.view_perspective == 'CAMERA' :
                if context.scene.camera:
                    if context.scene.camera.type == 'CAMERA' :
                        if context.area.spaces[0].lock_camera:
                            icon="LOCKVIEW_ON"
                        else:
                            icon="LOCKVIEW_OFF"
                        self.layout.prop(context.area.spaces[0], "lock_camera", text="", icon=icon )
                        # break

def get_use_dof(self):
    return self.id_data.dof.use_dof

def set_use_dof(self, value):
    if self.show_focus_plane == True:
        cam_obj = [o for o in bpy.data.objects if o.type == 'CAMERA' and o.data is self.id_data][0]
        for c in cam_obj.children:
            if c.get("is_focus_plane", False):
                if isinstance(c, bpy.types.Object):
                    c.hide_viewport = not value
    self.id_data.dof.use_dof = value
    return None

def get_focus_plane_color(self):
    return self.get('focus_plane_color',  (1,0,0,0.4))

def set_focus_plane_color(self,value):
    self['focus_plane_color'] = value
    # Get Camera Object
    cam_obj = [o for o in bpy.data.objects if o.type == 'CAMERA' and o.data is self.id_data][0]
    # Get Focus Plane as children object with "is_focus_plane"
    for c in cam_obj.children:
        if c.get("is_focus_plane", False):
            # Get first material
            if c.data.materials:
                # Assign to 1st material slot
                mat = c.data.materials[0]
                mat.diffuse_color = value
                mat.node_tree.nodes["Emission"].inputs[0].default_value = value
                mat.node_tree.nodes["Mix Shader"].inputs[0].default_value = value[3]
    return None

def worlds_items(self,context):
    worlds = []
    for w in bpy.data.worlds:
        worlds.append((w.name,w.name,''))
    return worlds

def update_world(self,context):
    # Do not update the world if it's already the right one, fixes freezes
    if context.scene.world != bpy.data.worlds[self.cam_world]:
        context.scene.world = bpy.data.worlds[self.cam_world]

        # Refresh HDRI preview
        if bpy.context.preferences.addons[__package__].preferences.hdri_lib_path:
            if context.scene.world.get('is_world_hdri',False):
                bpy.ops.lightmixer.refresh_hdri_preview()
        # Make sure the world gets saved even if not looking through the camera
        bpy.data.worlds[self.cam_world].use_fake_user = True

def update_lock_vfov(self,context):
    if self.lock_vertical_fov:
        self.id_data.sensor_fit = "VERTICAL"
    else:
        self.id_data.sensor_fit = "AUTO"

def update_frames(self,context):
    if context.scene.camera.data == self.id_data:
        context.scene.frame_start = self.cam_frame_start
        context.scene.frame_end = self.cam_frame_end

def update_frame_start(self,context):
    if self.cam_frame_start > self.cam_frame_end: self.cam_frame_end = self.cam_frame_start
    context.scene.frame_start = self.cam_frame_start

def update_frame_end(self,context):
    if self.cam_frame_end < self.cam_frame_start: self.cam_frame_start = self.cam_frame_end
    context.scene.frame_end = self.cam_frame_end

class PHOTOGRAPHER_OT_MakeCamActive(bpy.types.Operator):
    bl_idname = "photographer.makecamactive"
    bl_label = "Make Camera Active"
    bl_description = "Make this Camera the active camera in the Scene"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        bpy.context.scene.camera = bpy.context.active_object
        update_settings(self,context)
        return{'FINISHED'}

class PHOTOGRAPHER_OT_ApplyPhotographerSettings(bpy.types.Operator):
    bl_idname = "photographer.applyphotographersettings"
    bl_label = "Update All Photographer Camera Settings"
    bl_description = "If you changed Render engines and settings outside of the Photographer addon, reapply the settings to make sure they are up to date"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        update_settings(self,context)
        bokeh.update_bokeh_size(self,context)
        bpy.ops.photographer.applylightsettings()
        return{'FINISHED'}

class PHOTOGRAPHER_OT_SelectActiveCam(bpy.types.Operator):
    bl_idname = "photographer.selectactivecam"
    bl_label = "Select Active Camera"
    bl_description = "Select the Active Camera in the Scene"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        bpy.data.objects[context.scene.camera.name].select_set(True)
        context.view_layer.objects.active = context.scene.camera
        return{'FINISHED'}

class PHOTOGRAPHER_OT_SetShutterAngle(bpy.types.Operator):
    bl_idname = "photographer.setshutterangle"
    bl_label = "Switch to Shutter Angle"
    bl_description = "Switch to Shutter Angle"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        try:
            context.camera.photographer.shutter_mode = 'ANGLE'
        except AttributeError:
            context.scene.camera.data.photographer.shutter_mode = 'ANGLE'
        update_settings(self,context)
        return{'FINISHED'}

class PHOTOGRAPHER_OT_SetShutterSpeed(bpy.types.Operator):
    bl_idname = "photographer.setshutterspeed"
    bl_label = "Switch to Shutter Speed"
    bl_description = "Switch to Shutter Speed"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        try:
            context.camera.photographer.shutter_mode = 'SPEED'
        except AttributeError:
            context.scene.camera.data.photographer.shutter_mode = 'SPEED'
        update_settings(self,context)
        return{'FINISHED'}

class PHOTOGRAPHER_OT_RenderMotionBlur(bpy.types.Operator):
    bl_idname = "photographer.rendermotionblur"
    bl_label = "Enable Motion Blur render"
    bl_description = "Enable Motion Blur in the Render Settings"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        context.scene.render.use_motion_blur = True
        context.scene.eevee.use_motion_blur = True
        return{'FINISHED'}

class PHOTOGRAPHER_OT_AutoLensShift(bpy.types.Operator):
    bl_idname = "photographer.auto_lens_shift"
    bl_label = "Automatic Lens Shift"
    bl_description = "Calculates Lens Shift from current Camera rotation to make vertical lines parallel"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        obj = context.scene.camera
        camera = context.scene.camera.data
        photographer = camera.photographer

        old_rot = obj.rotation_euler.x
        old_vert_shift = photographer.lens_shift
        old_atan = math.atan(photographer.lens_shift/(camera.lens/36))
        rot = old_rot + old_atan

        if rot == 0:
            self.report({'WARNING'}, "Impossible to calculate Lens Shift, the Camera has no vertical rotation")
            return{'CANCELLED'}
        else:
            shift = -(camera.lens/36)/math.tan(rot)
            if shift > 20 or shift < -20:
                self.report({'WARNING'}, "Camera vertical rotation is too extreme, reduce angle to calculate Lens Shift")
                return{'CANCELLED'}
            photographer.lens_shift = shift
            if rot < 0:
                obj.rotation_euler.x = math.radians(-90)
            else:
                obj.rotation_euler.x = math.radians(90)
            return{'FINISHED'}


class PhotographerCameraSettings(bpy.types.PropertyGroup):

    renderable : bpy.props.BoolProperty(
        name = "Include Camera in Render Queue", description = "The camera will be rendered when using Render All Enabled",
        default = True,
    )
    wb_color : bpy.props.FloatVectorProperty(
        name='Color Picker', description="Use the Color Picker on the viewport and pick a grey material in your scene to do the white balance",
        subtype='COLOR', min=0.0, max=1.0, size=3, default=(0.5,0.5,0.5),
        options = {'HIDDEN'},
        update = update_wb_color,
    )
    target_enabled : bpy.props.BoolProperty(
        name = "Camera Target", description = "Camera Target Tracking: Place a target on an object and the camera will aim at it and keep it centered",
        options = {'HIDDEN'},
        default = False,
    )
    sensor_type : bpy.props.EnumProperty(
        name = "Sensor Type", description = "Camera Sensor Size",
        items = camera_sensors.sensor_type_items,
        # default = '36',
        get = get_sensor_type,
        set = set_sensor_type,
    )
    fisheye : bpy.props.BoolProperty(
        name = "Fisheye",
        default = False,
        options = {'HIDDEN'},
        update = update_fisheye,
    )
    fisheye_focal : bpy.props.FloatProperty(
        name = "Fisheye Focal Length", description = "Fisheye Focal Length in mm",
        default = 50, step = 100,
        min = 1, max = 100, precision = 0,
        unit = 'CAMERA',
        get = get_fisheye_focal,
        set = set_fisheye_focal,
    )
    focal : bpy.props.FloatProperty(
        name = "Focal Length", description = "Focal Length in mm",
        default = 50, step = 100,
        min = 1, precision = 0,
        unit = 'CAMERA',
        get = get_focal,
        set = set_focal,
    )
    lens_shift : bpy.props.FloatProperty(
        name = "Lens Shift", description = "Adjusts Vertical Shift while maintaining framing",
        default = 0,
        soft_min = -1, soft_max = 1,
        get = get_lens_shift,
        set = set_lens_shift,
    )
    # breathing : bpy.props.FloatProperty(
    #     name = "Focus Breathing", description = "Changing the focus distance will slightly affect the focal length."
    #     "Negative values will narrow the Field of View, Positive values with expand the Field of View",
    #     default = 0,
    #     soft_min = -1, soft_max = 1,
    #     get = get_breathing,
    #     set = set_breathing,
    # )
    exposure_enabled : bpy.props.BoolProperty(
        name = "Enable Exposure Controls",
        default = False,
        options = {'HIDDEN'},
        update = update_settings
    )
    motionblur_enabled : bpy.props.BoolProperty(
        name = "Enable Motion Blur control", description = "Motion Blur will be controlled by the Shutter Speed / Shutter Angle values",
        default = False,
        options = {'HIDDEN'},
        get = get_motionblur_enabled,
        set = set_motionblur_enabled,
    )

    # Exposure properties
    exposure_mode : bpy.props.EnumProperty(
        name = "Exposure Mode",
        description = ("EV mode: Only adjusts the brightness of the images without affecting Depth of Field or Motion Blur. \n"
                        "Auto Exposure: Samples the viewport luminance and adjusts the Exposure value until the average luminance reaches half-grey (sRGB 127). \n"
                        "Manual: Exposure is calculated using Shutter Speed or Angle, Aperture and ISO. These will also affect Motion Blur and Depth of Field"),
        items = [('EV','EV', 'Exposure Value'),('AUTO','Auto','Auto Exposure metering'),('MANUAL','Manual','Manual Settings using Shutter Speed, Aperture and ISO')],
        default = 'EV', #bpy.context.preferences.addons[__package__].preferences.exposure_mode_pref if bpy.context.preferences.addons[__package__].preferences.exposure_mode_pref else 'EV',
        options = {'HIDDEN'},
        update = update_settings
    )
    ev : bpy.props.FloatProperty(
        name = "Exposure Value",
        description = "",
        default = base_ev, #- math.log2(0.78 / bpy.context.preferences.addons[__package__].preferences.lens_attenuation),
        soft_min = -6, soft_max = 16, step = 1, precision = 2,
        get = get_ev,
        set = set_ev,
    )
    exposure_compensation : bpy.props.FloatProperty(
        name = "Exposure Compensation", description = "Additive Exposure Value adjustment",
        default = 0, soft_min = -3,    soft_max = 3, step = 1, precision = 2,
        get = get_exposure_compensation,
        set = set_exposure_compensation,
    )
    ae : bpy.props.FloatProperty(
        name = "Auto Exposure", description = "Auto Exposure compensation value",
        default = 0, soft_min = -3, soft_max = 3, step = 25, precision = 2,
        get = get_ae,
        set = set_ae,
    )
    center_weight : bpy.props.IntProperty(
        name = "Center Weight", description = "Gives more weight to the center of the frame instead of the entire viewport",
        default = 25, min = 0, max = 100,
        subtype = 'PERCENTAGE'
    )
    ae_speed : bpy.props.FloatProperty(
        name = "AE Speed", description = "Speed at which the Auto Exposure will reach its luminance target",
        default = 0.1, min = 0.02, soft_max = 0.5, max = 1,
    )
    # ae_animated : bpy.props.BoolProperty(
    #     name = "Animate Auto Exposure",    description = "Sets keys on Exposure Value when using Auto Exposure",
    #     options = {'HIDDEN'},
    #     default = False,
    #     update = update_ae_animated,
    # )
    falsecolor_enabled : bpy.props.BoolProperty(
        name = "False Color",
        description = "Enable False Color view transform to validate your exposure",
        default = False,
        options = {'HIDDEN'},
        update = update_falsecolor,
    )
    wb_enabled : bpy.props.BoolProperty(
        name = "Enable White Balance controls",
        description = "Adjusts colors using Temperature and Tint values",
        default = False,
        options = {'HIDDEN'},
        get = get_wb_enabled,
        set = set_wb_enabled,
    )
    # Shutter Speed properties
    shutter_mode : bpy.props.EnumProperty(
        name = "Shutter Mode", description = "Switch between Shutter Speed and Shutter Angle",
        items = [('SPEED','Shutter Speed',''),('ANGLE','Shutter Angle', '')],
        default = 'SPEED',
        options = {'HIDDEN'},
        update = update_settings,
    )
    shutter_speed : bpy.props.FloatProperty(
        name = "Shutter Speed 1/X second", description = "Shutter Speed - controls the amount of Motion Blur",
        default = 100, soft_min = 0.1, soft_max = 1000,    precision = 2,
        get = get_shutter_speed,
        set = set_shutter_speed,
    )
    shutter_speed_slider_enable : bpy.props.BoolProperty(
        name = "Shutter Speed Slider", description = "Enable Shutter Speed slider instead of preset list",
        # default = bpy.context.preferences.addons[__package__].preferences.shutter_speed_slider_pref if bpy.context.preferences.addons[__package__].preferences.shutter_speed_slider_pref else False,
        options = {'HIDDEN'},
        update = update_shutter_speed,
    )
    shutter_speed_preset : bpy.props.EnumProperty(
        name = "Shutter Speed",    description = "Camera Shutter Speed",
        items = [('0.033','30 "',''),('0.04','25 "',''),('0.05','20 "',''),('0.066','15 "',''),('0.077','13 "',''),('0.1','10 "',''),('0.125','8 "',''),('0.1666','6 "',''),('0.2','5 "',''),('0.25','4 "',''),('0.3125','3.2 "',''),('0.4','2.5 "',''),
        ('0.5','2 "',''),('0.625','1.6 "',''),('0.769','1.3 "',''),('1','1 "',''),('1.25','0.8 "',''),('1.666','0.6 "',''),('2','0.5 "',''),('2.5','0.4 "',''),('3.333','0.3 "',''),('4','1 / 4 s',''),('5','1 / 5 s',''),('6','1 / 6 s',''),
        ('8','1 / 8 s',''),('10','1 / 10 s',''),('13','1 / 13 s',''),('15','1 / 15 s',''),('20','1 / 20 s',''),('25','1 / 25 s',''),('30','1 / 30 s',''),('40','1 / 40 s',''),('50','1 / 50 s',''),('60','1 / 60 s',''),('80','1 / 80 s',''),
        ('100','1 / 100 s',''),('125','1 / 125 s',''),('160','1 / 160 s',''),('200','1 / 200 s',''),('250','1 / 250 s',''),('320','1 / 320 s',''),('400','1 / 400 s',''),('500','1 / 500 s',''),('640','1 / 640 s',''),('800','1 / 800 s',''),
        ('1000','1 / 1000 s',''),('1250','1 / 1250 s',''),('1600','1 / 1600 s',''),('2000','1 / 2000 s',''),('2500','1 / 2500 s',''),('3200','1 / 3200 s',''),('4000','1 / 4000 s',''),('5000','1 / 5000 s',''),('6400','1 / 6400 s',''),('8000','1 / 8000 s', '')],
        default = '100',
        get = get_shutter_speed_preset,
        set = set_shutter_speed_preset,
    )

    # Shutter Angle properties
    shutter_angle : bpy.props.FloatProperty(
        name = "Shutter Angle", description = "Shutter Angle in degrees - controls the Shutter Speed and amount of Motion Blur",
        default = 180, soft_min = 1, soft_max = 360, precision = 1,
        get = get_shutter_angle,
        set = set_shutter_angle,
    )
    shutter_angle_preset : bpy.props.EnumProperty(
        name = "Shutter Angle",    description = "Camera Shutter Angle",
        items = [('8.6','8.6 degree',''),('11','11 degree',''),('22.5','22.5 degree',''),
        ('45','45 degree',''),('72','72 degree',''),('90','90 degree',''),
        ('144','144 degree',''),('172.8','172.8 degree',''),('180','180 degree',''),
        ('270','270 degree',''),('360','360 degree','')],
        default = '180',
        get = get_shutter_angle_preset,
        set = set_shutter_angle_preset,
    )

    # Aperture properties
    aperture : bpy.props.FloatProperty(
        name = "Aperture F-stop", description = "Lens aperture - controls the Depth of Field",
        default = 2.4, soft_min = 0.5, soft_max = 32, precision = 1,
        get = get_aperture,
        set = set_aperture,
    )
    aperture_slider_enable : bpy.props.BoolProperty(
        name = "Aperture Slider", description = "Enable Aperture slider instead of preset list",
        # default = bpy.context.preferences.addons[__package__].preferences.aperture_slider_pref,
        options = {'HIDDEN'},
        update = update_aperture
    )
    aperture_preset : bpy.props.EnumProperty(
        name = "Lens Aperture Presets",     description = "Lens Aperture",
        items = [('0.95','f / 0.95',''),('1.2','f / 1.2',''),('1.4','f / 1.4',''),('1.8','f / 1.8',''),('2.0','f / 2.0',''),('2.4','f / 2.4',''),('2.8','f / 2.8',''),('3.5','f / 3.5',''),    ('4.0','f / 4.0',''),
        ('4.9','f / 4.9',''),('5.6','f / 5.6',''),('6.7','f / 6.7',''),('8.0','f / 8.0',''),('9.3','f / 9.3',''),('11','f / 11',''),('13','f / 13',''),('16','f / 16',''),('20','f / 20',''),('22','f / 22','')],
        default = '2.8',
        get = get_aperture_preset,
        set = set_aperture_preset,
    )

    # ISO properties
    iso : bpy.props.IntProperty(
        name = "ISO", description = "ISO setting",
        default = 100, soft_min = 50, soft_max = 12800,
        get = get_iso,
        set = set_iso,
    )
    iso_slider_enable : bpy.props.BoolProperty(
        name = "Iso Slider", description = "Enable ISO setting slider instead of preset list",
        # default = bpy.context.preferences.addons[__package__].preferences.iso_slider_pref,
        options = {'HIDDEN'},
        update = update_ev,
    )
    iso_preset : bpy.props.EnumProperty(
        name = "Iso Presets", description = "Camera Sensitivity",
        items = [('100','100',''),('125','125',''),('160','160',''),('200','200',''),('250','250',''),('320','320',''),('400','400',''),('500','500',''),('640','640',''),('800','800',''),('1000','1000',''),('1250','1250',''),
        ('1600','1600',''),('2000','2000',''),('2500','2500',''),('3200','3200',''),('4000','4000',''),('5000','5000',''),('6400','6400',''),('8000','8000',''),('10000','10000',''),('12800','12800',''),('16000','16000',''),
        ('20000','20000',''),('25600','25600',''),('32000','32000',''),('40000','40000',''),('51200','51200','')],
        default = '100',
        update = update_ev,
        get = get_iso_preset,
        set = set_iso_preset,
    )

    # White Balance properties
    color_temperature : bpy.props.IntProperty(
        name="Color Temperature", description="Color Temperature (Kelvin)",
        min=min_color_temperature, max=max_color_temperature, default=default_color_temperature,
        get=get_color_temperature,
        set=set_color_temperature,
    )
    preview_color_temp : bpy.props.FloatVectorProperty(
        name='Preview Color', description="Color Temperature preview color",
        subtype='COLOR', min=0.0, max=1.0, size=3,
        options = {'HIDDEN'},
        get=get_preview_color_temp,
        set=set_preview_color_temp,
    )
    tint : bpy.props.IntProperty(
        name="Tint", description="Adjusts the amoung of Green or Magenta cast",
        min=min_color_tint, max=max_color_tint, default=default_tint,
        get=get_tint,
        set=set_tint,
    )
    preview_color_tint : bpy.props.FloatVectorProperty(
        name="Preview Color Tint", description="Tint preview color",
        subtype='COLOR', min=0.0, max=1.0, size=3,
        options = {'HIDDEN'},
        get=get_preview_color_tint,
        set=set_preview_color_tint,
    )

    # Resolution properties
    resolution_enabled : bpy.props.BoolProperty(
        name = "Enable Resolution override for this Camera",
        default = False,
        update = update_resolution_enabled
    )
    resolution_mode : bpy.props.EnumProperty(
        name = "Format", description = "Choose Custom Resolutions or Ratio presets",
        items = [('CUSTOM_RES','Custom Resolution',''),('CUSTOM_RATIO','Custom Ratio',''),
                ('11','1:1', ''),('32','3:2', ''),('43','4:3', ''),('67','6:7', ''),
                ('169','16:9', ''),('2351','2.35:1', ''),('2391','2.39:1', '')],
        options = {'HIDDEN'},
        update = update_resolution
    )
    resolution_x : bpy.props.IntProperty(
        name = "X", description = "Horizontal Resolution",
        default = 1920, min = 0, subtype = 'PIXEL',
        options = {'HIDDEN'},
        update = update_resolution
    )
    resolution_y : bpy.props.IntProperty(
        name = "Y", description = "Vertical Resolution",
        min = 0, default = 1080, subtype='PIXEL',
        options = {'HIDDEN'},
        update = update_resolution
    )
    ratio_x : bpy.props.FloatProperty(
        name = "X", description = "Horizontal Ratio",
        min = 0, default = 16, precision = 2,
        options = {'HIDDEN'},
        update = update_resolution
    )
    ratio_y : bpy.props.FloatProperty(
        name = "Y", description = "Vertical Ratio",
        min = 0, default = 9, precision = 2,
        options = {'HIDDEN'},
        update = update_resolution
    )
    longedge : bpy.props.IntProperty(
        name = "Long Edge", description = "Long Edge Resolution",
        default = 1920, min = 0, subtype = 'PIXEL',
        options = {'HIDDEN'},
        update = update_resolution
    )
    resolution_rotation : bpy.props.EnumProperty(
        name = "Orientation", description = "Rotation of the camera",
        items = [('LANDSCAPE','Landscape',''),('PORTRAIT','Portrait', '')],
        options = {'HIDDEN'},
        update = update_resolution
    )

    # AF-C property
    af_continuous_enabled : bpy.props.BoolProperty(
        name = "AF-C", description = "Autofocus Continuous: Realtime focus on the center of the frame.\n"
        "Requires to look through the Camera",
        default = False,
        options = {'HIDDEN'},
        update = update_af_continuous,
    )
    af_continuous_interval : bpy.props.FloatProperty(
        name="AF-C interval", description="Number of seconds between each autofocus update",
        default = 0.6, soft_min = 0.05,    min = 0.01,    soft_max = 3, precision = 2,
        subtype='TIME'
    )
    af_animate : bpy.props.BoolProperty(
        name = "Animate Autofocus", description = "Set keys on focus distance when using AF-S and AF-C",
        options = {'HIDDEN'},
        default = False,
    )
    # Master Camera Settings
    match_speed : bpy.props.FloatProperty(
        name = "Transition Speed", description = "Speed at which it switches to the other camera. 4 is instant",
        default = 0.2, min = 0.01, soft_min = 0.02, soft_max= 1, max = 4,
    )
    is_matching : bpy.props.BoolProperty(
        name = "Is matchin camera",
        default = False,
    )
    target_camera : bpy.props.PointerProperty(
        type=bpy.types.Object,
        name="Target Camera", description="The camera that the Master Camera will match"
    )
    # Light Threshold property
    light_threshold_warning:bpy.props.BoolProperty(
        name = "Light Threshold Warning",
        default = False,
    )
    # Use Dof replicate
    use_dof:bpy.props.BoolProperty(
        name = "Enable Depth of Field",
        default = False,
        options = {'HIDDEN'},
        get = get_use_dof,
        set = set_use_dof,
    )
    # Show Focus Plane
    show_focus_plane:bpy.props.BoolProperty(
        name = "Focus Plane",description="Show Focus Plane debug",
        default = False,
    )
    focus_plane_mat : bpy.props.PointerProperty(
        type=bpy.types.Material,
        name="Focus Plane Material", description="Material used for Focus plane"
    )
    focus_plane_color : bpy.props.FloatVectorProperty(
        name="Focus Plane Color", description="Set Color and Alpha opacity of the Focus Plane debug",
        subtype='COLOR', min=0.0, max=1.0, size=4,
        # default=bpy.context.preferences.addons[__package__].preferences.default_focus_plane_color,
        default=(1.0,0.0,0.0,0.4),
        options = {'HIDDEN'},
        get=get_focus_plane_color,
        set=set_focus_plane_color,
    )
    # Optical Vignetting
    opt_vignetting : bpy.props.BoolProperty(
        name = "Optical Vignetting",
        description=("Optical Vignetting can create Cat's Eye bokeh or Matte Box mechanical vignetting. \n"
                    "WARNING: Computational-heavy feature, expect longer render times. \n"
                    "Requires a very short clip start that will create Z-fighting issues in the viewport"),
        default = False,
        options = {'HIDDEN'},
        update = bokeh.update_opt_vignetting,
    )
    ov_scale : bpy.props.FloatProperty(
        name = "Optical Vignetting Scale",
        description="Controls the amount of optical vignetting",
        default = 0.5,
        min = 0.05,
        soft_max = 1,
    )
    ov_rotation: bpy.props.FloatProperty(
        name='Rotation',
        default=0, soft_min=-3.14159, soft_max=3.14159, unit='ROTATION',
    )
    opt_vignetting_tex: bpy.props.EnumProperty(
        name="Optical Vignetting Texture",
        items=bokeh.enum_previews_opt_vignetting,
        update=bokeh.update_opt_vignetting_tex,
    )
    # Bokeh
    bokeh : bpy.props.BoolProperty(
        name = "Bokeh Texture",
        description=("Bokeh Texture defines the looks of the Depth of Field, uniformly across the image. \n"
                    "WARNING: Computational-heavy feature, expect longer render times.\n"
                    "Requires a very short clip start that will create Z-fighting issues in the viewport"),
        default = False,
        options = {'HIDDEN'},
        update = bokeh.update_bokeh,
    )
    bokeh_rotation: bpy.props.FloatProperty(
        name='Rotation',
        default=0, soft_min=-3.14159, soft_max=3.14159, unit='ROTATION',
    )
    bokeh_brightness: bpy.props.FloatProperty(
    name='Brightness Multiplier',
    description="Adjusts brightness to compensate for energy loss due to a dark bokeh texture",
    default=1, soft_min=1, soft_max=5,
    )
    # bokeh_contrast: bpy.props.FloatProperty(
    # name='Contrast',
    # description="Adjust contrast of the bokeh texture to accentuate details",
    # default=0, soft_min=-1, soft_max=1,
    # )
    bokeh_tex: bpy.props.EnumProperty(
        name="Optical Vignetting Texture",
        items=bokeh.enum_previews_bokeh,
        update=bokeh.update_bokeh_tex,
    )
    override_world : bpy.props.BoolProperty(
        name = "Set World per Camera",
        description = ("Requires to override World for each of your cameras, "
                    "or they will use the last World that was applied"),
        default = False,
        options = {'HIDDEN'},
    )
    cam_world: bpy.props.EnumProperty(
        name="World Override",
        items = worlds_items,
        description = "List of Worlds available",
        options = {'HIDDEN'},
        update = update_world,
    )
    lock_vertical_fov: bpy.props.BoolProperty(
        name = "Lock Vertical FOV",
        description = "Use Vertical Sensor Fit to get correct Field of View when recreating an Anamorphic lens",
        default = False,
        options = {'HIDDEN'},
        update = update_lock_vfov,
    )
    override_frames: bpy.props.BoolProperty(
        name = "Frames Override",
        description = ("Requires to override frames for each of your cameras, "
                    "or they will use the last settings that were applied"),
        default = False,
        options = {'HIDDEN'},
        update = update_frames,
    )
    cam_frame_start: bpy.props.IntProperty(
        name = "Frame Start",
        description = "Overrides Scene Frame Start for this camera",
        default = 1, min = 0,
        options = {'HIDDEN'},
        update = update_frame_start,
    )
    cam_frame_end: bpy.props.IntProperty(
        name = "Frame End",
        description = "Overrides Scene Frame End for this camera",
        default = 250, min = 0,
        options = {'HIDDEN'},
        update = update_frame_end,
    )
