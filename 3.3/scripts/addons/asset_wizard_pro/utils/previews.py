# Copyright (C) 2022 Thomas Hoppe (h0bB1T). All rights reserved.
#
# Unauthorized copying of this file via any medium is strictly prohibited.
# Proprietary and confidential.

import bpy, traceback

from typing import Union


def thumbnail_of_current_render(target: str, dimension: int) -> Union[str, None]:
    """
    Create a NxN image of the current render and save it to target.
    Returns None on success or error string.
    """
    if 'Render Result' in bpy.data.images:
        ise = bpy.context.scene.render.image_settings
        fmt = ise.file_format
        cmp = ise.compression
        cm = ise.color_mode
        copy, final = None, None

        try:
            ise.file_format = 'PNG'
            ise.color_mode = 'RGBA'
            ise.compression = 0

            # Store render result temporarily and load to new image.
            bpy.data.images['Render Result'].save_render(target)
            copy = bpy.data.images.load(target)

            # Calc resize and crop parameters.
            w, h = copy.size
            if w > h:
                a = w / h
                sw, sh = round(a * dimension), dimension
                ox = (sw - dimension) // 2
                oy = 0
            else:
                a = h / w
                sw, sh = dimension, round(a * dimension)
                ox = 0
                oy = (sh - dimension) // 2

            # Scale image down, so the smaller dimension it target dimension.
            copy.scale(sw, sh)

            # Crop pixels into a new image,
            final = bpy.data.images.new('awp-thumbnail', dimension, dimension, alpha=copy.alpha_mode != None)
            for l in range(dimension):
                od = (l * dimension) * copy.channels
                os = ((l + oy) * sw + ox) * copy.channels
                n = dimension * copy.channels
                final.pixels[od:od + n] = copy.pixels[os:os + n]

            # Store final image.
            ise.compression = 100
            final.save_render(target)

            return None
        except Exception as ex:
            print(traceback.format_exc())
            return f'Failed to create thumbnail (see Console)'
        finally:
            ise.file_format = fmt
            ise.compression = cmp
            ise.color_mode = cm
            if copy: bpy.data.images.remove(copy)
            if final: bpy.data.images.remove(final)
    else:
        return 'Can\t access render Result, please render first'