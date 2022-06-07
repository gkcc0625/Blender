import bpy
from bpy.props import StringProperty, BoolProperty, FloatProperty
import os
from .. utils.registration import get_addon, get_prefs, get_path
from .. utils.ui import popup_message
from .. utils.asset import get_catalogs_from_asset_libraries
from .. utils.object import parent


decalmachine = None
meshmachine = None


class CreateAssemblyAsset(bpy.types.Operator):
    bl_idname = "machin3.create_assembly_asset"
    bl_label = "MACHIN3: Creaste Assembly Asset"
    bl_description = "Create Assembly Asset from the selected Objects"
    bl_options = {'REGISTER', 'UNDO'}

    name: StringProperty(name="Asset Name", default="AssemblyAsset")
    move: BoolProperty(name="Move instead of Copy", description="Move Objects into Asset Collection, instead of copying\nThis will unlink them from any existing collections", default=True)

    remove_decal_backups: BoolProperty(name="Remove Decal Backups", description="Remove DECALmachine's Decal Backups, if present", default=False)
    remove_stashes: BoolProperty(name="Remove Stashes", description="Remove MESHmachine's Stashes, if present", default=False)

    render_thumbnail: BoolProperty(name="Render Thumbnail", default=True)
    thumbnail_lens: FloatProperty(name="Thumbnail Lens", default=100)

    def update_hide_instance(self, context):
        if self.avoid_update:
            self.avoid_update = False
            return

        if self.hide_instance and self.hide_collection:
            self.avoid_update = True
            self.hide_collection = False

    def update_hide_collection(self, context):
        if self.avoid_update:
            self.avoid_update = False
            return

        if self.hide_collection and self.hide_instance:
            self.avoid_update = True
            self.hide_instance = False

    unlink_collection: BoolProperty(name="Unlink Collection", description="Useful to clean up the scene, and optionally start using the Asset locally right away", default=True)
    hide_collection: BoolProperty(name="Hide Collection", default=True, description="Useful when you want to start using the Asset locally, while still having easy access to the individual objects", update=update_hide_collection)
    hide_instance: BoolProperty(name="Hide Instance", default=False, description="Useful when you want to keep working on the Asset's objects", update=update_hide_instance)

    avoid_update: BoolProperty()

    @classmethod
    def poll(cls, context):
        return context.mode == 'OBJECT' and context.selected_objects

    def draw(self, context):
        global decalmachine, meshmachine

        layout = self.layout

        column = layout.column(align=True)
        column.prop(self, 'name')
        column.prop(context.window_manager, 'M3_asset_catalogs', text='Catalog')

        column.separator()
        column.prop(self, 'move', toggle=True)

        if decalmachine or meshmachine:
            row = column.row(align=True)

            if decalmachine:
                row.prop(self, 'remove_decal_backups', toggle=True)

            if meshmachine:
                row.prop(self, 'remove_stashes', toggle=True)

        row = column.row(align=True)
        row.prop(self, 'unlink_collection', toggle=True)
        r = row.row(align=True)
        r.active = not self.unlink_collection
        r.prop(self, 'hide_collection', toggle=True)
        r.prop(self, 'hide_instance', toggle=True)

        row = column.row(align=True)
        row.prop(self, 'render_thumbnail', toggle=True)
        r = row.row(align=True)
        r.active = self.render_thumbnail
        r.prop(self, 'thumbnail_lens', text='Lens')


    def invoke(self, context, event):
        global decalmachine, meshmachine

        if decalmachine is None:
            decalmachine = get_addon('DECALmachine')[0]

        if meshmachine is None:
            meshmachine = get_addon('MESHmachine')[0]

        self.update_asset_catalogs(context)

        return context.window_manager.invoke_props_dialog(self)

    def execute(self, context):
        global decalmachine, meshmachine

        name = self.name.strip()



        if name:
            print(f"INFO: Creation Assembly Asset: {name}")

            objects = self.get_assembly_asset_objects(context)

            if decalmachine and self.remove_decal_backups:
                self.delete_decal_backups(objects)

            if meshmachine and self.remove_stashes:
                self.delete_stashes(objects)

            instance = self.create_asset_instance_collection(context, name, objects)

            self.adjust_workspace(context)

            if self.render_thumbnail:
                thumbpath = os.path.join(get_path(), 'resources', 'thumb.png')
                self.render_viewport(context, thumbpath)

                if os.path.exists(thumbpath):
                    bpy.ops.ed.lib_id_load_custom_preview({'id': instance}, filepath=thumbpath)
                    os.unlink(thumbpath)

            return {'FINISHED'}

        else:
            popup_message("The chosen asset name can't be empty", title="Illegal Name")

            return {'CANCELLED'}

    def update_asset_catalogs(self, context):
        self.catalogs = get_catalogs_from_asset_libraries(context, debug=False)

        items = [('NONE', 'None', '')]

        for catalog in self.catalogs:
            items.append((catalog, catalog, ""))

        default = get_prefs().preferred_default_catalog if get_prefs().preferred_default_catalog in self.catalogs else 'NONE'
        bpy.types.WindowManager.M3_asset_catalogs = bpy.props.EnumProperty(name="Asset Categories", items=items, default=default)

    def get_assembly_asset_objects(self, context):

        sel = context.selected_objects
        objects = set()

        for obj in sel:
            objects.add(obj)

            if obj.parent and obj.parent not in sel:
                objects.add(obj.parent)

            booleans = [mod for mod in obj.modifiers if mod.type == 'BOOLEAN']

            for mod in booleans:
                if mod.object and mod.object not in sel:
                    objects.add(mod.object)

            mirrors = [mod for mod in obj.modifiers if mod.type == 'MIRROR']

            for mod in mirrors:
                if mod.mirror_object and mod.mirror_object not in sel:
                    objects.add(mod.mirror_object)

        for obj in context.visible_objects:
            if obj not in objects and obj.parent and obj.parent in objects:
                objects.add(obj)

        return objects

    def delete_decal_backups(self, objects):
        decals_with_backups = [obj for obj in objects if obj.DM.isdecal and obj.DM.decalbackup]

        for decal in decals_with_backups:
            print(f"WARNING: Removing {decal.name}'s backup")

            if decal.DM.decalbackup:
                bpy.data.meshes.remove(decal.DM.decalbackup.data, do_unlink=True)

    def delete_stashes(self, objects):
        objs_with_stashes = [obj for obj in objects if obj.MM.stashes]

        for obj in objs_with_stashes:
            print(f"WARNING: Removing {obj.name}'s {len(obj.MM.stashes)} stashes")

            for stash in obj.MM.stashes:
                stashobj = stash.obj

                if stashobj:
                    print(" *", stash.name, stashobj.name)
                    bpy.data.meshes.remove(stashobj.data, do_unlink=True)

            obj.MM.stashes.clear()

    def create_asset_instance_collection(self, context, name, objects):
        mcol = context.scene.collection
        acol = bpy.data.collections.new(name)

        mcol.children.link(acol)

        if self.move:
            for obj in objects:
                for col in obj.users_collection:
                    col.objects.unlink(obj)

        for obj in objects:
            acol.objects.link(obj)

            if get_prefs().hide_wire_objects_when_creating_assembly_asset and obj.display_type == 'WIRE':
                obj.hide_set(True)

        instance = bpy.data.objects.new(name, object_data=None)
        instance.instance_collection = acol
        instance.instance_type = 'COLLECTION'

        mcol.objects.link(instance)
        instance.asset_mark()


        catalog = context.window_manager.M3_asset_catalogs

        if catalog and catalog != 'NONE':
            instance.asset_data.catalog_id = self.catalogs[catalog]['uuid']


        if self.unlink_collection:
            mcol.children.unlink(acol)

        else:
            if self.hide_collection:
                context.view_layer.layer_collection.children[acol.name].hide_viewport = True
                instance.select_set(True)
                context.view_layer.objects.active = instance

            elif self.hide_instance:
                instance.hide_set(True)

        return instance

    def adjust_workspace(self, context):
        asset_browser_workspace = get_prefs().preferred_assetbrowser_workspace_name

        if asset_browser_workspace:
            ws = bpy.data.workspaces.get(asset_browser_workspace)

            if ws and ws != context.workspace:
                print("INFO: Switching to preffered Asset Browser Workspace")
                bpy.ops.machin3.switch_workspace('INVOKE_DEFAULT', name=asset_browser_workspace)

                self.switch_asset_browser_to_LOCAL(ws)
                return

        ws = context.workspace
        self.switch_asset_browser_to_LOCAL(ws)

    def switch_asset_browser_to_LOCAL(self, workspace):
        for screen in workspace.screens:
            for area in screen.areas:
                if area.type == 'FILE_BROWSER' and area.ui_type == 'ASSETS':
                    for space in area.spaces:
                        if space.type == 'FILE_BROWSER':
                            if space.params.asset_library_ref != 'LOCAL':
                                space.params.asset_library_ref = 'LOCAL'

                            space.show_region_tool_props = True

    def render_viewport(self, context, filepath):

        resolution = (context.scene.render.resolution_x, context.scene.render.resolution_y)
        file_format = context.scene.render.image_settings.file_format
        lens = context.space_data.lens


        context.scene.render.resolution_x = 500
        context.scene.render.resolution_y = 500
        context.scene.render.image_settings.file_format = 'JPEG'

        context.space_data.lens = self.thumbnail_lens

        bpy.ops.render.opengl()

        thumb = bpy.data.images.get('Render Result')

        if thumb:
            thumb.save_render(filepath=filepath)

        context.scene.render.resolution_x = resolution[0]
        context.scene.render.resolution_y = resolution[1]
        context.space_data.lens = lens

        context.scene.render.image_settings.file_format = file_format


class AssembleCollectionInstance(bpy.types.Operator):
    bl_idname = "machin3.assemble_collection_instance"
    bl_label = "MACHIN3: Assemle Collection Instance"
    bl_description = "Make Collection Instance objects accessible\nALT: Keep Empty as Root"
    bl_options = {'REGISTER'}

    keep_empty: BoolProperty(name="Keep Empty as Root", default=False)

    @classmethod
    def poll(cls, context):
        active = context.active_object
        return active and active.type == 'EMPTY' and active.instance_collection and active.instance_type == 'COLLECTION'

    def invoke(self, context, event):
        self.keep_empty = event.alt
        return self.execute(context)

    def execute(self, context):
        global decalmachine, meshmachine

        if decalmachine is None:
            decalmachine = get_addon('DECALmachine')[0]

        if meshmachine is None:
            meshmachine = get_addon('MESHmachine')[0]

        active = context.active_object

        instances = {active} | {obj for obj in context.selected_objects if obj.type == 'EMPTY' and obj.instance_collection}

        if any((i.instance_collection.library for i in instances)):
            bpy.ops.object.make_local(type='ALL')

            for instance in instances:
                instance.select_set(True)

        for instance in instances:
            collection = instance.instance_collection

            root_children = self.assemble_collection_instance(context, instance, collection)

            if self.keep_empty:
                for child in root_children:
                    parent(child, instance)

                    instance.select_set(True)
                    context.view_layer.objects.active = instance
            else:
                bpy.data.objects.remove(instance, do_unlink=True)

        if decalmachine:
            decals = [obj for obj in context.scene.objects if obj.DM.isdecal]
            backups = [obj for obj in decals if obj.DM.isbackup]

            if decals:
                from DECALmachine.utils.collection import sort_into_collections

                for obj in decals:
                    sort_into_collections(context, obj, purge=False)

            if backups:
                bpy.ops.machin3.sweep_decal_backups()

        if meshmachine:
            stashobjs = [obj for obj in context.scene.objects if obj.MM.isstashobj]

            if stashobjs:
                bpy.ops.machin3.sweep_stashes()

        bpy.ops.outliner.orphans_purge(do_local_ids=True, do_linked_ids=True, do_recursive=True)

        return {'FINISHED'}

    def assemble_collection_instance(self, context, instance, collection):

        cols = [col for col in instance.users_collection]
        imx = instance.matrix_world


        children = [obj for obj in collection.objects]

        bpy.ops.object.select_all(action='DESELECT')

        for obj in children:
            for col in cols:
                col.objects.link(obj)
            obj.select_set(True)

        if len(collection.users_dupli_group) > 1:

            bpy.ops.object.duplicate()

            for obj in children:
                for col in cols:
                    col.objects.unlink(obj)

            children = [obj for obj in context.selected_objects]

            for obj in children:
                if obj.name in collection.objects:
                    collection.objects.unlink(obj)

        root_children = [obj for obj in children if not obj.parent]

        for obj in root_children:
            obj.matrix_world = imx @ obj.matrix_world

            obj.select_set(True)
            context.view_layer.objects.active = obj

        instance.instance_type = 'NONE'
        instance.instance_collection = None

        if len(collection.users_dupli_group) == 0:
            bpy.data.collections.remove(collection)

        return root_children
