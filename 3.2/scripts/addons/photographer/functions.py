import bpy, math

from bpy_extras import view3d_utils
from mathutils import Vector
from mathutils.geometry import distance_point_to_plane
from .constants import base_ev

class InterpolatedArray(object):
  # An array-like object that provides interpolated values between set points.

    def __init__(self, points):
        self.points = sorted(points)

    def __getitem__(self, x):
        if x < self.points[0][0] or x > self.points[-1][0]:
            raise ValueError
        lower_point, upper_point = self._GetBoundingPoints(x)
        return self._Interpolate(x, lower_point, upper_point)

    def _GetBoundingPoints(self, x):
    #Get the lower/upper points that bound x.
        lower_point = None
        upper_point = self.points[0]
        for point  in self.points[1:]:
            lower_point = upper_point
            upper_point = point
            if x <= upper_point[0]:
                break
        return lower_point, upper_point

    def _Interpolate(self, x, lower_point, upper_point):
    #Interpolate a Y value for x given lower & upper bounding points.
        slope = (float(upper_point[1] - lower_point[1]) / (upper_point[0] - lower_point[0]))
        return lower_point[1] + (slope * (x - lower_point[0]))

ev_lookup =  ["Starlight","Aurora Borealis","Half Moon","Full Moon","Full Moon in Snowscape",
            "Dim artifical light","Dim artifical light","Distant view of lit buildings",
            "Distant view of lit buildings","Fireworks","Candle","Campfire","Home interior",
            "Night Street","Office Lighting","Neon Signs","Skyline after Sunset","Sunset",
            "Heavy Overcast","Bright Cloudy","Hazy Sun","Sunny","Bright Sun"]

# sRGB to linear function
def srgb_to_linear(x):
    a = 0.055
    if x <= 0.04045 :
        y = x / 12.92
    else:
        y = pow( (x + a) * (1.0 / (1 + a)), 2.4)
    return y

def linear_to_srgb(x):
    if (x > 0.0031308):
        y = 1.055 * (pow(x, (1.0 / 2.4))) - 0.055
    else:
        y = 12.92 * x
    return y

def rgb_to_luminance(color):
    luminance = 0.2126729*color[0] + 0.7151522*color[1] + 0.072175*color[2]
    return luminance

def lerp(a, b, percent):
    return (a + percent*(b - a))

def interpolate_float(float1, float2, speed):
    float = float1 + (float2 - float1) * speed
    return float, abs(float-float2)

def interpolate_int(int1, int2, speed):
    if (int2 - int1) != 0:
        delta = (int2 - int1) * speed
        if 0 < delta < 1:
            delta = 1
        elif -1 < delta < 0:
            delta = -1
    else:
        delta = 0
    int = int1 + delta
    return int, abs(int-int2)

def update_exposure_guide(self,context,ev):
    if ev <= 16 and ev >= -6:
        ev = int(ev+6)
        ev_guide = ev_lookup[ev]
    else:
        ev_guide = "Out of realistic range"
    return ev_guide

def calc_exposure_value(self,context,settings):
    if settings.exposure_mode == 'EV':
        EV = settings.ev - settings.exposure_compensation

    elif settings.exposure_mode == 'AUTO':
        EV = base_ev - settings.ae - settings.exposure_compensation

    else:
        if not settings.aperture_slider_enable:
            aperture = float(settings.aperture_preset)
        else:
            aperture = settings.aperture
        A = aperture

        if settings.shutter_mode == 'SPEED':
            if not settings.shutter_speed_slider_enable:
                shutter_speed = float(settings.shutter_speed_preset)
            else:
                shutter_speed = settings.shutter_speed

        if settings.shutter_mode == 'ANGLE':
            shutter_speed = shutter_angle_to_speed(self,context,settings)

        S = 1 / shutter_speed

        if not settings.iso_slider_enable:
            iso = float(settings.iso_preset)
        else:
            iso = settings.iso
        I = iso

        EV = math.log((100*(A*A)/(I*S)), 2)
        EV = round(EV, 2) - settings.exposure_compensation
    return EV

def shutter_angle_to_speed(self,context,settings):
    if not settings.shutter_speed_slider_enable:
        shutter_angle = float(settings.shutter_angle_preset)
    else:
        shutter_angle = settings.shutter_angle
    fps = context.scene.render.fps / context.scene.render.fps_base
    shutter_speed = 1 / (shutter_angle / 360) * fps
    return shutter_speed

def shutter_speed_to_angle(self,context,settings):
    fps = context.scene.render.fps / context.scene.render.fps_base
    if not settings.shutter_speed_slider_enable:
        shutter_angle = (fps * 360) / float(settings.shutter_speed_preset)
    else:
        shutter_angle = (fps * 360) / settings.shutter_speed
    return shutter_angle

def lc_exposure_check(self,context):
    if context.scene.camera:
        settings = context.scene.camera.data.photographer
        if bpy.context.scene.render.engine == 'LUXCORE' and settings.exposure_enabled:
            tonemapper = context.scene.camera.data.luxcore.imagepipeline.tonemapper
            if not tonemapper.enabled:
                return True
            else:
                if (tonemapper.type != 'TONEMAP_LINEAR' or tonemapper.use_autolinear or round(tonemapper.linear_scale,6) != 0.001464 ):
                    return True
                else:
                    return False
        else:
            return False

# Focus picker
def raycast(context, event, focus, continuous, cam_obj):
    scene = bpy.context.scene

    if continuous:
        # Shoot ray from Scene camera
        # Offset origin to avoid hitting Bokeh objects
        org = cam_obj.matrix_world @ Vector((0.0, 0.0, 0.0))
        dir = cam_obj.matrix_world @ Vector((0.0, 0.0, -100)) - org

    else:
        # Shoot ray from mouse pointer
        region = context.region
        rv3d = context.region_data
        coord = event.mouse_region_x, event.mouse_region_y

        org = view3d_utils.region_2d_to_origin_3d(region, rv3d, coord)
        dir = view3d_utils.region_2d_to_vector_3d(region, rv3d, coord)

    # Offset origin to avoid hitting DoF objects
    offset = 0.02
    for c in cam_obj.children:
        if c.get("is_opt_vignetting", False):
            offset -= c.location.z * context.scene.unit_settings.scale_length
            break
    offset /= context.scene.unit_settings.scale_length
    dir.normalize()
    org += (offset * dir)

    if bpy.app.version >= (2, 91, 0):
        vl = bpy.context.view_layer.depsgraph
    else:
        vl = bpy.context.view_layer

    result, location, normal, index, object, matrix = scene.ray_cast(vl, org, dir)

    if result:
        if focus:
            cam_dir = cam_obj.matrix_world.to_quaternion() @ Vector((0.0, 0.0, -1.0))
            dist = abs(distance_point_to_plane(cam_obj.location, location, cam_dir))
            # print ('dist = ' + str(dist))
            cam_obj.data.dof.focus_distance = dist
        return result, location, object

    else:
        return result, None, None

def traverse_tree(t):
    yield t
    for child in t.children:
        yield from traverse_tree(child)

def copy_collections(object, target):
    colls = object.users_collection

    # Remove collections from object if it is in another collection than the default Scene / Master Collection
    if not (len(colls) == 1 and colls == (bpy.data.scenes[bpy.context.scene.name].collection,)):
        bpy.context.view_layer.objects.active = target
        bpy.ops.collection.objects_remove_all()
        # Assign Object collections to Target
        for coll in colls:
            bpy.data.collections[coll.name].objects.link(target)

def list_collections(context):
    scene_colls = context.scene.collection

    # Get names of collections and sort them
    collections = [c for c in traverse_tree(scene_colls)]
    collection_names = [c.name for c in traverse_tree(scene_colls)]
    collection_names = sorted(collection_names)

    # Get Collections from Collection names, but still sorted.
    collections=[]
    for c in collection_names:
        # Ignore 'Master Collection' or 'Scene Collection' (Blender 3.0), adding it as scene.collection)
        if c not in {'Master Collection', 'Scene Collection'}:
            collections.append(bpy.data.collections[c])
        else:
            collections.append(context.scene.collection)
    return collections

def show_message(message = "", title = "Message Box", icon = 'INFO'):
    def draw(self, context):
        self.layout.label(text=message)
    bpy.context.window_manager.popup_menu(draw, title = title, icon = icon)

def has_keyframe(ob, attr):
    anim = ob.animation_data
    if anim is not None and anim.action is not None:
        for fcu in anim.action.fcurves:
            if fcu.data_path == attr:
                return len(fcu.keyframe_points) > 0
    return False

def list_cameras(context):
    master_cam = None
    cam_collections = []
    cam_list = []

    cameras = [cam for cam in context.scene.collection.all_objects if cam.type=='CAMERA']
    cam_list = [cam.name for cam in cameras]
    cam_list.sort()
    if 'MasterCamera' in cam_list:
        master_cam = 'MasterCamera'
        cam_list.remove('MasterCamera')

    collections = list_collections(context)
    for coll in collections:
        coll_cams = [obj.name for obj in coll.objects if obj.type=='CAMERA']
        if coll_cams:
            cam_collections.append(coll)

    return cam_list,master_cam,cam_collections
