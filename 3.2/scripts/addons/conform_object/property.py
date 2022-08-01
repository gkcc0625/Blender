import sys
import traceback

import bpy

from bpy.types import PropertyGroup, CollectionProperty, StringProperty, PointerProperty, BoolProperty
from bpy.props import *
from bpy.utils import register_class, unregister_class

class conform_object(PropertyGroup):
    is_conform_obj : BoolProperty(default=False)
    is_conform_shrinkwrap : BoolProperty(default=False)
    is_grid_obj : BoolProperty(default=False)
    original_location : FloatVectorProperty()


classes = [
    conform_object]


def register():
    for cls in classes:
        register_class(cls)

    bpy.types.Object.conform_object = PointerProperty(name='Conform Object', type=conform_object)


def unregister():
    del bpy.types.Object.conform_object

    for cls in classes:
        unregister_class(cls)
