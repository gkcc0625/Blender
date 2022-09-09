import bpy

def isEqualZero( val, decimal_points = 5 ):
    ''' Returns True if val equale to zero when
        rounded by the provided number of decimal_points
    '''
    return round(val, decimal_points) == 0