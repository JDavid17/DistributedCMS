from DHT.settings import *
import hashlib

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

def hash(s):
    return hashlib.sha1(s.encode('utf-8')).hexdigest()[:int(M/4)]

class ChordKey:
    def __init__(self, ip, port):
        self.id = hashlib.sha1(str(ip + ":" + str(port)).encode('utf-8')).hexdigest()[:int(M/4)]
        self.ip = ip
        self.port = port

    def __str__(self):
        return "({}, {}, {})".format(self.id, self.ip, self.port)

    def __repr__(self):
        return self.id