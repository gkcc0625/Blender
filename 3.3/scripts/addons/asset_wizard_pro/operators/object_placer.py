# Copyright (C) 2022 Thomas Hoppe (h0bB1T). All rights reserved.
#
# Unauthorized copying of this file via any medium is strictly prohibited.
# Proprietary and confidential.

import bpy, math, mathutils

from typing import Union

from bpy.types import Operator, UILayout
from bpy.props import StringProperty, BoolProperty
from mathutils import Vector
from bpy_extras import view3d_utils

from ..awp.shared import bounding_box
from ..utils.transformation import Transformation
from ..utils.osd import OSD2D, OSD3D
from ..utils.dev import err
from ..utils.blender import IntersectInfo, SelectionHelper, area_under_cursor, duplicate_object, intersection_at_2d, intersection_at_2d_plane, object_by_name, region_of_area, set_active_object
from ..utils.common import round_next, round_next_vector

axis_colors = ( (223/255, 56/255, 80/255, 1), (107/255, 154/255, 31/255, 1), (46/255, 137/255, 239/255, 1) )

class ASSET_OT_object_placer(Operator):
    """
    Used to relocate current object on other objects faces.
    """
    bl_idname = 'awp.object_placer'
    bl_label = ''
    bl_description = ''


    placemode: StringProperty()
    quick: BoolProperty()
    create_copy: BoolProperty()
    linked_copy: BoolProperty()
    auto_parent: BoolProperty()


    @classmethod
    def description(cls, context, properties):
        return {
            'place': 'Place active Object on faces of other Objects',
            'replace': 'Replace targetted Object with active Object',
        }.get(properties.placemode, '??')


    def __init__(self):
        self.__stage = 'place'

        # Changes if axis mode is select. Multiplier for transformation.
        self.__transform_multiplier = Vector((1, 1, 1))
        self.__rotate_to_normal = True
        self.__include_base_location = False
        self.__include_base_rotation = False
        self.__include_base_scale = True

        self.__intersection = None # type: IntersectInfo
        self.__start_point = [0, 0] # Used in sub-adjust modes.
        self.__start_point_3d = Vector((0, 0, 0))
        self.__start_point_view_vector = Vector((0, 0, 1))
        self.__end_point = [0, 0]

        # Used for auto parent feature.
        self.__current_target = None # type: str

        # Used for replace, to restore visual state. Use name here, as
        # the object may be removed.
        self.__old_target = None # type: str
        self.__old_target_display = 'TEXTURED' # default should never be used ..

        # The start transformation of the object that is placed anywhere (moving obj).
        self.__source_transformation = Transformation()

        # These are the values from target (valid in replace mode).
        self.__target_normal = Vector((0, 0, 1))
        self.__target_transformation = Transformation()

        # These are our local ajustments, controlled in 'adjust' stage.
        self.__current_transformation = Transformation()

        # These are values when in G, R or S stage
        self.__temp_transformation = Transformation()
        self.__incr_transformation = Transformation()

        # OSD info panel.
        color_header = ( 0, 162/255, 213/255, 1 )
        color_values = ( .9, .9, .9, 1 )
        color_help = ( .6, .6, .6, 1)

        size_header = 24
        size_values = 16
        size_help = 12

        self.__osd = OSD2D()
        self.__grp = self.__osd.add_group('group', [.2, .2, .2, .9])
        self.__o_header = self.__grp.add_text('header', '', (0, 0), size_header, color=color_header)
        self.__o_spacer1 = self.__grp.add_spacer('spacer1', 6, self.__o_header)
        self.__o_mode = self.__grp.add_text('mode', '', size=size_values, color=color_values, top_element=self.__o_spacer1)
        self.__o_mode_plus = self.__grp.add_text('mode_plus', '', size=size_values, color=color_values, top_element=self.__o_mode)
        self.__o_offset = self.__grp.add_text('offset', '', size=size_values, color=color_values, top_element=self.__o_mode_plus)
        self.__o_rotation = self.__grp.add_text('rotation', '', size=size_values, color=color_values, top_element=self.__o_offset)
        self.__o_scale = self.__grp.add_text('scale', '', size=size_values, color=color_values, top_element=self.__o_rotation)
        self.__o_spacer2 = self.__grp.add_spacer('spacer2', 6, self.__o_scale)
        self.__o_help1 = self.__grp.add_text('help1', '', size=size_help, color=color_help, top_element=self.__o_spacer2)
        self.__o_help2 = self.__grp.add_text('help2', '', size=size_help, color=color_help, top_element=self.__o_help1)
        self.__o_help3 = self.__grp.add_text('help3', '', size=size_help, color=color_help, top_element=self.__o_help2)
        self.__o_help4 = self.__grp.add_text('help4', '', size=size_help, color=color_help, top_element=self.__o_help3)
        self.__o_help5 = self.__grp.add_text('help5', '', size=size_help, color=color_help, top_element=self.__o_help4)
        self.__o_help6 = self.__grp.add_text('help6', '', size=size_help, color=color_help, top_element=self.__o_help5)
        self.__o_help7 = self.__grp.add_text('help7', '', size=size_help, color=color_help, top_element=self.__o_help6)
        self.__o_help8 = self.__grp.add_text('help8', '', size=size_help, color=color_help, top_element=self.__o_help7)
        self.__o_help9 = self.__grp.add_text('help9', '', size=size_help, color=color_help, top_element=self.__o_help8)
        self.__o_help10 = self.__grp.add_text('help10', '', size=size_help, color=color_help, top_element=self.__o_help9)
        self.__o_help = [ 
            self.__o_help1, self.__o_help2, self.__o_help3, self.__o_help4, self.__o_help5,
            self.__o_help6, self.__o_help7, self.__o_help8, self.__o_help9, self.__o_help10,
        ]

        # OSD 3-Point axis.
        self.__osd3d = OSD3D()
        self.__o_x_axis = self.__osd3d.add_lines('X', [ (-0.1, 0, 0), (1, 0, 0) ], axis_colors[0])
        self.__o_y_axis = self.__osd3d.add_lines('Y', [ (0, -0.1, 0), (0, 1, 0) ], axis_colors[1])
        self.__o_z_axis = self.__osd3d.add_lines('Z', [ (0, 0, -0.1), (0, 0, 1) ], axis_colors[2])
        self.__o_sx_axis = self.__osd3d.add_lines('SX', [ (-0.01, 0, 0), (0.1, 0, 0) ], axis_colors[0])
        self.__o_sy_axis = self.__osd3d.add_lines('SY', [ (0, -0.01, 0), (0, 0.1, 0) ], axis_colors[1])
        self.__o_sz_axis = self.__osd3d.add_lines('SZ', [ (0, 0, -0.01), (0, 0, 0.1) ], axis_colors[2])
        self.__o_axes = [ self.__o_x_axis, self.__o_y_axis, self.__o_z_axis, self.__o_sx_axis, self.__o_sy_axis, self.__o_sz_axis ]

        self.__update_osd()


    def __update_osd(self):
        translate_rotate_modifier = self.__translate_rotate_modifier()

        if self.__osd:
            if self.quick:
                stage = 'Quick'
            else:
                stage = {
                    'place': 'Place',
                    'adjust': 'Adjust',
                    'adjustG': 'Move',
                    'adjustR': 'Rotate',
                    'adjustS': 'Scale',
                }.get(self.__stage)

            mode_x = 'X' if self.__transform_multiplier[0] > 0 else ''
            mode_y = 'Y' if self.__transform_multiplier[1] > 0 else ''
            mode_z = 'Z' if self.__transform_multiplier[2] > 0 else ''
            scale_mode = mode_x + mode_y + mode_z
            mode_x = 'X' if translate_rotate_modifier[0] > 0 else ''
            mode_y = 'Y' if translate_rotate_modifier[1] > 0 else ''
            mode_z = 'Z' if translate_rotate_modifier[2] > 0 else ''  
            mode = mode_x + mode_y + mode_z          

            self.__o_mode.text = f'Stage: {stage}, Normal: { "On" if self.__rotate_to_normal else "Off" }, Mode: {mode}, Scale-Mode: {scale_mode}'
            self.__o_mode_plus.text = f'Base Location: { "On" if self.__include_base_location else "Off" }, Rotation: { "On" if self.__include_base_rotation else "Off" }, Scale: { "On" if self.__include_base_scale else "Off" }'

            combined = self.__current_transformation + self.__temp_transformation
            self.__o_offset.text = f'Offset: {combined.str_location()}'
            self.__o_rotation.text = f'Rotation: {combined.str_rotation()}'
            self.__o_scale.text = f'Scale: {combined.str_scale()}'

            help = []
            if self.quick:
                help = [
                    'N - Align to Normal . LMB - Finish . RMB,ESC - Cancel',
                    'Ctrl-Wheel - Rotate . Alt-Wheel - Scale . Ctrl-Alt-Wheel - Move',
                    'C,X,Y,Z - Select Axis . Shift - Fine Control . OSKey - Coarse Control',
                    'Ctrl-X, Ctrl-Y, Ctrl-Z - Flip Rotation by 180° on Axis',
                    'Alt-G, Alt-R, Alt-S - Toggle Base Inclusion',
                    'H - Toggle Visibility of this Panel . Q - Reset Transformation',
                ]
            elif self.__stage == 'place':
                help = [
                    'N - Align to Normal . LMB - Continue . RMB,ESC - Cancel',
                ]
            elif self.__stage == 'adjust':
                help = [
                    'LMB - Finish . RMB,ESC - Return to Placement',
                    'G - Move Mode . R - Rotate Mode . S - Scale Mode',
                    'Ctrl-Wheel - Rotate . Alt-Wheel - Scale . Ctrl-Alt-Wheel - Move',
                    'C,X,Y,Z - Select Axis . Shift - Fine Control . OSKey - Coarse Control',
                    'Ctrl-X, Ctrl-Y, Ctrl-Z - Flip Rotation by 180° on Axis',
                    'Alt-G, Alt-R, Alt-S - Toggle Base Inclusion',
                    'H - Toggle Visibility of this Panel . Q - Reset Transformation',
                ]
            elif self.__stage in { 'adjustG', 'adjustR', 'adjustS' }:
                mode = {
                    'adjustG': 'Move',
                    'adjustR': 'Rotate',
                    'adjustS': 'Scale'
                }[self.__stage]
                help = [
                    'LMB - Assign, back to Adjust . RMB,ESC - Drop, back to Adjust',
                    f'Mouse - {mode} . G - Move Mode . R - Rotate Mode . S - Scale Mode',
                    'C,X,Y,Z - Axis . Shift - Fine Control . Ctrl - Snap',
                    'Alt-G, Alt-R, Alt-S - Toggle Base Inclusion',
                    'H - Toggle Visibility of this Panel',
                ]

            [ o.set_visible(False) for o in self.__o_help ]
            for i, h in enumerate(help):
                self.__o_help[i].set_visible(True)
                self.__o_help[i].text = h


        if self.__osd3d:
            for i in range(3):
                on = translate_rotate_modifier[i] > 0
                self.__o_axes[i].color = axis_colors[i] if on else (.3, .3, .3, 1)
                self.__o_axes[i].width = 3 if on else 1
                on = self.__transform_multiplier[i] > 0
                self.__o_axes[3+i].color = axis_colors[i] if on else (.3, .3, .3, 1)
                self.__o_axes[3+i].width = 30 if on else 5


    def __translate_rotate_modifier(self) -> Vector:
        """
        Depending on mode, the transform modifier is useless to be (1, 1, 1) for 
        translation and rotation. Specific when using the wheel in quick and adjust mode.
        Limit it to 'Z' in this case.
        """
        if self.quick or self.__stage == 'adjust':
            if sum(self.__transform_multiplier[:]) > 2.999:
                return Vector((0, 0, 1))
        return self.__transform_multiplier


    def __cleanup(self, success: bool):
        """
        Called when exiting the operator. success is true, when leaving the object 
        at the new position, false to revert old or remove the copy.
        """
        # Clear UI overlay.
        if self.__osd:
            self.__osd.unregister()
            self.__osd = None

        if self.__osd3d:
            self.__osd3d.unregister()
            self.__osd3d = None

        ASSET_OT_object_placer.set_active(False)

        # Redraw all areas of type 3DView, to remove overlay artifacts..
        area: bpy.types.Area
        for area in bpy.context.screen.areas:
            if area.type == 'VIEW_3D':
                area.tag_redraw()

        # Cleanup if user cancels.
        if not success:
            obj = self.__moving_obj()
            if obj:
                if self.create_copy:
                    # Remove copy.
                    bpy.data.objects.remove(obj)
                else:
                    # Restore original position.
                    self.__source_transformation.to_object(obj)
        else:
            if self.placemode == 'place' and self.auto_parent and self.__current_target:
                obj = self.__moving_obj()
                if self.__current_target in bpy.data.objects:
                    target = bpy.data.objects[self.__current_target]
                if obj and target:
                    self.__selection_helper.select_only(obj)
                    if obj.parent:
                        bpy.ops.object.parent_clear()        
                    set_active_object(target)
                    bpy.ops.object.parent_set()

            # In replace mode, on succes, remove target.
            if self.placemode == 'replace':
                o = object_by_name(self.__old_target)
                if o: bpy.data.objects.remove(o)
                    
        # Restore default state.
        self.__visualize_target(self.__old_target, False)
        self.__old_target = None

        # Restore previous selection state.
        self.__selection_helper.restore()


    def __moving_obj(self) -> Union[bpy.types.Object, None]:
        """
        Return currently moving object, original or copy.
        """
        if self.__obj_name in bpy.data.objects:
            return bpy.data.objects[self.__obj_name]


    def __visualize_target(self, target: Union[str, None], enable: bool):
        """
        Set potentional replace target into wireframe mode, so the replacement
        can be better seen.
        """
        if target and (target in bpy.data.objects):
            t = bpy.data.objects[target]
            if enable:
                self.__old_target_display = t.display_type
                t.display_type = 'WIRE'
            else:
                t.display_type = self.__old_target_display


    def __update_object(self, obj: bpy.types.Object, intersection: Union[IntersectInfo, None] = None):
        """
        Place moved object to intersection point or replace position, depending on current mode.
        """
        # Use from last call, but may still be None
        if not intersection:
            intersection = self.__intersection
        self.__intersection = intersection

        if intersection:
            if self.placemode == 'place':
                self.__update_object_place(obj, intersection)
            else:
                self.__update_object_replace(obj, intersection)

            self.__adjust()


    def __update_object_place(self, obj: bpy.types.Object, intersection: IntersectInfo):
        """
        Used in place mode.
        """
        self.__target_transformation = Transformation(location=intersection.world_location)
        self.__target_normal = Vector(intersection.world_normal)


    def __update_object_replace(self, obj: bpy.types.Object, intersection: Union[IntersectInfo, None] = None):
        """
        Used in replace mode.
        """
        # Need target in any case.
        target = intersection.obj
        if target:
            # Check if target has changed, update visualization in this case.
            if target.name != self.__old_target:
                # Reset old and activate current.
                self.__visualize_target(self.__old_target, False)
                self.__visualize_target(target.name, True)
                self.__old_target = target.name

            # Use target objects data for moving object.
            self.__target_transformation = Transformation.from_object(target)


    def __adjust(self):
        """
        Calculate the final transformation on our current values and apply to moving object.
        """
        obj = self.__moving_obj()
        if obj:
            # Convert normal to rotation.
            if self.__rotate_to_normal:
                normal_t = Transformation(rotation=Vector((0, 0, 1)).rotation_difference(self.__target_normal))
            else:
                normal_t = Transformation()

            # We may include some transformation from the object we want to place anywhere (default scale).
            source_t = self.__source_transformation.copy()
            if not self.__include_base_location: source_t.reset_location()
            if not self.__include_base_rotation: source_t.reset_rotation()
            if not self.__include_base_scale: source_t.reset_scale()

            # The transformation, where to insert to object.
            target_t = self.__target_transformation

            # This is static and dynamic transformation we adjust in the operator, combine them.
            total_t = self.__current_transformation + self.__temp_transformation

            # Combine the final transformation, order is very important!
            final_t = total_t + normal_t + target_t + source_t

            final_t.to_object(obj)

            for a in self.__o_axes:
                a.location = target_t.location()
                if self.placemode == 'place':
                    a.rotation = normal_t.rotation_euler()
                else:
                    a.rotation = target_t.rotation_euler()

            self.__update_osd()


    def __reset_temp(self):
        """
        Reset temp transformation, when switch G, R or S or leaving these modes.
        """
        self.__incr_transformation.reset()
        self.__temp_transformation.reset()


    def __evaluate_temp(self, window: Union[bpy.types.Region, None], fine: bool, snap: bool):
        """
        Used in sub-adjust modes (adjust*), to calculate temp transformation
        from object origin to mouse cursor.
        """
        # Need to find mouse positions on coplanar view plane, relative to object origin.
        if window:
            plane_pos = self.__start_point_3d
            plane_normal = self.__start_point_view_vector.normalized()
            start = intersection_at_2d_plane(window, window.data, self.__start_point, plane_pos, plane_normal)
            end = intersection_at_2d_plane(window, window.data, self.__end_point, plane_pos, plane_normal)
            self.__start_point = self.__end_point

            if self.__rotate_to_normal:
                normal_rotation = self.__target_normal.rotation_difference(Vector((0, 0, 1))).to_euler()
            else:
                normal_rotation = mathutils.Euler()

            if start and end:
                start_3d = Vector(start.world_location)
                end_3d = Vector(end.world_location)
                start_3d.rotate(normal_rotation)
                end_3d.rotate(normal_rotation)

                fac = 0.1 if fine else 1
                rfac = math.radians(1 if fine else 5)
                if self.__stage == 'adjustG':
                    move_vector = (end_3d - start_3d) * fac
                    self.__incr_transformation.add_location(move_vector)
                    temp_position = self.__incr_transformation.location()
                    if snap:
                        temp_position = round_next_vector(temp_position, fac)
                    self.__temp_transformation.set_location(self.__transform_multiplier * temp_position)
                elif self.__stage == 'adjustR': 
                    v0 = start_3d - plane_pos # type: Vector
                    v1 = end_3d - plane_pos # type: Vector
                    rotation_euler = v0.rotation_difference(v1).to_euler()
                    rotation_vector = Vector(rotation_euler[:]) * fac * 5
                    self.__incr_transformation.add_rotation(rotation_vector)
                    temp_rotation = Vector(self.__incr_transformation.rotation_euler()[:])
                    if snap:
                        temp_rotation = round_next_vector(temp_rotation, rfac)
                    self.__temp_transformation.set_rotation(self.__transform_multiplier * temp_rotation)
                elif self.__stage == 'adjustS':
                    d_start = (start_3d - plane_pos).length
                    d_end = (end_3d - plane_pos).length
                    move_dist = (d_end - d_start) * fac # type: float
                    self.__incr_transformation.add_scale(move_dist)
                    temp_scale = self.__incr_transformation.scale()
                    if snap:
                        temp_scale = round_next_vector(temp_scale, fac)
                    # Set to 1 where __transform_multiplier == 1
                    self.__temp_transformation.set_scale(Vector((
                        temp_scale[0] if self.__transform_multiplier[0] > 0 else 1.0,
                        temp_scale[1] if self.__transform_multiplier[1] > 0 else 1.0,
                        temp_scale[2] if self.__transform_multiplier[2] > 0 else 1.0,
                    )))


    def modal(self, context: bpy.types.Context, event: bpy.types.Event):
        try:
            return self.__modal(context, event)
        except:
            err('Something goes wrong')

            # Clear UI overlay.
            if self.__osd:
                self.__osd.unregister()
                self.__osd = None

            if self.__osd3d:
                self.__osd3d.unregister()
                self.__osd3d = None

            ASSET_OT_object_placer.set_active(False)

            return {'CANCELLED'}


    def __modal(self, context: bpy.types.Context, event: bpy.types.Event):
        """
        Called on every event.
        """
        # Force redraw.
        context.area.tag_redraw()

        # Find info about the view below the cursor.
        # Check if cursor is in 3D view area, get this one.
        px, py, area = area_under_cursor(event.mouse_x, event.mouse_y)
        if area and area.type == 'VIEW_3D':
            # Find region of type window.
            view3d_window = region_of_area(area, 'WINDOW')
        else:
            view3d_window = None

        # Update OSD.
        #self.__o_header.position = (25, self.__grp.size()[1] + 10)
        self.__o_header.position = (px + 40, py - 40)
        self.__update_osd()

        if event.type == 'MOUSEMOVE':
            # Adjust position/target in this stage only.
            if self.__stage == 'place' or self.quick: 
                obj = self.__moving_obj()
                if obj:
                    if view3d_window:
                        # Now we can do the intersection test in the 3d view, the cursor is currently in.
                        # Find all meshes to test intersection with, exclude self.
                        meshes = [ o for o in context.selectable_objects if o.type == 'MESH' ]
                        if obj in meshes:
                            meshes.remove(obj)

                        # Check for intersections.
                        intersections = intersection_at_2d(view3d_window, view3d_window.data, (px, py), meshes)
                        if intersections:
                            self.__current_target = intersections[0].obj.name
                            self.__update_object(obj, intersections[0])
                            self.__o_header.text = intersections[0].obj.name
                        else:
                            # No object intersection, use world plane.
                            self.__current_target = None
                            self.__update_object(obj, intersection_at_2d_plane(view3d_window, view3d_window.data, (px, py)))
                            self.__o_header.text = 'Ground Plane'
            elif self.__stage.startswith('adjust'):
                self.__end_point = [event.mouse_region_x, event.mouse_region_y]
                self.__evaluate_temp(view3d_window, event.shift, event.ctrl)
                self.__adjust()

                self.__update_osd()


        elif event.type in { 'WHEELDOWNMOUSE', 'WHEELUPMOUSE' }:
            dir = -1 if event.type == 'WHEELDOWNMOUSE' else 1
            offset_step_size = 1 if event.oskey else (0.01 if event.shift else 0.1)
            scale_step_size = offset_step_size
            rotate_step_size = math.radians(45 if event.oskey else (1 if event.shift else 5))
            translate_rotate_modifier = self.__translate_rotate_modifier()

            if self.__stage == 'adjust' or self.quick:
                if event.ctrl or event.alt:
                    if event.ctrl and event.alt:
                        self.__current_transformation.add_location(translate_rotate_modifier * (dir * offset_step_size))
                    elif event.alt:
                        self.__current_transformation.add_scale(self.__transform_multiplier * (dir * scale_step_size))
                    elif event.ctrl:
                        self.__current_transformation.add_rotation(translate_rotate_modifier * (dir * rotate_step_size))

                    self.__adjust()
                    return {'RUNNING_MODAL'}

        elif event.type in { 'G', 'R', 'S' } and event.value == 'PRESS':
            if self.__stage.startswith('adjust') or self.quick:
                if event.alt:
                    if event.type == 'G': self.__include_base_location = not self.__include_base_location
                    elif event.type == 'R': self.__include_base_rotation = not self.__include_base_rotation
                    elif event.type == 'S': self.__include_base_scale = not self.__include_base_scale
                    self.__adjust()
                    return {'RUNNING_MODAL'}

            # If pressed in adjust mode, enter sub-adjust mode or switches to them.
            if self.__stage.startswith('adjust'):
                # Set start point only when entering sub-adjust, not switching.
                if self.__stage == 'adjust':
                    self.__start_point = [event.mouse_region_x, event.mouse_region_y]
                    o = self.__moving_obj()
                    if o:
                        self.__start_point_3d = Vector(o.location[:])
                        if view3d_window:
                            self.__start_point_view_vector = \
                                view3d_utils.region_2d_to_vector_3d(view3d_window, view3d_window.data, (px, py))
                self.__stage = f'adjust{event.type}'
                self.__reset_temp()
                self.__evaluate_temp(view3d_window, event.shift, event.ctrl)
                self.__adjust()
            return {'RUNNING_MODAL'}

        elif event.type in { 'X', 'Y', 'Z', 'C' } and event.value == 'PRESS':
            if event.ctrl and event.type in { 'X', 'Y', 'Z' }:
                amount = math.radians(180)
                self.__current_transformation += Transformation(rotation={
                    'X': [ amount, 0, 0 ],
                    'Y': [ 0, amount, 0 ],
                    'Z': [ 0, 0, amount ],
                }[event.type])
                self.__adjust()
                return {'RUNNING_MODAL'}

            # Adjusts axis affected by transformation.
            if self.__stage.startswith('adjust') or self.quick:
                if event.shift:
                    self.__transform_multiplier = Vector({
                        'X': (0, 1, 1),
                        'Y': (1, 0, 1),
                        'Z': (1, 1, 0),
                        'C': (1, 1, 1),
                    }.get(event.type))
                else:
                    self.__transform_multiplier = Vector({
                        'X': (1, 0, 0),
                        'Y': (0, 1, 0),
                        'Z': (0, 0, 1),
                        'C': (1, 1, 1),
                    }.get(event.type))

                self.__evaluate_temp(view3d_window, event.shift, event.ctrl)
                self.__adjust()
            return {'RUNNING_MODAL'}

        elif event.type == 'N' and event.value == 'PRESS':
            # Toggle flag to use intersection normal for orientation.
            if self.__stage == 'place' or self.quick:
                self.__rotate_to_normal = not self.__rotate_to_normal

                self.__adjust()
                return {'RUNNING_MODAL'}

        elif event.type == 'H' and event.value == 'PRESS':
            # Toggle OSD visibility.
            self.__osd.toggle_visibility()
            return {'RUNNING_MODAL'}               

        elif event.type == 'Q' and event.value == 'PRESS':
            # Reset current transformations.
            if self.__stage == 'adjust' or self.quick:
                self.__current_transformation.reset()
                self.__adjust()
            return {'RUNNING_MODAL'}                        

        elif event.type in { 'LEFTMOUSE' } and event.value == 'PRESS':
            # LMB in quick mode just finishes.
            if self.quick:
                self.__cleanup(True)
                return {'CANCELLED'}

            # LMB in place mode enters adjust mode.
            if self.__stage == 'place':
                self.__stage = 'adjust'
                return {'RUNNING_MODAL'}

            # LMB in adjust mode finishes.
            if self.__stage == 'adjust':
                self.__cleanup(True)
                return {'CANCELLED'}
            
            # LMB in sub-adjust mode (GRS) adds temp to current and returns to
            # adjust mode.
            if self.__stage.startswith('adjust'):
                self.__stage = 'adjust'
                self.__current_transformation += self.__temp_transformation
                self.__reset_temp()
                return {'RUNNING_MODAL'}

        elif event.type in { 'ESC', 'RIGHTMOUSE' } and event.value == 'PRESS':
            # RMB in quick mode just cancels.
            if self.quick:
                self.__cleanup(False)
                return {'CANCELLED'}

            # RMB in place mode cancels.
            if self.__stage == 'place':
                self.__cleanup(False)
                return {'CANCELLED'}

            # RMB in adjust mode falls back to place mode.
            if self.__stage == 'adjust':
                self.__stage = 'place'
                return {'RUNNING_MODAL'}

            # RMB in sub-adjust mode (GRS) resets temp returns to
            # adjust mode.
            if self.__stage.startswith('adjust'):
                self.__stage = 'adjust'
                self.__reset_temp()
                return {'RUNNING_MODAL'}


        # Pass through to be able to navigate 3D view.
        return {'PASS_THROUGH'}


    def invoke(self, context: bpy.types.Context, event: bpy.types.Event):
        if ASSET_OT_object_placer.is_active():
            return {'FINISHED'}

        obj = context.active_object
        if not obj:
            self.report({'ERROR'}, 'No active Object')
            return {'FINISHED'}

        if obj.library:
            self.report({'ERROR'}, 'Object is Library Object, make Library Override first')
            return {'FINISHED'}

        self.__selection_helper = SelectionHelper(True)

        self.__original_obj_name = obj.name
        if self.create_copy:
            self.__obj = duplicate_object(obj, self.linked_copy)
        else:
            self.__obj = obj

        self.__selection_helper.select_only(self.__obj)
        self.__obj_name = self.__obj.name
        self.__source_transformation = Transformation.from_object(obj)

        self.__osd.register()
        self.__osd3d.register()

        # Scale axis to 2 times largest dimension of object bounding box.
        length = max(0.5, 2 * max(bounding_box([obj])[0]))
        for a in self.__o_axes:
            a.scale = Vector((length, length, length))

        #bpy.context.workspace.status_text_set(text='ESC - Stop')
        context.window_manager.modal_handler_add(self)

        ASSET_OT_object_placer.set_active(True)

        return {'RUNNING_MODAL'}


    @staticmethod
    def is_active() -> bool:
        global _object_placer_active
        return _object_placer_active


    @staticmethod
    def set_active(active: bool):
        global _object_placer_active
        _object_placer_active = active


    @staticmethod
    def create_ui(l: UILayout, replace: bool, quick: bool, create_copy: bool, linked_copy: bool, auto_parent: bool):
        text = 'Place Copy' if create_copy else 'Place Object'
        op = l.operator(ASSET_OT_object_placer.bl_idname, text=text, icon='ORIENTATION_NORMAL') # type: ASSET_OT_object_placer
        op.placemode = 'replace' if replace else 'place'
        op.quick = quick
        op.create_copy = create_copy
        op.linked_copy = linked_copy
        op.auto_parent = auto_parent


_object_placer_active = False
