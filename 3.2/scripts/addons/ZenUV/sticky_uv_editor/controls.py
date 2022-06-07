# ##### BEGIN GPL LICENSE BLOCK #####
#
#  This program is free software; you can redistribute it and/or
#  modify it under the terms of the GNU General Public License
#  as published by the Free Software Foundation; either version 2
#  of the License, or (at your option) any later version.
#
#  This program is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#  GNU General Public License for more details.
#
#  You should have received a copy of the GNU General Public License
#  along with this program; if not, write to the Free Software Foundation,
#  Inc., 51 Franklin Street, Fifth Floor, Boston, MA 02110-1301, USA.
#
# ##### END GPL LICENSE BLOCK #####

# <pep8 compliant>

# Sticky UV Editor
# Developed by Oleg Stepanov (DotBow)
# https://github.com/DotBow/Blender-Sticky-UV-Editor-Add-on


import os
import bpy
from bpy.props import BoolProperty
from bpy.types import GizmoGroup, Operator


def get_prefs():
    """ Return Zen UV Properties obj """
    return bpy.context.preferences.addons[get_name()].preferences


def get_name():
    """Get Name"""
    return os.path.basename(get_path())


def get_path():
    """Get the path of Addon"""
    return os.path.dirname(os.path.dirname(os.path.realpath(__file__)))


class StickyUVEditorSplit(Operator):
    """Open UV Editor in a separate window."""
    bl_idname = "wm.sticky_uv_editor_split"
    bl_label = "Sticky UV Editor Split"
    bl_options = {'INTERNAL'}

    @classmethod
    def poll(self, context):
        return context.area.ui_type == 'VIEW_3D'

    def invoke(self, context, event):
        scene = context.scene
        active_area = context.area
        addon_prefs = get_prefs()

        if addon_prefs.uv_editor_side == 'LEFT':
            for area in reversed(context.screen.areas):
                if area.ui_type == 'VIEW_3D':
                    uv_area = area
                    break
        else:
            uv_area = active_area

        ui_type = active_area.ui_type
        uv_area.ui_type = 'UV'

        # Set UV Editor area settings
        uv_editor_settings = scene.uv_editor_settings

        if (uv_editor_settings.initialized is False) or \
                (addon_prefs.remember_uv_editor_settings is False):
            uv_editor_settings.save_from_property(
                addon_prefs.uv_editor_settings)
            uv_editor_settings.initialized = True
            scene.tool_settings.use_uv_select_sync = \
                addon_prefs.use_uv_select_sync

        uv_editor_settings.set(uv_area)

        # Set view mode
        view_mode = addon_prefs.view_mode

        if (view_mode != 'DISABLE') and (context.mode == 'EDIT_MESH'):
            override = {'window': context.window,
                        'screen': context.window.screen, 'area': uv_area}

            if view_mode == 'FRAME_ALL':
                bpy.ops.image.view_all(override)
            elif view_mode == 'FRAME_SELECTED':
                bpy.ops.image.view_selected(override)
            elif view_mode == 'FRAME_ALL_FIT':
                bpy.ops.image.view_all(override, fit_view=True)

        # Open UV Editor in new window
        # if event.alt:
        bpy.ops.screen.area_dupli('INVOKE_DEFAULT')
        active_area.ui_type = ui_type

        return {'FINISHED'}


class StickyUVEditor(Operator):
    """\
Show/Hide UV Editor on the right side of the 3D Viewport.
Hold 'Alt' to open UV Editor in a separate window."""
    bl_idname = "wm.sticky_uv_editor"
    bl_label = "Sticky UV Editor"
    bl_options = {'INTERNAL'}

    ui_button: BoolProperty(default=False)

    @classmethod
    def poll(self, context):
        return context.area.ui_type in ['UV', 'VIEW_3D']

    def invoke(self, context, event):
        scene = context.scene
        active_area = context.area
        app_version = bpy.app.version

        if not event.alt:
            if context.window.screen.show_fullscreen is True:
                self.report({'WARNING'},
                            "Sticky UV Editor: Fullscreen mode is not supported!")
                return {'FINISHED'}

            areas = context.screen.areas
            active_area_x = active_area.x
            active_area_y = active_area.y
            active_area_width = active_area.width

            # Close existing UV Editor
            if active_area.ui_type == 'UV':
                for area in areas:
                    if area.ui_type == 'VIEW_3D':
                        area_x = area.x
                        area_y = area.y
                        area_width = area.width

                        # Areas in one horizontal space
                        if area_y == active_area_y:
                            # UV Editor on left
                            if (active_area_x + active_area_width + 1) == area_x:
                                # Save UV Editor area settings
                                scene.uv_editor_settings.save_from_area(
                                    active_area)

                                # Close UV Editor area
                                if app_version >= (3, 0, 0):
                                    bpy.ops.screen.area_close(
                                        {"area": active_area})
                                else:
                                    bpy.ops.screen.area_join(
                                        cursor=(area_x, area_y + 10))

                                    # Force update layout
                                    space = area.spaces[0]
                                    space.show_region_toolbar = \
                                        space.show_region_toolbar

                                return {'FINISHED'}

                            # UV Editor on right
                            if (area_x + area_width + 1) == active_area_x:
                                # Save UV Editor area settings
                                scene.uv_editor_settings.save_from_area(
                                    active_area)

                                # Close UV Editor area
                                if app_version >= (3, 0, 0):
                                    bpy.ops.screen.area_close(
                                        {"area": active_area})
                                else:
                                    bpy.ops.screen.area_swap(
                                        cursor=(active_area_x, active_area_y + 10))
                                    bpy.ops.screen.area_join(
                                        cursor=(active_area_x, active_area_y + 10))

                                    # Force update layout
                                    space = active_area.spaces[0]
                                    space.show_region_toolbar = \
                                        space.show_region_toolbar

                                return {'FINISHED'}

                self.report({'WARNING'},
                            "Sticky UV Editor: Failed to figure out current layout!")
                return {'FINISHED'}
            elif active_area.ui_type == 'VIEW_3D':
                for area in areas:
                    if area.ui_type == 'UV':
                        area_x = area.x
                        area_y = area.y
                        area_width = area.width

                        # Areas in one horizontal space
                        if area_y == active_area_y:
                            # 3D View on left
                            if (active_area_x + active_area_width + 1) == area_x:
                                # Save UV Editor area settings
                                scene.uv_editor_settings.save_from_area(area)

                                # Close UV Editor area
                                if app_version >= (3, 0, 0):
                                    bpy.ops.screen.area_close({"area": area})
                                else:
                                    bpy.ops.screen.area_swap(
                                        cursor=(area_x, area_y + 10))
                                    bpy.ops.screen.area_join(
                                        cursor=(area_x, area_y + 10))

                                    # Force update layout
                                    space = area.spaces[0]
                                    space.show_region_toolbar = \
                                        space.show_region_toolbar

                                return {'FINISHED'}

                            # 3D View on right
                            if (area_x + area_width + 1) == active_area_x:
                                # Save UV Editor area settings
                                scene.uv_editor_settings.save_from_area(area)

                                # Close UV Editor area
                                if app_version >= (3, 0, 0):
                                    bpy.ops.screen.area_close({"area": area})
                                else:
                                    bpy.ops.screen.area_join(
                                        cursor=(active_area_x, active_area_y + 10))

                                    # Force update layout
                                    space = active_area.spaces[0]
                                    space.show_region_toolbar = \
                                        space.show_region_toolbar

                                return {'FINISHED'}

            # Split active 3D View area
            bpy.ops.screen.area_split(
                direction='VERTICAL', factor=0.5)

        # Open UV Editor
        addon_prefs = get_prefs()

        if addon_prefs.uv_editor_side == 'LEFT':
            for area in reversed(context.screen.areas):
                if area.ui_type == 'VIEW_3D':
                    uv_area = area
                    break

            if self.ui_button is True:
                context.window.cursor_warp(
                    event.mouse_x + context.area.width * 0.5, event.mouse_y)
        else:
            uv_area = active_area

            if self.ui_button is True:
                context.window.cursor_warp(
                    event.mouse_x - context.area.width * 0.5, event.mouse_y)

        ui_type = active_area.ui_type
        uv_area.ui_type = 'UV'

        # Set UV Editor area settings
        uv_editor_settings = scene.uv_editor_settings

        if (uv_editor_settings.initialized is False) or \
                (addon_prefs.remember_uv_editor_settings is False):
            uv_editor_settings.save_from_property(
                addon_prefs.uv_editor_settings)
            uv_editor_settings.initialized = True
            scene.tool_settings.use_uv_select_sync = \
                addon_prefs.use_uv_select_sync

        uv_editor_settings.set(uv_area)

        # Set view mode
        view_mode = addon_prefs.view_mode

        if (view_mode != 'DISABLE') and (context.mode == 'EDIT_MESH'):
            override = {'window': context.window,
                        'screen': context.window.screen, 'area': uv_area}

            if view_mode == 'FRAME_ALL':
                bpy.ops.image.view_all(override)
            elif view_mode == 'FRAME_SELECTED':
                bpy.ops.image.view_selected(override)
            elif view_mode == 'FRAME_ALL_FIT':
                bpy.ops.image.view_all(override, fit_view=True)

        # Open UV Editor in new window
        if event.alt:
            bpy.ops.screen.area_dupli('INVOKE_DEFAULT')
            active_area.ui_type = ui_type

        return {'FINISHED'}


class StickyUVEditor_UI_Button(GizmoGroup):
    bl_idname = "StickyUVEditor_UI_Button"
    bl_label = "Sticky UV Editor UI Button"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'WINDOW'
    bl_options = {'PERSISTENT', 'SCALE'}

    @classmethod
    def poll(cls, context):
        addon_prefs = get_prefs()
        return (addon_prefs.show_ui_button) and \
            (not context.window.screen.show_fullscreen)

    def draw_prepare(self, context):
        addon_prefs = get_prefs()
        ui_scale = context.preferences.view.ui_scale

        width = 0
        padding = 20 * ui_scale

        if addon_prefs.uv_editor_side == 'LEFT':
            for region in bpy.context.area.regions:
                if region.type == "TOOLS":
                    width = region.width
                    break

            self.foo_gizmo.matrix_basis[0][3] = width + padding
        else:
            for region in bpy.context.area.regions:
                if region.type == "UI":
                    width = region.width
                    break

            self.foo_gizmo.matrix_basis[0][3] = \
                context.region.width - padding - width

        # self.foo_gizmo.matrix_basis[1][3] = context.region.height * 0.1
        self.foo_gizmo.matrix_basis[1][3] = context.region.height * addon_prefs.stk_ed_button_v_position * 0.01

    def setup(self, context):
        mpr = self.gizmos.new("GIZMO_GT_button_2d")
        mpr.show_drag = False
        mpr.icon = 'UV'
        mpr.draw_options = {'BACKDROP', 'OUTLINE'}

        mpr.color = 0.0, 0.0, 0.0
        mpr.alpha = 0.5
        mpr.color_highlight = 0.8, 0.8, 0.8
        mpr.alpha_highlight = 0.2

        mpr.scale_basis = (80 * 0.35) / 2  # Same as buttons defined in C
        op = mpr.target_set_operator("wm.sticky_uv_editor")
        op.ui_button = True
        self.foo_gizmo = mpr
