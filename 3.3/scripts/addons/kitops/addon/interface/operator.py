import re

from copy import deepcopy as copy

import bpy

from math import radians
from mathutils import *
from pathlib import Path

from bpy.types import Operator
from bpy.props import *
from bpy.utils import register_class, unregister_class
from bpy_extras.io_utils import ExportHelper, ImportHelper

from .. utility import addon, backup, bbox, dpi, insert, ray, remove, update, view3d, collections, smart, persistence, handler, id

from .. t3dn_bip import ops

import os

authoring_enabled = True
try: from .. utility import matrixmath
except: authoring_enabled = False


class KO_OT_purchase(Operator):
    bl_idname = 'ko.purchase'
    bl_label = 'KIT OPS PRO'
    bl_description = 'Buy KIT OPS PRO'

    def execute(self, context):
        # Do nothing, this option should always be disabled in the ui
        return {'FINISHED'}


class KO_OT_store(Operator):
    bl_idname = 'ko.store'
    bl_label = 'Store'
    bl_description = 'Visit the KIT OPS Store'

    def execute(self, context):
        bpy.ops.wm.url_open('INVOKE_DEFAULT', url='https://www.kit-ops.com/the-store')

        return {'FINISHED'}


class KO_OT_documentation(Operator):
    bl_idname = 'ko.documentation'
    bl_label = 'Documentation'
    bl_description = 'View the KIT OPS documentation'

    authoring: BoolProperty(default=False)

    def execute(self, context):
        bpy.ops.wm.url_open('INVOKE_DEFAULT', url='http://cw1.me/kops2docs')

        return {'FINISHED'}


class KO_OT_add_kpack_path(Operator):
    bl_idname = 'ko.add_kpack_path'
    bl_label = 'Add KIT OPS KPACK path'
    bl_description = 'Add a path to a KIT OPS KPACK'

    def execute(self, context):
        preference = addon.preference()

        folder = preference.folders.add()
        folder['location'] = 'Choose Path'

        return {'FINISHED'}


class KO_OT_remove_kpack_path(Operator):
    bl_idname = 'ko.remove_kpack_path'
    bl_label = 'Remove path'
    bl_description = 'Remove path'

    index: IntProperty()

    def execute(self, context):
        preference = addon.preference()

        preference.folders.remove(self.index)

        update.kpack(None, context)

        return {'FINISHED'}


class KO_OT_refresh_kpacks(Operator):
    bl_idname = 'ko.refresh_kpacks'
    bl_label = 'Refresh KIT OPS KPACKS'
    bl_description = 'Refresh KIT OPS KPACKS'

    record_previous : BoolProperty(default=False) # record the previous selection to keep the KPACK in the UI.

    def execute(self, context):
        if self.record_previous:
            option = addon.option()
            previous_kpack = str(option.kpacks)
            category = option.kpack.categories[option.kpack.active_index]
            previous_thumbnail = str(category.thumbnail)

        update.kpack(None, context)

        if self.record_previous:
            option = addon.option()
            try:
                option.kpacks = previous_kpack
            except TypeError:
                pass
            if option.kpacks == previous_kpack:
                try:
                    category = option.kpack.categories[option.kpack.active_index]
                    category.thumbnail = previous_thumbnail
                except TypeError:
                    pass

        return {'FINISHED'}


class KO_OT_next_kpack(Operator):
    bl_idname = 'ko.next_kpack'
    bl_label = 'Next KPACK'
    bl_description = 'Change to the next INSERT\n  Ctrl - Change KPACK'
    bl_options = {'INTERNAL'}


    def invoke(self, context, event):
        option = addon.option()

        if event.ctrl:
            index = option.kpack.active_index + 1 if option.kpack.active_index + 1 < len(option.kpack.categories) else 0

            option.kpacks = option.kpack.categories[index].name

        else:
            category = option.kpack.categories[option.kpack.active_index]
            index = category.active_index + 1 if category.active_index + 1 < len(category.blends) else 0

            category.active_index = index
            category.thumbnail = category.blends[category.active_index].name

        return {'FINISHED'}


class KO_OT_previous_kpack(Operator):
    bl_idname = 'ko.previous_kpack'
    bl_label = 'Previous KPACK'
    bl_description = 'Change to the previous INSERT\n  Ctrl - Change KPACK'
    bl_options = {'INTERNAL'}


    def invoke(self, context, event):
        option = addon.option()

        if event.ctrl:
            index = option.kpack.active_index - 1 if option.kpack.active_index - 1 > -len(option.kpack.categories) else 0

            option.kpacks = option.kpack.categories[index].name

        else:
            category = option.kpack.categories[option.kpack.active_index]
            index = category.active_index - 1 if category.active_index - 1 > -len(category.blends) else 0

            category.active_index = index
            category.thumbnail = category.blends[category.active_index].name

        return {'FINISHED'}

def _add_material(obj, material):
        if len(obj.data.materials) and obj.active_material_index < len(obj.data.materials):
            obj.data.materials[obj.active_material_index] = material
        else:
            obj.data.materials.append(material)

class add_insert():
    bl_options = {'REGISTER', 'UNDO'}

    location: StringProperty(
        name = 'Blend path',
        description = 'Path to blend file')

    material: BoolProperty(name='Material')
    material_link: BoolProperty(name='Link Materials')

    mouse = Vector()
    main = None
    duplicate = None

    data_to = None
    boolean_target = None

    inserts = list()

    init_active = None
    init_selected = list()
    cutter_objects = list()

    insert_scale = ('LARGE', 'MEDIUM', 'SMALL')

    import_material = None

    original_scale : FloatVectorProperty(default=[1,1,1])

    rotation_amount : FloatProperty(default=0)

    @classmethod
    def poll(cls, context):
        return not context.space_data.region_quadviews and not context.space_data.local_view


    def invoke(self, context, event):
        global authoring_enabled

        preference = addon.preference()

        insert.operator = self

        #select active object if not already.
        if context.active_object and context.active_object.mode == 'EDIT':
            context.active_object.select_set(True)

        # assign active object to internal variables.
        self.init_active = bpy.data.objects[context.active_object.name] if context.active_object and context.active_object.select_get() else None
        self.init_selected = [bpy.data.objects[obj.name] for obj in context.selected_objects]

        collections.init(context)

        if self.init_active:
            if self.init_active.kitops.insert and self.init_active.kitops.insert_target:
                self.boolean_target = self.init_active.kitops.insert_target
            elif preference.mode == 'REGULAR' and self.init_active.kitops.reserved_target:
                self.boolean_target = self.init_active.kitops.reserved_target
            elif self.init_active.kitops.insert:
                self.boolean_target = None
            elif self.init_active.type == 'MESH':
                self.boolean_target = self.init_active
            else:
                self.boolean_target = None
        else:
            self.boolean_target = None

        for obj in context.selected_objects:
            obj.select_set(False)

        if self.init_active and self.init_active.mode != 'OBJECT':
            bpy.ops.object.mode_set(mode='OBJECT')

        if self.boolean_target:
            ray.make_duplicate(self)


        self.material_link = not event.ctrl

        if not self.main:
            insert.add(self, context)

        prev_name = ''
        if self.material and self.init_active and self.import_material:
            if hasattr(self.init_active, 'material_slots') and len(self.init_active.material_slots[:]) and self.init_active.material_slots[0].material:
                prev_name = self.init_active.material_slots[0].material.name

        
            _add_material(self.init_active, self.import_material)

            for obj in self.init_selected:
                if obj != self.init_active and obj.type == 'MESH':
                    _add_material(obj, self.import_material)


        if self.material:
            if not self.import_material:
                self.report({'WARNING'}, 'No materials found to import')

            elif not prev_name:
                self.report({'INFO'}, F'Imported material: {self.import_material.name}')

            else:
                self.report({'INFO'}, F'Material assigned: {self.import_material.name}')

            self.exit(context, clear=True)
            return {'FINISHED'}

        insert.show_solid_objects()
        insert.show_cutter_objects()
        insert.show_wire_objects()

        if self.main and self.main.kitops.animated:
            bpy.ops.screen.animation_play()

        # Record the original scale of the insert and apply a re-scale is needed.
        self.original_scale = self.main.scale.copy() if self.main else self.original_scale
        if not preference.auto_scale and self.main:
            option = addon.option()
            self.main.scale = self.main.scale * option.scale_amount

        if self.init_selected and self.boolean_target:
            self.mouse = Vector((event.mouse_x, event.mouse_y))
            self.mouse.x -= view3d.region().x - preference.insert_offset_x * dpi.factor()
            self.mouse.y -= view3d.region().y - preference.insert_offset_y * dpi.factor()

            insert.hide_handler(self)

            context.window_manager.modal_handler_add(self)

            return {'RUNNING_MODAL'}
        else:
            if self.init_active and self.init_active.kitops.insert:
                self.report({'WARNING'}, 'An INSERT can not be added to an existing INSERT that has no target object.')
            if self.main:
                self.main.location = bpy.context.scene.cursor.location
            self.exit(context)
            return {'FINISHED'}


    def modal(self, context, event):
        global authoring_enabled

        if authoring_enabled:
            context.workspace.status_text_set(text="Add KIT OPS INSERT:    [F] Snap to FACE    [E] Snap to EDGE ([C] Toggle Snap to Edge Center)    [V] Snap to VERTEX    [N] Cancel SNAP MODE    |    [P] Toggle Place on Selected Insert    [I] Flip Placement")

        preference = addon.preference()
        

        if not insert.operator:
            self.exit(context)
            return {'FINISHED'}

        if authoring_enabled and event.type in {'F', 'E', 'V', 'N', 'P', 'I'} and event.value == 'PRESS':
            if event.type == 'F':
                preference.snap_mode = 'FACE'
            if event.type == 'E':
                preference.snap_mode = 'EDGE'
            if event.type == 'V':
                preference.snap_mode = 'VERTEX'
            if event.type == 'N':
                preference.snap_mode = 'NONE'
            if event.type == 'P':
                preference.place_on_insert = not preference.place_on_insert
            if event.type == 'I':
                preference.flip_placement = not preference.flip_placement

            ray.refresh_duplicate(self)
            
            return {'RUNNING_MODAL'}
    
        if authoring_enabled and preference.snap_mode == 'EDGE' and event.type == 'C' and event.value == 'PRESS':
            preference.snap_mode_edge = 'NEAREST' if preference.snap_mode_edge == 'CENTER' else 'CENTER'
            return {'RUNNING_MODAL'}

        if event.type == 'MOUSEMOVE':
            temp_scale = self.main.scale.copy()
            self.mouse = Vector((event.mouse_x, event.mouse_y))
            self.mouse.x -= view3d.region().x - preference.insert_offset_x * dpi.factor()
            self.mouse.y -= view3d.region().y - preference.insert_offset_y * dpi.factor()
            update.location()
            self.main.scale = temp_scale
            self.main.rotation_euler.rotate_axis("Z", radians(self.rotation_amount))

        insert.hide_handler(self)

        if event.type in {'ESC', 'RIGHTMOUSE'} and event.value == 'PRESS':

            self.exit(context, clear=True)
            return {'CANCELLED'}

        elif event.type in {'LEFTMOUSE', 'RET', 'NUMPAD_ENTER'} and event.value == 'PRESS':
            if ray.location:
                option = addon.option()
                option.scale_amount = (self.main.scale.magnitude / Vector(self.original_scale).magnitude)
                if event.shift and preference.mode == 'SMART':
                    self.exit(context)
                    bpy.ops.ko.add_insert('INVOKE_DEFAULT', 
                        location=self.location,
                        rotation_amount=self.rotation_amount)
                else:
                    self.exit(context)
                return{'FINISHED'}
            else:

                self.exit(context, clear=True)
                return {'CANCELLED'}

        elif event.type == 'WHEELDOWNMOUSE':      
            if event.alt:
                rotation_amount = 15 if not event.shift else 1
                self.main.rotation_euler.rotate_axis("Z", radians(rotation_amount))
                self.rotation_amount+=rotation_amount
                return {'RUNNING_MODAL'}

            if preference.auto_scale:
                if self.insert_scale.index(preference.insert_scale) + 1 < len(self.insert_scale):
                    preference.insert_scale = self.insert_scale[self.insert_scale.index(preference.insert_scale) + 1]
            else:
                step = 0.1 if not event.shift else 0.01
                self.main.scale -= self.main.scale * step
            return {'RUNNING_MODAL'}

        elif event.type == 'WHEELUPMOUSE':
            if event.alt:
                rotation_amount = 15 if not event.shift else 1
                self.main.rotation_euler.rotate_axis("Z", radians(-rotation_amount))
                self.rotation_amount-=rotation_amount
                return {'RUNNING_MODAL'}


            if preference.auto_scale:
                if self.insert_scale.index(preference.insert_scale) - 1 >= 0:
                    preference.insert_scale = self.insert_scale[self.insert_scale.index(preference.insert_scale) - 1]
            else:
                step = 0.1 if not event.shift else 0.01
                self.main.scale += self.main.scale * step
            return {'RUNNING_MODAL'}

        elif event.type in {'G', 'R', 'S'}:
            insert.operator = None

        return {'PASS_THROUGH'}


    def exit(self, context, clear=False):

        context.workspace.status_text_set(text=None)

        option = addon.option()

        if self.main and self.main.kitops.animated:
            bpy.ops.screen.animation_cancel(restore_frame=True)

        if not option.show_cutter_objects:
            for obj in self.cutter_objects:
                obj.hide_viewport = True

        if clear:
            for obj in self.inserts:
                try:
                    insert.delete_hierarchy(obj, target_obj=self.boolean_target)
                    bpy.data.objects.remove(obj)
                except ReferenceError:
                    pass
                
            for obj in self.init_selected:
                obj.select_set(True)

            if self.init_active:
                context.view_layer.objects.active = self.init_active
                
        else:
            for obj in self.inserts:
                if obj.select_get() and obj.kitops.selection_ignore:
                    obj.select_set(False)
                else:
                    obj.select_set(True)

                if self.boolean_target and obj.parent is None:
                    # Add parent if we have a boolean target.
                    insert.parent_objects(obj, self.boolean_target)

            # set active object to main INSERT.
            if self.main:
                context.view_layer.objects.active = self.main

                self.main.kitops.rotation_amount = self.rotation_amount

        #TODO: collection helper: collection.remove
        if 'INSERTS' in bpy.data.collections:
            for child in bpy.data.collections['INSERTS'].children:
                if not child.objects and not child.children:
                    bpy.data.collections.remove(child)

        ray.success = bool()
        ray.location = Vector()
        ray.normal = Vector()
        ray.face_index = int()
        ray.free(self)

        insert.operator = None

        if 'INSERTS' in bpy.data.collections and not bpy.data.collections['INSERTS'].objects and not bpy.data.collections['INSERTS'].children:
            bpy.data.collections.remove(bpy.data.collections['INSERTS'])

        for mesh in bpy.data.meshes:
            if mesh.users == 0:
                bpy.data.meshes.remove(mesh)

        insert.show_solid_objects()
        insert.show_cutter_objects()
        insert.show_wire_objects()

def get_description():
    if authoring_enabled:
        return  ('Add INSERT to the scene \n'
                            ' \n'
                            ' Alt + mouse scroll - rotate insert\n'
                            ' \n'
                            ' V - Snap to Vertex\n'
                            ' E - Snap to Edge\n'
                            '  [C - Toggle Snap to Edge Center]\n'
                            ' F - Snap to Face\n'
                            ' N - Cancel Snap Mode\n'
                            ' \n'
                            ' P - Toggle Place on Selected Insert\n'
                            ' I - Flip Placement')
    else:
        return  ('Add INSERT to the scene \n'
                    ' Alt + mouse scroll - rotate insert\n'
                    ' Snap to Face/Edge/Vertex: Purchase KIT OPS Pro')


def _toggle_boolean(obj, is_enabled):
    """Toggle whether the object's boolean operator is on or off"""
    inserts = insert.collect([obj])
    for obj in inserts:
        if obj.kitops.reserved_target:
            for mod in obj.kitops.reserved_target.modifiers:
                if mod.type == "BOOLEAN" and mod.object == obj:
                    mod.show_render = is_enabled
                    mod.show_viewport = is_enabled
            bpy.context.view_layer.update()


class move_insert(add_insert):
    bl_options = {'REGISTER', 'UNDO'}

    original_matrix_world = None

    original_scale_option = None

    old_active = None

    @classmethod
    def poll(cls, context):
        return context.active_object and context.active_object.kitops.insert

    def invoke(self, context, event):
        self.main = context.active_object.kitops.main_object        
        
        self.original_matrix_world = self.main.matrix_world.copy()
        option = addon.option()
        self.original_scale_option = option.scale_amount
        option.scale_amount = 1
        self.rotation_amount = self.main.kitops.rotation_amount
        self.old_active = context.view_layer.objects.active
        context.view_layer.objects.active = self.main.kitops.reserved_target
        context.view_layer.objects.active.select_set(True)

        _toggle_boolean(self.main, False)
        result = super().invoke(context, event)
        _toggle_boolean(self.main, True)
        
        return result

    def exit(self, context, clear=False):
        context.workspace.status_text_set(text=None)
        option = addon.option()

        if self.main.kitops.animated:
            bpy.ops.screen.animation_cancel(restore_frame=True)

        if not option.show_cutter_objects:
            for obj in self.cutter_objects:
                obj.hide_viewport = True

        if clear:
            self.main.matrix_world = self.original_matrix_world

            option = addon.option()
            context.view_layer.objects.active.select_set(False)
            context.view_layer.objects.active = self.old_active

        else:
            self.main.select_set(True)
            context.view_layer.objects.active = self.main
            inserts = insert.collect([self.main])
            for ins in inserts:
                ins.select_set(True)
            self.main.kitops.rotation_amount = self.rotation_amount


        option.scale_amount = self.original_scale_option

        ray.success = bool()
        ray.location = Vector()
        ray.normal = Vector()
        ray.face_index = int()
        ray.free(self)

        insert.operator = None

        context.view_layer.update()


class KO_OT_auto_create_insert(Operator):
    
    bl_idname = 'ko.auto_create_insert'
    bl_label = 'Create INSERT'
    bl_description = "Automatically Create an INSERT from the selected object"
    bl_options = {'UNDO', 'INTERNAL'}

    set_object_origin_to_bottom : BoolProperty(default=False)

    @classmethod
    def poll(cls, context):
        return context.active_object # todo consider context.selected_objects

    def execute(self, context):
        obj = context.active_object

        # remember old location and rotation as we will reset these.
        if self.set_object_origin_to_bottom:
            original_translation = obj.matrix_world.copy().translation
            insert.origin_to_bottom(obj)
            context.view_layer.update()
        old_loc = obj.location.copy()
        obj.location = Vector((0,0,0))
        old_euler = obj.rotation_euler.copy()
        obj.rotation_euler = [0,0,0]
        
        # because of sys.exit() protection, we have to set the objects into a temporary state.
        old_saving = handler.is_saving
        handler.is_saving = True
        old_id = obj.kitops.id
        old_main = obj.kitops.main
        try:

            # open a new factory mode, position the camera, save the insert, and render the thumbnail.
            obj.kitops.id = id.uuid()
            obj.kitops.main = True

            if not bpy.data.use_autopack:
                bpy.ops.file.autopack_toggle()

            bpy.ops.object.mode_set(mode='OBJECT')

            persistence.new_factory_scene(context, link_selected=True, link_children=True, duplicate=True, material_base=False)

            bpy.ops.view3d.camera_to_view_selected()
            path = persistence.insert_path(obj.name, context)
            persistence.save_insert(path=path)

            thumb_path = persistence.insert_thumb_path(obj.name, context)
            persistence.create_snapshot(self, context, thumb_path)
            bpy.ops.ko.refresh_kpacks(record_previous=True)

            persistence.close_factory_scene(self, context, log=False)
        finally:
            obj.location = old_loc
            if self.set_object_origin_to_bottom:
                context.view_layer.update()
                insert.set_origin(obj, original_translation)
            obj.rotation_euler = old_euler
            handler.is_saving = old_saving
            obj.kitops.id = old_id
            if old_main:
                obj.kitops.main = True
            else:
                # temporarily set the active to false so we can set the main parameter to false. 
                context.view_layer.objects.active =  None
                obj.kitops.main = old_main
                context.view_layer.objects.active = obj



        return {'FINISHED'}



class KO_OT_auto_create_insert_confirm(bpy.types.Operator):
    """Automatically Create an INSERT from the selected object"""
    bl_idname = 'ko.auto_create_insert_confirm'
    bl_label = "This will overwrite an existing INSERT.  Are you sure?"

    bl_options = {'INTERNAL','UNDO'}

    set_object_origin_to_bottom : BoolProperty(default=False)

    def invoke(self, context, event):
        return context.window_manager.invoke_confirm(self, event)

    @classmethod
    def poll(self, context):
        return context.active_object

    def execute(self, context):
        bpy.ops.ko.auto_create_insert('INVOKE_DEFAULT', set_object_origin_to_bottom=self.set_object_origin_to_bottom)
        return {'FINISHED'}





#TODO: Collections
class KO_OT_add_insert(Operator, add_insert):
    bl_idname = 'ko.add_insert'
    bl_label = 'Add INSERT'
    bl_description = get_description()

class KO_OT_move_insert(Operator, move_insert):
    bl_idname = 'ko.move_insert'
    bl_label = 'Relocate INSERT'
    bl_description = "Move INSERT in the scene using KIT OPS controls"


class KO_OT_add_insert_material(Operator, add_insert):
    bl_idname = 'ko.add_insert_material'
    bl_label = 'Add Material'
    bl_description = ('Add INSERT\'s materials to target \n'
                      '  Ctrl - Add unique material instance')


class KO_OT_select_inserts(Operator):
    bl_idname = 'ko.select_inserts'
    bl_label = 'Select All'
    bl_description = 'Select all INSERTS'
    bl_options = {'REGISTER', 'UNDO'}

    solids: BoolProperty(
        name = 'Solid inserts',
        description = 'Select solid INSERTS',
        default = True)

    cutters: BoolProperty(
        name = 'Cutter inserts',
        description = 'Select cutter INSERTS',
        default = True)

    wires: BoolProperty(
        name = 'Wire inserts',
        description = 'Select wire INSERTS',
        default = True)


    def draw(self, context):
        layout = self.layout

        preference = addon.preference()
        option = addon.option()

        column = layout.column()
        column.active = preference.mode == 'REGULAR'
        column.prop(self, 'solids')
        column.prop(self, 'cutters')
        column.prop(self, 'wires')


    def check(self, context):
        return True


    def execute(self, context):
        solids = insert.collect(solids=True, all=True)
        cutters = insert.collect(cutters=True, all=True)
        wires = insert.collect(wires=True, all=True)

        if self.solids:
            for obj in solids:
                obj.select_set(True)

        if self.cutters:
            for obj in cutters:
                obj.select_set(True)

        if self.wires:
            for obj in wires:
                obj.select_set(True)

        return {'FINISHED'}


class remove_insert_properties():
    bl_options = {'UNDO'}

    remove: BoolProperty()
    uuid: StringProperty()


    def execute(self, context):
        objects = context.selected_objects if not self.uuid else [obj for obj in bpy.data.objects if obj.kitops.id == self.uuid]
        for obj in objects:
            obj.kitops['insert'] = False
            obj.kitops['insert_target'] = None
            obj.kitops['mirror_target'] = None
            obj.kitops['reserved_target'] = None
            obj.kitops['main_object'] = None

        if self.remove:
            bpy.ops.object.delete({'active_object': objects[0], 'selected_objects': objects}, confirm=False)

        return {'FINISHED'}


class KO_OT_remove_insert_properties(Operator, remove_insert_properties):
    bl_idname = 'ko.remove_insert_properties'
    bl_label = 'Remove KIT OPS props'
    bl_description = 'Remove properties from the selected OBJECTS'


class KO_OT_remove_insert_properties_x(Operator, remove_insert_properties):
    bl_idname = 'ko.remove_insert_properties_x'
    bl_label = 'Remove INSERT'
    bl_description = 'Deletes selected INSERTS'


class KO_OT_export_settings(Operator, ExportHelper):
    bl_idname = 'ko.export_settings'
    bl_label = 'Export Settings'
    bl_options = {'REGISTER', 'INTERNAL'}
    bl_description = '.\n'.join((
        'Save KIT OPS preferences to a file',
        'Made possible by PowerBackup'))

    filter_glob: bpy.props.StringProperty(default='*.json', options={'HIDDEN'})
    filename_ext: bpy.props.StringProperty(default='.json', options={'HIDDEN'})


    def invoke(self, context, event):
        self.filepath = backup.filepath()
        return super().invoke(context, event)


    def execute(self, context):
        result = backup.backup(self.filepath)
        self.report(result[0], result[1])
        return result[2]


class KO_OT_import_settings(Operator, ImportHelper):
    bl_idname = 'ko.import_settings'
    bl_label = 'Import Settings'
    bl_options = {'REGISTER', 'UNDO', 'INTERNAL'}
    bl_description = '.\n'.join((
        'Load KIT OPS preferences from a file',
        'Made possible by PowerBackup'))

    filter_glob: bpy.props.StringProperty(default='*.json', options={'HIDDEN'})
    filename_ext: bpy.props.StringProperty(default='.json', options={'HIDDEN'})


    def invoke(self, context, event):
        self.filepath = backup.filepath()
        return super().invoke(context, event)


    def execute(self, context):
        result = backup.restore(self.filepath)
        self.report(result[0], result[1])
        return result[2]


class KO_OT_convert_to_mesh(Operator):
    bl_idname = 'ko.convert_to_mesh'
    bl_label = 'Convert to mesh'
    bl_description = 'Apply modifiers and remove kitops properties of selected objects'
    bl_options = {'UNDO'}

    @classmethod
    def poll(cls, context):
        return context.selected_objects


    def execute(self, context):
        bpy.ops.object.convert(target='MESH')

        for obj in context.selected_objects:
            for mod in obj.modifiers:
                if mod.type == 'BOOLEAN' and mod.object:
                    mod.object.kitops['insert_target'] = None
                    mod.object.kitops['mirror_target'] = None
                    mod.object.kitops['reserved_target'] = None
                    mod.object.kitops['main_object'] = None

            obj.kitops['insert'] = False
            obj.kitops['main'] = False
            obj.kitops['insert_target'] = None
            obj.kitops['mirror_target'] = None
            obj.kitops['reserved_target'] = None
            obj.kitops['main_object'] = None

        for obj in context.selected_objects:
            for mod in obj.modifiers:
                obj.modifiers.remove(mod)

        return {'FINISHED'}


class KO_OT_remove_wire_inserts(Operator):
    bl_idname = 'ko.remove_wire_inserts'
    bl_label = 'Remove Unused Wire INSERTS'
    bl_description = 'Remove unused wire objects from the INSERTS collection, keeping transforms on child objects'
    bl_options = {'REGISTER', 'UNDO'}

    @classmethod
    def poll(cls, context):
        return 'INSERTS' in bpy.data.collections


    def execute(self, context):
        collection = bpy.data.collections['INSERTS']
        wires = {obj for obj in collection.all_objects if obj.display_type in {'WIRE', 'BOUNDS'}}

        for obj in bpy.data.objects:
            if obj.type != 'MESH':
                continue

            for mod in obj.modifiers:
                if mod.type == 'BOOLEAN' and mod.object in wires:
                    wires.remove(mod.object)

        for obj in collection.all_objects:
            if obj.parent in wires:
                obj.matrix_local = obj.matrix_world
                obj.parent = None

        for obj in wires:
            bpy.data.objects.remove(obj)

        return {'FINISHED'}


class KO_OT_clean_duplicate_materials(Operator):
    bl_idname = 'ko.clean_duplicate_materials'
    bl_label = 'Clean Duplicate Materials'
    bl_description = 'Find duplicate materials by name, remap users and remove them'
    bl_options = {'REGISTER', 'UNDO'}


    def execute(self, context):
        count = len(bpy.data.materials)

        for mat in bpy.data.materials[:]:
            if re.search('[0-9][0-9][0-9]$', mat.name):
                original = mat.name[:-4]

                if original in bpy.data.materials:
                    mat.user_remap(bpy.data.materials[original])
                    bpy.data.materials.remove(mat)

        self.report({'INFO'}, F'Removed {count - len(bpy.data.materials)} materials')
        return {'FINISHED'}


class KO_OT_move_folder(Operator):
    bl_idname = 'ko.move_folder'
    bl_label = 'Move Folder'
    bl_description = 'Move the chosen folder up or down in the list'
    bl_options = {'REGISTER', 'INTERNAL'}

    index: IntProperty()
    direction: IntProperty()


    def execute(self, context):
        preference = addon.preference()
        neighbor = max(0, self.index + self.direction)
        preference.folders.move(neighbor, self.index)
        return {'FINISHED'}

class KO_OT_install_pillow(Operator, ops.InstallPillow):
    bl_idname = 'ko.install_pillow'
    bl_label = 'Install Pillow'
    bl_description = 'Install Pillow for thumbnail caching'
    bl_options = {'INTERNAL'}


    def execute(self: bpy.types.Operator, context: bpy.types.Context) -> set:
        # Install Pillow first.
        super().execute(context)
        update.kpack(None, context)
        return {'FINISHED'}

class KO_OT_OpenHelpURL(Operator):
    bl_idname = "ko.open_help_url" 
    bl_label = "KIT OPS Help"
    bl_description = 'Open KIT OPS documentation'
    bl_options = {'INTERNAL', 'UNDO'}
    
    url : StringProperty()

    def execute(self, context):
        bpy.ops.wm.url_open(url = self.url)
        return {'FINISHED'}

class KO_MT_KITOPS(bpy.types.Menu):
    bl_idname = 'KO_MT_KITOPS'
    bl_label = 'KIT OPS'

    def draw(self, context):
        col = self.layout.column()
        col.operator_context = 'INVOKE_DEFAULT'
        col.operator(KO_OT_move_insert.bl_idname)
        if context.active_object and os.path.exists(persistence.insert_path(context.active_object.name, context)):
            col.operator(KO_OT_auto_create_insert_confirm.bl_idname, text="Create INSERT - Use Object Origin").set_object_origin_to_bottom = False
            col.operator(KO_OT_auto_create_insert_confirm.bl_idname, text="Create INSERT - Use Bottom of Object as Origin").set_object_origin_to_bottom = True
        else:
            col.operator(KO_OT_auto_create_insert.bl_idname, text="Create INSERT - Use Object Origin").set_object_origin_to_bottom = False
            col.operator(KO_OT_auto_create_insert.bl_idname, text="Create INSERT - Use Bottom of Object as Origin").set_object_origin_to_bottom = True



classes = [
    KO_OT_purchase,
    KO_OT_store,
    KO_OT_documentation,
    KO_OT_add_kpack_path,
    KO_OT_remove_kpack_path,
    KO_OT_refresh_kpacks,
    KO_OT_next_kpack,
    KO_OT_previous_kpack,
    KO_OT_add_insert,
    KO_OT_move_insert,
    KO_OT_add_insert_material,
    KO_OT_select_inserts,
    KO_OT_remove_insert_properties,
    KO_OT_remove_insert_properties_x,
    KO_OT_export_settings,
    KO_OT_import_settings,
    KO_OT_convert_to_mesh,
    KO_OT_remove_wire_inserts,
    KO_OT_clean_duplicate_materials,
    KO_OT_move_folder,
    KO_OT_install_pillow,
    KO_OT_OpenHelpURL,
    KO_OT_auto_create_insert,
    KO_OT_auto_create_insert_confirm,
    KO_MT_KITOPS
]




def menu_func(self, context):
    self.layout.menu(KO_MT_KITOPS.bl_idname)
    col = self.layout.column()
    # col.operator_context = 'INVOKE_DEFAULT'
    # col.operator(KO_OT_move_insert.bl_idname)
    # col.operator(KO_OT_auto_create_insert.bl_idname)


def register():
    for cls in classes:
        register_class(cls)
    smart.register()
    try:
        from .. utility import matrixmath
        matrixmath.register()
    except: pass

    bpy.types.VIEW3D_MT_object_context_menu.append(menu_func)


def unregister():
    bpy.types.VIEW3D_MT_object_context_menu.remove(menu_func)

    for cls in classes:
        unregister_class(cls)

    smart.unregister()
    try:
        from .. utility import matrixmath
        matrixmath.unregister()
    except: pass
