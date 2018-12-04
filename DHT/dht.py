from settings import DISTRIBUTE_WAIT
from network import remote, repeat_wait, ping
from ckey import ChordKey, betweenclosedopen, hash
from chord import ChordNode
from log import *
import Pyro4
import threading
import hashlib


class DHT:
    def __init__(self, ip, port, remoteIp=None, remotePort=None):
        self.Node = ChordNode(ip, port)
        self.Node.join(remoteIp, remotePort)
        self.data = {}
        self.isRunning = False

    @property
    @Pyro4.expose
    def database(self):
        return self.data

    @property
    @Pyro4.expose
    def node(self):
        return self.Node

    def start(self):
        if not self.isRunning:
            self.isRunning = True

            def converter(classname, dict):
                return ChordKey(dict['ip'], dict['port'])

            Pyro4.util.SerializerBase.register_dict_to_class("ckey.ChordKey", converter)

            t = threading.Thread(target=self.distribute_data)
            t.daemon = True
            t.start()

            def run(node):
                with Pyro4.Daemon(host=node.Node.key.ip, port=int(node.Node.key.port)) as daemon:
                    print(daemon.register(node.Node, objectId=node.Node.id))
                    print(daemon.register(node, objectId="DHT_" + node.Node.id))
                    print("daemon started for Node {} on {}:{}".format(node.Node.id, node.Node.key.ip, node.Node.key.port))
                    daemon.requestLoop()

            t = threading.Thread(target=run, args=(self,))
            t.daemon = True
            t.start()

    def shutdown(self):
        self.isRunning = False
        self.Node.shutdown()

    @Pyro4.expose
    def get(self, key):
        try:
            return self.data[key]
        except Exception:
            if betweenclosedopen(key, self.Node.predecessor.id, self.Node.id):
                # We dont have the data yet
                return None
            succ = self.Node.find_successor(key)        # *****
            with remote(succ, isDHT=True) as succDHT:   # *****
                return succDHT.get(key)                 # *****

    @Pyro4.expose
    def get_all(self, tipo):
        # Returns all data store in every DHT node
        return_data = {}

        for suc in self.Node.successors:
            if ping(suc):
                with remote(suc, isDHT=True) as succDHT:
                    for item in succDHT.database:
                        if not return_data.__contains__(succDHT.database[item]['key']) and succDHT.database[item]['type'] == tipo:
                            return_data[item] = succDHT.database[item]

            else:
                print("Lost Node {}".format(suc))

        print(return_data)
        return return_data

    @Pyro4.expose
    def set(self, key, val):
        # Data will eventually be forwarded to the correct DHT peer if its not the local one
        self.data[key] = val

    @repeat_wait(DISTRIBUTE_WAIT)
    def distribute_data(self):
        to_remove = []
        keys = self.data.keys()
        for key in keys:
            if not betweenclosedopen(key, self.Node.predecessor.id, self.Node.id):
                succ = self.Node.find_successor(key)        # ***** Needs error handling ???
                with remote(succ, isDHT=True) as succDHT:   # *****
                    succDHT.set(key, self.data[key])        # *****

                to_remove.append(key)
                log("migrated key {} to node {}".format(key, succ.id))

        # Remove migrated data
        for key in to_remove:
            del self.data[key]


if __name__ == "__main__":
    host = "localhost"
    port = input()

    rhost = host
    rport = input()
    if rport == "":
        rport = None

    d = DHT(host, port, rhost, rport)
    d.start()

    while True:
        cmd = input("-")
        l = cmd.split()
        if l[0] == "join":
            d.Node.join("localhost", l[1])
        if l[0] == "set":
            log(d.set(hash(l[1]), l[2]))
        if l[0] == "get":
            log(d.get(hash(l[1])))
        if l[0] == "get_all_page":
            log(d.get_all('page'))
        if l[0] == "get_all_widget":
            log(d.get(hash('widget')))
        if cmd == "":
            break
