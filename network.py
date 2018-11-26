import Pyro4
from settings import *

def ping(nsname):
    try:
        with Pyro4.Proxy("PYRONAME:" + nsname) as node:
            node.id 
    except Pyro4.errors.CommunicationError:
        if not reconnected(node):
            return False
    return True

def reconnected(proxy):
    # If cant create a proxy then it might be a temporary network error
    try: 
        proxy._pyroReconnect(CON_RETRIES) # Try to reconnect
    except Pyro4.errors.ConnectionClosedError:
        # If after 3 attemps the successor is still unreachable then node is disconnected
        return False
    return True

def remote(name):
    s = Pyro4.Proxy("PYRONAME:" + name)
    if not ping:
        raise Pyro4.errors.CommunicationError
    return s