import bpy
from bpy.props import EnumProperty, BoolProperty
import bmesh
from mathutils import Matrix, Vector
from math import radians
from .. items import adjust_mode_items
from .. utils.decal import set_props_and_node_names_of_decal, set_decalobj_props_from_material, set_decalobj_name, set_defaults, change_panel_width, get_available_panel_decals
from .. utils.modifier import get_displace, get_nrmtransfer
from .. utils.material import get_parallaxgroup_from_decalmat, get_decalmat, get_decalgroup_from_decalmat, get_decal_texture_nodes, get_panel_material, get_decalgroup_as_dict, set_decalgroup_from_dict
from .. utils.math import get_loc_matrix, get_rot_matrix, get_sca_matrix
from .. utils.ui import draw_init, draw_title, draw_prop, init_cursor, wrap_cursor, init_status, finish_status, draw_info
from .. utils.uv import get_selection_uv_bbox
from .. utils.registration import get_prefs
from .. utils.property import set_cycles_visibility, get_cycles_visibility
from .. colors import red


class Adjust(bpy.types.Operator):
    bl_idname = "machin3.adjust_decal"
    bl_label = "MACHIN3: Adjust Decal"
    bl_options = {"REGISTER", "UNDO"}
    bl_description = "Adjust Decal Height, Parallax and Various Other Properties"

    mode: EnumProperty(name="Mode", items=adjust_mode_items, default="HEIGHT")

    passthrough: BoolProperty(default=False)

    @classmethod
    def poll(cls, context):
        return any(obj.DM.isdecal for obj in context.selected_objects)

    def draw_HUD(self, args):
        context, event = args

        draw_init(self, event)

        draw_title(self, "Adjust Decals" if len(self.decals) > 1 else "Adjust Decal")

        draw_prop(self, "Mode", self.mode, offset=0, hint="switch Q, W, E, A, S, D", hint_offset=280)

        if self.mode == "HEIGHT":
            draw_prop(self, "Δ Height", self.delta_height, decimal=5 if event.shift else 3 if event.ctrl else 4, offset=18, hint=f"{'ALT ' if get_prefs().adjust_use_alt_height else ''}move LEFT/RIGHT, X to set %0.4f" % (context.scene.DM.height), hint_offset=280)

        elif self.mode == "WIDTH":
            draw_prop(self, "Δ Width", self.delta_width + 1, decimal=4 if event.shift else 2 if event.ctrl else 3, offset=18, hint="move LEFT/RIGHT, X to set 1", hint_offset=280)

        elif self.mode == "PARALLAX":
            draw_prop(self, "Δ Amount", self.delta_parallax, decimal=3 if event.shift else 1 if event.ctrl else 2, offset=18, hint="move LEFT/RIGHT, X to reset", hint_offset=280)

        elif self.mode == "AO":
            draw_prop(self, "Δ AO Strength", self.delta_ao, decimal=3 if event.shift else 1 if event.ctrl else 2, offset=18, hint="move LEFT/RIGHT, X to set 1, C to set 0", hint_offset=280)

        elif self.mode == "STRETCH":
            draw_prop(self, "Panel UV Stretch", self.delta_stretch + 1, decimal=3 if event.shift else 1 if event.ctrl else 2, offset=18, hint="move LEFT/RIGHT, X to set 1", hint_offset=280)

        elif self.mode == "EMISSION":
            draw_prop(self, "Δ Brightness", self.delta_emit, decimal=2 if event.shift else 0 if event.ctrl else 1, offset=18, hint="move LEFT/RIGHT, X to set 0, C to set 10", hint_offset=280)

        if self.panel_decals:
            self.offset += 18

            if self.cycle_libs:
                draw_prop(self, "Panel", self.panel_decals[0].active_material.DM.decalname, offset=18, hint="CTRL scroll UP/DOWN", hint_offset=280)

            else:
                draw_info(self, "Found no Panel Decals to cycle through", size=11, HUDcolor=red, HUDalpha=1, offset=18)

        self.offset += 18
        draw_prop(self, "Rotate", self.rotate, offset=18, hint="scroll UP/DOWN, SHIFT: 5°, SHIFT + CTRL: 1°", hint_offset=280)
        draw_prop(self, "Rotate UVs", self.uvrotate, offset=18, hint="ALT scroll UP/DOWN", hint_offset=280)
        draw_prop(self, "Mirror U", self.umirror, offset=18, hint="toggle U", hint_offset=280)
        draw_prop(self, "Mirror V", self.vmirror, offset=18, hint="toggle V", hint_offset=280)

        self.offset += 18
        draw_prop(self, "Glossy Rays", "", offset=18, hint="toggle G", hint_offset=280)
        if any(mat[4] for mat in self.decaltypemats):
            draw_prop(self, "Mute Parallax", "", offset=18, hint="toggle P", hint_offset=280)

        self.offset += 18
        if any(mat[2] is not None for mat in self.decalmats):
            draw_prop(self, "Invert Info Decals", "", offset=18, hint="toggle I", hint_offset=280)
        draw_prop(self, "Custom Normals", "", offset=18, hint="toggle N", hint_offset=280)
        draw_prop(self, "Alpha Blend/Hashed", "", offset=18, hint="toggle B", hint_offset=280)

    def modal(self, context, event):
        context.area.tag_redraw()

        if event.type == "MOUSEMOVE":
            wrap_cursor(self, context, event)

        events = ['MOUSEMOVE', 'WHEELUPMOUSE', 'ONE', 'WHEELDOWNMOUSE', 'TWO', 'X', 'Q', 'W', 'E', 'A', 'S', 'D', 'C', 'I', 'N', 'G', 'P', 'U', 'V', "B"]

        if event.type in events:


            if event.type == 'MOUSEMOVE':
                if self.passthrough:
                    self.passthrough = False

                elif not (event.alt and event.type in {'LEFTMOUSE', 'RIGHTMOUSE'}):

                    if self.mode == "HEIGHT":
                        divisor = 10000 if event.shift else 100 if event.ctrl else 1000
                        self.adjust_height(event, divisor)

                    elif self.mode == "WIDTH":
                        divisor = 1000 if event.shift else 10 if event.ctrl else 100
                        self.adjust_panel_width(event, divisor, context.scene)

                    elif self.mode == "PARALLAX":
                        divisor = 1000 if event.shift else 10 if event.ctrl else 100
                        self.adjust_parallax(event, divisor)

                    elif self.mode == "AO":
                        divisor = 1000 if event.shift else 10 if event.ctrl else 100
                        self.adjust_ao(event, divisor)

                    elif self.mode == "STRETCH":
                        divisor = 1000 if event.shift else 10 if event.ctrl else 100
                        self.adjust_panel_uv_stretch(event, divisor)

                    elif self.mode == "EMISSION":
                        divisor = 100 if event.shift else 1 if event.ctrl else 10
                        self.adjust_emission(event, divisor)



            elif event.type == 'Q' and event.value == "PRESS":
                self.mode = "HEIGHT"

            elif event.type == 'W' and event.value == "PRESS":
                self.mode = "WIDTH"

            elif event.type == 'D' and event.value == "PRESS":
                self.mode = "PARALLAX"

            elif event.type == 'A' and event.value == "PRESS":
                self.mode = "AO"

            elif event.type == 'S' and event.value == "PRESS":
                self.mode = "STRETCH"

            elif event.type == 'E' and event.value == "PRESS":
                self.mode = "EMISSION"



            elif event.type == 'X' and event.value == "PRESS":
                if self.mode == "HEIGHT":
                    for obj, displace, init_mid_level, _, _, _ in self.decals:
                        if init_mid_level:
                            get_displace(obj).mid_level = context.scene.DM.height
                    self.delta_height = 0

                elif self.mode == "WIDTH":
                    for obj, initbm in self.init_bms:
                        initbm.to_mesh(obj.data)

                    self.delta_width = 0

                elif self.mode == "PARALLAX":
                    for mat, _, pg, _, init_parallax in self.decaltypemats:
                        if init_parallax is not None:
                            pg.inputs[0].default_value = mat.DM.parallaxdefault

                    self.delta_parallax = 0

                elif self.mode == "AO":
                    for mat, _, dg, _, init_ao, _ in self.decalmats:
                        if init_ao is not None:
                            dg.inputs["AO Multiplier"].default_value = 1

                    self.delta_ao = 1

                elif self.mode == "STRETCH":
                    for obj, initbm in self.init_bms:
                        initbm.to_mesh(obj.data)

                    self.delta_stretch = 0

                elif self.mode == "EMISSION":
                    for mat, _, dg, _, _, init_emit in self.decalmats:
                        dg.inputs["Emission Multiplier"].default_value = 0

                    self.delta_emit = 0

            elif event.type == 'C' and event.value == "PRESS":
                if self.mode == "AO":
                    for mat, _, dg, _, init_ao, _ in self.decalmats:
                        if init_ao is not None:
                            dg.inputs["AO Multiplier"].default_value = 0

                    self.delta_ao = 0

                elif self.mode == "EMISSION":
                    for mat, _, dg, _, _, init_emit in self.decalmats:
                        dg.inputs["Emission Multiplier"].default_value = 10

                    self.delta_emit = 10



            elif event.type == 'I' and event.value == "PRESS":
                for mat, _, dg, init_invert, _, _ in self.decalmats:
                    if init_invert is not None:
                        dg.inputs["Invert"].default_value = 1 - dg.inputs["Invert"].default_value



            elif event.type == 'N' and event.value == "PRESS":
                for obj, _, _, nrmtransfer, init_shownrms, _ in self.decals:
                    if init_shownrms is not None:
                        nrmtransfer.show_render = not nrmtransfer.show_render
                        nrmtransfer.show_viewport = nrmtransfer.show_render


            elif event.type == 'G' and event.value == "PRESS":
                for obj, _, _, _, _, _ in self.decals:
                    set_cycles_visibility(obj, 'glossy', not get_cycles_visibility(obj, 'glossy'))
                    obj.data.update()


            elif event.type == 'P' and event.value == "PRESS":
                for mat, _, pg, _, _ in self.decaltypemats:
                    if pg:
                        pg.mute = not pg.mute


            elif event.type == 'B' and event.value == "PRESS":
                for mat, _, _, _, _, _ in self.decalmats:
                    mat.blend_method = "HASHED" if mat.blend_method == "BLEND" else "BLEND"



            elif event.type in ['U', 'V'] and event.value == "PRESS":
                if event.type == 'U':
                    self.umirror = not self.umirror

                elif event.type == 'V':
                    self.vmirror = not self.vmirror

                self.mirror_uvs()


            elif event.type in {'WHEELUPMOUSE', 'ONE'} and event.value == 'PRESS':

                if event.ctrl and not event.alt and not event.shift:
                    if self.cycle_libs and self.panel_decals:
                        self.change_panel_decal(context, 1)

                elif event.alt:
                    self.rotate_uvs("CCW")

                else:
                    if event.shift and event.ctrl:
                        self.rotate += 1
                        rmx = Matrix.Rotation(radians(1), 4, "Z")
                    elif event.shift:
                        self.rotate += 5
                        rmx = Matrix.Rotation(radians(5), 4, "Z")
                    else:
                        self.rotate += 45
                        rmx = Matrix.Rotation(radians(45), 4, "Z")

                    for obj, _, _, _, _, _ in self.decals:
                        if not obj.DM.issliced and not obj.DM.isprojected:
                            loc, rot, sca = obj.matrix_basis.decompose()
                            obj.matrix_basis = get_loc_matrix(loc) @ get_rot_matrix(rot) @ rmx @ get_sca_matrix(sca)

            elif event.type in {'WHEELDOWNMOUSE', 'TWO'} and event.value == 'PRESS':

                if event.ctrl and not event.alt and not event.shift:
                    if self.cycle_libs and self.panel_decals:
                        self.change_panel_decal(context, -1)

                elif event.alt:
                    self.rotate_uvs("CW")

                else:
                    if event.shift and event.ctrl:
                        self.rotate -= 1
                        rmx = Matrix.Rotation(radians(-1), 4, "Z")
                    elif event.shift:
                        self.rotate -= 5
                        rmx = Matrix.Rotation(radians(-5), 4, "Z")
                    else:
                        self.rotate -= 45
                        rmx = Matrix.Rotation(radians(-45), 4, "Z")

                    for obj, _, _, _, _, _ in self.decals:
                        if not obj.DM.issliced and not obj.DM.isprojected:
                            loc, rot, sca = obj.matrix_basis.decompose()
                            obj.matrix_basis = get_loc_matrix(loc) @ get_rot_matrix(rot) @ rmx @ get_sca_matrix(sca)


        elif event.type in {'MIDDLEMOUSE'} or (event.alt and event.type in {'LEFTMOUSE', 'RIGHTMOUSE'}):
            self.passthrough = True
            return {'PASS_THROUGH'}


        elif event.type in {'LEFTMOUSE', 'SPACE'}:
            self.finish()
            return {'FINISHED'}


        elif event.type in {'RIGHTMOUSE', 'ESC'}:
            self.cancel_modal()
            return {'CANCELLED'}

        self.last_mouse_x = event.mouse_x
        self.last_mouse_y = event.mouse_y

        return {"RUNNING_MODAL"}

    def finish(self):
        bpy.types.SpaceView3D.draw_handler_remove(self.HUD, 'WINDOW')

        finish_status(self)

    def cancel_modal(self):
        self.finish()

        for obj, displace, init_mid_level, nrmtransfer, init_shownrms, init_glossy in self.decals:
            if init_mid_level:
                displace.mid_level = init_mid_level

            if init_shownrms:
                nrmtransfer.show_render = init_shownrms
                nrmtransfer.show_viewport = init_shownrms

            set_cycles_visibility(obj, 'glossy', init_glossy)

        for mat, init_blend, dg, init_invert, init_ao, init_emit in self.decalmats:
            mat.blend_method = init_blend

            if init_invert:
                dg.inputs["Invert"].default_value = init_invert

            if init_ao:
                dg.inputs["AO Multiplier"].default_value = init_ao

            dg.inputs["Emission Multiplier"].default_value = init_emit


        for mat, dg, pg, init_pmute, init_parallax in self.decaltypemats:

            if init_pmute is not None:
                pg.mute = init_pmute

            if init_parallax:
                pg.inputs[0].default_value = init_parallax


        for obj, initbm in self.init_bms:
            initbm.to_mesh(obj.data)
            initbm.clear()

    def invoke(self, context, event):
        self.dg = context.evaluated_depsgraph_get()

        decals = [obj for obj in context.selected_objects if obj.DM.isdecal]

        decalmats = {get_decalmat(obj) for obj in decals if get_decalmat(obj)}

        decalmatuuids = {mat.DM.uuid for mat in decalmats}

        decaltypemats = {mat for mat in bpy.data.materials if mat.DM.uuid in decalmatuuids}

        self.decals = []

        for obj in decals:
            displace = get_displace(obj)
            midvalue = displace.mid_level if displace else None

            nrmtransfer = get_nrmtransfer(obj)
            shownrms = nrmtransfer.show_viewport if nrmtransfer else None

            glossy = get_cycles_visibility(obj, 'glossy')

            self.decals.append((obj, displace, midvalue, nrmtransfer, shownrms, glossy))

        self.decalmats = []

        for mat in decalmats:
            blendmethod = mat.blend_method

            decalgroup = get_decalgroup_from_decalmat(mat)
            invert = decalgroup.inputs["Invert"].default_value if mat.DM.decaltype == "INFO" else None
            ao = decalgroup.inputs["AO Multiplier"].default_value if mat.DM.decaltype != "INFO" else None
            emit = decalgroup.inputs["Emission Multiplier"].default_value

            self.decalmats.append((mat, blendmethod, decalgroup, invert, ao, emit))


        self.decaltypemats = []

        for mat in decaltypemats:
            decalgroup = get_decalgroup_from_decalmat(mat)

            parallaxgroup = get_parallaxgroup_from_decalmat(mat) if mat.DM.decaltype in ['SIMPLE', 'SUBSET', 'PANEL'] else None
            parallaxmute = parallaxgroup.mute if parallaxgroup else None
            parallax = parallaxgroup.inputs[0].default_value if parallaxgroup else None

            self.decaltypemats.append((mat, decalgroup, parallaxgroup, parallaxmute, parallax))

        self.init_bms = []

        for obj in decals:
            initbm = bmesh.new()
            initbm.from_mesh(obj.data)
            initbm.normal_update()
            initbm.verts.ensure_lookup_table()

            self.init_bms.append((obj, initbm))

        self.panel_decals = [obj for obj in decals if obj.DM.decaltype == "PANEL" and get_decalmat(obj)]
        self.panel_decal_mats = {}

        self.cycle_libs = [lib.name for lib in get_prefs().decallibsCOL if (lib.ispanel or lib.istrimsheet) and lib.ispanelcycle]

        self.delta_height = 0
        self.delta_width = 0
        self.delta_parallax = 0
        self.delta_ao = 0
        self.delta_stretch = 0
        self.delta_emit = 0
        self.mode = "HEIGHT"
        self.rotate = 0
        self.uvrotate = 0
        self.umirror = False
        self.vmirror = False

        init_cursor(self, event)

        init_status(self, context, f"Adjust Decal{'s' if len(self.decals) > 1 else ''}")

        args = (context, event)
        self.HUD = bpy.types.SpaceView3D.draw_handler_add(self.draw_HUD, (args, ), "WINDOW", "POST_PIXEL")
        context.window_manager.modal_handler_add(self)
        return {"RUNNING_MODAL"}



    def adjust_height(self, event, divisor):
        if get_prefs().adjust_use_alt_height and not event.alt:
            return

        delta_x = event.mouse_x - self.last_mouse_x
        delta_height = delta_x / divisor

        self.delta_height += delta_height

        for obj, displace, init_mid_level, _, _, glossy in self.decals:
            if init_mid_level is not None:
                displace.mid_level -= delta_height

    def adjust_panel_width(self, event, divisor, scene):
        delta_x = event.mouse_x - self.last_mouse_x
        delta_width = delta_x / divisor

        self.delta_width += delta_width

        for obj, initbm in self.init_bms:
            if obj.DM.issliced:
                bm = initbm.copy()
                bm.verts.ensure_lookup_table()

                change_panel_width(bm, 1 + self.delta_width, panel=obj, scene=scene, set_prop=len(self.panel_decals) == 1)

                bm.to_mesh(obj.data)
                bm.clear()

    def adjust_parallax(self, event, divisor):
        delta_x = event.mouse_x - self.last_mouse_x
        delta_parallax = delta_x / divisor

        self.delta_parallax += delta_parallax

        for mat, _, pg, _, init_parallax in self.decaltypemats:
            if init_parallax is not None:
                amount = pg.inputs[0].default_value

                pg.inputs[0].default_value = max(amount + delta_parallax, 0)
                pg.mute = False

    def adjust_ao(self, event, divisor):
        delta_x = event.mouse_x - self.last_mouse_x
        delta_ao = delta_x / divisor

        self.delta_ao += delta_ao

        for mat, _, dg, _, init_ao, _ in self.decalmats:
            if init_ao is not None:
                i = get_decalgroup_from_decalmat(mat).inputs["AO Multiplier"]
                ao = i.default_value
                newamount = ao + delta_ao

                if 0 <= newamount <= 1:
                    i.default_value = newamount

    def adjust_panel_uv_stretch(self, event, divisor):
        delta_x = event.mouse_x - self.last_mouse_x
        delta_stretch = delta_x / divisor

        self.delta_stretch += delta_stretch

        smx = Matrix.Scale(1 + self.delta_stretch, 2, (1, 0)).inverted_safe()

        for obj, initbm in self.init_bms:
            if obj.DM.issliced:
                bm = initbm.copy()
                bm.verts.ensure_lookup_table()

                uvs = bm.loops.layers.uv.active

                for face in bm.faces:
                    for loop in face.loops:
                        loop[uvs].uv = smx @ loop[uvs].uv

                bm.to_mesh(obj.data)
                bm.clear()

    def adjust_emission(self, event, divisor):
        delta_x = event.mouse_x - self.last_mouse_x
        delta_emit = delta_x / divisor

        self.delta_emit += delta_emit

        for mat, _, dg, _, _, init_emit in self.decalmats:
                i = get_decalgroup_from_decalmat(mat).inputs["Emission Multiplier"]
                emit = i.default_value

                newamount = emit + delta_emit if emit + delta_emit >= 0 else 0
                i.default_value = newamount



    def rotate_uvs(self, direction):
        self.uvrotate += 90 if direction == "CW" else -90

        rmx = Matrix.Rotation(radians(self.uvrotate), 2, "Z")

        for obj, initbm in self.init_bms:

            if obj.DM.prejoindecals:
                continue

            bm = initbm.copy()
            bm.verts.ensure_lookup_table()

            uvs = bm.loops.layers.uv.active
            loops = [loop for face in bm.faces for loop in face.loops]

            dmid = get_selection_uv_bbox(uvs, loops)[1] if obj.DM.preatlasmats else Vector((0.5, 0.5))

            for loop in loops:
                loop[uvs].uv = dmid + rmx @ (loop[uvs].uv - dmid)

            bm.to_mesh(obj.data)
            bm.clear()

    def mirror_uvs(self):
        for obj, initbm in self.init_bms:

            if obj.DM.prejoindecals and obj.DM.preatlasmats:
                continue

            bm = initbm.copy()
            bm.verts.ensure_lookup_table()

            if any([self.umirror, self.vmirror]):
                uvs = bm.loops.layers.uv.active
                loops = [loop for face in bm.faces for loop in face.loops]

                dmid = get_selection_uv_bbox(uvs, loops)[1] if obj.DM.preatlasmats else Vector((0.5, 0.5))
                mmx = Matrix(((-1 if self.umirror else 1, 0), (0, -1 if self.vmirror else 1)))

                for loop in loops:
                    loop[uvs].uv = dmid + mmx @ (loop[uvs].uv - dmid)

            bm.to_mesh(obj.data)
            bm.clear()

    def change_panel_decal(self, context, direction):
        availablepanels = get_available_panel_decals(cycle_libs=self.cycle_libs)

        currentuuid = self.panel_decals[0].DM.uuid
        currentidx = None

        for idx, panel in enumerate(availablepanels):
            if panel[0] == currentuuid:
                currentidx = idx
                break

        if currentidx is None:
            newidx = 0

        else:
            newidx = currentidx - direction

            if newidx < 0:
                newidx = len(availablepanels) - 1
            elif newidx == len(availablepanels):
                newidx = 0

        newpanel = availablepanels[newidx]

        mat = None

        uuid = newpanel[0]
        name = newpanel[1]
        library = newpanel[2]

        if uuid in self.panel_decal_mats:
            mat = self.panel_decal_mats[uuid]

            for panel in self.panel_decals:
                panel.active_material = mat

                set_decalobj_props_from_material(panel, mat)
                set_decalobj_name(panel, decalname=mat.DM.decalname, uuid=uuid)

            context.window_manager.paneldecals = uuid

        else:
            mat, appended, _, _ = get_panel_material(context, uuid)

            if mat:
                self.panel_decal_mats[uuid] = mat

                if appended:
                    set_props_and_node_names_of_decal(library, name, decalobj=None, decalmat=mat)

                    set_defaults(decalmat=mat)

                for panel in self.panel_decals:
                    oldmat = panel.active_material

                    mat.blend_method = oldmat.blend_method

                    set_decalobj_props_from_material(panel, mat)

                    if mat.DM.decaltype != 'INFO' and oldmat.DM.decaltype != 'INFO':

                        old_decalgroup = get_decalgroup_from_decalmat(oldmat)

                        if old_decalgroup:
                            material, material2, subset = get_decalgroup_as_dict(old_decalgroup)

                            decalgroup = get_decalgroup_from_decalmat(mat)

                            if decalgroup:

                                if mat.DM.decaltype == 'SIMPLE':
                                    material2 = None
                                    subset = None
                                elif mat.DM.decaltype == 'SUBSET':
                                    material2 = None

                                set_decalgroup_from_dict(decalgroup, material, material2, subset)

                                mat.DM.ismatched = oldmat.DM.ismatched
                                mat.DM.matchedmaterialto = oldmat.DM.matchedmaterialto
                                mat.DM.matchedmaterial2to = oldmat.DM.matchedmaterial2to
                                mat.DM.matchedsubsetto = oldmat.DM.matchedsubsetto

                    panel.active_material = mat

                    set_decalobj_name(panel, decalname=mat.DM.decalname, uuid=uuid)


                context.window_manager.paneldecals = uuid
