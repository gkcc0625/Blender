# Copyright (C) 2022 Thomas Hoppe (h0bB1T). All rights reserved.
#
# Unauthorized copying of this file via any medium is strictly prohibited.
# Proprietary and confidential.

import bpy, os

from pathlib import Path
from typing import List, Union

ResourceType = Union[bpy.types.Object, bpy.types.Collection, bpy.types.Material, bpy.types.NodeGroup]
ResourceTypes = List[ResourceType]

log_prefix = 'AWP'

config_dir = os.path.expanduser(os.path.join(Path.home(), '.asset-wizard-pro'))
config = os.path.join(config_dir, 'config.json')
dev_config = os.path.join(config_dir, 'config-dev.json')
key_map_config = os.path.join(config_dir, 'keymap.json')
asset_cache_file = os.path.join(config_dir, 'asset_cache.json')
panel_name = 'Asset Wizard Pro'
