import bpy, os, shutil
from . import constants

def listfiles(path):
    files = []
    for dirName, subdirList, fileList in os.walk(path):
        # print(dirName)
        # print(subdirList)
        # print(fileList)
        dir = dirName.replace(path, '')
        for fname in fileList:
            if fname.endswith((".py", ".png")):
                files.append(os.path.join(dir, fname))
    return files

def register():
    # Create presets folder if it doesn't exist
    if not os.path.exists(constants.photographer_presets_folder):
      os.makedirs(constants.photographer_presets_folder, exist_ok=True)

    bundled_presets_folder = os.path.join(constants.addon_folder, 'photographer','presets')
    # # Check what's in the add-on presets folder
    source = listfiles(bundled_presets_folder)
    # print (source)

    for f in source:
        file = os.path.join(bundled_presets_folder, f[1:])
        # print (file)
        dest_file = os.path.join(constants.photographer_presets_folder, f[1:])
        dest_folder = os.path.dirname(dest_file)
        try:
            if not os.path.exists(dest_folder):
                os.makedirs(dest_folder,exist_ok=True)
            if os.path.exists(dest_file):
                if os.stat(file).st_mtime - os.stat(dest_file).st_mtime > 1:
                    shutil.copy2(file, dest_folder)
                    print ("Photographer: Updated preset" + str(f))
            else:
                shutil.copy2(file, dest_folder)
                print ("Photographer: Installed preset" + str(f))
        except:
            print ("Photographer could not install this preset: " + str(f))
            pass
            