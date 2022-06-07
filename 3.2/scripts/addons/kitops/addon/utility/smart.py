import os

import bpy

from bpy.types import Operator
from bpy.props import *
from bpy.utils import register_class, unregister_class

from . import addon, bbox, id, insert, modifier, remove

#XXX: type and reference error
#DEPRECATED TODO this method now does nothing - remove if it works out ok.
def toggles_depsgraph_update_post():
    return
    option = addon.option()

    solid_inserts = insert.collect(solids=True, all=True)
    count = 0
    for obj in solid_inserts:
        try:
            if obj.hide_viewport:
                option['show_solid_objects'] = False
                break
            elif obj.name in bpy.context.view_layer.objects and not obj.select_get():
                count += 1
        except RuntimeError: pass

    if count > 2 and count == len(solid_inserts):
        option['show_solid_objects'] = True

    boolean_inserts = insert.collect(cutters=True, all=True)
    count = 0
    for obj in boolean_inserts:
        try:
            if obj.hide_viewport:
                option['show_cutter_objects'] = False
                break
            elif not obj.select_get():
                count += 1
        except RuntimeError: pass

    if count > 2 and count == len(boolean_inserts):
        option['show_cutter_objects'] = True

    wire_inserts = insert.collect(wires=True, all=True)
    count = 0
    for obj in wire_inserts:
        try:
            if obj.hide_viewport:
                option['show_wire_objects'] = False
                break
            elif not obj.select_get():
                count += 1
        except RuntimeError: pass

    if count > 2 and count == len(wire_inserts):
        option['show_wire_objects'] = True


def insert_depsgraph_update_pre():
    collected_objects = bpy.context.scene.collection.all_objects[:]

    if not hasattr(bpy.context, 'visible_objects'):
        return

    if bpy.context.scene and not bpy.context.scene.kitops.thumbnail:
        for obj in bpy.context.visible_objects:
            for mod in obj.modifiers:
                if mod.type != 'BOOLEAN':
                    continue

                if mod.object and mod.object.kitops.insert and mod.object not in collected_objects:
                    obj.modifiers.remove(mod)

    if addon.preference().mode != 'SMART':
        return

    if not insert.operator:
        insert.show_solid_objects()
        insert.show_cutter_objects()
        insert.show_wire_objects()

    objects = [obj for obj in collected_objects if not obj.kitops.insert and obj.type == 'MESH']
    inserts = [obj for obj in sorted(collected_objects, key=lambda o: o.name) if obj.kitops.insert and not obj.kitops.applied]

    for ins in inserts:
        if ins.kitops.type == 'CUTTER' and ins.kitops.insert_target:
            available = False
            for mod in ins.kitops.insert_target.modifiers:
                if mod.type == 'BOOLEAN' and mod.object == ins:
                    available = True

                    break

            if not available and ins.kitops.boolean_type != 'INSERT':
                insert.add_boolean(ins)

        if ins.kitops.type != 'CUTTER':
            continue

        for obj in objects:
            for mod in obj.modifiers:
                if mod.type != 'BOOLEAN':
                    continue

                if mod.object == obj and obj != obj.kitops.insert_target and obj.kitops.boolean_type != 'INSERT':
                    obj.modifiers.remove(mod)


def add_mirror(obj, axis='X'):
    obj.kitops.mirror = True
    mod = obj.modifiers.new(name='KIT OPS Mirror', type='MIRROR')

    if mod:
        mod.show_expanded = False
        mod.use_axis[0] = False

        index = {'X': 0, 'Y': 1, 'Z': 2} # patch inplace for api change
        axis_to_use = getattr(obj.kitops, F'mirror_{axis.lower()}')
        mod.use_axis[index[axis]] = axis_to_use


        mod.mirror_object = obj.kitops.insert_target
        obj.kitops.mirror_target = obj.kitops.insert_target


def validate_mirror(inserts, axis='X'):
    for obj in inserts:
        if obj.kitops.mirror:

            available = False
            # assuming our mirror is most recent
            for modifier in reversed(obj.modifiers):

                if modifier.type == 'MIRROR' and modifier.mirror_object == obj.kitops.mirror_target:
                    available = True
                    index = {'X': 0, 'Y': 1, 'Z': 2} # patch inplace for api change
                    axis_to_use = getattr(obj.kitops, F'mirror_{axis.lower()}')
                    modifier.use_axis[index[axis]] = axis_to_use


                    if True not in modifier.use_axis[:]:
                        obj.kitops.mirror = False
                        obj.kitops.mirror_target = None
                        obj.modifiers.remove(modifier)

                    break

            if not available:
                add_mirror(obj, axis=axis)

        else:
            add_mirror(obj, axis=axis)



# XXX: align needs to check dimensions with current insert disabled
class KO_OT_align_horizontal(Operator):
    bl_idname = 'ko.align_horizontal'
    bl_label = 'Align horizontal'
    bl_description = 'Align selected INSERTS horizontally within target bounds'
    bl_options = {'REGISTER', 'UNDO'}

    y_axis: BoolProperty(
        name = 'Y Axis',
        description = 'Use the y axis of the INSERT TARGET for alignment',
        default = False)

    def execute(self, context):

        # get mains
        mains = insert.collect(context.selected_objects, mains=True)

        for main in mains:
            if main.kitops.insert_target:
                center = bbox.center(main.kitops.insert_target)
                setattr(main.location, 'y' if self.y_axis else 'x', getattr(center, 'y' if self.y_axis else 'x'))

        return {'FINISHED'}


class KO_OT_align_vertical(Operator):
    bl_idname = 'ko.align_vertical'
    bl_label = 'Align vertical'
    bl_description = 'Align selected INSERTS vertically within target bounds'
    bl_options = {'REGISTER', 'UNDO'}

    z_axis: BoolProperty(
        name = 'Z Axis',
        description = 'Use the Z axis of the INSERT TARGET for alignment',
        default = False)

    def execute(self, context):

        # get mains
        mains = insert.collect(context.selected_objects, mains=True)

        for main in mains:
            if main.kitops.insert_target:
                center = bbox.center(main.kitops.insert_target)
                setattr(main.location, 'z' if self.z_axis else 'y', getattr(center, 'z' if self.z_axis else 'y'))

        return {'FINISHED'}


class KO_OT_align_left(Operator):
    bl_idname = 'ko.align_left'
    bl_label = 'Align left'
    bl_description = 'Align selected INSERTS to the left of the target bounds'
    bl_options = {'REGISTER', 'UNDO'}

    y_axis: BoolProperty(
        name = 'Y Axis',
        description = 'Use the y axis of the INSERT TARGET for alignment',
        default = False)

    def execute(self, context):

        mains = insert.collect(context.selected_objects, mains=True)

        for main in mains:
            if main.kitops.insert_target:
                left = bbox.back(main.kitops.insert_target).y if self.y_axis else bbox.left(main.kitops.insert_target).x
                setattr(main.location, 'y' if self.y_axis else 'x', left)

        return {'FINISHED'}


class KO_OT_align_right(Operator):
    bl_idname = 'ko.align_right'
    bl_label = 'Align right'
    bl_description = 'Align selected INSERTS to the right of the target bounds'
    bl_options = {'REGISTER', 'UNDO'}

    y_axis: BoolProperty(
        name = 'Y Axis',
        description = 'Use the y axis of the INSERT TARGET for alignment',
        default = False)

    def execute(self, context):

        mains = insert.collect(context.selected_objects, mains=True)

        for main in mains:
            if main.kitops.insert_target:
                right = bbox.front(main.kitops.insert_target).y if self.y_axis else bbox.right(main.kitops.insert_target).x
                setattr(main.location, 'y' if self.y_axis else 'x', right)

        return {'FINISHED'}


class KO_OT_align_top(Operator):
    bl_idname = 'ko.align_top'
    bl_label = 'Align top'
    bl_description = 'Align selected INSERTS to the top of the target bounds'
    bl_options = {'REGISTER', 'UNDO'}

    z_axis: BoolProperty(
        name = 'Z Axis',
        description = 'Use the Z axis of the INSERT TARGET for alignment',
        default = False)

    def execute(self, context):

        mains = insert.collect(context.selected_objects, mains=True)

        for main in mains:
            if main.kitops.insert_target:
                top = bbox.top(main.kitops.insert_target).z if self.z_axis else bbox.back(main.kitops.insert_target).y
                setattr(main.location, 'z' if self.z_axis else 'y', top)

        return {'FINISHED'}


class KO_OT_align_bottom(Operator):
    bl_idname = 'ko.align_bottom'
    bl_label = 'Align bottom'
    bl_description = 'Align selected INSERTS to the bottom of the target bounds'
    bl_options = {'REGISTER', 'UNDO'}

    z_axis: BoolProperty(
        name = 'Z Axis',
        description = 'Use the Z axis of the INSERT TARGET for alignment',
        default = False)

    def execute(self, context):

        mains = insert.collect(context.selected_objects, mains=True)

        for main in mains:
            if main.kitops.insert_target:
                bottom = bbox.bottom(main.kitops.insert_target).z if self.z_axis else bbox.front(main.kitops.insert_target).y
                setattr(main.location, 'z' if self.z_axis else 'y', bottom)

        return {'FINISHED'}


class KO_OT_stretch_wide(Operator):
    bl_idname = 'ko.stretch_wide'
    bl_label = 'Stretch wide'
    bl_description = 'Stretch selected INSERTS to the width of the target bounds'
    bl_options = {'REGISTER', 'UNDO'}

    y_axis: BoolProperty(
        name = 'X axis',
        description = 'Use the Y axis of the INSERT TARGET for stretching',
        default = False)

    halve: BoolProperty(
        name = 'Halve',
        description = 'Halve the stretch amount',
        default = False)

    def execute(self, context):

        mains = insert.collect(context.selected_objects, mains=True)

        for main in mains:
            if main.kitops.insert_target:
                dimension = main.kitops.insert_target.dimensions[1 if self.y_axis else 0]

                if self.halve:
                    dimension /= 2

                main.scale.x = dimension / main.dimensions[0] * main.scale.x

        return {'FINISHED'}


class KO_OT_stretch_tall(Operator):
    bl_idname = 'ko.stretch_tall'
    bl_label = 'Stretch tall'
    bl_description = 'Stretch selected INSERTS to the height of the target bounds'
    bl_options = {'REGISTER', 'UNDO'}

    z_axis: BoolProperty(
        name = 'Side',
        description = 'Use the Z axis of the INSERT TARGET for stretching',
        default = False)

    halve: BoolProperty(
        name = 'Halve',
        description = 'Halve the stretch amount',
        default = False)

    def execute(self, context):

        mains = insert.collect(context.selected_objects, mains=True)

        for main in mains:
            if main.kitops.insert_target:
                dimension = main.kitops.insert_target.dimensions[2 if self.z_axis else 1]

                if self.halve:
                    dimension /= 2

                main.scale.y = dimension / main.dimensions[1] * main.scale.y

        return {'FINISHED'}


class update:
    def main(prop, context):
        for obj in bpy.data.objects:
            if obj != context.active_object:
                obj.kitops['main'] = False
            else:
                obj.kitops['main'] = True

    def insert_target(prop, context):
        inserts = insert.collect(context.selected_objects)

        for obj in inserts:
            if not context.active_object:
                continue
            obj.kitops.applied = False
            obj.kitops['insert_target'] = context.active_object.kitops.insert_target

            if obj.kitops.insert_target:
                obj.kitops.reserved_target = context.active_object.kitops.insert_target

    def mirror_x(prop, context):
        inserts = insert.collect(context.selected_objects)

        for obj in inserts:
            obj.kitops['mirror_x'] = bpy.context.active_object.kitops.mirror_x

        validate_mirror(inserts, axis='X')

    def mirror_y(prop, context):
        inserts = insert.collect(context.selected_objects)

        for obj in inserts:
            obj.kitops['mirror_y'] = bpy.context.active_object.kitops.mirror_y

        validate_mirror(inserts, axis='Y')

    def mirror_z(prop, context):
        inserts = insert.collect(context.selected_objects)

        for obj in inserts:
            obj.kitops['mirror_z'] = bpy.context.active_object.kitops.mirror_z

        validate_mirror(inserts, axis='Z')


classes = [
    KO_OT_align_horizontal,
    KO_OT_align_vertical,
    KO_OT_align_left,
    KO_OT_align_right,
    KO_OT_align_top,
    KO_OT_align_bottom,
    KO_OT_stretch_wide,
    KO_OT_stretch_tall]


def register():
    for cls in classes:
        register_class(cls)


def unregister():
    for cls in classes:
        unregister_class(cls)
