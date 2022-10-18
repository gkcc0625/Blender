# Copyright (C) 2022 Thomas Hoppe (h0bB1T). All rights reserved.
#
# Unauthorized copying of this file via any medium is strictly prohibited.
# Proprietary and confidential.

import bpy

from typing import Dict

from ..utils.dev import dbg


class PreviewsCollection:
    """
    Single, lazy initiated preview collection.
    """
    def __init__(self, name: str):
        dbg(f'Initialize p-collection: {name}')
        self.__name = name
        self.__collection = None # type bpy.types.ImagePreviewCollection


    def load(self, name: str, filename: str) -> int:
        if not self.__collection:
            dbg(f'Create p-collection: {self.__name}')
            self.__collection = bpy.utils.previews.new()
        if name in self.__collection:
            return self.__collection[name].icon_id
        else:
            return self.__collection.load(name, filename, 'IMAGE').icon_id


    def remove(self, id: int):
        del self.__collection[id]


    def dispose(self):
        if self.__collection:
            dbg(f'Dispose p-collection: {self.__name}')
            bpy.utils.previews.remove(self.__collection)


class PreviewsRegistry:
    """
    Helper class to manage preview collections.
    """
    def __init__(self):
        self.__collections = {} # type: Dict[str, PreviewsCollection]


    def register(self, name: str):
        if name in self.__collections:
            return
            #raise Exception(f'Preview collection {name} already registered')
        self.__collections[name] = PreviewsCollection(name)


    def collection(self, name: str) -> PreviewsCollection:
        self.register(name)
        return self.__collections[name]


    def dispose(self):
        for v in self.__collections.values():
            v.dispose()
        self.__collections.clear()


    @staticmethod
    def instance() -> 'PreviewsRegistry':
        """
        Access as singleton.
        """
        global _previews_instance
        return _previews_instance


_previews_instance = PreviewsRegistry()
