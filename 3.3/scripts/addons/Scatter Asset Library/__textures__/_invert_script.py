

"""

This script will automatically invert the jpg of a folder 
and name the files 'file_name' + _invert +'.jpg'

be sure that your files are '.jpg' and there's not invertion already inside the folder. 

PIL module must be installed.

"""

import os
from PIL import Image
import PIL.ImageOps    

path = "C:/path/to/folder/"

for file in os.listdir(path):
    star = os.path.join(path,file)
    land = os.path.join(path, file.split('.jpg')[0] + '_invert' + '.jpg' )

    image = Image.open(star)
    inverted_image = PIL.ImageOps.invert(image)
    inverted_image.save(land)
