import bpy
import bpy_extras
import pathlib
import json
from .. import utils


class BackupPreferences(bpy.types.Operator, bpy_extras.io_utils.ExportHelper):
    bl_idname = 'powermanage.backup_preferences'
    bl_label = 'Backup Preferences'
    bl_description = 'Backup PowerManage preferences to a JSON file'
    bl_options = {'REGISTER', 'INTERNAL'}

    filepath: bpy.props.StringProperty(options={'HIDDEN'})
    filter_glob: bpy.props.StringProperty(default='*.json', options={'HIDDEN'})
    filename_ext: bpy.props.StringProperty(default='.json', options={'HIDDEN'})

    def execute(self, context: bpy.types.Context) -> set:
        prefs = utils.meta.prefs()
        data = utils.backup.save_recursive_group(prefs)

        text = json.dumps(data, indent=1)
        path = pathlib.Path(self.filepath)
        path.write_text(text)

        self.report({'INFO'}, f'Saved preferences to "{self.filepath}"')
        return {'FINISHED'}


class RestorePreferences(bpy.types.Operator, bpy_extras.io_utils.ImportHelper):
    bl_idname = 'powermanage.restore_preferences'
    bl_label = 'Restore Preferences'
    bl_description = 'Restore PowerManage preferences from a JSON file'
    bl_options = {'REGISTER', 'INTERNAL'}

    filepath: bpy.props.StringProperty(options={'HIDDEN'})
    filter_glob: bpy.props.StringProperty(default='*.json', options={'HIDDEN'})
    filename_ext: bpy.props.StringProperty(default='.json', options={'HIDDEN'})

    def execute(self, context: bpy.types.Context) -> set:
        path = pathlib.Path(self.filepath)
        text = path.read_text()
        data = json.loads(text)

        prefs = utils.meta.prefs()
        utils.backup.load_recursive_group(prefs, data)
        utils.meta.save_userpref()

        self.report({'INFO'}, f'Loaded preferences from "{self.filepath}"')
        return {'FINISHED'}
