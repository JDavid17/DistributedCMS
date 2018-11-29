from ckey import hash
import Pyro4


def set_to_dht(uri, data):
    try:
        with Pyro4.Proxy(uri) as obj:
            print("Succesfuly connected to node, through URI: {}".format(uri))
            obj.set(hash(data.key), data.data)
    except Pyro4.errors.CommunicationError:
        print("Unable to Connect to node in URI: {}".format(uri))

def get_to_dht(key):
    try:
        with Pyro4.Proxy(uri) as obj:
            obj.get(key)
    except Pyro4.errors.CommunicationError:
        print("Unable to Connect to node in URI: {}".format(uri))

def get_all():
    pass
