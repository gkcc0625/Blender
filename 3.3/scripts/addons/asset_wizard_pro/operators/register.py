# Copyright (C) 2022 Thomas Hoppe (h0bB1T). All rights reserved.
#
# Unauthorized copying of this file via any medium is strictly prohibited.
# Proprietary and confidential.

from .blend_importer import ASSET_OT_blend_importer
from .create_catalog import ASSET_OT_create_catalog
from .create_new_blend import ASSET_OT_create_new_blend
from .export_assets import ASSET_OT_export
from .import_assets import ASSET_OT_import
from .import_cleaner import ASSET_OT_import_cleaner
from .invoke_pie import ASSET_OT_invoke_pie
from .multi_purpose import ASSET_OT_multi_purpose
from .object_placer import ASSET_OT_object_placer
from .pack_select import ASSET_OT_pack_select
from .std_node_drop import ASSET_OT_std_node_drop
from .tag_manager import ASSET_OT_tag_manager
from .update_local import ASSET_OT_update_local

register_operators = [
    ASSET_OT_blend_importer,
    ASSET_OT_create_catalog,
    ASSET_OT_create_new_blend,
    ASSET_OT_export,
    ASSET_OT_import,
    ASSET_OT_import_cleaner,
    ASSET_OT_invoke_pie,
    ASSET_OT_multi_purpose,
    ASSET_OT_object_placer,
    ASSET_OT_pack_select,
    ASSET_OT_std_node_drop,
    ASSET_OT_tag_manager,
    ASSET_OT_update_local,
]
