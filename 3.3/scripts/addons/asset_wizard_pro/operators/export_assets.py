# Copyright (C) 2022 Thomas Hoppe (h0bB1T). All rights reserved.
#
# Unauthorized copying of this file via any medium is strictly prohibited.
# Proprietary and confidential.

import bpy, os, traceback

from bpy.types import Operator, UILayout
from bpy.props import StringProperty, BoolProperty

from typing import List, Tuple

from ..constants import ResourceType, ResourceTypes
from ..preferences import PreferencesPanel
from ..properties import Properties, PropertySection
from ..registries.resource_lists_registry import ResourceListsRegistry
from ..awp.invoke_external import render_preview, update_settings
from ..utils.previews import thumbnail_of_current_render
from ..utils.io import os_path, TempFile
from ..registries.image_packer_registry import ImagePackerRegistry
from ..operators.pack_select import ASSET_OT_pack_select


class ASSET_OT_export(Operator):
    """
    Export resource.
    """
    bl_idname = 'awp.export'
    bl_label = ''
    bl_description = ''
    bl_options = {'REGISTER'}


    mode: StringProperty()
    filename: StringProperty()
    name: StringProperty()
    catalog: StringProperty()
    desc: StringProperty()
    author: StringProperty()
    tags: StringProperty()
    extra_tag: StringProperty()
    use_render_as_preview: BoolProperty()

    
    def __fix_volume_path(self, objects: List[bpy.types.Object]) -> List[Tuple[bpy.types.Object, str]]:
        """
        Make all paths of volumes absolute, return pairs of objects 
        and there relative paths for restoring them.
        """
        r = []
        for o in objects:
            if isinstance(o, bpy.types.Object) and o.type == 'VOLUME':
                old_volume_path = o.data.filepath
                o.data.filepath = os_path(old_volume_path)
                r.append((o, old_volume_path))

        return r


    def __export_render_preview_and_fix(self, filename: str, rsc: ResourceType, reimport_blend: str) -> bool:
        """
        Export rsc to library, render preview and apply asset settings to it.
        Returns False on failure.
        """
        export = reimport_blend if reimport_blend else filename

        # Transform path to .vdb of all volumes into an absolute path, relative remap seems to fail.
        original_paths = []
        if isinstance(rsc, bpy.types.Object):
            original_paths = self.__fix_volume_path([rsc])
        elif isinstance(rsc, bpy.types.Collection):
            original_paths = self.__fix_volume_path(rsc.all_objects)

        try:
            bpy.data.libraries.write(
                export,
                set([rsc]),
                path_remap='ABSOLUTE',
                fake_user=True,
                compress=True
            )
        except Exception as ex:
            self.report({'ERROR'}, f'Failure to export Resource: {ex} (see Console)')
            print(traceback.format_exc())
            return False
        finally:
            # Restore original volume paths.
            for o, p in original_paths:
                o.data.filepath = p

        tags = self.tags.split('~')
        with TempFile('png') as image_file:
            preview = ''
            if self.use_render_as_preview:
                error = thumbnail_of_current_render(image_file, PreferencesPanel.get().dimension)
                if error:
                    self.report({'ERROR'}, error)
                    return False
                preview = image_file
            elif self.mode in [ 'MATERIAL', 'OBJECT', 'COLLECTION', 'SELECTED_OBJECTS' ]:
                render_preview(
                    export, 
                    image_file, 
                    'OBJECT' if self.mode == 'SELECTED_OBJECTS' else self.mode, 
                    rsc.name
                )
                if os.path.exists(image_file):
                    preview = image_file
                else:
                    self.report({'ERROR'}, 'Preview rendering failed (see Console)')
                    return False
            elif self.mode == 'NODE_GROUP':
                if rsc.bl_idname == 'ShaderNodeTree':
                    preview = os.path.join(os.path.dirname(__file__), '..', 'data', 'images', 's-node.png')
                else:
                    preview = os.path.join(os.path.dirname(__file__), '..', 'data', 'images', 'g-node.png')
                
            update_settings(
                filename, 
                reimport_blend, 
                preview, 
                'OBJECT' if self.mode == 'SELECTED_OBJECTS' else self.mode, 
                rsc.name, 
                self.catalog, 
                self.desc, 
                self.author, 
                tags, 
                self.extra_tag,
                ImagePackerRegistry.get().selected(),
                True
            )

            return True


    def __get_all_resources(self, context: bpy.context) -> ResourceTypes:
        if self.mode == 'SELECTED_OBJECTS':
            rscs = context.selected_objects
        else:
            rsc = {
                'MATERIAL': bpy.data.materials,
                'OBJECT': bpy.data.objects,
                'COLLECTION': bpy.data.collections,
                'NODE_GROUP': bpy.data.node_groups,
            }[self.mode][self.name]
            rscs = [rsc]
        return rscs


    @classmethod
    def description(cls, context, properties):
        if properties.mode == 'SELECTED_OBJECTS':
            return f'Export selected Objects to "{properties.filename}"'
        else:
            m = {
                'MATERIAL': 'material',
                'OBJECT': 'object',
                'COLLECTION': 'collection',
                'NODE_GROUP': 'node group',
            }.get(properties.mode, '??')
            return f'Export {m} "{properties.name}" to "{properties.filename}"'


    def execute(self, context: bpy.context):
        #self.report({'WARNING'}, 'Currently disabled, remove after dev')
        #return {'FINISHED'}

        # Get ressources to export.
        rscs = self.__get_all_resources(context)
        for rsc in rscs:
            # If the file exists, we export to a temp file
            # and re-import in a background process from this temp-file.
            # Otherwise, just export and fix settings in it.
            if os.path.exists(self.filename):
                with TempFile('blend') as n:
                    result = self.__export_render_preview_and_fix(self.filename, rsc, n)
            else:
                result = self.__export_render_preview_and_fix(self.filename, rsc, '')
            
            # Break in case of export / preview gen error.
            if not result:
                break

        # Update node list.
        ResourceListsRegistry.get().update()
        ResourceListsRegistry.get().update_nodes()

        # Update asset browser.
        # Seems to be unstable
        #try:
        #    update_asset_browser(context)
        #except:
        #    pass

        return {'FINISHED'}


    def draw(self, context: bpy.context):
        self.layout.ui_units_x = 40
        a = self.layout.column(align=True)
        r = a.row(align=True)
        ASSET_OT_pack_select.create_ui(r, 'CHECKBOX_HLT', 'Select All', False, 'ALL', '')
        ASSET_OT_pack_select.create_ui(r, 'CHECKBOX_DEHLT', 'Select None', False, 'NONE', '')
        g = a.grid_flow(row_major=True, columns=2, align=True)
        for k, v in ImagePackerRegistry.get().images().items():
            r = g.box().row(align=True)
            
            c = r.column(align=True)
            sr = c.row(align=True)
            ASSET_OT_pack_select.create_ui(sr, 'CHECKBOX_HLT' if v.selected else 'CHECKBOX_DEHLT', '', v.selected, 'TOGGLE', k)
            ASSET_OT_pack_select.create_ui(sr, 'QUESTION', '', v.show_info, 'INFO', k)
            if v.show_info:
                if v.image.preview and v.image.preview.icon_id:
                    c.template_icon(v.image.preview.icon_id, scale=3)
                else:
                    c.label(text='No preview')

            c = r.column(align=True)
            r = g.box().column(align=True)
            r.label(text=f'Image: {v.image.name} [ {v.image.file_format}, {v.image.generated_width}x{v.image.generated_width} ]  [ {v.image.filepath} ]')
            if v.show_info:
                for o in v.origins:
                    r.label(text=str(o))

    
    def invoke(self, context: bpy.context, event):
        # Get ressources to export.
        rscs = self.__get_all_resources(context)
        if rscs:
            ImagePackerRegistry.get().update(rscs)
            if ImagePackerRegistry.get().images():
                return context.window_manager.invoke_props_dialog(self)
            else:
                return self.execute(context)

        return {'FINISHED'}


    @staticmethod
    def create_ui(l: UILayout, mitn: Tuple[str, str, str, str], section: PropertySection):
        if len(mitn) == 4:
            mode, icon, title, name = mitn
            extra_tag = ''
        elif len(mitn) == 5:
            mode, icon, title, name, extra_tag = mitn
        file = section.export_file
        op = l.operator(ASSET_OT_export.bl_idname, text=f'Export {title}', icon=icon) # type: ASSET_OT_export
        op.mode = mode
        op.filename = os.path.join(section.export_library, file)
        op.name = name
        op.catalog = section.catalog if ResourceListsRegistry.get().catalogs(section.export_library) else ''
        op.desc = section.description
        op.author = Properties.get().author
        op.tags = '~'.join([ t.title for t in section.tags])
        op.extra_tag = extra_tag
        op.use_render_as_preview = section.use_render_as_preview
