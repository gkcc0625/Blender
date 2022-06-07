bl_info = {
    "name": "kekit_keymap",
    "author": "Kjell Emanuelsson",
    "category": "preferences",
    "version": (1, 0, 0),
    "blender": (2, 80, 0),
}

import bpy
import json
from .ke_utils import get_ke_operators, get_ke_wm_piemenus


def write_keymap(data):
    jsondata = json.dumps(data, indent=2, ensure_ascii=True)
    wpath = bpy.utils.script_path_user()
    file_name = wpath + "/ke_keymap" + ".json"
    with open(file_name, "w") as text_file:
        text_file.write(jsondata)
    text_file.close()


def read_keymap():
    wpath = bpy.utils.script_path_user()
    file_name = wpath + "/ke_keymap.json"
    try:
        with open(file_name, "r") as jf:
            prefs = json.load(jf)
            jf.close()
    except (OSError,IOError):
        prefs = None
    return prefs


class KE_OT_KEKIT_KEYMAP(bpy.types.Operator):
    bl_idname = "ke.kit_keymap"
    bl_label = "keKit Keymap Export/Import"
    bl_description = "keKit Keymap Export/Import.\nExports -only- keKit Operators & Pie-menus mappings to JSON file"

    mode: bpy.props.EnumProperty(
        items=[("SAVE", "Export keKit Keymap JSON file", "", "SAVE", 1),
               ("LOAD", "Import keKit Keymap JSON file", "", "LOAD", 2),
               ],
        name="Export / Import keKit Keymap",
        options={'HIDDEN'},
        default="SAVE")


    def execute(self, context):

        wm = bpy.context.window_manager
        keymaps = {}
        keys = ["id", "active", "shift", "ctrl", "alt", "any", "oskey", "repeat", "keymod",
                "map_type", "type", "value", "properties"]


        if self.mode == "SAVE":

            keops = get_ke_operators()
            ke_wm_pies = get_ke_wm_piemenus()
            stored = 0

            for km in wm.keyconfigs.user.keymaps:
                for ki in km.keymap_items:

                    if ki.properties is not None:
                        kipv = [i for i in ki.properties.values()]
                        if kipv:
                            kipv = kipv[0]

                    if ki.idname in keops or (
                            ki.idname == "wm.call_menu_pie" and kipv in ke_wm_pies):
                        if km.name not in keymaps:
                            keymaps[km.name] = {}

                        # note: km.name == category (e.g: 3D View)
                        kiv = [i for i in ki.properties.items()]
                        values = [ki.id, ki.active, ki.shift, ki.ctrl, ki.alt, ki.any, ki.oskey, ki.repeat,
                                  ki.key_modifier, ki.map_type, ki.type, ki.value, kiv]

                        storage_name = ki.idname + " " + ki.to_string()
                        keymaps[km.name][storage_name] = dict(zip(keys, values))
                        stored += 1

            write_keymap(keymaps)

            # Report
            self.report({"INFO"},"keKit JSON Keymap Exported. (Nr. of Shortcuts: %s)" %str(stored))


        elif self.mode == "LOAD":

            data = read_keymap()

            if data is None:
                self.report({"INFO"}, "Import Failed - Is file in keKit Keymap path?")
                return{"CANCELLED"}

            conflicting = []
            conflicting_report = []
            shortcut_changed_report = []
            props_changed_report = []
            new_report = []
            failed = []
            total = 0

            for cat in data.keys():

                key_ref_name = []
                key_ref_tostr = []
                stored_keys = []

                for k in data[cat].keys():
                    name = k.split(" ")[0]
                    trim = len(name) + 1
                    to_str = k[trim:]
                    key_ref_name.append(name)
                    key_ref_tostr.append(to_str)
                    stored_keys.append(k)
                    total += 1

                for ki in wm.keyconfigs.user.keymaps[cat].keymap_items:

                    found = False
                    to_str = ki.to_string()

                    # -----------------------------------------------------------------------
                    # Mapping Matched - Check for operator prop-enum changes (only) for identical hotkey entries
                    # -----------------------------------------------------------------------
                    if to_str in key_ref_tostr:

                        for i, j in zip(key_ref_name, key_ref_tostr):

                            if i == ki.idname and j == to_str:

                                stored_key = i + " " + j
                                sk = data[cat][stored_key]
                                props = sk["properties"]

                                # Blender only stores changed props -> mismatch = reset and set from import (id-match)
                                # Todo: Simplify with a combined reset-set for all?
                                if props and (len(props) != len(ki.properties.items())):
                                    wm.keyconfigs.user.keymaps[cat].restore_item_to_default(ki)
                                    break

                                else:
                                    found = True

                                    ki.active = sk["active"]

                                    if props:
                                        changed = ""
                                        for p in props:
                                            if ki.properties[p[0]] != p[1]:
                                                changed += " (" + p[0] + ")"
                                                ki.properties[p[0]] = p[1]

                                        if changed:
                                            props_changed_report.append(stored_key + changed)

                                    # print(stored_key)
                                    if stored_key in stored_keys:
                                        stored_keys.remove(stored_key)
                                    break

                        if not found and ki.active:
                            conflicting.append(ki)

                    # -----------------------------------------------------------------------
                    # Mapping Changed - Check for hotkey change (and the rest) with ID value
                    # -----------------------------------------------------------------------
                    if not found and ki.idname in key_ref_name:

                        idmatch = False

                        for k in stored_keys:

                            if data[cat][k]["id"] == ki.id:

                                idmatch = True
                                sk = data[cat][k]

                                ki.active = sk["active"]
                                ki.any = sk["any"]  # must be set before other modifiers?
                                ki.shift = sk["shift"]
                                ki.ctrl = sk["ctrl"]
                                ki.alt = sk["alt"]
                                ki.oskey = sk["oskey"]
                                ki.repeat = sk["repeat"]
                                ki.key_modifier = sk["keymod"]
                                ki.map_type = sk["map_type"]
                                ki.type = sk["type"]
                                ki.value = sk["value"]

                                props = sk["properties"]
                                if props:
                                    for p in props:
                                        ki.properties[p[0]] = p[1]

                                shortcut_changed_report.append(k)
                                stored_keys.remove(k)
                                break

                        if not idmatch:
                            # Whoops. Outtalucko. I guess we just disable and add a new one?
                            ki.active = False
                            f = ki.idname + " " + to_str
                            if f != "ke.call_pie Shift Ctrl Alt 0":
                                failed.append(f)

                # -----------------------------------------------------------------------
                # Mapping Missing - Add it back from stored key
                # -----------------------------------------------------------------------
                if stored_keys:
                    # ...If -still- items in stored_keys, they are not mapped at all
                    ki = wm.keyconfigs.user.keymaps[cat].keymap_items
                    for key in stored_keys:
                        k = data[cat][key]
                        idname = key.split(" ")[0]
                        new = ki.new(idname, type=k["type"], value=k["value"], any=k["any"], shift=k["shift"],
                                     ctrl=k["ctrl"], alt=k["alt"], oskey=k["oskey"], key_modifier=k["keymod"],
                                     repeat=k["repeat"])

                        new.active = k["active"]
                        new.map_type = k["map_type"]

                        props = k["properties"]
                        if props:
                            for p in props:
                                new.properties[p[0]] = p[1]

                        new_report.append(key)

                # -----------------------------------------------------------------------
                # Disable Conflicting Mappings
                # -----------------------------------------------------------------------
                if conflicting:
                    for k in conflicting:
                        if k.idname not in key_ref_name:
                            k.active = False
                            cn = k.idname + " " + k.to_string()
                            conflicting_report.append(cn)

            # -----------------------------------------------------------------------
            # Final Report
            # -----------------------------------------------------------------------
            self.report({"INFO"}, "keKit JSON Keymap Imported. (System Console Window for details) ^")
            print("")
            print("---keKit JSON Keymap Import Details---")
            print("Nr.of Shortcuts Processed: %s" % str(total))
            print("Changed Shortcuts Mapping / Properties (%s) :" % str(
                len(shortcut_changed_report) + len(props_changed_report)))
            if shortcut_changed_report or props_changed_report:
                print(shortcut_changed_report + props_changed_report)
            print("Conflicting Shortcuts Disabled (%s) :" % str(len(conflicting_report)))
            if conflicting_report:
                print(conflicting_report)
            print("Missing Shortcuts Added (%s) :" % str(len(new_report)))
            if new_report:
                print(new_report)
            print("Invalid Shortcuts Disabled (%s) :" % str(len(failed)))
            if failed:
                print(failed)
            print("")

            # Helps?
        context.area.tag_redraw()

        return {"FINISHED"}


def register():
    bpy.utils.register_class(KE_OT_KEKIT_KEYMAP)

def unregister():
    bpy.utils.unregister_class(KE_OT_KEKIT_KEYMAP)

if __name__ == "__main__":
    register()
