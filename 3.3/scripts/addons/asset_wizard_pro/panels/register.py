# Copyright (C) 2022 Thomas Hoppe (h0bB1T). All rights reserved.
#
# Unauthorized copying of this file via any medium is strictly prohibited.
# Proprietary and confidential.

from .export_geometry import NODE_PT_awp_export_geometry_panel
from .export_material import NODE_PT_awp_export_material_panel
from .export_object import VIEW3D_PT_awp_export_object_panel
from .import_shader_geometry import NODE_PT_awp_import_shader_geometry_panel
from .tools_object import VIEW3D_PT_awp_tools_panel

register_panels = [
    NODE_PT_awp_export_geometry_panel,
    NODE_PT_awp_export_material_panel,
    VIEW3D_PT_awp_export_object_panel,
    NODE_PT_awp_import_shader_geometry_panel,
    VIEW3D_PT_awp_tools_panel,
]
