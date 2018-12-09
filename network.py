from settings import *
from ckey import *
import time
import Pyro4

def ping(key, isDHT=False):
    try:
        if isDHT:
            with Pyro4.Proxy("PYRO:DHT_{}@{}:{}".format(key.id, key.ip, key.port)) as node:
                node.database
        else:
            with Pyro4.Proxy("PYRO:{}@{}:{}".format(key.id, key.ip, key.port)) as node:
                node.id
    except Pyro4.errors.CommunicationError:
        if not reconnected(node):
            return False
    return True

def history_contains(id, history):
    for node in history:
        # print(node)
        if id == node.id:
            return True

    return False

def reconnected(proxy):
    # If cant create a proxy then it might be a temporary network error
    try:
        proxy._pyroReconnect(CON_RETRIES)  # Try to reconnect
    except Pyro4.errors.ConnectionClosedError:
        # If after 3 attemps the successor is still unreachable then node is disconnected
        return False
    return True


def remote(key, isDHT=False):
    if isDHT:
        s = Pyro4.Proxy("PYRO:DHT_{}@{}:{}".format(key.id, key.ip, key.port))
    else:
        s = Pyro4.Proxy("PYRO:{}@{}:{}".format(key.id, key.ip, key.port))
    if not ping(key, isDHT):
        raise Pyro4.errors.CommunicationError
    return s


def repeat_wait(waitTime):
    def decorator(func):
        def inner(self, *args, **kwargs):
            while True:
                if not self.running:
                    break
                try:
                    func(self, *args, **kwargs)
                except Pyro4.errors.CommunicationError:
                    pass
                time.sleep(waitTime)
        return inner

    return decorator
