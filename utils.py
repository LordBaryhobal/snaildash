import string

abc = string.digits + string.ascii_uppercase

def toBase(n, base=10):
    if n < base:
        return abc[n]
    
    return toBase(n//base, base) + abc[n%base]

def fromBase(s, base=10):
    s = s.upper()
    if len(s) == 1:
        return abc.index(s)
    
    return base*fromBase(s[:-1], base) + abc.index(s[-1])