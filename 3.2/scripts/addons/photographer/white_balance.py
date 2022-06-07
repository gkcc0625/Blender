import bpy, bgl, math
from bpy.app.handlers import persistent
from .functions import srgb_to_linear, InterpolatedArray
from .autofocus import hide_focus_planes

# Default variables
default_color_temperature = 6500
default_tint = 0

# Creating Color Temperature to RGB look up tables (CIE 1964 10 degree CMFs)
# from http://www.vendian.org/mncharity/dir3/blackbody/UnstableURLs/bbr_color.html
# Using 6500 as default white: purposefully changed 255,249,251 to 255,255,255
color_temperature_red = ((1000,255),(1200,255),(1400,255),(1600,255),(1800,255),
                        (2000, 255),(2200,255),(2400,255),(2700,255),(3000,255),
                        (3300,255),(3600,255),(3900,255),(4300,255),
                        (5000,255),(6000,255),(6500, 255),(7000,245),(8000,227),
                        (9000,214),(10000,204),(11000,196),(12000,191),(13000,120),
                        (14000, 30))
color_temperature_green = ((1000,56),(1200,83),(1400,101),(1600,115),(1800,126),
                        (2000,137),(2200,147),(2400,157),(2700,169),(3000,180),
                        (3300,190),(3600,199),(3900,206),(4300,219),(5000,228),
                        (6000,243),(6500, 255),(7000,243),(8000,233),(9000,225),
                        (10000,219),(11000,215),(12000,211),(13000,200),(14000, 100))                        
color_temperature_blue = ((1000,1),(1200,1),(1400,1),(1600,1),(1800,1),(2000,18),
                        (2200,44),(2400,63),(2700,87),(3000,107),(3300,126),
                        (3600,143),(3900,159),(4300,175),(5000,206),(6000,239),
                        (6500, 255),(7000,255),(8000,255),(9000,255),(10000,255),
                        (11000,255),(12000,255),(13000,255),(14000,255))

#White Balance functions ##############################################################

def processing_function(red_temp, blue_temp):
    return (float(red_temp[1]) / blue_temp[1], red_temp[0])

def convert_temperature_to_RGB_table(color_temperature):

    # Interpolate Tables
    table_red = InterpolatedArray(color_temperature_red)
    table_green = InterpolatedArray(color_temperature_green)
    table_blue = InterpolatedArray(color_temperature_blue)

    # Convert Temperature to RGB using the look up tables
    red = table_red[color_temperature]
    green = table_green[color_temperature]
    blue = table_blue[color_temperature]

    return (red / 255, green / 255, blue / 255)

def convert_RGB_to_temperature_table(red, blue):
    temperature_ratio = list(map(processing_function, color_temperature_red, color_temperature_blue))
    table_ratio = InterpolatedArray(temperature_ratio)

    # Min and Max ratios from the table
    maxratio = temperature_ratio[0][0]
    minratio = temperature_ratio[-1][0]

    # Make sure to not divide by 0
    if blue == 0:
        ratio = minratio
    else: ratio = red / blue

    #Clamping ratio to avoid looking outside of the table
    ratio = maxratio if ratio > maxratio else minratio if ratio < minratio else ratio

    color_temperature = table_ratio[ratio]

    return (color_temperature)

def convert_RBG_to_whitebalance(picked_color,use_scene_camera):
    if use_scene_camera:
        settings = bpy.context.scene.camera.data.photographer
    else:
        settings = bpy.context.camera.photographer

    # glReadPixels returns raw linear pixel values
    red = picked_color[0]
    green = picked_color[1]
    blue = picked_color[2]

    average = (red + blue) / 2

    if average != 0:

        # Calculating Curves values
        red_mult = red / average
        green_mult = green / average
        blue_mult = blue / average

        # Accurate multiplier to test accuracy of color temperature conversion
        # bpy.context.scene.view_settings.curve_mapping.white_level[0] = red_mult
        # bpy.context.scene.view_settings.curve_mapping.white_level[1] = green_mult
        # bpy.context.scene.view_settings.curve_mapping.white_level[2] = blue_mult

        # Convert Curve value to Tint
        if green_mult < 1 :
            settings.tint = (green_mult - 1) * 200 # Reverse Tint Math
        else:
            settings.tint = (green_mult - 1) * 50 # Reverse Tint Math

        # Convert Curve value to Temperature
        settings.color_temperature = convert_RGB_to_temperature_table(red_mult,blue_mult)

class PHOTOGRAPHER_OT_WBReset(bpy.types.Operator):
    bl_idname = "white_balance.reset"
    bl_label = "Reset White Balance"
    bl_description = "Reset White Balance"
    bl_options = {'UNDO'}

    use_scene_camera: bpy.props.BoolProperty(default=False)

    def execute(self, context):
        if self.use_scene_camera:
            settings = context.scene.camera.data.photographer
        else:
            settings = context.camera.photographer

        settings.color_temperature = default_color_temperature
        settings.tint = default_tint
        settings.wb_color = (0.5,0.5,0.5)

        return{'FINISHED'}

def white_balance_picker(self,context,event,use_scene_camera):
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

        red = 0
        green = 0
        blue = 0

        # Sample a 9*9 pixels square
        for i in range(x-4, x+5):
            for j in range(y-4, y+5):
                bgl.glReadPixels(i, j, 1, 1, bgl.GL_RGB, bgl.GL_FLOAT, buf)
                red += buf[0]
                green += buf[1]
                blue += buf[2]

        average_r = red / 81
        average_g = green / 81
        average_b = blue / 81

        picked_average = [average_r,average_g,average_b]
        # print (picked_average)

        # Clear Buffer
        del buf

        if picked_average != [0.0,0.0,0.0]:
            convert_RBG_to_whitebalance(picked_average,use_scene_camera)

class PHOTOGRAPHER_OT_WBPicker(bpy.types.Operator):
    bl_idname = "white_balance.picker"
    bl_label = "Pick White Balance"
    bl_description = "Pick a grey area in the 3D view to adjust the White Balance.\n Shift + Click to reset"
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
            context.scene.view_settings.use_curve_mapping = self.stored_use_curve_mapping
            settings.color_temperature = self.stored_color_temperature
            settings.tint = self.stored_tint

            # Restore Focus Planes visibility
            for o in self.fp:
                o.hide_viewport = False

            # Restore Mouse Cursor from EYEDROPPER Icon
            if self.cursor_set:
                context.window.cursor_modal_restore()

            return {'CANCELLED'}

        return {'RUNNING_MODAL'}


    def invoke(self, context, event):
        if event.shift == True:
            bpy.ops.white_balance.reset(use_scene_camera=True)
            return {'FINISHED'}
            
        else:        
            if self.use_scene_camera:
                settings = context.scene.camera.data.photographer
            else:
                settings = context.camera.photographer

            # Store state
            self.stored_use_curve_mapping = context.scene.view_settings.use_curve_mapping
            self.stored_color_temperature = settings.color_temperature
            self.stored_tint = settings.tint

            self.fp = hide_focus_planes()

            if not context.scene.view_settings.use_curve_mapping:
                context.scene.view_settings.use_curve_mapping = True

            args = (self, context, event, self.use_scene_camera)
            if context.area.type=='VIEW_3D':
                self._handle = bpy.types.SpaceView3D.draw_handler_add(white_balance_picker, args, 'WINDOW', 'PRE_VIEW')

            # Set Cursor to EYEDROPPER icon
            self.cursor_set = True
            context.window.cursor_modal_set('EYEDROPPER')

            context.window_manager.modal_handler_add(self)

            return {'RUNNING_MODAL'}
        