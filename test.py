import Pyro4
from ckey import *
import sys

sys.excepthook = Pyro4.util.excepthook

def converter(classname, dict):
    return ChordKey(dict['ip'], dict['port'])
Pyro4.util.SerializerBase.register_dict_to_class("ckey.ChordKey", converter)

host = "localhost"
port = "10000"

# print(Pyro4.Pr oxy("PYRO:DHT_2@localhost:10000").set(hash("h"), "100"))
print(Pyro4.Proxy("PYRO:DHT_2@localhost:10000").set(hash("h"), { "name": "Julio Maja", "edad": 40}))

# print(betweenclosedclosed("5", "7", "2"))