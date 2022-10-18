# Copyright (C) 2022 Thomas Hoppe (h0bB1T). All rights reserved.
#
# Unauthorized copying of this file via any medium is strictly prohibited.
# Proprietary and confidential.

import bpy, os, subprocess, io, json, tempfile

from typing import Any, Dict, List

from ..utils.dev import inf


def run_blender(args: List[str]):
    """
    Runs Blender in background.
    """
    args.insert(0, bpy.app.binary_path)
    inf(f'Start: {" ".join(args)}')
    subprocess.Popen(args, universal_newlines=True).wait()


def os_path(blender_path: str) -> str:
    """
    Return file file in blender format as os path.
    """
    return os.path.realpath(bpy.path.abspath(blender_path))


def unified_path(path_or_file) -> str:
    """
    As c:\\bla is the same as C:/blA/, we need to bring 
    paths on a single notation, when used as dict-key.
    """
    return os.path.normcase(os_path(path_or_file))


def write_json(filename: str, data: Dict[str, Any]):
    try:
        with io.open(filename, mode='w', encoding='utf-8') as dest:
            json.dump(data, dest, indent=4)
    except Exception:
        pass


def read_json(filename: str) -> Dict[str, Any]:
    try:
        with io.open(filename, mode='r', encoding='utf-8') as src:
            return json.load(src)
    except Exception:
        pass
    return dict()


def decode_json(tag: str) -> Dict[str, Any]:
    if tag:
        return json.loads(tag)
    else:
        return {}      


class TempFile:
    """
    Creates a temp file using 'with' statement and deletes (RAII).
    """
    def __init__(self, ext: str):
        self.name = os.path.join(tempfile.gettempdir(), f'awp.tmp.{ext}')


    def __enter__(self):
        return self.name
        

    def __exit__(self, type, value, tb):
        if os.path.exists(self.name):
            os.remove(self.name)              
