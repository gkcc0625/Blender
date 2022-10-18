# Copyright (C) 2022 Thomas Hoppe (h0bB1T). All rights reserved.
#
# Unauthorized copying of this file via any medium is strictly prohibited.
# Proprietary and confidential.

import json, os

from typing import List

from ..preferences import PreferencesPanel
from ..utils.io import run_blender
from .render_preview import RenderPreviewSettings
from .update_settings import SettingsUpdateSettings

"""
Functions in the script invoke a new Blender instance externally, 
primary to run background tasks.
"""

def render_preview(blend_file: str, image_file: str, mode: str, name: str):
    """
    Render preview image for any collection, object or material.
    blend_file: Blend-File that contains the object to render.
    image_file: Output image filename.
    mode: COLLECTION, OBJECT or MATERIAL.
    name: Name of collection, object or material to render.
    """
    # Eventually delete old one.
    if os.path.exists(image_file):
        try:
            os.remove(image_file)
        except:
            pass

    info = RenderPreviewSettings(
        blend_file, image_file, mode, name, 
        PreferencesPanel.get().render_engine,
        PreferencesPanel.get().cycles_samples,
        PreferencesPanel.get().dimension
    ).to_js()
    
    run_blender([
        '--background',
        '--factory-startup',
        os.path.join(os.path.dirname(__file__), '..', 'data', 'preview.blend'),
        '--python',
        os.path.join(os.path.dirname(__file__), 'render_preview.py'),
        '--',
        info
    ])


def update_settings(
    blend_file: str, 
    reimport_blend: str,
    image_file: str, 
    mode: str, 
    name: str, 
    catalog: str, 
    description: str, 
    author: str,
    tags: List[str],
    extra_tag: str,
    pack_images: List[str],
    image_cleanup: bool
    ):
    """
    See update_settings.py
    """
    info = SettingsUpdateSettings(
        reimport_blend,
        image_file,
        mode,
        name,
        catalog,
        description,
        author,
        tags,
        extra_tag,
        PreferencesPanel.get().auto_place,
        pack_images,
        image_cleanup,
        PreferencesPanel.get().relative_paths
    ).to_js()
    run_blender([
        '--background',
        '--factory-startup',
        blend_file,
        '--python',
        os.path.join(os.path.dirname(__file__), 'update_settings.py'),
        '--',
        info
    ])
    