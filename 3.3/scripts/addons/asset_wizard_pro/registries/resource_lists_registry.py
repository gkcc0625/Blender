# Copyright (C) 2022 Thomas Hoppe (h0bB1T). All rights reserved.
#
# Unauthorized copying of this file via any medium is strictly prohibited.
# Proprietary and confidential.

import bpy, os, shutil

from typing import Dict, List, Tuple

from .asset_registry import AssetInfoCache
from ..utils.io import os_path
from ..utils.common import format_bytes


class ResourceListsRegistry:
    """
    Manages various lists used in the UI.
    Libraries, catalogs, .blend statistics, as well as infos to 
    available nodes in active asset libs.
    """
    def __init__(self):
        self.__library_files = {} # type: Dict[str, List[Tuple[str, str, str]]]
        self.__catalogs = {} # type: Dict[str, List[Tuple[str, str, str]]]
        self.__catalogs_info = {} # type: Dict[str, List[Tuple[str, str, str]]]
        self.__stats = {} # type: Dict[str, List[Tuple[str, str]]]
        self.__shader_nodes = {} # type: Dict[str, List[Tuple[str, str, str]]]
        self.__geometry_nodes = {} # type: Dict[str, List[Tuple[str, str, str]]]

        # Just a flag that rescans on first requesting shader or geometry nodes.
        # This can't be done in register() as access to library.load is restricted.
        self.__nodes_initialized = False 

        self.__update_library_files()
        self.__update_catalogs()


    def __update_library_files(self):
        """
        Build list of all asset .blend files.
        """
        self.__library_files.clear()
        for l in bpy.context.preferences.filepaths.asset_libraries:
            if not os.path.exists(l.path): continue
            path = os_path(l.path)
            r = []
            if l.path:
                for _f in os.listdir(path):
                    if _f.endswith('.blend'):
                        f = os.path.join(path, _f)
                        s = os.path.splitext(_f)[0]
                        r.append((f, s, f))
            self.__library_files[l.path] = sorted(r, key=lambda x: x[1])


    def library_files(self, library_path: str):
        return self.__library_files.get(library_path, list())


    def __update_catalogs(self):
        """
        Parse catalog files in all repositories.
        """
        self.__catalogs.clear()
        self.__catalogs_info.clear()
        for lib in bpy.context.preferences.filepaths.asset_libraries:
            if not os.path.exists(lib.path): continue
            catalog_file = os.path.join(os_path(lib.path), 'blender_assets.cats.txt')
            r, i = [], []
            if os.path.exists(catalog_file):
                with open(catalog_file, 'r', encoding='utf-8') as f:
                    for l in f.readlines():
                        l = l.strip()
                        if not l or l[0] == '#' or l.startswith('VERSION'):
                            continue
                        entry = l.split(':')
                        if len(entry) > 2:
                            short_name = (len(entry[1].split('/')) - 1) * '  ' + entry[1].split('/')[-1]
                            r.append((entry[0], short_name, f'{entry[1]} in {lib.name}'))
                            i.append((entry[0], entry[1], entry[2]))
            self.__catalogs[lib.path] = r
            self.__catalogs_info[lib.path] = i


    def catalogs(self, library_path: str):
        return self.__catalogs[library_path]


    def catalog_info(self, library_path: str, catalog_uuid: str):
        """
        Get line from catalogs file, split into the 3 components or None.
        """
        for e in self.__catalogs_info[library_path]:
            if e[0] == catalog_uuid:
                return e


    def add_catalog(self, library_path: str, id: str, full_name: str, simple_name: str) -> bool:
        """
        Adds catalog, returns False if already exists.
        """
        for e in self.__catalogs_info[library_path]:
            if e[1] == full_name or e[2] == simple_name:
                return False

        self.__catalogs_info[library_path].append((id, full_name, simple_name))
        
        catalog_file = os.path.join(os_path(library_path), 'blender_assets.cats.txt')
        if os.path.exists(catalog_file):
            shutil.copy(catalog_file, catalog_file + '.bak')

        with open(catalog_file, 'w', encoding='utf-8') as f:
            f.write('# This is an Asset Catalog Definition file for Blender.\n')
            f.write('#\n')
            f.write('# Empty lines and lines starting with `#` will be ignored.\n')
            f.write('# The first non-ignored line should be the version indicator.\n')
            f.write('# Other lines are of the format "UUID:catalog/path/for/assets:simple catalog name"\n\n')
            f.write('VERSION 1\n\n')
            for u, fn, sn in sorted(self.__catalogs_info[library_path], key=lambda x: x[1]):
                f.write(f'{u}:{fn}:{sn}\n')

        self.update()
        return True



    def update(self):
        """
        Update file and catalog lists.
        """
        self.__update_library_files()
        self.__update_catalogs()
        self.__stats.clear()


    def stats(self, blend_file: str):
        """
        Generate name, value pairs for file information.
        """
        file = os_path(blend_file)
        if file not in self.__stats:
            r = []
            r.append(('File Size', format_bytes(os.path.getsize(file))))
            with bpy.data.libraries.load(file, link=False, assets_only=True) as (data_from, _):
                if len(data_from.objects): r.append(('Asset Objects', f'{len(data_from.objects)}'))
                if len(data_from.collections): r.append(('Asset Collections', f'{len(data_from.collections)}'))
                if len(data_from.materials): r.append(('Asset Materials', f'{len(data_from.materials)}'))
                if len(data_from.node_groups): r.append(('Asset Node Groups', f'{len(data_from.node_groups)}'))

            self.__stats[blend_file] = r

        return self.__stats[file]


    def update_nodes(self):
        """
        Parses all geometry and shader nodes from all .blend files
        in all asset libraries. Uses the asset cache for faster loading.
        Sorts them into categories from first tag entry, to the respective dicts.
        """
        self.__nodes_initialized = True
        self.__shader_nodes.clear()
        self.__geometry_nodes.clear()

        cache = AssetInfoCache.get()
        cache.re_init()
        for _, filelist in self.__library_files.items():
            for file in [ e[0] for e in filelist]:
                cache.update_info(file)

        cache.update_dicts(self.__shader_nodes, self.__geometry_nodes)


    def shader_nodes(self):
        if not self.__nodes_initialized:
            self.update_nodes()
        return self.__shader_nodes


    def geometry_nodes(self):
        if not self.__nodes_initialized:
            self.update_nodes()
        return self.__geometry_nodes


    @staticmethod
    def get() -> 'ResourceListsRegistry':
        global _resource_lists_instance
        return _resource_lists_instance


_resource_lists_instance = ResourceListsRegistry()        
