
def sumHexInt(hex, integer):
    return int(hex, 16) + integer

def intToKey(x, M):        
    return format(x, '0>{}x'.format(int(M/4)))

def betweenclosedclosed(x, l, r):
    e1 = int(l, 16) < int(x, 16) < int(r, 16)
    e2 = int(x, 16) < int(r, 16) or int(x, 16) > int(l, 16)
    return e1 if int(r, 16) >= int(l, 16) else e2 

def betweenclosedopen(x, l, r):
    e1 = int(l, 16) < int(x, 16) <= int(r, 16)
    e2 = int(x, 16) <= int(r, 16) or int(x, 16) > int(l, 16)
    return e1 if int(r, 16) >= int(l, 16) else e2 