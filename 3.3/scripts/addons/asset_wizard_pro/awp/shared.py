# Copyright (C) 2022 Thomas Hoppe (h0bB1T). All rights reserved.
#
# Unauthorized copying of this file via any medium is strictly prohibited.
# Proprietary and confidential.

import bpy, os, hashlib

from math import ceil
from mathutils import Vector

from typing import Dict, List, Tuple, Union


"""
User both in the Addon directly, but also from update_settings script externally.
"""

def create_image_hash(image: bpy.types.Image, packed_only: bool) -> Union[str, None]:
    """
    Create hash from image source (file on disk or packed data)
    """
    # If packed, use the packed data to create the hash.
    if image.packed_file and image.packed_file.data:
        return hashlib.blake2s(image.packed_file.data).hexdigest()

    # First try to use external data.
    if not packed_only and image.filepath:
        path = os.path.realpath(bpy.path.abspath(image.filepath))
        #print(f'Create hash from file: {image.filepath} -> {bpy.path.abspath(image.filepath)} -> {path}')
        if os.path.exists(path):
            with open(path, 'rb') as f:
                return hashlib.blake2s(f.read()).hexdigest()

    return None


def remove_duplicate_images(packed_only: bool):
    """
    Remove double or more occurences of images using binary comparision.
    """
    # Build dict of images by their binary hash. Identical images
    # will end in the same entry.
    hashes = {} # type: Dict[str, List[bpy.types.Image]]
    for i in bpy.data.images:
        hash = create_image_hash(i, packed_only)
        if hash:
            if hash in hashes:
                hashes[hash].append(i)
            else:
                hashes[hash] = [i]

    # Eliminte duplicates.
    for images in hashes.values():
        if len(images) > 1: # Have duplicates of this image?
            # We prefer a packed one to use.
            used_image = images[0]
            for i in images:
                if i.packed_file and i.packed_file.data:
                    used_image = i
                    break
            
            # Assign image 'used_image' to all others.
            for i in images:
                if i != used_image:
                    i.user_remap(used_image.id_data)


def bounding_box(objects: List[bpy.types.Object]) -> Tuple[Tuple[int, int, int], Tuple[int, int, int]]:
    """
    Find bounding box enclosing the given object, return dimension and center.
    """
    if objects:
        vecs = []
        for o in objects:
            try:
                vecs.extend([ o.matrix_world @ Vector(corner) for corner in o.bound_box ])
            except:
                pass

        if vecs:
            bmix = min([ v[0] for v in vecs ])
            bmiy = min([ v[1] for v in vecs ])
            bmiz = min([ v[2] for v in vecs ])
            bmax = max([ v[0] for v in vecs ])
            bmay = max([ v[1] for v in vecs ])
            bmaz = max([ v[2] for v in vecs ])

            dx, dy, dz = bmax - bmix, bmay - bmiy, bmaz - bmiz
            cx, cy, cz = dx/2 + bmix, dy/2 + bmiy, dz/2 + bmiz

            return ((dx, dy, dz), (cx, cy, cz))
        #else:
        #    return ((0, 0, 0), objects[0].location)
    else:
        return ((0, 0, 0), (0, 0, 0))


def do_place(assets: List[Union[bpy.types.Collection, bpy.types.Object]], padding: float = 0.2):
    if not assets: return

    # Find the largest dimension from all assets to place.
    mx = 0
    all = [] # type: List[float]
    for a in assets:
        try:
            if isinstance(a, bpy.types.Object):
                d, _ = bounding_box([a])
            elif isinstance(a, bpy.types.Collection):
                d, _ = bounding_box(a.all_objects)
        
            all.append(d[0])
            all.append(d[1])
            mx = max(mx, d[0], d[1])
        except:
            pass

    distance = (1 + padding) * mx
    distance = (1 + padding) * (sum(all) / len(all))

    # Determine grid.
    if assets:
        grid_dim = ceil(len(assets) ** 0.5)
        offset = -grid_dim * distance / 2 + distance / 2

        # Place.
        n = 0
        for a in assets:
            try:
                x = (n % grid_dim) * distance + offset
                y = (n // grid_dim) * distance + offset
                if isinstance(a, bpy.types.Object) and not a.parent:
                    a.location = (x, y, 0)
                elif isinstance(a, bpy.types.Collection):
                    # Collections are somewhat special,
                    # objects must stay relative to each other.
                    objs = a.all_objects
                    if objs:
                        rel = (
                            x - objs[0].location[0],
                            y - objs[0].location[1],
                            0 - objs[0].location[2]
                        )
                        for o in objs:
                            if not o.parent:
                                o.location = (
                                    o.location[0] + rel[0],
                                    o.location[1] + rel[1],
                                    o.location[2] + rel[2],
                                )
            except:
                pass

            n += 1


def auto_place(padding: float = 0.2):
    """
    Places all asset-related object in a grid.
    """
    # Collect all collections & objects.
    assets = []
    # Collections.
    for c in bpy.data.collections:
        if c.asset_data:
            assets.append(c)

    # Objects.
    for o in bpy.data.objects:
        if o.asset_data:
            assets.append(o)

    # Objects that contain materials with asset mark.
    for m in bpy.data.materials:
        if m.asset_data:
            for o in bpy.data.objects:
                found = False
                for ms in o.material_slots:
                    if ms.material == m:
                        found = True
                        break
                if found:
                    assets.append(o)

    do_place(assets, padding)

