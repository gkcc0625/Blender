# Copyright (C) 2022 Thomas Hoppe (h0bB1T). All rights reserved.
#
# Unauthorized copying of this file via any medium is strictly prohibited.
# Proprietary and confidential.

import os

from typing import List, Tuple

from ..constants import config
from ..utils.io import read_json, write_json


class ConfigRegistry:
    """
    Manages tag and shader type names. Hold info persistant in user folder.
    """
    def __init__(self):
        self.__agreed = False

        self.__tags = [] # type: List[str]
        self.__shader_tags = [] # type: List[str]
        self.__geometry_tags = [] # type: List[str]

        self.__tags_enums = [] # type: List[Tuple[str, str, str]]
        self.__shader_tags_enums = [] # type: List[Tuple[str, str, str]]
        self.__geometry_tags_enums = [] # type: List[Tuple[str, str, str]]


    def show_initial_info(self):
        return not self.__agreed


    def agree(self):
        self.__agreed = True
        self.__write()


    def read(self):
        js = read_json(config)
        self.__agreed = js.get('agreed', False)
        self.__tags = list(sorted(js.get('tags', list())))
        self.__shader_tags = list(sorted(js.get('shader_tags', list())))
        self.__geometry_tags = list(sorted(js.get('geometry_tags', list())))

        self.__tags_enums = [ (t, t, t) for t in self.__tags ]
        self.__shader_tags_enums = [ (t, t, t) for t in self.__shader_tags ]
        self.__geometry_tags_enums = [ (t, t, t) for t in self.__geometry_tags ]


    def __write(self):
        write_json(
            config, {
                'agreed': self.__agreed,
                'tags': self.__tags,
                'shader_tags': self.__shader_tags,
                'geometry_tags': self.__geometry_tags,
            }
        )
        self.read()


    def add_tag(self, tag: str):
        if tag not in self.__tags:
            self.__tags.append(tag)
            self.__tags = list(sorted(self.__tags))
            self.__write()


    def remove_tag(self, tag: str):
        if tag in self.__tags:
            self.__tags.remove(tag)
            self.__write()


    def add_shader_tag(self, tag: str):
        if tag not in self.__shader_tags:
            self.__shader_tags.append(tag)
            self.__shader_tags = list(sorted(self.__shader_tags))
            self.__write()


    def remove_shader_tag(self, tag: str):
        if tag in self.__shader_tags:
            self.__shader_tags.remove(tag)
            self.__write()


    def add_geometry_tag(self, tag: str):
        if tag not in self.__geometry_tags:
            self.__geometry_tags.append(tag)
            self.__geometry_tags = list(sorted(self.__geometry_tags))
            self.__write()


    def remove_geometry_tag(self, tag: str):
        if tag in self.__geometry_tags:
            self.__geometry_tags.remove(tag)
            self.__write()


    def tags(self): return self.__tags_enums
    def shader_tags(self): return self.__shader_tags_enums
    def geometry_tags(self): return self.__geometry_tags_enums


    def init_default(self):
        """
        If no config exists, create a new one with example settings.
        """
        if not os.path.exists(config):
            write_json(
                config, {
                    'tags': 'My,CC0,Prop,Nature,Favourite'.split(','),
                    'shader_tags': 'PBR,Noise,Pattern,Generator,Tool'.split(','),
                    'geometry_tags': 'Generator,Tool,Builder'.split(','),
                }
            )


    @staticmethod
    def get() -> 'ConfigRegistry':
        global _config_instance
        return _config_instance


_config_instance = ConfigRegistry()
