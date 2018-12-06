from settings import DISTRIBUTE_WAIT, REPLICATE_WAIT, CHECK_REP_WAIT
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
        self.rep_data = {}
        self.isRunning = False

    @property
    @Pyro4.expose
    def database(self):
        return self.data

    @property
    @Pyro4.expose
    def replicas(self):
        return self.rep_data

    def start(self):
        if not self.isRunning:
            self.isRunning = True

            def converter(classname, dict):
                return ChordKey(dict['ip'], dict['port'])

            Pyro4.util.SerializerBase.register_dict_to_class("ckey.ChordKey", converter)

            t = threading.Thread(target=self.distribute_data)
            t.daemon = True
            t.start()

            t = threading.Thread(target=self.replicate_data)
            t.daemon = True
            t.start()

            t = threading.Thread(target=self.check_replicas)
            t.daemon = True
            t.start()

            def run(node):
                with Pyro4.Daemon(host=node.Node.key.ip, port=int(node.Node.key.port)) as daemon:
                    print(daemon.register(node.Node, objectId=node.Node.id))
                    print(daemon.register(node, objectId="DHT_" + node.Node.id))
                    print("daemon started for Node {} on {}:{}".format(node.Node.id, node.Node.key.ip,
                                                                       node.Node.key.port))
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
            succ = self.Node.find_successor(key)  # *****
            with remote(succ, isDHT=True) as succDHT:  # *****
                return succDHT.get(key)  # *****

    @Pyro4.expose
    def get_all(self, tipo):
        # Returns all data store in every DHT node
        return_data = {}
        succ = self.Node
        with remote(succ, isDHT=True) as succDHT:
            for item in succDHT.database:
                if not return_data.__contains__(succDHT.database[item]['key']) and succDHT.database[item]['type'] == tipo:
                    return_data[item] = succDHT.database[item]

        succ = self.Node.find_successor()

        while succ.id != self.Node.id:
            if ping(succ):
                with remote(suc, isDHT=True) as succDHT:
                    for item in succDHT.database:
                        if not return_data.__contains__(succDHT.database[item]['key']) and succDHT.database[item]['type'] == tipo:
                            return_data[item] = succDHT.database[item]
                succ = succDHT.Node
            else:
                log("Lost Node {}".format(suc))

        return return_data

    @Pyro4.expose
    def set(self, key, val):
        # Check if its a write on a replica
        with remote(self.Node.predecessor, isDHT=False) as pred:
            if betweenclosedopen(key, pred.predecessor.id, self.Node.predecessor.id):
                self.rep_data[key] = val
                with remote(self.Node.predecessor, isDHT=True) as pred:
                    pred.set(key, val)
            else:
                # Data will eventually be forwarded to the correct DHT peer if its not the local one
                self.data[key] = val

    @Pyro4.expose
    def take_replica(self, key, value):
        self.rep_data[key] = value

    @repeat_wait(DISTRIBUTE_WAIT)
    def distribute_data(self):
        if not self.Node.running or self.Node.id == self.Node.successor():
            # No need to migrate data if the system has 1 Node or hasn't started
            return

        to_remove = []
        keys = self.data.keys()
        for key in keys:
            if not betweenclosedopen(key, self.Node.predecessor.id, self.Node.id):
                succ = self.Node.find_successor(key)  # ***** Needs error handling ???
                with remote(succ, isDHT=True) as succDHT:  # *****
                    succDHT.set(key, self.data[key])  # *****

                to_remove.append(key)
                log("migrated key {} to node {}".format(key, succ.id))

        # Remove migrated data
        for key in to_remove:
            del self.data[key]

    @repeat_wait(REPLICATE_WAIT)
    def replicate_data(self):
        if not self.Node.running or self.Node.id == self.Node.successor():
            # Do not replicate if the system has 1 Node or hasn't started
            return

        to_replicate = self.data
        for key in to_replicate.keys():
            if betweenclosedopen(key, self.Node.predecessor.id, self.Node.id):
                with remote(self.Node.successor(),
                            isDHT=True) as succ:  # Push replicas to multiple successors ? 2 replicas enough ?
                    succ.take_replica(key, to_replicate[key])

    @repeat_wait(CHECK_REP_WAIT)
    def check_replicas(self):
        if not self.Node.running:
            return

        replicated_data = self.rep_data
        to_remove = []
        for key in replicated_data.keys():
            # Check if we must take over this replica in case the owner left the system
            if betweenclosedopen(key, self.Node.predecessor.id, self.Node.id):
                # We are now responsible for this data
                self.data[key] = replicated_data[key]
                to_remove.append(key)

            # Check if we can clean up this replica
            with remote(self.Node.predecessor, isDHT=False) as pred:
                if not betweenclosedopen(key, pred.predecessor.id, self.Node.predecessor.id):
                    # We no longer have to keep this replica
                    if not to_remove.__contains__(key):
                        to_remove.append(key)

        for key in to_remove:
            del self.rep_data[key]


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
        if l[0] == "get_history":
            log(d.Node.history)
        if cmd == "":
            break
