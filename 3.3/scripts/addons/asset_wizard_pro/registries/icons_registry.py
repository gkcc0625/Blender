# Copyright (C) 2022 Thomas Hoppe (h0bB1T). All rights reserved.
#
# Unauthorized copying of this file via any medium is strictly prohibited.
# Proprietary and confidential.

import os

from typing import Dict

from .previews_registry import PreviewsRegistry


class IconsRegistry:
    """
    Very simple interface to manage icons. Uses Previews from utils.
    Assumes icon file as 'data/icons/[name].png' and lazily loads on first access.
    """
    def __init__(self):
        PreviewsRegistry.instance().register('__icons')
        self.__icons = {} # type: Dict[str, int]


    def __get_icon(self, name: str) -> int:
        if name not in self.__icons:
            filename = os.path.join(os.path.dirname(__file__), '..', 'data', 'icons', f'{name}.png')
            self.__icons[name] = PreviewsRegistry.instance().collection('__icons').load(name, filename)
        return self.__icons[name]


    def get_icon(name: str) -> int:
        return IconsRegistry.instance().__get_icon(name)


    @staticmethod
    def instance() -> 'IconsRegistry':
        """
        Access as singleton.
        """
        global _instance
        return _instance


_instance = IconsRegistry()
