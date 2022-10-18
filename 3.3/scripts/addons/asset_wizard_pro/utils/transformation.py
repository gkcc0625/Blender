# Copyright (C) 2022 Thomas Hoppe (h0bB1T). All rights reserved.
#
# Unauthorized copying of this file via any medium is strictly prohibited.
# Proprietary and confidential.

import numbers, math

from mathutils import Vector, Euler, Quaternion
from typing import Union, Tuple

from bpy.types import Object

V3DInput = Union[float, Tuple[float, float, float], Vector]
V3DInputRotation = Union[Tuple[float, float, float], Vector, Euler, Quaternion]

class Transformation:
    """
    Utility class to store, combine, read and merge transformations.
    Used in AWP Object Placer.
    """
    def __init__(
        self, 
        location: V3DInput = 0,
        rotation: V3DInputRotation = 0,
        scale: V3DInput = 1
        ):
        self.__location = Transformation.to_vector(location)
        self.__rotation = Transformation.to_rotation(rotation)
        self.__scale = Transformation.to_vector(scale)


    def copy(self) -> 'Transformation':
        return Transformation(self.__location, self.__rotation, self.__scale)


    def reset(self):
        """
        Reset to no transform.
        """
        self.reset_location()
        self.reset_rotation()
        self.reset_scale()


    def reset_location(self): self.__location = Transformation.to_vector(0)
    def reset_rotation(self): self.__rotation = Transformation.to_rotation(0)
    def reset_scale(self): self.__scale = Transformation.to_vector(1)


    def __str__(self):
        return f'L:{self.str_location()}, R:{self.str_rotation()}, S:{self.str_scale()}'


    def __add__(self, other: 'Transformation') -> 'Transformation':
        """
        Combine two transformation.
        """
        #if abs(other.__rotation.to_euler()[0]) > 0.1:
        #    print('hmm')
        #tmp_r = self.__rotation.copy()
        #tmp_r.rotate(other.__rotation)
        tmp_r = self.__rotation.copy()
        tmp_r.rotate(other.__rotation)
        tmp_l = self.__location.copy()
        tmp_l.rotate(other.__rotation)

        return Transformation(
            tmp_l.to_3d() + other.__location.to_3d(),
            tmp_r,
            self.__scale * other.__scale
        )


    def __iadd__(self, other: 'Transformation'):
        """
        Combine two transformation.
        """
        # Do it just in one location ..
        tmp = self + other

        self.__location = tmp.__location
        self.__rotation = tmp.__rotation
        self.__scale = tmp.__scale

        return self


    def add_location(self, relative: V3DInput):
        self.__location += Transformation.to_vector(relative)


    def set_location(self, absolute: V3DInput):
        self.__location = Transformation.to_vector(absolute)        


    def add_rotation(self, relative: V3DInputRotation):
        self.__rotation.rotate(Transformation.to_rotation(relative))


    def set_rotation(self, absolute: V3DInputRotation):
        self.__rotation = Transformation.to_rotation(absolute)


    def add_scale(self, relative: V3DInput):
        # Do NOT multiply here, some axes may be 0!
        self.__scale += Transformation.to_vector(relative)


    def set_scale(self, absolute: V3DInput):
        self.__scale = Transformation.to_vector(absolute)        


    def filter_by_axes(self, axes: Vector) -> 'Transformation':
        """
        Return transformation where the given axes (==1) stay as they are
        and the other axes are zeroed.
        """
        # Rotation is a little bit tricky.
        euler = Euler(Vector(self.rotation_euler()[:]) * axes)
        return Transformation(
            self.__location * axes,
            euler.to_quaternion(),
            self.__scale * axes
        )


    def str_location(self) -> str:
        return f'{self.__location[0]:.2f}, {self.__location[1]:.2f}, {self.__location[2]:.2f}'


    def str_rotation(self) -> str:
        euler = self.rotation_euler()[:]
        return f'{math.degrees(euler[0]):.2f}°, {math.degrees(euler[1]):.2f}°, {math.degrees(euler[2]):.2f}°'


    def str_scale(self) -> str:
        return f'{self.__scale[0]:.2f}, {self.__scale[1]:.2f}, {self.__scale[2]:.2f}'


    def location(self) -> Vector:
        return self.__location.copy()


    def rotation_euler(self) -> Euler:
        return self.__rotation.to_euler()


    def rotation_quaternion(self) -> Euler:
        return self.__rotation.copy()


    def scale(self) -> Vector:
        return self.__scale.copy()


    def to_object(self, object: Object):
        """
        Apply transformation to object.
        """
        object.location = self.__location.copy()
        if object.rotation_mode == 'QUATERNION':
            object.rotation_quaternion = self.rotation_quaternion()
        else:
            object.rotation_euler = self.rotation_euler()
        object.scale = self.__scale.copy()


    @staticmethod
    def from_object(object: Object) -> 'Transformation':
        """
        Create transformation from objects data.
        """
        if object.rotation_mode == 'QUATERNION':
            return Transformation(
                object.location,
                object.rotation_quaternion,
                object.scale
            )
        else:
            return Transformation(
                object.location,
                object.rotation_euler,
                object.scale
            )

    
    @staticmethod
    def to_vector(input: V3DInput) -> Vector:
        """
        Convert any form of input into Vector.
        """
        if isinstance(input, Vector):
            return input.copy().to_3d()
        elif isinstance(input, numbers.Number):
            return Vector((input, input, input))
        else:
            return Vector(input)

        
    @staticmethod
    def to_rotation(input: V3DInputRotation) -> Quaternion:
        """
        Convert any form of input into quaternion.
        """
        if isinstance(input, Euler):
            return input.to_quaternion()
        elif isinstance(input, Quaternion):
            return input.copy()
        else:
            return Euler(Transformation.to_vector(input)).to_quaternion()

