import os
import numpy as np
from shutil import copy
from .. items import textype_color_mapping_dict



def scale_image(path, scale=None, size=None):
    from PIL import Image

    img = Image.open(path)

    if scale:
        size = (round(img.size[0] * scale), round(img.size[1] * scale))

    resized = img.resize(size, Image.BICUBIC)
    resized.save(path)
    del img, resized


def crop_image(img=None, imagepath=None, cropbox=None, padding=0, debug=False):
    from PIL import Image

    if not img:
        img = Image.open(imagepath)

    if cropbox:
        cropped = img.crop(cropbox)

    else:
        bbox = (0, 0, img.size[0], img.size[1])

        cmaxbox = img.convert('RGBA').convert("RGBa").getbbox()

        if debug:
            print("image bounds:", bbox)
            print(" max cropped:", cmaxbox)

        xmin = cmaxbox[0] - padding if cmaxbox[0] - padding > 0 else 0
        ymin = cmaxbox[1] - padding if cmaxbox[1] - padding > 0 else 0
        xmax = cmaxbox[2] + padding if cmaxbox[2] + padding < img.size[0] else img.size[0]
        ymax = cmaxbox[3] + padding if cmaxbox[3] + padding < img.size[1] else img.size[1]

        cropbox = (xmin, ymin, xmax, ymax)

        if debug:
            print("     cropped:", cropbox)

        cropped = img.crop(cropbox)

    size = cropped.size

    cropped.save(imagepath)
    del img, cropped

    return size


def crop_trimsheet_texture(path, trimpath, loc, sca, dimensions):
    from . core import core
    return core.crop_trimsheet_texture(path, trimpath, loc, sca, dimensions)


def increase_canvas_size(path, size, textype):
    from PIL import Image

    img = Image.open(path)
    canvas = create_dummy_texture('', '', mode=img.mode, resolution=size, color=textype_color_mapping_dict[textype], return_image=True)

    canvas.paste(img, box=(0, 0))
    canvas.save(path)

    del img, canvas




def change_contrast(imagepath, contrast):
    from PIL import Image, ImageEnhance

    img = Image.open(imagepath)

    enhance = ImageEnhance.Contrast(img)
    img = enhance.enhance(contrast)

    img.save(imagepath)
    del img


def change_height_contrast(img, amount=1):
    def contrast(c):
        return 128 + amount * (c - 128)

    return img.point(contrast)


def adjust_height_channel(img, amount=1):
    from PIL import Image

    aocurvheight = img.convert('RGB')

    ao, curv, height = aocurvheight.split()
    height = change_height_contrast(height, amount=amount)
    aocurvheight = Image.merge('RGB', (ao, curv, height))

    del ao, curv, height
    return aocurvheight


def set_gamma(img, gamma, bandcount):
    invert_gamma = 1.0 / gamma
    lut = [pow(x / 255., invert_gamma) * 255 for x in range(256)]
    lut = lut * bandcount  # need one set of data for each band for RGB
    img = img.point(lut)
    return img



def convert_I_to_L(img):
    from PIL import Image

    array = np.uint8(np.array(img) / 256)
    return Image.fromarray(array)


def convert_to_L(img):
    if img.mode == 'I':
        img = convert_I_to_L(img)

    elif img.mode != 'L':
        img = img.convert('L')

    return img


def ensure_mode(textype, path):
    from PIL import Image

    img = Image.open(path)

    if img.mode == 'I':
        img = convert_I_to_L(img)

    elif img.mode == 'RGBA':
        img = img.convert('RGB')

    img.save(path)


def avoid_P_mode(img):
    if img.mode == 'P':
        return img.convert('RGB')

    elif img.mode == 'PA':
        return img.convert('RGBA')

    return img



def split_alpha(destination, imagepath, textype, fix_legacy_normals=False):
    from PIL import Image

    img = Image.open(imagepath).convert('RGBA')

    alpha = img.split()[3]

    rgb = img.convert('RGB')

    if textype == 'NRM_ALPHA':
        path = os.path.join(destination, 'normal.png')

        if fix_legacy_normals:
            nrmbg = Image.new('RGBA', img.size, (128, 128, 255, 255))
            normal = Image.alpha_composite(nrmbg, img).convert('RGB')
            normal.save(path)

            del normal

        else:
            rgb.save(path)

    elif textype == 'COLOR_ALPHA':
        path = os.path.join(destination, 'color.png')
        rgb.save(path)

    del img, rgb

    return alpha, path


def split_ao_curv_height(destination, imgpath, paths):
    from PIL import Image

    aocurvheight_map = Image.open(imgpath).convert('RGB')
    channels = aocurvheight_map.split()

    for idx, textype in enumerate(['AO', 'CURVATURE', 'HEIGHT']):
        savepath = os.path.join(destination, "%s.png" % (textype.lower()))

        print(" • %s map saved to: %s" % (textype, savepath))
        channels[idx].save(savepath)

        paths[textype] = savepath

    del aocurvheight_map, channels


def split_masks(destination, imgpath, paths):
    from PIL import Image

    masks_map = Image.open(imgpath)
    channels = masks_map.split()

    for idx, textype in enumerate(['ALPHA', 'SUBSET', 'MATERIAL2']):
        savepath = os.path.join(destination, "%s.png" % (textype.lower()))

        print(" • %s map saved to: %s" % (textype, savepath))
        channels[idx].save(savepath)

        paths[textype] = savepath

    del masks_map, channels


def split_off_height(destination, imgpath):
    from PIL import Image

    aocurvheight_map = Image.open(imgpath).convert('RGB')
    height = aocurvheight_map.split()[2]

    savepath = os.path.join(destination, "height.png")
    print(" • split off HEIGHT map to: %s" % (savepath))
    height.save(savepath)

    del aocurvheight_map, height
    return savepath



def check_image_for_nonblack_pixels(path, threshold=10):
    if os.path.exists(path):
        from PIL import Image

        img = Image.open(path)

        return np.any(np.array(img) > threshold)


def check_for_alpha(path):
    if os.path.exists(path):
        from PIL import Image

        img = Image.open(path)

        if img.mode == 'RGBA':
            alpha = img.split()[3]

            if np.any(np.array(img) > 0):
                alphapath = os.path.join(os.path.dirname(path), "alpha.png")
                alpha.save(alphapath)

                return alphapath


def get_image_size(path):
    from PIL import Image

    img = Image.open(path)
    size = img.size

    del img
    return size


def get_delta(path, amount=1):
    from PIL import Image

    aocurvheight = Image.open(path).convert('RGB')

    height = aocurvheight.split()[2]
    adjusted = change_height_contrast(height, amount=amount)

    extrema = adjusted.getextrema()
    delta = min(extrema[0], 255 - extrema[1])

    del height, adjusted
    return delta



def text2img(savepath, text, font, fontsize=100, padding=(0, 0), offset=(0, 0), align='left', color=(1, 1, 1, 1), bgcolor=(1, 1, 1, 0), gamma=2.2):
    from PIL import Image, ImageFont, ImageDraw

    color = tuple(int(c * 255) for c in color)
    bgcolor = tuple(int(c * 255) for c in bgcolor)

    font = ImageFont.truetype(font, fontsize)
    textsize = font.getsize(text)

    splittext = text.split("\n")
    lines = len(splittext)

    width = max([font.getsize(line)[0] for line in splittext])
    height = lines * textsize[1]
    size = (width + 2 * padding[0], height + 2 * padding[1])

    img = Image.new("RGBA", size, bgcolor)

    draw = ImageDraw.Draw(img)
    draw.multiline_text((padding[0] + offset[0], padding[1] + offset[1]), text, color, font=font, align=align)

    if gamma != 1:
        set_gamma(img, gamma, 4)

    img.save(savepath)


def create_material2_mask(imagepath, width, height):
    from PIL import Image, ImageDraw

    img = Image.new("L", (width, height), 0)
    draw = ImageDraw.Draw(img)
    draw.rectangle([(0, 0), (width, round(height / 2))], fill=255)

    img.save(imagepath)

    del img


def create_dummy_texture(destination, name, mode='RGB', resolution=(1, 1), color=(0, 0, 0), return_image=False):
    from PIL import Image

    img = Image.new(mode, resolution, color)

    if return_image:
        return img

    else:
        path = os.path.join(destination, name)
        img.save(path)

        del img
        return path


def create_new_masks_texture(destination, alpha, maskspath=None, legacytype=None, decaltype=None):
    from PIL import Image

    if maskspath:
        oldmasks = Image.open(maskspath).convert('RGBA')

        if legacytype == 'SUBSET':
            subset = oldmasks.split()[0]
            mat2 = Image.new("L", alpha.size, 0)

        elif legacytype == 'PANEL':
            subset = Image.new("L", alpha.size, 0)
            mat2 = oldmasks.split()[0]

        else:
            if decaltype == 'PANEL':
                subset, mat2 = oldmasks.split()[:2]

            else:
                subset = oldmasks.split()[0]
                mat2 = Image.new("L", alpha.size, 0)

        white = Image.new("L", alpha.size, 255)

        masks = Image.merge("RGBA", (alpha, subset, mat2, white))

        del subset, mat2

    else:
        empty = Image.new("L", alpha.size, 0)
        white = Image.new("L", alpha.size, 255)

        masks = Image.merge("RGBA", (alpha, empty, empty, white))

        del empty

    path = os.path.join(destination, 'masks.png')
    masks.save(path)

    del alpha, masks, white

    return path


def create_trim_ao_curv_height_map(destination, textures):
    from PIL import Image

    ao_curv_height_maps = {j: k for j, k in textures.items() if j in ['AO', 'CURVATURE', 'HEIGHT']}
    ao_curv_height_images = {}

    if ao_curv_height_maps:
        images = [(textype, Image.open(path)) for textype, path in ao_curv_height_maps.items()]
        maxres = max(images, key=lambda x: x[1].size[0])[1].size

        for textype, img in images:
            img = convert_to_L(img)

            ao_curv_height_images[textype] = img if img.size == maxres else img.resize(maxres, Image.BICUBIC)

        for textype in ['AO', 'CURVATURE', 'HEIGHT']:
            if textype not in ao_curv_height_maps:
                ao_curv_height_images[textype] = create_dummy_texture(destination, "%s.png" % textype.lower(), mode='L', resolution=maxres, color=128 if textype in ['CURVATURE', 'HEIGHT'] else 255, return_image=True)


        ao = ao_curv_height_images.get('AO')
        curv = ao_curv_height_images.get('CURVATURE')
        height = ao_curv_height_images.get('HEIGHT')

        path = os.path.join(destination, 'ao_curv_height.png')
        ao_curv_height = Image.merge('RGB', (ao, curv, height))
        ao_curv_height.save(path)

        del ao, curv, height, ao_curv_height

    else:
        path = create_dummy_texture(destination, 'ao_curv_height.png', color=(255, 128, 128))

    return path


def create_trim_masks_map(destination, textures, decaltype):
    from PIL import Image

    if decaltype == 'INFO':
        if 'ALPHA' in textures:
            alpha = convert_to_L(Image.open(textures.get('ALPHA')))
            empty = Image.new('L', alpha.size, color=0)
            masks = Image.merge('RGB', (alpha, empty, empty))

            path = os.path.join(destination, 'masks.png')
            masks.save(path)

        else:
            path = create_dummy_texture(destination, 'masks.png', color=(255, 0, 0))

    else:

        alpha_subset_mat2_maps = {j: k for j, k in textures.items() if j in ['ALPHA', 'SUBSET', 'MATERIAL2']}
        alpha_subset_mat2_images = {}

        if alpha_subset_mat2_maps:
            images = [(textype, Image.open(path)) for textype, path in alpha_subset_mat2_maps.items()]
            maxres = max(images, key=lambda x: x[1].size[0])[1].size

            for textype, img in images:
                img = convert_to_L(img)

                alpha_subset_mat2_images[textype] = img if img.size == maxres else img.resize(maxres, Image.BICUBIC)

            for textype in ['ALPHA', 'SUBSET', 'MATERIAL2']:
                if textype not in alpha_subset_mat2_maps:
                    alpha_subset_mat2_images[textype] = create_dummy_texture(destination, "%s.png" % textype.lower(), mode='L', resolution=maxres, color=255 if textype == 'ALPHA' else 0, return_image=True)

            alpha = alpha_subset_mat2_images.get('ALPHA')
            subset = alpha_subset_mat2_images.get('SUBSET')
            mat2 = alpha_subset_mat2_images.get('MATERIAL2')

            path = os.path.join(destination, 'masks.png')
            masks = Image.merge('RGB', (alpha, subset, mat2))
            masks.save(path)

            del alpha, subset, mat2, masks

        else:
            path = create_dummy_texture(destination, 'masks.png', color=(255, 0, 0))

    return path


def create_smoothness_map(roughnesspath, savepath=None):
    from PIL import Image, ImageChops

    roughness = convert_to_L(Image.open(roughnesspath))
    smoothness = ImageChops.invert(roughness)

    if savepath:
        smoothness.save(savepath)
        del roughness, smoothness
    else:
        del roughness
        return smoothness


def create_subset_occlusion_map(subsetpath, aopath, savepath=None):
    from PIL import Image, ImageChops

    subset = convert_to_L(Image.open(subsetpath))
    ao = convert_to_L(Image.open(aopath))

    subsetocclusion = ImageChops.screen(subset, ImageChops.invert(ao))

    if savepath:
        subsetocclusion.save(savepath)
        del ao, subset, subsetocclusion
    else:
        del ao, subset
        return subsetocclusion


def create_white_height_map(heightpath, savepath=None):
    from PIL import Image

    def white_height(img):
        def contrast(c):
            return c + 128
        return img.point(contrast)

    height = convert_to_L(Image.open(heightpath))

    whiteheight = white_height(height)

    if savepath:
        whiteheight.save(savepath)
        del height, whiteheight
    else:
        del height
        return whiteheight


def create_channel_packed_atlas_map(sources, resolution, savepath):
    from PIL import Image

    for channel, data in sources.items():

        if data and data['mode'] == 'LOAD':
            if channel == 'RED':
                red = convert_to_L(Image.open(data['path']))
            if channel == 'GREEN':
                green = convert_to_L(Image.open(data['path']))
            if channel == 'BLUE':
                blue = convert_to_L(Image.open(data['path']))
            if channel == 'ALPHA':
                alpha = convert_to_L(Image.open(data['path']))

        elif data and data['mode'] == 'CREATE':
            if data['type'] == 'SMOOTHNESS':
                img = create_smoothness_map(data['path'])

            elif data['type'] == 'WHITEHEIGHT':
                img = create_white_height_map(data['path'])

            elif data['type'] == 'SUBSETOCCLUSION':
                img = create_subset_occlusion_map(*data['paths'])

            if channel == 'RED':
                red = img
            elif channel == 'GREEN':
                green = img
            elif channel == 'BLUE':
                blue = img
            elif channel == 'ALPHA':
                alpha = img

        else:
            if channel == 'RED':
                red = create_dummy_texture('', '', mode='L', resolution=resolution, color=0, return_image=True)
            elif channel == 'GREEN':
                green = create_dummy_texture('', '', mode='L', resolution=resolution, color=0, return_image=True)
            elif channel == 'BLUE':
                blue = create_dummy_texture('', '', mode='L', resolution=resolution, color=0, return_image=True)
            elif channel == 'ALPHA':
                alpha = None

    if alpha:
        packed = Image.merge('RGBA', (red, green, blue, alpha))

    else:
        packed = Image.merge('RGB', (red, green, blue))

    packed.save(savepath)



def pack_textures(dm, decalpath, textures, size=None, crop=False, padding=0):
    from . core import core
    return core.pack_textures(dm, decalpath, textures, size=size, crop=crop, padding=padding)



def create_empty_map(bakebasepath, baketype, targetname, size):
    from PIL import Image

    if baketype == 'COLOR':
        empty_map = Image.new("RGBA", size, color=(0, 0, 0, 0))

    elif baketype == 'NORMAL':
        empty_map = Image.new("RGB", size, color=(128, 128, 255))

    elif baketype in ['EMISSION_NORMAL', 'EMISSION_COLOR']:
        empty_map = Image.new("RGB", size, color=(0, 0, 0))

    elif baketype == 'AO_CURV_HEIGHT':
        empty_map = Image.new("RGB", size, color=(255, 128, 128))

    elif baketype == 'SUBSET':
        empty_map = Image.new("L", size, color=0)

    path = os.path.join(bakebasepath, "%s_%s.png" % (targetname, baketype.lower()))
    print("Info: Creating %s's empty %s map: %s" % (targetname, baketype.lower(), path))

    empty_map.save(path)

    return path


def create_decals_mask(bakebasepath, targetname, baketype, target_uv, margin_0_uv, margin_3_uv):
    from . core import core
    return core.create_decals_mask(bakebasepath, targetname, baketype, target_uv, margin_0_uv, margin_3_uv)


def apply_decals_mask(margin_map, bake_map, baketype, targetname):
    from PIL import Image

    print("Info: Applying decals mask to %s's %s map." % (targetname, baketype.lower()))

    margin = Image.open(margin_map)
    bake_margin = Image.open(bake_map)
    bake_margin.putalpha(margin)

    size = bake_margin.size

    if baketype == 'NORMAL':
        bake_base = Image.new("RGBA", size, color=(128, 128, 255, 255))
    elif baketype in ['COLOR', 'EMISSION_NORMAL', 'EMISSION_COLOR']:
        bake_base = Image.new("RGBA", size, color=(0, 0, 0, 0))
    elif baketype == 'AO_CURV_HEIGHT':
        bake_base = Image.new("RGBA", size, color=(255, 128, 128, 255))
    elif baketype == 'SUBSET':
        bake_base = Image.new("RGBA", size, color=(0, 0, 0, 255))

    bake = Image.alpha_composite(bake_base, bake_margin)

    if baketype in ['NORMAL', 'AO_CURV_HEIGHT', 'EMISSION_NORMAL', 'EMISSION_COLOR']:
        bake = bake.convert('RGB')

    elif baketype in ['SUBSET']:
        bake = convert_to_L(bake)

    bake.save(bake_map)

    del margin, bake_margin, bake_base, bake


def combine(bakebasepath, bakes, support_bakes):
    from PIL import Image

    maps = {}

    for idx, (target, baketypedict) in enumerate(bakes.items()):
        for baketype, path in baketypedict.items():
            if idx == 0:
                maps[baketype] = [path]

            else:
                maps[baketype].append(path)


    bakes['COMBINED'] = {}

    for baketype, paths in maps.items():

        if baketype in ['COMBINE', 'MASKS']:
            continue

        savepath = os.path.join(bakebasepath, "Combined_%s.png" % (baketype.lower()))
        print("Info: Combining %s bakes: %s" % (baketype.lower(), savepath))

        for idx, path in enumerate(paths):

            if idx == 0:
                combined = Image.open(path).convert('RGBA')

            else:
                if baketype == 'COLOR':
                    mask = None
                    layer = Image.open(path)
                else:
                    mask = convert_to_L(Image.open(maps['COMBINE'][idx]))
                    layer = Image.open(path).convert('RGBA')

                    layer.putalpha(mask)

                combined = Image.alpha_composite(combined, layer)

                del mask, layer

            if idx == len(paths) - 1:

                if baketype in ['NORMAL', 'AO_CURV_HEIGHT', 'EMISSION_NORMAL', 'EMISSION_COLOR']:
                    combined = combined.convert('RGB')

                elif baketype in ['SUBSET']:
                    combined = convert_to_L(combined)

                combined.save(savepath)
                del combined

                bakes['COMBINED'][baketype] = savepath

                if baketype in ['AO_CURV_HEIGHT', 'EMISSION_NORMAL', 'EMISSION_COLOR']:
                    support_bakes.append(savepath)


def split_ao_curv_height_channels(bakebasepath, bakes):
    from PIL import Image

    maptype = 'AO_CURV_HEIGHT'

    for target, baketypedict in bakes.items():
        targetname = target.capitalize() if target == 'COMBINED' else target.name

        print("Info: Splitting %s's %s map" % (targetname, maptype.lower()))

        path = baketypedict[maptype]

        aocurvheight_map = Image.open(path)
        channels = aocurvheight_map.split()

        for idx, name in enumerate(maptype.split('_')):
            savepath = os.path.join(bakebasepath, "%s_%s.png" % (targetname, name.lower()))

            print(" • %s's %s map: %s" % (targetname, name, savepath))
            channels[idx].save(savepath)

            bakes[target][name] = savepath

        del aocurvheight_map, channels

    print()


def combine_emission_maps(bakebasepath, bakes):
    from PIL import Image, ImageChops

    for target, baketypedict in bakes.items():
        targetname = target.capitalize() if target == 'COMBINED' else target.name

        print("Info: Merging %s's emission maps" % (targetname))

        emission_normal_path = baketypedict['EMISSION_NORMAL']
        emission_color_path = baketypedict['EMISSION_COLOR']

        if emission_normal_path and emission_color_path:
            emission_normal = Image.open(emission_normal_path)
            emission_color = Image.open(emission_color_path)

            emission = ImageChops.screen(emission_normal, emission_color)
            savepath = os.path.join(bakebasepath, "%s_emission.png" % (targetname))

            print(" • %s's EMISSION map: %s" % (targetname, savepath))
            emission.save(savepath)

            bakes[target]['EMISSION'] = savepath

            del emission, emission_normal, emission_color

    print()



def create_atlas(destination, sources, solution, textype):
    from . core import core
    return core.create_atlas(destination, sources, solution, textype)
