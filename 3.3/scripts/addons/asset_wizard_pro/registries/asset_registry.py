# Copyright (C) 2022 Thomas Hoppe (h0bB1T). All rights reserved.
#
# Unauthorized copying of this file via any medium is strictly prohibited.
# Proprietary and confidential.

import bpy, os, traceback

from dataclasses import dataclass
from typing import Dict, List, Tuple

from ..utils.io import read_json, unified_path, write_json
from ..constants import asset_cache_file


@dataclass
class AssetNodeEntry:
    name: str
    type: str
    catalog: str
    description: str
    tags: List[str]
    

class AssetInfoEntry:
    """
    Stores all information about a specific blend file.
    """
    def __init__(self):
        self.last_mod = 0 # Last file mod time.
        # Name, GroupType, Catalog, Tags.
        self.nodes = [] # type: List[AssetNodeEntry]


    def to_dict(self):
        """
        Create dict from contents for saving.
        """
        return {
            'last_mod': self.last_mod,
            'nodes': [
                {
                    'name': n.name,
                    'type': n.type,
                    'catalog': n.catalog,
                    'description': n.description,
                    'tags': n.tags
                } for n in self.nodes
            ]
        }


    def from_dict(self, data: Dict):
        """
        Restore data from json.
        """
        self.last_mod = data['last_mod']
        for e in data['nodes']:
            self.nodes.append(AssetNodeEntry(e['name'], e['type'], e['catalog'], e['description'], e['tags']))


class AssetInfoCache:
    """
    Tracks catalog & tag info from assets in a separate json,
    as they are not accessible (yet) in Blenders API.
    """
    def __init__(self):
        self.__cache = {} # type: Dict[str, AssetInfoEntry]
        self.__active = {}
        self.__use_caching = True # Deactive temporarily.
        self.__load()


    def __load(self):
        self.__cache.clear()

        # Restore info from json.
        js = read_json(asset_cache_file)
        for e in js.get('libs', list()):
            try:
                entry = AssetInfoEntry()
                entry.from_dict(e['entry'])
                self.__cache[e['name']] = entry
            except:
                pass


    def __save(self):
        """
        Store info to ~/.asset-wizard-pro/asset_cache.json.
        """
        write_json(
            asset_cache_file, {
                'libs': [ { 'name': k, 'entry': v.to_dict() } for k, v in self.__cache.items() ]
            }
        )


    def re_init(self):
        """
        Called before updating the cache with single blends. In the cache
        files may be files that are not in the repo paths. Remove them.
        """
        self.__active.clear()


    def update_info(self, blend_file: str):
        """
        If .blend is newer than cache entry, update all node infos, store in cache file.
        """
        blend_file = unified_path(blend_file)
        if os.path.exists(blend_file):
            last_mod = os.stat(blend_file).st_mtime

            # Check if update for this file is necessary.
            if self.__use_caching:
                if blend_file in self.__cache:
                    entry = self.__cache[blend_file]
                else:
                    entry = AssetInfoEntry()
                    self.__cache[blend_file] = entry
            else:
                entry = AssetInfoEntry()

            self.__active[blend_file] = entry
            if last_mod - entry.last_mod > 0.01:
                # Clear outdated information.
                entry.last_mod = last_mod
                entry.nodes.clear()

                # Ok, we need to gather the infos.
                loaded_nodes = [] # type: List[bpy.types.NodeGroup]
                try:
                    # Load nodes temporary to current blend to get details, they were removed in finally below.
                    with bpy.data.libraries.load(blend_file, link=True, assets_only=True) as (data_from, data_to):
                        data_to.node_groups = data_from.node_groups
                        new_nodes = data_to.node_groups # type: List[bpy.types.NodeGroup]

                    loaded_nodes.extend(new_nodes)
                    for node in new_nodes:
                        entry.nodes.append(AssetNodeEntry(
                            node.name,
                            node.bl_idname,
                            node.asset_data.catalog_id,
                            node.asset_data.description,
                            [ tag.name for tag in node.asset_data.tags ]
                        ))

                    self.__save()
                except:
                    # Just dump.
                    print(traceback.format_exc())
                finally:
                    for node in loaded_nodes:
                        bpy.data.node_groups.remove(node)


    def update_dicts(self, shader: Dict, geometry: Dict):
        """
        Fills the given dicts with node info.
        """
        for k, v in self.__active.items():
            for node in v.nodes:
                dct = shader if node.type == 'ShaderNodeTree' else geometry
                section = node.tags[0] if node.tags else 'Other'
                entry = (k, node.name, node.name, node.description)
                if section in dct:
                    dct[section].append(entry)
                else:
                    dct[section] = [entry]            


    @staticmethod
    def get() -> 'AssetInfoCache':
        global _asset_info_cache_instance
        return _asset_info_cache_instance


_asset_info_cache_instance = AssetInfoCache()   