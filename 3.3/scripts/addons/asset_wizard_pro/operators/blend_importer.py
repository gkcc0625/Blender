# Copyright (C) 2022 Thomas Hoppe (h0bB1T). All rights reserved.
#
# Unauthorized copying of this file via any medium is strictly prohibited.
# Proprietary and confidential.

import bpy, os

from bpy.types import Operator, UILayout
from bpy.props import StringProperty, BoolProperty, CollectionProperty, EnumProperty
from bpy_extras.io_utils import ImportHelper

from typing import List, Union

from ..awp.shared import do_place


class ASSET_OT_blend_importer(Operator, ImportHelper):
    """
    Batch import from multiple .blend files.
    """
    bl_idname = 'awp.blend_importer'
    bl_label = 'Import'
    bl_description = 'Import multiple Blend Files at once'
    bl_options = {'REGISTER', 'UNDO'}


    filename_ext = '.blend'
    filter_glob: StringProperty(default='*.blend', options={'HIDDEN'}, maxlen=1024)
    files: CollectionProperty(type=bpy.types.PropertyGroup)

    collection_per_file: BoolProperty(
        name='Collection per File', 
        description='Create a separate Collection for each File',        
        default=True,
    )

    types: EnumProperty(
        name='', 
        description='What kind of Data to import',
        items=[
            ( 'C', 'Collections', '', 'OUTLINER_COLLECTION', 1 ),
            ( 'O', 'Objects', '', 'OBJECT_DATA', 2 ),
            ( 'M', 'Materials', '', 'MATERIAL', 4 ),
        ],
        options={'ENUM_FLAG'},
        default={'C', 'O'}
    )

    ignore: EnumProperty(
        name='',
        description='Data types to ignore (remove after import)',
        items=[
            ( 'C', 'Cameras', '', 'OUTLINER_OB_CAMERA', 1 ),
            ( 'L', 'Lights', '', 'OUTLINER_OB_LIGHT', 2 ),
        ],
        options={'ENUM_FLAG'},
        default={'C', 'L'}
    )

    create_material_plane: BoolProperty(
        name='Material Preview',
        description='Create a Preview Plane for each Material',
        default=True
    )

    def __add_plane(self) -> bpy.types.Object:
        """
        Add a plane to the scene to hold materials.
        """
        # Store names of existing elements and create plane.
        existing = [ o.name for o in bpy.data.objects ]
        bpy.ops.mesh.primitive_plane_add()

        # Find the one not in the list above.
        for o in bpy.data.objects:
            if o.name not in existing:
                # Plane is added to master collection, remove from there.
                if o.name in bpy.context.scene.collection.objects:
                    bpy.context.scene.collection.objects.unlink(o)
                return o    


    def __is_in_collections(self, col: bpy.types.Collection, other: List[bpy.types.Collection]) -> bool:
        """
        Check if the given collection (col) is a subcollection of any other (recursive).
        """
        for o in other:
            if o == col: continue # No self-check.
            for c in o.children:
                if c == col:
                    return True
                is_sub = self.__is_in_collections(col, o.children)
                if is_sub:
                    return True
        return False


    def execute(self, context: bpy.context):
        # Collect all here for auto placement.
        all_objects = [] # type: List[Union[bpy.types.Collection, bpy.types.Object]]

        # All imported collections and objects must me directly or indirectly linked to this collection.
        master_collection = context.scene.collection

        # Loop over all selected files.
        folder = (os.path.dirname(self.filepath))
        for i in self.files:
            file = (os.path.join(folder, i.name))

            # Import collections and objects.
            collections, objects, materials = [], [], []
            with bpy.data.libraries.load(file, link=False) as (data_from, data_to):
                if 'C' in self.types:
                    data_to.collections = data_from.collections
                    collections = data_to.collections

                if 'O' in self.types:
                    data_to.objects = data_from.objects
                    objects = data_to.objects # type: List[bpy.types.Object]

                if 'M' in self.types:
                    data_to.materials = data_from.materials
                    materials = data_to.materials

            # Imported anything?
            if collections or objects or materials:
                new_collections = [] # type: List[bpy.data.Collection]

                # Depending on mode, either create a sub-collection for each file.
                if self.collection_per_file:
                    parent_collection = bpy.data.collections.new(os.path.splitext(i.name)[0])
                    master_collection.children.link(parent_collection)
                else:
                    parent_collection = master_collection

                # Add all collections to the master collection.
                for c in collections:
                    new_collections.append(c)
                    if not self.__is_in_collections(c, collections):
                        parent_collection.children.link(c)

                # Add them to for placement.
                all_objects.extend(collections)

                # Objects are somewhat special, they may belong to collections
                # already added to the scene. Check this, and only add
                # those not already in a collection.
                for o in objects:
                    found = False
                    for c in collections:
                        for co in c.all_objects:
                            if co == o:
                                found = True
                                break
                        if found:
                            break

                    if not found:
                        parent_collection.objects.link(o)
                        all_objects.append(o)

                if self.create_material_plane:
                    if materials:
                        materials_collection = bpy.data.collections.new('Materials')
                        parent_collection.children.link(materials_collection)
                        for m in materials:
                            o = self.__add_plane()
                            materials_collection.objects.link(o)

                            o.name = m.name
                            o.data.materials.append(m)
                            all_objects.append(o)

                # Eventually remove cams & lights.
                remove = []
                for o in objects:
                    if 'C' in self.ignore and o.type == 'CAMERA':
                        remove.append(o)
                    if 'L' in self.ignore and o.type == 'LIGHT':
                        remove.append(o)

                for o in remove: bpy.data.objects.remove(o)

                # Remove empty collections.
                remove.clear()
                for c in new_collections:
                    if not c.all_objects and not c.children:
                        remove.append(c)
                for c in remove: bpy.data.collections.remove(c)

                do_place(all_objects)
            else:
                self.report({'WARNING'}, 'Nothing imported with selected Options')

        return {'FINISHED'}


    def draw(self, context):
        l = self.layout # type: bpy.types.UILayout
        c = l.box().column(align=False)

        c.label(text='Import Behaviour:')
        c.prop(self, 'collection_per_file', toggle=True, icon='COLLECTION_NEW')

        c2 = c.column(align=True)
        r = c2.row()
        r.label(text='Types to Import:')
        r.row(align=True).prop(self, 'types', expand=True)

        r = c2.row()
        r.label(text='Items to remove after Import')
        r.row(align=True).prop(self, 'ignore', expand=True)

        if 'M' in self.types:
            c2.prop(self, 'create_material_plane', toggle=True, icon='MESH_PLANE')



    @staticmethod
    def create_ui(l: UILayout, icon: str, text: str):
        op = l.operator(ASSET_OT_blend_importer.bl_idname, icon=icon, text=text) # type: ASSET_OT_blend_importer

