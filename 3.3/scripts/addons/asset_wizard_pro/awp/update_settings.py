# Copyright (C) 2022 Thomas Hoppe (h0bB1T). All rights reserved.
#
# Unauthorized copying of this file via any medium is strictly prohibited.
# Proprietary and confidential.

import dataclasses
import os, sys, bpy, json, traceback

from typing import List
from dataclasses import dataclass

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__))))

@dataclass
class SettingsUpdateSettings:
    reimport_blend: str
    image_file: str
    mode: str
    name: str 
    catalog: str
    description: str
    author: str
    tags: List[str]
    extra_tag: str
    auto_place: bool
    pack_images: List[str]
    image_cleanup: bool
    relative_paths: bool

    def to_js(self) -> str:
        return json.dumps(dataclasses.asdict(self))

    @staticmethod
    def from_js(js: str) -> 'SettingsUpdateSettings':
        j = json.loads(js)
        return SettingsUpdateSettings(
            j['reimport_blend'],
            j['image_file'],
            j['mode'],
            j['name'],
            j['catalog'],
            j['description'],
            j['author'],
            j['tags'],
            j['extra_tag'],
            j['auto_place'],
            j['pack_images'],
            j['image_cleanup'],
            j['relative_paths'],
        )


class SettingsUpdate:
    def __init__(self, settings: SettingsUpdateSettings):
        self.settings = settings


    @staticmethod
    def name_for(suffix: str) -> str:
        """
        Create unique names for objects, material ...
        """
        return f'Asset Wizard {suffix}'


    def prepere_scene(self) -> bpy.types.Collection:
        """
        Create a scene and return the master collection.
        """
        if not bpy.data.scenes:
            scene = bpy.data.scenes.new()
        else:
            scene = bpy.data.scenes[0]
        
        # Get master collection.
        return scene.collection


    def create_collection(self, master_collection: bpy.types.Collection, suffix: str) -> bpy.types.Collection:
        """
        Create collection for collections, object or materials.
        """
        # Create or get collection.
        name = SettingsUpdate.name_for(suffix)
        if name not in bpy.data.collections:
            col = bpy.data.collections.new(name)
            master_collection.children.link(col)
        else:
            col = bpy.data.collections[name]

        return col


    def add_plane(self) -> bpy.types.Object:
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


    def add_to_blend(self):
        """
        The primary method.
        """
        from shared import auto_place, remove_duplicate_images, create_image_hash

        # Eventually prepare scene and get master collection.
        master_collection = self.prepere_scene()

        if self.settings.reimport_blend:
            # Import the resource and use name object from returned list, may be renamed during import.
            with bpy.data.libraries.load(self.settings.reimport_blend, link=False, relative=False) as (_, data_to):
                if self.settings.mode == 'MATERIAL':
                    data_to.materials = [self.settings.name]
                    rscs = data_to.materials
                elif self.settings.mode == 'OBJECT':
                    data_to.objects = [self.settings.name]
                    rscs = data_to.objects
                elif self.settings.mode == 'COLLECTION':
                    data_to.collections = [self.settings.name]
                    rscs = data_to.collections
                elif self.settings.mode == 'NODE_GROUP':
                    data_to.node_groups = [self.settings.name]
                    rscs = data_to.node_groups

            rsc = rscs[0]
        else:
            # Get access to the resource to store.
            rsc = {
                'MATERIAL': bpy.data.materials,
                'OBJECT': bpy.data.objects,
                'COLLECTION': bpy.data.collections,
                'NODE_GROUP': bpy.data.node_groups,
            }[self.settings.mode][self.settings.name]

        # Act depending on type.
        if self.settings.mode == 'COLLECTION':
            # Add collection to this collection.
            col = self.create_collection(master_collection, 'Collections')
            col.children.link(rsc)
        if self.settings.mode == 'OBJECT': 
            # Add object to this collection.
            col = self.create_collection(master_collection, 'Objects')
            col.objects.link(rsc)
        elif self.settings.mode == 'MATERIAL':
            # Create mesh + object to host material and add material.
            o = self.add_plane()
            o.name = f'AW Material - {self.settings.name}'
            o.data.materials.append(rsc)
            o.use_fake_user = True

            # Add to this collection.
            col = self.create_collection(master_collection, 'Materials and Nodes')
            col.objects.link(o)

        # Mark resource as asset.
        rsc.asset_mark()
        
        # Set fake user, so blender always stores it.
        #bpy.ops.ed.lib_id_fake_user_toggle(override)
        rsc.use_fake_user = True

        # Apply image, catalog, description and author to asset.
        if self.settings.image_file: 
            try:
                if (3, 2, 0) > bpy.app.version:
                    override = bpy.context.copy()
                    override['id'] = rsc
                    bpy.ops.ed.lib_id_load_custom_preview(override, filepath=self.settings.image_file)
                else:
                    with bpy.context.temp_override(id=rsc):
                        bpy.ops.ed.lib_id_load_custom_preview(filepath=self.settings.image_file)
            except:
                # May occur in older Blender versions for nodes.
                print(traceback.format_exc())

        # The following crashes (headless rendering)?
        #elif self.mode in [ 'MATERIAL', 'OBJECT', 'COLLECTION' ]:
        #    bpy.ops.ed.lib_id_generate_preview(override)

        if self.settings.catalog: rsc.asset_data.catalog_id = self.settings.catalog
        if self.settings.description: rsc.asset_data.description = self.settings.description
        if self.settings.author: rsc.asset_data.author = self.settings.author

        # Used for node groups, use as first tag.
        if self.settings.extra_tag: 
            rsc.asset_data.tags.new(self.settings.extra_tag, skip_if_exists=True)

        for tag in self.settings.tags:
            if tag:
                rsc.asset_data.tags.new(tag, skip_if_exists=True)


        # If enabled, automatically place all items in a grid.
        if self.settings.auto_place: auto_place()

        # If enabled, auto remove doule images in library.
        if self.settings.image_cleanup: remove_duplicate_images(False)

        # Adjust all paths.
        if self.settings.relative_paths: bpy.ops.file.make_paths_relative()

        # Pack all images (that are not already packed) that have one 
        # of the following hashes.
        for image in bpy.data.images:
            # If already packed, skip.
            if image.packed_file and image.packed_file.data: continue
            hash = create_image_hash(image, False)
            if hash:
                # Check if we should pack this image.
                if hash in self.settings.pack_images:
                    print(f'Pack image: {image.filepath}')
                    # Yes, pack it.
                    image.pack()

        # Prepare for saving
        bpy.context.preferences.filepaths.save_version = 0 # No backup blends needed
        bpy.context.preferences.filepaths.use_file_compression = True
        bpy.context.preferences.filepaths.use_relative_paths = True
        bpy.context.view_layer.update()
        bpy.ops.wm.save_mainfile(compress=True, relative_remap=True)        


def main(args):
    settings = SettingsUpdateSettings.from_js(args[0])
    print(settings)
    SettingsUpdate(settings).add_to_blend()


if __name__ == '__main__':
    if '--' not in sys.argv:
        argv = []  # as if no args are passed
    else:
        argv = sys.argv[sys.argv.index('--') + 1:]  # get all args after "--"
    main(argv)
