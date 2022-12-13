#Snaildash is a small game created in the scope of a school project
#Copyright (C) 2022  Louis HEREDERO & Mathéo BENEY

import string

abc = string.digits + string.ascii_uppercase

def toBase(n, base=10):
    """Converts an integer to the given base

    Args:
        n (int): number to convert
        base (int, optional): new base. Defaults to 10.

    Returns:
        str: converted number
    """
    
    if n < base:
        return abc[n]
    
    return toBase(n//base, base) + abc[n%base]

def fromBase(s, base=10):
    """Converts a number from the given base

    Args:
        s (str): number in the base
        base (int, optional): base. Defaults to 10.

    Returns:
        int: converted integer
    """
    
    s = s.upper()
    if len(s) == 1:
        return abc.index(s)
    
    return base*fromBase(s[:-1], base) + abc.index(s[-1])