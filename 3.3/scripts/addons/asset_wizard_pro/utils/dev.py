# Copyright (C) 2022 Thomas Hoppe (h0bB1T). All rights reserved.
#
# Unauthorized copying of this file via any medium is strictly prohibited.
# Proprietary and confidential.

import traceback

from time import time
from ..constants import log_prefix

def debug_level():
    return 3

def err(m: str):
    print(f'[{log_prefix}-ERR] {m}')
    print(traceback.format_exc())

def wrn(m: str): 
    if debug_level() > 0: 
        print(f'[{log_prefix}-WRN] {m}')

def inf(m: str): 
    if debug_level() > 1: 
        print(f'[{log_prefix}-INF] {m}')

def dbg(m: str): 
    if debug_level() > 2: 
        print(f'[{log_prefix}-DBG] {m}')

def dmp(m: str): 
    if debug_level() > 3: 
        print(f'[{log_prefix}-DMP] {m}')


# Used to measure timing on a specific part of the code.
class _MeasureObject:
    def __init__(self, text: str):
        self.text = text
        self.start = time()

    def finish(self):
        inf('%s: %i ms' % (self.text, int((time() - self.start) * 1000)))


# Used to measure timing on a specific part of the code.
class Measure:
    def __init__(self, text: str):
        self.text = text

    def __enter__(self):
        self._mo = _MeasureObject(self.text)
        return self._mo

    def __exit__(self, type, value, traceback):
        self._mo.finish()  
        