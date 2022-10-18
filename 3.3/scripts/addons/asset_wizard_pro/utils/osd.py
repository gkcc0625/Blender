# Copyright (C) 2022 Thomas Hoppe (h0bB1T). All rights reserved.
#
# Unauthorized copying of this file via any medium is strictly prohibited.
# Proprietary and confidential.

import bpy, blf, gpu, mathutils
from gpu_extras.batch import batch_for_shader
from mathutils import Vector

from typing import Dict, List, Tuple


def fill_rectangle_2d(
    tl: Tuple[float, float], 
    br: Tuple[float, float], 
    color: Tuple[float, float, float, float]
    ):
    """
    Draw filled rectange <tl>-<br> with given color.
    """
    vertices = ( tl, (br[0], tl[1]), br, (tl[0], br[1]) )
    indices = ( (0, 1, 2),  (0, 2, 3) )
    shader = gpu.shader.from_builtin('2D_UNIFORM_COLOR')
    batch = batch_for_shader(shader, 'TRIS', { 'pos': vertices }, indices=indices)
    shader.bind()
    shader.uniform_float('color', color)
    batch.draw(shader)



def lines_3d(
    vertices: List[Tuple[float, float, float]],
    color: Tuple[float, float, float, float],
    width: float
    ):
    """
    Draw lines in 3D space.
    """
    shader = gpu.shader.from_builtin('3D_UNIFORM_COLOR')
    batch = batch_for_shader(shader, 'LINES', { 'pos': vertices })
    shader.bind()
    shader.uniform_float('color', color)
    old_width = gpu.state.line_width_get()
    gpu.state.line_width_set(width)
    batch.draw(shader)
    gpu.state.line_width_set(old_width)


class OSD2DElement:
    """
    Base element that can be drawn into the canvas.
    """
    def __init__(self):
        self.visible = True


    def draw(self):
        pass


    def set_visible(self, visible: bool):
        self.visible = visible


    def toggle_visibility(self):
        self.visible = not self.visible


    def rect(self) -> Tuple[Tuple[float, float], Tuple[float, float]]:
        return ((0, 0), (0, 0))


    def size(self) -> Tuple[float, float]:
        r = self.rect()
        return (r[1][0] - r[0][0], r[1][1] - r[0][1])


class OSD2DSpacer(OSD2DElement):
    """
    Vertical spacer when using automatic vertical layout. Requires the 
    previous vertical element.
    """
    def __init__(self, height: float, top_element: OSD2DElement):
        super().__init__()
        self.height = height
        self.top_element = top_element


    def rect(self) -> Tuple[Tuple[float, float], Tuple[float, float]]:
        r = self.top_element.rect()
        pos = (r[0][0], r[1][1])
        return (pos, (pos[0], pos[1] - self.height))    


class OSD2DText(OSD2DElement):
    """
    Draws simple horizontal text. If position is given, uses it,
    otherwise places below top_element using the given info.
    """
    def __init__(
        self, 
        text: str, 
        position: Tuple[float, float] = None,
        size: float = 20, 
        color: Tuple[float, float, float, float] = [ 0, 0, 0, 1 ], 
        font_id: int = 0, 
        top_element: OSD2DElement = None
        ):
        super().__init__()
        self.text = text
        self.position = position
        self.size = size
        self.color = color
        self.font_id = font_id
        self.top_element = top_element


    def current_position(self) -> Tuple[float, float]:
        """
        Top left corner.
        """
        if self.position:
            return self.position
        if self.top_element:
            r = self.top_element.rect()
            if self.visible:
                return (r[0][0], r[1][1] - OSD2D.spacing())
            else:
                return (r[0][0], r[1][1])
        return (0, 0)


    def rect(self) -> Tuple[Tuple[float, float], Tuple[float, float]]:
        """
        Area of text. Think about top is positive, bottom is negative in blender.
        """
        pos = self.current_position()
        if self.visible:
            blf.size(self.font_id, self.size, 72)
            size = blf.dimensions(self.font_id, self.text)
        else:
            size = (0, 0)
        return (pos, (pos[0] + size[0], pos[1] - size[1]))


    def draw(self):
        """
        Draw the text.
        """
        if self.visible:
            blf.size(self.font_id, self.size, 72)
            size = blf.dimensions(self.font_id, self.text)
            pos = self.current_position()
            blf.position(self.font_id, pos[0], pos[1] - size[1], 0)
            blf.size(self.font_id, self.size, 72)
            blf.color(self.font_id, *self.color)
            blf.draw(self.font_id, self.text)            


class OSD2DParent(OSD2DElement):
    """
    Abstract base object that itself can have childern.
    """
    def __init__(self):
        super().__init__()
        self.elements = {} # type: Dict[str, OSD2DElement]


    def add_element(self, name: str, element: OSD2DElement) -> OSD2DElement:
        self.elements[name] = element
        return element


    def add_spacer(self, name: str, height: float, top_element: OSD2DElement = None) -> OSD2DSpacer:
        return self.add_element(name, OSD2DSpacer(height, top_element))


    def add_text(
        self, 
        name: str,
        text: str, 
        position: Tuple[float, float] = None,
        size: float = 20, 
        color: Tuple[float, float, float, float] = [ 0, 0, 0, 1 ], 
        font_id: int = 0, 
        top_element: OSD2DElement = None
        ) -> OSD2DText:
        return self.add_element(name, OSD2DText(text, position, size, color, font_id, top_element))


    def add_group(self, name: str, background: Tuple[float, float, float, float] = None) -> 'OSD2DGroup':
        return self.add_element(name, OSD2DGroup(background))


    def remove_element(self, name: str):
        if name in self.elements:
            del self.elements[name]


    def element(self, name: str):
        return self.elements.get(name)        


class OSD2DGroup(OSD2DParent):
    """
    Groups vertical element, which can have a background rect (if background != None).
    """
    def __init__(self, background: Tuple[float, float, float, float] = None):
        super().__init__()
        self.background = background


    def rect(self) -> Tuple[Tuple[float, float], Tuple[float, float]]:
        rects = [ e.rect() for e in self.elements.values() ]
        l = min([ r[0][0] for r in rects ])
        t = min([ r[1][1] for r in rects ])
        r = max([ r[1][0] for r in rects ])
        b = max([ r[0][1] for r in rects ])
        m = 8 # margin.
        return ( (l - m, t - m), (r + m, b + m))


    def draw(self):
        if self.background:
            fill_rectangle_2d(*self.rect(), self.background)
        for v in self.elements.values():
            v.draw()
    

class OSD2D(OSD2DParent):
    """
    Class that paints different 2D features into viewport.
    """

    @staticmethod
    def spacing():
        return 4


    def __init__(self):
        super().__init__()
        self.__handle = None


    def register(self):
        """
        Call to register automatic drawing. Don't forget to call unregister for clearing.
        """
        self.__handle = bpy.types.SpaceView3D.draw_handler_add(OSD2D.draw, (self,), 'WINDOW', 'POST_PIXEL')


    def unregister(self):
        """
        Remove handler that draws this object.
        """
        if self.__handle:
            bpy.types.SpaceView3D.draw_handler_remove(self.__handle, 'WINDOW')
            self.__handle = None


    def draw(self):
        if self.visible:
            for v in self.elements.values():
                v.draw()


class OSD3DElement:
    """
    Base element that can be drawn into the canvas.
    """
    def __init__(self):
        self.location = Vector((0, 0, 0))
        self.rotation = mathutils.Euler()
        self.scale = Vector((1, 1, 1))


    def draw(self):
        pass


    def transform(self, vertices: List[Tuple[float, float, float]]) -> List[Tuple[float, float, float]]:
        r = []
        for v in vertices:
            v = Vector(v)
            v *= self.scale
            v.rotate(self.rotation)
            v += self.location
            r.append(v[:])
        return r


class OSD3DLines(OSD3DElement):
    """
    One connected line.
    """    
    def __init__(
        self, 
        vertices: List[Tuple[float, float, float]],
        color: Tuple[float, float, float, float],
        width: float = 1
        ):
        super().__init__()
        self.vertices = vertices
        self.color = color
        self.width = width


    def draw(self):
        lines_3d(self.transform(self.vertices), self.color, self.width)


class OSD3DParent:
    """
    Abstract base object that itself can have childern.
    """
    def __init__(self):
        self.elements = {} # type: Dict[str, OSD3DElement]


    def add_element(self, name: str, element: OSD3DElement) -> OSD3DElement:
        self.elements[name] = element
        return element


    def add_lines(
        self, 
        name: str,
        vertices: List[Tuple[float, float, float]],
        color: Tuple[float, float, float, float],
        width: float = 1
        ) -> OSD3DLines:    
        return self.add_element(
            name,
            OSD3DLines(vertices, color, width)
        )


    def remove_element(self, name: str):
        if name in self.elements:
            del self.elements[name]


    def element(self, name: str):
        return self.elements.get(name)     


class OSD3D(OSD3DParent):
    """
    Class that paints different 2D features into viewport.
    """

    @staticmethod
    def spacing():
        return 4


    def __init__(self):
        super().__init__()
        self.__handle = None


    def register(self):
        """
        Call to register automatic drawing. Don't forget to call unregister for clearing.
        """
        self.__handle = bpy.types.SpaceView3D.draw_handler_add(OSD3D.draw, (self,), 'WINDOW', 'POST_VIEW')


    def unregister(self):
        """
        Remove handler that draws this object.
        """
        if self.__handle:
            bpy.types.SpaceView3D.draw_handler_remove(self.__handle, 'WINDOW')
            self.__handle = None


    def draw(self):
        for v in self.elements.values():
            v.draw()
                