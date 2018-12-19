from dht import *
from chord import *
import Pyro4


def set_to_dht(uri, key, data):
    try:
        with Pyro4.Proxy(uri) as obj:
            obj.set(hash(key), data)
            print("Succesfuly connected to node, through URI: {}".format(uri))
    except Pyro4.errors.CommunicationError:
        print("Unable to Connect to DHT through URI: {}".format(uri))

def get_to_dht(key, uri):
    try:
        with Pyro4.Proxy(uri) as obj:
            obj.get(hash(key))
    except Pyro4.errors.CommunicationError:
        print("Unable to Connect to DHT through URI: {}".format(uri))

def get_all(uri, type):
    try:
        with Pyro4.Proxy(uri) as obj:
            # print("Connected")
            return obj.get_all(type)
            # custom_successors(obj.node)
    except Pyro4.errors.CommunicationError:
        print("Unable to Connect to DHT through URI: {}".format(uri))


# def custom_successors(node):
#     print("Enter for loop")
#     for suc in node.successors:
#         if ping(suc):
#             print("Successor found with id: {} through ip: {} and port: {}".format(suc.id, suc.ip, suc.port))
#         else:
#             print("Successor {} lost in battle".format(suc))
