from ckey import hash
from network import ping
import Pyro4


def set_to_dht(uri, data):
    try:
        with Pyro4.Proxy(uri) as obj:
            print("Succesfuly connected to node, through URI: {}".format(uri))
            obj.set(hash(data['key']), data['data'])
    except Pyro4.errors.CommunicationError:
        print("Unable to Connect to node in URI: {}".format(uri))

def get_to_dht(key, uri):
    try:
        with Pyro4.Proxy(uri) as obj:
            obj.get(hash(key))
    except Pyro4.errors.CommunicationError:
        print("Unable to Connect to node in URI: {}".format(uri))

def get_all(uri):
    try:
        with Pyro4.Proxy(uri) as obj:
            print("Connected")
            return obj.get_all()
            # custom_successors(obj.node)
    except Pyro4.errors.CommunicationError:
        print("Unable to Connect to node in URI: {}".format(uri))


# def custom_successors(node):
#     print("Enter for loop")
#     for suc in node.successors:
#         if ping(suc):
#             print("Successor found with id: {} through ip: {} and port: {}".format(suc.id, suc.ip, suc.port))
#         else:
#             print("Successor {} lost in battle".format(suc))