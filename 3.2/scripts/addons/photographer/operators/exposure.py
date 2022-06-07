import bpy, bgl, math
from ..functions import show_message, rgb_to_luminance
from ..autofocus import hide_focus_planes
from ..constants import base_ev

def get_exposure_node(self,context):
    scene = context.scene
    if scene.use_nodes:
        nodes = scene.node_tree.nodes
        exp = [n for n in nodes if n.bl_idname=='CompositorNodeExposure'
            and n.get('photographer_exposure',False)]
        if exp:
            return exp[0]
        else:
            return False

class PHOTOGRAPHER_OT_AddExposureNode(bpy.types.Operator):
    bl_idname = "photographer.add_exposure_node"
    bl_label = "Add Exposure Node"
    bl_description = ("Apply Exposure during Compositing. \n Exposure won't be "
                    "visible in viewport, but will be applied to EXR files")
    bl_options = {'UNDO'}

    # @classmethod
    # def poll(cls,context):
    #     return context.scene.use_nodes

    def execute(self, context):
        scene = context.scene
        if not scene.use_nodes:
            scene.use_nodes = True

        nodes = scene.node_tree.nodes
        links = scene.node_tree.links

        comp = [n for n in nodes if n.bl_idname=='CompositorNodeComposite']
        if not comp:
            show_message("Did not find a Composite node in the graph, "
                        "the operation is cancelled.")
            return {'CANCELLED'}
        else:
            comp = comp[0]
            img = comp.inputs['Image']

        exp = get_exposure_node(self,context)
        if exp:
            exp.mute = False
        else:
            exp = nodes.new('CompositorNodeExposure')
            exp.label = 'Photographer Exposure'
            exp['photographer_exposure'] = True
            exp.location = comp.location
            comp.location[0] += 200

        # Find links to Composite and Viewer node
        link_comp = [l for l in links if l.to_node == comp and l.to_socket == img]
        inc_comp = link_comp[0].from_node
        inc_comp_socket = link_comp[0].from_socket
        inc_comp_links = [l for l in links if l.from_socket == inc_comp_socket]

        # Insert node
        if inc_comp != exp:
            links.new(inc_comp.outputs[inc_comp_socket.name], exp.inputs[0])
        for l in inc_comp_links:
            links.new(exp.outputs[0], l.to_node.inputs[l.to_socket.name])

        # Turn on Compositing rendering
        scene.render.use_compositing = True
        exp.inputs['Exposure'].default_value = scene.view_settings.exposure
        scene.view_settings.exposure = 0
        # scene.photographer.comp_exposure = True

        return {'FINISHED'}

class PHOTOGRAPHER_OT_DisableExposureNode(bpy.types.Operator):
    bl_idname = "photographer.disable_exposure_node"
    bl_label = "Disable Exposure Node"
    bl_description = "Remove Exposure from Compositing and use Color Management Exposure"
    bl_options = {'UNDO'}

    # @classmethod
    # def poll(cls,context):
    #     return context.scene.use_nodes

    def execute(self, context):
        scene = context.scene
        nodes = scene.node_tree.nodes

        exp = get_exposure_node(self,context)
        if exp:
            exp.mute = True
        scene.view_settings.exposure = exp.inputs['Exposure'].default_value
        # scene.photographer.comp_exposure = False

        return {'FINISHED'}

def exposure_picker(self,context,event,use_scene_camera):
    if self.use_scene_camera:
        settings = context.scene.camera.data.photographer
    else:
        settings = context.camera.photographer

    x,y = event.mouse_x, event.mouse_y

    area = context.area
    if area.type=='VIEW_3D':
        corner_x = area.x
        corner_y = area.y
        header_height = area.regions[0].height
        lpanel_width = area.regions[2].width

        x -= corner_x + lpanel_width
        y -= corner_y + header_height

        bgl.glDisable(bgl.GL_DEPTH_TEST)
        buf = bgl.Buffer(bgl.GL_FLOAT, 3)

        values = count = 0

        # Sample a 9*9 pixels square
        for i in range(x-4, x+5):
            for j in range(y-4, y+5):
                bgl.glReadPixels(i, j, 1, 1, bgl.GL_RGB, bgl.GL_FLOAT, buf)
                lum = rgb_to_luminance(buf)
                if lum != 0:
                    values += lum
                    count += 1

        if count != 0:
            lum_avg = values/count
            # print("Luminance: " + str(lum_avg))

            # Exposure target
            mid_grey = 0.18
            diff_lum = lum_avg / mid_grey
            if diff_lum > 0:
                target = math.log2(diff_lum)
                settings.ev = base_ev + target
        del buf

class PHOTOGRAPHER_OT_EVPicker(bpy.types.Operator):
    bl_idname = "exposure.picker"
    bl_label = "Pick Exposure"
    bl_description = "Pick a mid grey area in the 3D view to adjust the Exposure"
    bl_options = {'REGISTER', 'UNDO'}

    use_scene_camera: bpy.props.BoolProperty(default=False)

    def modal(self, context, event):
        if self.use_scene_camera:
            settings = context.scene.camera.data.photographer
        else:
            settings = context.camera.photographer

        context.area.tag_redraw()

        # Allow navigation for Blender and Maya shortcuts
        if event.type in {'MIDDLEMOUSE', 'WHEELUPMOUSE', 'WHEELDOWNMOUSE'} or event.alt and event.type == 'LEFTMOUSE' or event.alt and event.type == 'RIGHTMOUSE':
            return {'PASS_THROUGH'}

        if event.type == 'LEFTMOUSE' and event.value == 'RELEASE':
            if context.area.type=='VIEW_3D':
                bpy.types.SpaceView3D.draw_handler_remove(self._handle, 'WINDOW')

            # Restore Mouse Cursor from EYEDROPPER Icon
            if self.cursor_set:
                context.window.cursor_modal_restore()

            # Restore Focus Planes visibility
            for o in self.fp:
                o.hide_viewport = False

            return {'FINISHED'}

        elif event.type in {'RIGHTMOUSE', 'ESC'}:
            if context.area.type=='VIEW_3D':
                bpy.types.SpaceView3D.draw_handler_remove(self._handle, 'WINDOW')

            # Restore previous state
            settings.ev = self.stored_exposure
            settings.exposure_mode = self.stored_exposure_mode
            # Restore Focus Planes visibility
            for o in self.fp:
                o.hide_viewport = False

            # Restore Mouse Cursor from EYEDROPPER Icon
            if self.cursor_set:
                context.window.cursor_modal_restore()

            return {'CANCELLED'}

        return {'RUNNING_MODAL'}


    def invoke(self, context, event):
        if self.use_scene_camera:
            settings = context.scene.camera.data.photographer
        else:
            settings = context.camera.photographer

        # Store state
        self.stored_exposure = settings.ev
        self.stored_exposure_mode = settings.exposure_mode

        self.fp = hide_focus_planes()

        if not settings.exposure_mode == 'EV':
            settings.exposure_mode = 'EV'

        args = (self, context, event, self.use_scene_camera)
        if context.area.type=='VIEW_3D':
            self._handle = bpy.types.SpaceView3D.draw_handler_add(exposure_picker, args, 'WINDOW', 'PRE_VIEW')

        # Set Cursor to EYEDROPPER icon
        self.cursor_set = True
        context.window.cursor_modal_set('EYEDROPPER')

        context.window_manager.modal_handler_add(self)

        return {'RUNNING_MODAL'}
