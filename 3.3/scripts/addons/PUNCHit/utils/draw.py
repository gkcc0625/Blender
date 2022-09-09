import bpy
from mathutils import Vector, Matrix
import gpu
from gpu_extras.batch import batch_for_shader
import blf
from .. utils.registration import get_prefs



def use_legacy_line_smoothing(alpha, width):

    if get_prefs().use_legacy_line_smoothing and alpha < 1:
        try:
            import bgl

            bgl.glEnable(bgl.GL_BLEND)
            bgl.glLineWidth(width)
            bgl.glEnable(bgl.GL_LINE_SMOOTH)
        except:
            pass


def draw_point(co, mx=Matrix(), color=(1, 1, 1), size=6, alpha=1, xray=True, modal=True):
    def draw():
        shader = gpu.shader.from_builtin('3D_UNIFORM_COLOR')
        shader.bind()
        shader.uniform_float("color", (*color, alpha))

        gpu.state.depth_test_set('NONE' if xray else 'LESS_EQUAL')
        gpu.state.blend_set('ALPHA' if alpha < 1 else 'NONE')
        gpu.state.point_size_set(size)

        batch = batch_for_shader(shader, 'POINTS', {"pos": [mx @ co]})
        batch.draw(shader)

    if modal:
        draw()

    else:
        bpy.types.SpaceView3D.draw_handler_add(draw, (), 'WINDOW', 'POST_VIEW')


def draw_line(coords, indices=None, mx=Matrix(), color=(1, 1, 1), width=1, alpha=1, xray=True, modal=True):
    def draw():
        nonlocal indices

        if not indices:
            indices = [(i, i + 1) for i in range(0, len(coords)) if i < len(coords) - 1]

        shader = gpu.shader.from_builtin('3D_UNIFORM_COLOR')
        shader.bind()
        shader.uniform_float("color", (*color, alpha))

        gpu.state.depth_test_set('NONE' if xray else 'LESS_EQUAL')
        gpu.state.blend_set('ALPHA' if alpha < 1 else 'NONE')
        gpu.state.line_width_set(width)

        use_legacy_line_smoothing(alpha, width)

        batch = batch_for_shader(shader, 'LINES', {"pos": [mx @ co for co in coords]}, indices=indices)
        batch.draw(shader)

    if modal:
        draw()

    else:
        bpy.types.SpaceView3D.draw_handler_add(draw, (), 'WINDOW', 'POST_VIEW')


def draw_vector(vector, origin=Vector((0, 0, 0)), mx=Matrix(), color=(1, 1, 1), width=1, alpha=1, xray=True, modal=True):
    def draw():
        coords = [mx @ origin, mx @ origin + mx.to_3x3() @ vector]

        shader = gpu.shader.from_builtin('3D_UNIFORM_COLOR')
        shader.bind()
        shader.uniform_float("color", (*color, alpha))

        gpu.state.depth_test_set('NONE' if xray else 'LESS_EQUAL')
        gpu.state.blend_set('ALPHA' if alpha < 1 else 'NONE')
        gpu.state.line_width_set(width)

        use_legacy_line_smoothing(alpha, width)

        batch = batch_for_shader(shader, 'LINES', {"pos": coords})
        batch.draw(shader)


    if modal:
        draw()

    else:
        bpy.types.SpaceView3D.draw_handler_add(draw, (), 'WINDOW', 'POST_VIEW')


def draw_tris(coords, indices=None, mx=Matrix(), color=(1, 1, 1), width=1, alpha=1, xray=True, modal=True):
    def draw():
        shader = gpu.shader.from_builtin('3D_UNIFORM_COLOR')
        shader.bind()
        shader.uniform_float("color", (*color, alpha))

        gpu.state.depth_test_set('NONE' if xray else 'LESS_EQUAL')
        gpu.state.blend_set('ALPHA' if alpha < 1 else 'NONE')
        gpu.state.line_width_set(width)

        use_legacy_line_smoothing(alpha, width)

        if mx != Matrix():
            batch = batch_for_shader(shader, 'TRIS', {"pos": [mx @ co for co in coords]}, indices=indices)

        else:
            batch = batch_for_shader(shader, 'TRIS', {"pos": coords}, indices=indices)

        batch.draw(shader)

    if modal:
        draw()

    else:
        bpy.types.SpaceView3D.draw_handler_add(draw, (), 'WINDOW', 'POST_VIEW')



def update_HUD_location(self, event, offsetx=20, offsety=20):

    self.HUD_x = event.mouse_x - self.region_offset_x + offsetx
    self.HUD_y = event.mouse_y - self.region_offset_y + offsety


def draw_label(context, title='', coords=None, center=True, size=12, color=(1, 1, 1), alpha=1):

    if not coords:
        region = context.region
        width = region.width / 2
        height = region.height / 2
    else:
        width, height = coords

    scale = context.preferences.view.ui_scale * get_prefs().HUD_scale

    font = 1
    fontsize = int(size * scale)

    blf.size(font, fontsize, 72)
    blf.color(font, *color, alpha)

    if center:
        blf.position(font, width - (int(len(title) * scale * 7) / 2), height + int(fontsize), 0)
    else:
        blf.position(font, *(coords), 1)


    blf.draw(font, title)
