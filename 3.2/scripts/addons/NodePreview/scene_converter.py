#
#     This file is part of NodePreview.
#     Copyright (C) 2021 Simon Wendsche
#
#     This program is free software: you can redistribute it and/or modify
#     it under the terms of the GNU General Public License as published by
#     the Free Software Foundation, either version 3 of the License, or
#     (at your option) any later version.
#
#     This program is distributed in the hope that it will be useful,
#     but WITHOUT ANY WARRANTY; without even the implied warranty of
#     MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#     GNU General Public License for more details.
#
#     You should have received a copy of the GNU General Public License
#     along with this program.  If not, see <http://www.gnu.org/licenses/>.

from math import ceil

def scene_to_script(context, needs_more_samples, thumb_resolution):
    # TODO OSL (needs support for OSL script nodes first!)
    # scene.cycles.shading_system = {context.scene.cycles.shading_system}

    script = f"""
scene = bpy.context.scene
scene.cycles.feature_set = '{context.scene.cycles.feature_set}'
scene.cycles.samples = {4 if needs_more_samples else 1}
bpy.context.scene.render.use_compositing = {needs_more_samples}  # Enables OIDN
"""

    if needs_more_samples:
        script += f"""
bpy.context.scene.render.threads = 4
if bpy.app.version < (3, 0, 0):
    bpy.context.scene.render.tile_x = {ceil(thumb_resolution / 2)}
    bpy.context.scene.render.tile_y = {ceil(thumb_resolution / 2)}
"""

    return script
