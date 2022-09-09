
#bunch of function i use for str a lot i guess?

import bpy 


aliens = ['/', '<', '>', ':', '"', '/', '\\', '|', '?', '*']


def is_illegal_string(string):
    """check if string has illegal char"""

    return any( (char in aliens) for char in string )

def legal(string):
    """make string legal"""

    if is_illegal_string(string):
        return ''.join(char for char in string if (not char in aliens) )
    return string 

def find_suffix(basename, collection_api, zeros=3,): 
    """find suffix with name that do not exists yet"""

    i = 1
    new = basename 
    while new in collection_api:
        suffix_idx = f"{i:03d}" if (zeros==3) else f"{i:02d}"
        new = f"{basename}.{suffix_idx}"
        i += 1

    return new 

def no_names_in_double( string, list_strings, startswith00=False, n=3,):
    """return a correct string with suffix to avoid doubles"""
    #used heavily in masks creation, to get correct names 
    #I Guess that this fct is a clone of find_suffix() ? 

    if startswith00: 
        #Always have suffix, startswith .00

        x=string
        i=0
        if string + ".00" not in list_strings:
            return string + ".00"

        while f"{x}.{i:02d}" in list_strings:
            i += 1

        return f"{x}.{i:02d}" 

    #else Normal Behavior
    x=string 
    i=1
    while x in list_strings:
        x = string + f".{i:03d}" if n==3 else string + f".{i:02d}"
        i +=1

    if string != x:
        return x

    return string 

def word_wrap( string="", layout=None, alignment="CENTER", max_char=70, active=False,):
    """word wrap a piece of string""" 
    
    addon_prefs = bpy.context.preferences.addons["Scatter5"].preferences 
    max_char = int(max_char*addon_prefs.ui_word_wrap_max_char_factor)
    scale_y = addon_prefs.ui_word_wrap_y
    
    def wrap(string,max_char):
        """word wrap function""" 

        newstring = ""
        
        while (len(string) > max_char):

            # find position of nearest whitespace char to the left of "width"
            marker = max_char - 1
            while (not string[marker].isspace()):
                marker = marker - 1

            # remove line from original string and add it to the new string
            newline = string[0:marker] + "\n"
            newstring = newstring + newline
            string = string[marker + 1:]
        
        return newstring + string
    
    #Multiline string? 
    if ("\n" in string):
          wrapped = "\n".join([wrap(l,max_char) for l in string.split("\n")])
    else: wrapped = wrap(string,max_char)

    #UI Layout Draw? 

    if (layout is not None):

        lbl = layout.column()
        lbl.active = active 
        lbl.scale_y = scale_y

        for l in wrapped.split("\n"):

            if alignment:
                line = lbl.row()
                line.alignment = alignment
                line.label(text=l)
                continue 

            lbl.label(text=l)
            continue
        
    return wrapped
