import bpy, blf
from ..functions import raycast
from ..autofocus import list_focus_planes, list_dof_objects
from ..rigs.build_rigs import get_camera_rig
from mathutils import Vector
from mathutils.geometry import distance_point_to_plane

def draw_callback_px(self,context):
    font_id = 0
    x_offset = context.region.width / 2 - 75
    # 75 = text horizontal dimension / 2
    y_offset = 35
    cam = context.scene.camera.data

    text = "Focal Length: " + str(round(cam.photographer.focal)) + " mm"
    # find text dimensions
    # print (blf.dimensions(font_id,text))
    blf.position(font_id, x_offset, y_offset ,0)
    blf.size(font_id, 28, 72)
    blf.color(font_id, 1.0,0.7,0.02,1.0)
    blf.draw(font_id,text)

class PHOTOGRAPHER_OT_DollyZoom(bpy.types.Operator):
    bl_idname = "photographer.dollyzoom"
    bl_label = "Dolly Zoom"
    bl_description = ("Dolly Zoom: Focal length adjustment, compensated by a Camera translation in depth. \n"
    "Click on an object's surface and move the mouse horizontally. Hold shift for smaller increment")
    bl_options = {'REGISTER', 'UNDO'}

    # Camera location has to be stored as property to work properly
    stored_cam_loc: bpy.props.FloatVectorProperty()
    stored_focus_distance: bpy.props.FloatProperty()

    def modal(self, context, event):
        # Allow navigation for Blender and Maya shortcuts
        if event.type in {'MIDDLEMOUSE', 'WHEELUPMOUSE', 'WHEELDOWNMOUSE'} or event.alt and event.type == 'LEFTMOUSE' or event.alt and event.type == 'RIGHTMOUSE':
            return {'PASS_THROUGH'}

        cam_obj = context.scene.camera
        cam = cam_obj.data
        settings = cam.photographer

        # Enter Dolly zoom
        if event.type == 'LEFTMOUSE' and context.space_data.type == 'VIEW_3D':
            if event.value == 'PRESS':
                # Store Mouse position of the leftmouse click
                self.pos = (event.mouse_region_x, event.mouse_region_y)

                # Raycast to find distance to object
                result, location, object = raycast(context, event, False, False, cam_obj)

                if result:
                    cam_dir = cam_obj.matrix_world.to_quaternion() @ Vector((0.0, 0.0, -1.0))
                    self.dist = abs(distance_point_to_plane(cam_obj.location, location, cam_dir))
                    self.focal_length = settings.focal
                    self.focus_distance = cam.dof.focus_distance
                    if self.rig_obj:
                        self.cam_loc = self.rig_obj.location
                    else:
                        self.cam_loc = cam_obj.location
                    self.left_press = True
                else:
                    if self.cursor_set:
                        context.window.cursor_modal_restore()
                    bpy.types.SpaceView3D.draw_handler_remove(self._handle, 'WINDOW')
                    self.report({'WARNING'}, "Raycast failed. Is the targeted object a mesh? Are you looking through the scene camera in this 3D view?")
                    return {'CANCELLED'}

        if self.left_press:
            if event.type == 'MOUSEMOVE' and self.pos:
                # Mouse Sensitivity
                if event.shift:
                    fac = 50
                else:
                    fac = 8
                focal_offset = (event.mouse_region_x - self.pos[0])/fac
                if settings.focal + focal_offset >= 4:
                    settings.focal += focal_offset
                    self.pos = (event.mouse_region_x, event.mouse_region_y)
                    offset_dist = focal_offset*0.1*(self.dist/(self.focal_length*0.1))
                    offset_vec = Vector((0.0, 0.0, offset_dist ))
                    rotation_matrix = cam_obj.rotation_euler.to_matrix()
                    rotation_matrix.invert()
                    if self.rig_obj:
                        self.rig_obj.location = self.cam_loc + offset_vec @ rotation_matrix
                    else:
                        cam_obj.location = self.cam_loc + offset_vec @ rotation_matrix
                    cam.dof.focus_distance += offset_dist

        if event.type == 'LEFTMOUSE' and event.value == 'RELEASE':
            if not event.type == 'MOUSEMOVE':
                self.left_press = False
                if self.cursor_set:
                    context.window.cursor_modal_restore()
                # Restore Focus Planes visibility
                for o in self.fp:
                    o.hide_viewport = False
                # for o in self.dof_objects:
                #     o.hide_viewport = False

                bpy.types.SpaceView3D.draw_handler_remove(self._handle, 'WINDOW')
                return {'FINISHED'}

        # Cancel Modal with RightClick and ESC
        if event.type in {'RIGHTMOUSE', 'ESC'}:
            if self.focal_length:
                settings.focal = self.focal_length
            if self.focus_distance:
                cam.dof.focus_distance = self.focus_distance


            if self.rig_obj:
                self.rig_obj.location = self.stored_cam_loc
            else:
                context.scene.camera.location = self.stored_cam_loc

            # Restore Focus Planes visibility
            for o in self.fp:
                o.hide_viewport = False
            # for o in self.dof_objects:
            #     o.hide_viewport = False

            if self.cursor_set:
                context.window.cursor_modal_restore()

            bpy.types.SpaceView3D.draw_handler_remove(self._handle, 'WINDOW')
            return {'CANCELLED'}

        return {'RUNNING_MODAL'}

    def invoke(self, context, event):
        if context.area.type == 'VIEW_3D':
            cam_obj = context.scene.camera
            self.left_press = False
            self.pos = None
            self.cursor_set = True
            self.dist = None
            self.focal_length = None
            self.focus_distance = None
            self.cam_loc = None
            self.rig_obj = None
            if cam_obj.get("is_rigged", False):
                self.rig_obj = get_camera_rig(cam_obj)
                if self.rig_obj:
                    self.stored_cam_loc = self.rig_obj.location
            else:
                self.stored_cam_loc = context.scene.camera.location
            self.stored_focus_distance = context.scene.camera.data.dof.focus_distance

            # Hide all Focus Planes
            self.fp = list_focus_planes()
            # self.dof_objects = list_dof_objects()

            args = (self, context)
            self._handle = bpy.types.SpaceView3D.draw_handler_add(draw_callback_px, args, 'WINDOW', 'POST_PIXEL')

            context.window.cursor_modal_set('EYEDROPPER')
            context.window_manager.modal_handler_add(self)

            return {'RUNNING_MODAL'}
        else:
            self.report({'WARNING'}, "View3D not found, cannot run operator")
            return {'CANCELLED'}


# SET EV KEY BUTTON
class PHOTOGRAPHER_OT_DollyZoom_Set_Key(bpy.types.Operator):
    """Set key on Focal Length, Focus Distance and Camera location"""
    bl_idname = "photographer.dollyzoom_set_key"
    bl_label = "Set Dolly Zoom Key"

    def execute(self, context):
        cam_obj = context.scene.camera
        cam = cam_obj.data
        current_frame = context.scene.frame_current
        cam_obj.keyframe_insert(data_path='location', frame=(current_frame))
        cam.photographer.keyframe_insert(data_path='focal', frame=(current_frame))
        cam.dof.keyframe_insert(data_path='focus_distance', frame=(current_frame))

        return{'FINISHED'}
