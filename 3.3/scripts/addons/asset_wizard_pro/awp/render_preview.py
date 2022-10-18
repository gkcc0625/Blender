# Copyright (C) 2022 Thomas Hoppe (h0bB1T). All rights reserved.
#
# Unauthorized copying of this file via any medium is strictly prohibited.
# Proprietary and confidential.

import dataclasses
import bpy, sys, json, os

from dataclasses import dataclass
from typing import List

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__))))

@dataclass
class RenderPreviewSettings:
    blend_file: str
    image_file: str
    mode: str
    name: str
    engine: str
    samples: str
    size: int

    def to_js(self) -> str:
        return json.dumps(dataclasses.asdict(self))

    @staticmethod
    def from_js(js: str) -> 'RenderPreviewSettings':
        j = json.loads(js)
        return RenderPreviewSettings(
            j['blend_file'],
            j['image_file'],
            j['mode'],
            j['name'],
            j['engine'],
            j['samples'],
            j['size']
        )


class PreviewRenderer:
    def __init__(self, settings: RenderPreviewSettings):
        self.settings = settings


    def cam_to_objects(self, objects: List[bpy.types.Object]):
        from shared import bounding_box

        # Align camera to objects.

        # Deselect all first.
        [ o.select_set(False) for o in bpy.context.scene.objects ]

        # Check if we should create a fake cube.
        types = set([ o.type for o in objects ])
        fake_cube = len(types) == 1 and 'VOLUME' in types

        if fake_cube:
            # Find dimension and center of bounding box.
            d, c = bounding_box(objects)

            # Create a temporary cube for the bounding box, as the op
            # does not work with volumes and scaling it a little bit up gives
            # a margin to the final preview.
            existing = [ o.name for o in bpy.data.objects ]
            bpy.ops.mesh.primitive_cube_add(size=1, location=c, scale=d)
            for o in bpy.data.objects:
                if o.name not in existing:
                    cube = o
                    break

            # Select just the cube.
            cube.select_set(True)
        else:
            # Select objects of interest.
            [ o.select_set(True) for o in objects ]

        # Move camera, so selected objects are optimal in view. 
        bpy.ops.view3d.camera_to_view_selected()

        if fake_cube:
            # Remove dummy cube.
            bpy.data.objects.remove(cube)


    def prepare_material_scene(self, material: str) -> bool:
        # Load materials from file.
        with bpy.data.libraries.load(self.settings.blend_file, link=False) as (data_from, data_to):
            if material not in data_from.materials:
                return False # Not available
            data_to.materials = [material]
            mats = data_to.materials

        # Set material to first imported one.
        bpy.data.objects['Preview'].material_slots[0].material = mats[0]

        #self.cam_to_objects([bpy.data.objects['Preview']])
        
        return True


    def prepare_object_scene(self, obj: str) -> bool:
        # Remove material preview object.
        bpy.data.objects.remove(bpy.data.objects['Preview'])

        # Deselect all objects.
        [ o.select_set(False) for o in bpy.context.scene.objects ]
        
        # Load object from file.
        with bpy.data.libraries.load(self.settings.blend_file, link=False) as (data_from, data_to):
            if obj not in data_from.objects:
                return False
            data_to.objects = [obj]
            objs = data_to.objects # type: List[bpy.types.Object]

        # Append object to it.
        coll = bpy.context.collection
        for l in objs:
            coll.objects.link(l)
            l.animation_data_clear()

        self.cam_to_objects(objs)
 
        return True


    def prepare_collection_scene(self, coll: str) -> bool:
        # Remove material preview object.
        bpy.data.objects.remove(bpy.data.objects['Preview'])

        # Deselect all objects.
        [ o.select_set(False) for o in bpy.context.scene.objects ]

        # Store existing objects.
        existing = [ o for o in bpy.context.scene.objects ]
        
        # Load collection from file.
        with bpy.data.libraries.load(self.settings.blend_file, link=False) as (data_from, data_to):
            if coll not in data_from.collections:
                return False
            data_to.collections = [coll]
            colls = data_to.collections

        # Append all collections to it.
        coll = bpy.context.collection
        for l in colls:
            for o in l.all_objects:
                o.animation_data_clear()
            coll.children.link(l)

        self.cam_to_objects([ o for o in bpy.context.scene.objects if o not in existing ])

        return True        


    def prepare_and_render(self):
        if self.settings.mode == 'MATERIAL':
            if not self.prepare_material_scene(self.settings.name):
                return
        elif self.settings.mode == 'OBJECT':
            if not self.prepare_object_scene(self.settings.name):
                return
        elif self.settings.mode == 'COLLECTION':
            if not self.prepare_collection_scene(self.settings.name):
                return

        bpy.context.scene.render.resolution_x = self.settings.size
        bpy.context.scene.render.resolution_y = self.settings.size
        bpy.context.scene.render.engine = self.settings.engine
        bpy.context.scene.cycles.samples = self.settings.samples
        bpy.context.scene.render.filepath= self.settings.image_file
        bpy.context.scene.render.image_settings.file_format = 'PNG'
        bpy.context.scene.render.film_transparent = True
        bpy.ops.render.render(write_still=True)


def main(args):
    settings = RenderPreviewSettings.from_js(args[0])
    print(settings)
    PreviewRenderer(settings).prepare_and_render()


if __name__ == '__main__':
    if '--' not in sys.argv:
        argv = []  # as if no args are passed
    else:
        argv = sys.argv[sys.argv.index('--') + 1:]  # get all args after "--"
    main(argv)
