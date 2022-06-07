import bpy, os

addon_name = 'photographer'

# Folders
script_dir = bpy.context.preferences.filepaths.script_directory
if script_dir and os.path.exists(script_dir):
    presets_folder = os.path.join(script_dir, 'presets')
    addon_folder = os.path.join(script_dir, 'addons')
else:
    if bpy.app.version >= (3,0,0):
        presets_folder = bpy.utils.user_resource('SCRIPTS', path="presets")
        addon_folder = bpy.utils.user_resource('SCRIPTS', path="addons")
    else:
        presets_folder = bpy.utils.user_resource('SCRIPTS', "presets")
        addon_folder = bpy.utils.user_resource('SCRIPTS', "addons")

photographer_presets_folder = os.path.join(presets_folder,'photographer')

photographer_folder = os.path.dirname(os.path.realpath(__file__))
photographer_folder_name = os.path.split(photographer_folder)[1]

# Compact UI panel size
panel_value_size = 0.88

# Default Exposure value
base_ev = 9.416 #Applying the 683 lm/W conversion (2^9.416 = 683)
