# Copyright (C) 2022 Thomas Hoppe (h0bB1T). All rights reserved.
#
# Unauthorized copying of this file via any medium is strictly prohibited.
# Proprietary and confidential.

import bpy

from typing import Dict, List, Union

from ..awp.shared import create_image_hash
from ..constants import ResourceTypes


class PackOrigin:
    """
    Recursive information about a single origin if a used image.
    """
    def __init__(self, type: str, name: str, origin: Union['PackOrigin', None]):
        self.type = type
        self.name = name
        self.origin = origin

    def __str__(self) -> str:
        if self.origin:
            return f'{self.origin} < {self.type}: {self.name}'
        else:
            return f'{self.type}: {self.name}'


class PackInfo:
    """
    Contains detailed info about a packable item (it's original hierarchy).
    Current this is Image only.
    """
    def __init__(self, image: bpy.types.Image, origin: PackOrigin, scanned: List['PackInfo']):
        self.image = image
        self.origin = origin

        # Id to identify the resource uniquely, even in the exported file.
        self.unique_id = ''

        # If this image already has been hashed (as it is used multiple times),
        # use this info.
        for s in scanned:
            if s.image == self.image:
                self.unique_id = s.unique_id
                break

        # Other create new hash.
        if not self.unique_id:
            self.unique_id = create_image_hash(self.image, False)
            if not self.unique_id:
                self.unique_id = '!!NO IMAGE DATA!!'


    def __str__(self) -> str:
        return f'{self.unique_id}: [{self.origin}]'


class PackInfoMerged:
    """
    Same as PackInfo, but identical images are merged and so may
    have multiple origins.
    """
    def __init__(self, image: bpy.types.Image, unique_id: str):
        self.image = image
        self.unique_id = unique_id
        self.origins = [] # type: List[PackOrigin]
        self.selected = False
        self.show_info = False


    def __str__(self) -> str:
        return f'{self.unique_id}: {len(self.origins)}'


def create_pack_info_list_node_tree(
    ng: bpy.types.NodeTree, 
    origin: Union[PackOrigin, None], 
    scanned: List[PackInfo]
    ) -> List[PackInfo]:
    """
    Find all images in node tree.
    """
    r = []
    for n in ng.nodes:
        if n.bl_idname == 'ShaderNodeTexImage':
            t = n # type: bpy.types.ShaderNodeTexImage
            if t.image:
                # If the image is already packed, than it is automatically
                # packed on export (as there may be no external reference, or is is lost).
                if t.image.packed_file and t.image.packed_file.data:
                    continue

                # It is external, add to list for choosing.
                r.append(
                    PackInfo(
                        t.image, 
                        PackOrigin('N', n.name, origin), 
                        scanned
                    )
                )
        elif n.bl_idname == 'ShaderNodeGroup':
            r.extend(
                create_pack_info_list_node_tree(
                    n.node_tree, 
                    PackOrigin('NG', n.name, origin), 
                    scanned
                )
            )
    return r


def create_pack_info_list_material(
    m: bpy.types.Material, 
    origin: Union[PackOrigin, None], 
    scanned: List[PackInfo]
    ) -> List[PackInfo]:
    """
    Find all images in material.
    """
    if m.use_nodes and m.node_tree:
        return create_pack_info_list_node_tree(m.node_tree, PackOrigin('M', m.name, origin), scanned)
    return []


def create_pack_info_list_object(
    o: bpy.types.Object, 
    origin: Union[PackOrigin, None], 
    scanned: List[PackInfo]
    ) -> List[PackInfo]:
    """
    Recursive scan material slots for images.
    """
    r = []
    if hasattr(o, 'material_slots'):
        for ms in o.material_slots:
            if ms and ms.material:
                r.extend(
                    create_pack_info_list_material(
                        ms.material, 
                        PackOrigin('O', o.name, origin), 
                        scanned
                    )
                )
    return r


def create_pack_info_list_collection(
    c: bpy.types.Collection, 
    origin: Union[PackOrigin, None], 
    scanned: List[PackInfo]
    ) -> List[PackInfo]:
    """
    Recursive scan all images.
    """
    r = []
    for o in c.all_objects:
        r.extend(create_pack_info_list_object(o, PackOrigin('C', c.name, origin), scanned))
    return r


def create_pack_info_list(resources: ResourceTypes) -> Dict[str, PackInfoMerged]:
    """
    Find all used images in resources and create hierarchy information.
    """
    images = [] # type: List[PackInfo]
    for r in resources:
        if isinstance(r, bpy.types.NodeTree): images.extend(create_pack_info_list_node_tree(r, None, images))
        if isinstance(r, bpy.types.Material): images.extend(create_pack_info_list_material(r, None, images))
        if isinstance(r, bpy.types.Object): images.extend(create_pack_info_list_object(r, None, images))
        if isinstance(r, bpy.types.Collection): images.extend(create_pack_info_list_collection(r, None, images))
        
    merged = {} # type: Dict[str, PackInfoMerged]
    for i in images:
        if i.unique_id not in merged:
            merged[i.unique_id] = PackInfoMerged(i.image, i.unique_id)
        merged[i.unique_id].origins.append(i.origin)

    """
    for k, v in merged.items():
        print(k)
        for o in v.origins:
            print(f'  {o}')
    """
    return merged


class ImagePackerRegistry:
    """
    Used to one time gather images potentially to pack on export,
    the information is used in the UI, so users can select the images
    they want to pack.
    """
    def __init__(self):
        self.__images = {} # type: Dict[str, PackInfoMerged]


    def update(self, rscs: ResourceTypes):
        """
        Refresh internal dict with images used by the given resources.
        """
        self.__images = create_pack_info_list(rscs)


    def images(self):
        return self.__images


    def set_all(self, enable: bool):
        for i in self.__images.values(): i.selected = enable


    def toggle(self, image: str):
        """
        Enable all, none or toggle image with given hash.
        """
        self.__images[image].selected = not self.__images[image].selected


    def toggle_info(self, image: str):
        """
        Enable all, none or toggle image with given hash.
        """
        self.__images[image].show_info = not self.__images[image].show_info


    def selected(self) -> List[str]:
        """
        Return hash for all images that were selected.
        """
        return [ i.unique_id for i in self.__images.values() if i.selected ]


    @staticmethod
    def get() -> 'ImagePackerRegistry':
        global _image_packer_instance
        return _image_packer_instance


_image_packer_instance = ImagePackerRegistry()  
