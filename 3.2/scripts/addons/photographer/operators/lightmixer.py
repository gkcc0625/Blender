import bpy
from ..constants import addon_name
from ..world import get_environment_tex

class LIGHTMIXER_OT_Add(bpy.types.Operator):
    """ Add Light """
    bl_idname = "lightmixer.add"
    bl_label = "Add Light"
    bl_options = {'REGISTER', 'UNDO'}

    type: bpy.props.EnumProperty(
            name = "Light Type",
            items = [('POINT','Point',''),('AREA','Area',''),
                    ('SPOT','Spot',''), ('SUN','Sun','')],
    )

    def execute(self, context):
        # Switch to object mode to create light
        if bpy.context.scene.collection.all_objects:
            if bpy.context.object and bpy.context.object.mode != 'OBJECT':
                bpy.ops.object.mode_set(mode='OBJECT')

        bpy.ops.object.light_add(type=self.type)
        # Select Light
        light_obj = context.view_layer.objects.active

        light = light_obj.data
        settings = light.photographer
        prefs = bpy.context.preferences.addons[addon_name].preferences

        # Apply Sun default settings
        if light.type == 'SUN':
            if prefs.use_physical_lights:
                settings.sunlight_unit = prefs.default_sunlight_unit
                if settings.sunlight_unit == 'irradiance':
                    settings.irradiance = prefs.default_irradiance
                elif settings.sunlight_unit == 'illuminance':
                    settings.illuminance = prefs.default_illuminance
                elif settings.sunlight_unit == 'artistic':
                    settings.intensity = prefs.default_intensity
                    settings.light_exposure = prefs.default_light_exposure
            elif context.scene.render.engine == 'LUXCORE' and not prefs.use_physical_lights:
                light.luxcore.light_type = prefs.default_lc_light_type
                if light.luxcore.light_type == 'sun':
                    light.luxcore.sun_sky_gain = prefs.default_sun_sky_gain
                else:
                    light.luxcore.gain = prefs.default_gain
                light.luxcore.exposure = prefs.default_light_exposure
            else:
                light.energy = prefs.default_irradiance
        else:
            # Apply other lights default settions
            unit = ''
            if prefs.use_physical_lights:
                data = settings
                unit = prefs.default_light_unit
                data.light_unit = unit
            elif context.scene.render.engine == 'LUXCORE' and not prefs.use_physical_lights:
                data = light.luxcore
                unit = prefs.default_lc_light_unit
                data.light_unit = unit
            if unit:
                if unit == 'artistic':
                    if context.scene.render.engine == 'LUXCORE' and not prefs.use_physical_lights:
                        data.gain = prefs.default_gain
                        data.exposure = prefs.default_light_exposure
                    else:
                        data.intensity = prefs.default_intensity
                        data.light_exposure = prefs.default_light_exposure
                if unit == 'power':
                    data.power = prefs.default_power
                if unit == 'advanced_power':
                    data.advanced_power = prefs.default_advanced_power
                    data.efficacy = prefs.default_efficacy
                if unit == 'lumen':
                    data.lumen = prefs.default_lumen
                if unit == 'candela':
                    data.candela = prefs.default_candela
                if unit in {'lumen','candela'}:
                    data.normalizebycolor = prefs.default_normalizebycolor
                    data.per_square_meter = prefs.default_per_square_meter
            else:
                light.energy = prefs.default_power

        # if context.scene.render.engine == 'EEVEE':
        unit_scale = context.scene.unit_settings.scale_length

        light.use_custom_distance = prefs.default_use_custom_distance
        light.cutoff_distance = prefs.default_cutoff_distance / unit_scale
        light.shadow_buffer_bias = prefs.default_shadow_buffer_bias
        light.use_contact_shadow = prefs.default_use_contact_shadow
        light.contact_shadow_distance = prefs.default_contact_shadow_distance / unit_scale
        light.contact_shadow_bias = prefs.default_contact_shadow_bias
        light.contact_shadow_thickness = prefs.default_contact_shadow_thickness

        if context.scene.render.engine == 'LUXCORE':
            settings.enable_lc_physical = prefs.use_physical_lights
            light_obj.data.luxcore.use_cycles_settings = prefs.use_physical_lights

        return{'FINISHED'}

class LIGHTMIXER_OT_Delete(bpy.types.Operator):
    bl_idname = "lightmixer.delete"
    bl_label = "Delete Light"
    bl_options = {'REGISTER', 'UNDO'}

    light: bpy.props.StringProperty()
    use_global: bpy.props.BoolProperty(
                default=False,
                name="Delete Global",
                description="Delete from all Scenes")
    @classmethod
    def description(self, context, event):
        return f'Shift-Click to delete "{event.light}" globally'

    def execute(self, context):
        scene = context.scene
        bpy.ops.photographer.target_delete(obj_name=self.light)

        light_obj = scene.objects.get(self.light)
        if light_obj:
            return bpy.ops.object.delete(
                {
                     "object" : None,
                     "selected_objects" : [light_obj]
                 },
                 use_global = self.use_global,
            )
        return {'CANCELLED'}

    def invoke(self, context, event):
        self.use_global = event.shift
        wm = context.window_manager
        if self.use_global:
            return wm.invoke_confirm(self, event)
        else:
            return self.execute(context)

class LIGHTMIXER_OT_Enable(bpy.types.Operator):
    bl_idname = "lightmixer.enable"
    bl_label = "Enable Light"
    bl_description = ("Shift-Click to Solo this light. \n"
                    "Ctrl-Click to enable/disable all linked lights")
    bl_options = {'UNDO'}

    light: bpy.props.StringProperty()
    linked: bpy.props.BoolProperty()
    shift: bpy.props.BoolProperty()

    def execute(self, context):
        light_objs = []
        light_obj = bpy.data.objects[self.light]

        if self.linked:
            for o in context.scene.collection.all_objects:
                if o.type == 'LIGHT' and o.data == light_obj.data:
                    light_objs.append(o)
        else:
            light_objs.append(light_obj)

        if self.shift:
            if context.scene.lightmixer.solo_active:
                solo_light=[o for o in context.scene.collection.all_objects if o.type=='LIGHT' and o.lightmixer.solo]
                emissive_mats=[mat for mat in bpy.data.materials if mat.get('is_emissive', False)]
                em_nodes = []
                for mat in emissive_mats:
                    nodes = mat.node_tree.nodes
                    for n in mat['em_nodes']:
                        em_nodes.append(nodes.get(n))

                solo_node = [n for n in em_nodes if n.lightmixer.solo]

                if solo_light:
                    if solo_light[0] == light_obj:
                        light_obj.lightmixer.solo = False
                    else:
                        solo_light[0].lightmixer.solo = False
                        light_obj.lightmixer.solo = True
                elif context.scene.world.solo:
                    context.scene.world.solo = False
                    light_obj.lightmixer.solo = True
                elif solo_node:
                    solo_node[0].lightmixer.solo = False
                    light_obj.lightmixer.solo = True
            else:
                light_obj.lightmixer.solo = not light_obj.lightmixer.solo

        else:
            for l in light_objs:
                if not context.scene.lightmixer.solo_active:
                    l.lightmixer.enabled = not l.lightmixer.enabled

        return{'FINISHED'}

    def invoke(self, context, event):
        self.linked = event.ctrl
        self.shift = event.shift
        return self.execute(context)

class LIGHTMIXER_OT_RefreshHDRIPreview(bpy.types.Operator):
    bl_idname = "lightmixer.refresh_hdri_preview"
    bl_label = "World changed! Refresh Preview"
    bl_description = "HDRI preview is outdated as the World changed"

    def execute(self,context):
        # Update HDRI thumbnail
        if context.scene.world.get('hdri_category',''):
            hdri_category = context.scene.world['hdri_category']

        if context.scene.world.get('hdri_tex',''):
            hdri_tex = context.scene.world['hdri_tex']
        else:
            if get_environment_tex(context):
                hdri_tex = get_environment_tex(context)[0].image.filepath

        try:
            context.scene.lightmixer.hdri_category = hdri_category
            context.scene.lightmixer.hdri_tex = hdri_tex
            return {'FINISHED'}
        except:
            print ("Did not update HDRI preview as it was not found")
            return {'CANCELLED'}
