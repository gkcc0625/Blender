# Copyright (C) 2022 Thomas Hoppe (h0bB1T). All rights reserved.
#
# Unauthorized copying of this file via any medium is strictly prohibited.
# Proprietary and confidential.

import bpy, uuid

from bpy.types import Operator, UILayout
from bpy.props import StringProperty, EnumProperty, BoolProperty

from ..registries.resource_lists_registry import ResourceListsRegistry
from ..awp.utils import section_by_name


class ASSET_OT_create_catalog(Operator):
    """
    Create a new (sub)-catalog.
    """
    bl_idname = 'awp.create_catalog'
    bl_label = 'Create'
    bl_description = 'Create new Catalog or Subcatalog'
    bl_options = {'REGISTER'}

    section: StringProperty()

    sub_catalog: BoolProperty(name='Create Subcatalog')

    catalog: EnumProperty(
        name='Catalog',
        description='Create Subcatalog',
        items=lambda self, _: ResourceListsRegistry.get().catalogs(section_by_name(self.section).export_library)
    )

    name: StringProperty(name='Name')


    def execute(self, context: bpy.context):
        if self.name:
            try:
                section = section_by_name(self.section)
                fname = sname = self.name
                if self.sub_catalog:
                    entry = ResourceListsRegistry.get().catalog_info(section.export_library, self.catalog)
                    if entry:
                        fname = f'{entry[1]}/{self.name}'
                        sname = f'{entry[2]}-{self.name}'

                id = str(uuid.uuid4())
                if ResourceListsRegistry.get().add_catalog(section.export_library, id, fname, sname):
                    section.catalog = id
                    self.report({'INFO'}, 'Catalog created')
                else:
                    self.report({'ERROR'}, 'Catalog already exists')
            except Exception as ex:
                self.report({'ERROR'}, 'Catalog creation failed (see Console)')
        else:
            self.report({'ERROR'}, 'Catalog Name empty')
        
        return {'FINISHED'}


    def draw(self, context: bpy.context):
        l = self.layout.column(align=True)
        section = section_by_name(self.section)
        if ResourceListsRegistry.get().catalogs(section.export_library):
            l.prop(self, 'sub_catalog', icon='ASSET_MANAGER', toggle=True)
            if self.sub_catalog:
                l.prop(self, 'catalog', text='Parent')
        l.prop(self, 'name')


    def invoke(self, context, event):
        return context.window_manager.invoke_props_dialog(self)


    def create_ui(l: UILayout, section: str):
        op = l.operator(ASSET_OT_create_catalog.bl_idname, icon='ADD', text='') # type: ASSET_OT_create_catalog
        op.section = section
