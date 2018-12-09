from ckey import *
from settings import *
from network import *
from log import *
import Pyro4
import threading
import random
import time

@Pyro4.expose
class ChordNode:
    def __init__(self, ip, port):

        self.next = -1
        self.finger = [None for i in range(M)]
        # TODO: Implement a separate class for chord id'
        self._history = []
        self._key = ChordKey(ip, port)
        self._successors = [None]
        self._predecessor = None
        self._running = False

    @property
    def key(self):
        return self._key

    @property
    def history(self):
        return self._history

    @property
    def id(self):
        return self._key.id

    @property
    def successors(self):
        return self._successors

    @successors.setter
    def successors(self, value):
        self._successors = value

    @property
    def predecessor(self):
        return self._predecessor

    @predecessor.setter
    def predecessor(self, value):
        self._predecessor = value

    @property
    def running(self):
        return self._running

    def join(self, ip=None, port=None):
        self._running = False
        time.sleep(SHUTDOWN_WAIT)
        if not ip or not port:
            self._successors[0] = self.predecessor = self.key
        else:
            gwnodeKey = ChordKey(ip, port)
            try:
                with remote(gwnodeKey) as gatewayNode:
                    self.predecessor = None
                    if gatewayNode.id == gatewayNode.successor().id:
                        self._successors[0] = gwnodeKey
                        self.predecessor = gwnodeKey
                        gatewayNode.successors = [self.key]
                        gatewayNode.predecessor = self.key

                        gatewayNode.start()

                    else:
                        self._successors[0] = gatewayNode.find_successor(self.id)
                log("Joining Chord through node %s:" % gwnodeKey.id)
                self.start()
            except Pyro4.errors.CommunicationError:
                log("Unable to join Chord through node {}:{}".format(ip, port))

    def successor(self):
        for suc in self._successors:
            if ping(suc):
                return suc
            else:
                if not history_contains(suc.id, self.history):
                    if len(self.history) < 100:
                        self.history.append(suc)
                    else:
                        self.history.pop(random.randint(0, 99))
                        self.history.append(suc)
                # log("Node {} is gone".format(suc))
        log("No successor was found for Node " + self.id)
        raise Exception()

    def find_successor(self, key):
        n = self.find_predecessor(key)
        return remote(n).successor()

    def find_predecessor(self, key):
        if self.id == self._successors[0].id:
            return self.key

        currentNode = self.successor()
        if betweenclosedopen(key, self.id, currentNode.id):
            return self.key
        while currentNode.id != self.id:
            with remote(currentNode) as n:
                if betweenclosedopen(key, n.id, n.successor().id):
                    break
                currentNode = n.closest_preceding_node(key)
        return currentNode

    def closest_preceding_node(self, key):
        for i in range(len(self.finger) - 1, 0, -1):
            if self.finger[i] and betweenclosedclosed(self.finger[i].id, self.id, key):
                return self.finger[i]
        return self.successor() if betweenclosedclosed(self.successor().id, self.id, key) else self.key

    def notify(self, predKey):
        if self.predecessor is None or betweenclosedclosed(predKey.id, self.predecessor.id, self.id) or not ping(
                self.predecessor):
            self.predecessor = predKey

    def resolve_maxkey(self):
        suc = self.successor()
        maxkey = self.key
        while suc.id != self.id:
            with remote(suc) as succ:
                if int(succ.id, 16) > int(maxkey.id, 16):
                    maxkey = suc
                suc = succ.successor()
        return maxkey


    @repeat_wait(STABILIZE_WAIT)
    def stabilize(self):
        # log("+++ Stabilizing")
        log_node(self)

        suc = self.successor()
        # log("current successor: ", str(suc))
        newsuclist = [suc]

        with remote(suc) as successorNode:
            x = successorNode.predecessor
            if betweenclosedclosed(x.id, self.id, successorNode.id):
                newsuclist = [x]
            with remote(newsuclist[0]) as newSuccessor:
                # log("updating successors list")
                newsuclist += newSuccessor.successors[:N_SUCCESSORS - 1]
                self._successors = newsuclist
                # log("successorlist: ", self.successors, "\n")
                newSuccessor.notify(self.key)

                # Registser all the successors so we can merge if the system splits into partitions  
                for newnode in newsuclist:
                    if not history_contains(newnode.id, self.history):
                        if len(self.history) < 100:
                            self.history.append(newnode)
                        else:
                            self.history.pop(random.randint(0, 99))
                            self.history.append(newnode)


    @repeat_wait(MERGE_WAIT)
    def merge_ring(self):
        # print("Try to merge")
        for node in self.history:
            if node.id != self.id:
                # print("checkin node {}".format(node))
                if ping(node):
                    with remote(node) as chord_node:
                        chord_nodemx = chord_node.resolve_maxkey()
                        selfmx = self.resolve_maxkey()
                        if int(chord_nodemx.id, 16) == int(selfmx.id, 16):
                            # print("Same Ring returning")
                            return
                        else:
                            log("Found a peer from another chord ring: ", node.id)
                            if int(chord_nodemx.id, 16) > int(selfmx.id, 16):
                                with remote(selfmx) as obj:
                                    print("Joining the their ring through gateway {}:{}".format(chord_nodemx.ip, chord_nodemx.port))
                                    obj.join(chord_nodemx.ip, chord_nodemx.port)
                            else:
                                with remote(chord_nodemx) as obj:
                                    print("Making the peer join our ring through this address {}:{}".format(selfmx.ip, selfmx.port))
                                    obj.join(selfmx.ip, selfmx.port)


    @repeat_wait(FFINGERS_WAIT)
    def fix_fingers(self):
        # log("fixing fingers")
        self.next = self.next + 1
        if self.next >= M:
            self.next = 0
        self.finger[self.next] = self.find_successor(intToKey(sumHexInt(self.id, 2 ** self.next) % 2 ** M, M))

        # Register my fingers to the nodes history
        if not history_contains(self.finger[self.next].id, self.history):
            if len(self.history) < 100:
                self.history.append(self.finger[self.next])
            else:
                self.history.pop(random.randint(0, 99))
                self.history.append(self.finger[self.next])


    def start(self):
        if not self.running:
            self._running = True

            t = threading.Thread(target=self.fix_fingers)
            t.daemon = True
            t.start()

            t = threading.Thread(target=self.stabilize)
            t.daemon = True
            t.start()

            t = threading.Thread(target=self.merge_ring)
            t.daemon = True
            t.start()

    def shutdown(self):
        self._running = False


# TESTINGS
def start_new_node(node, ip, port):
    with Pyro4.Daemon(host=host, port=int(port)) as daemon:
        uri = daemon.register(node, objectId=node.id)
        log(str(uri))
        print("daemon started for Node " + node.id)
        daemon.requestLoop()


if __name__ == "__main__":
    def converter(classname, dict):
        return ChordKey(dict['ip'], dict['port'])


    Pyro4.util.SerializerBase.register_dict_to_class("ckey.ChordKey", converter)

    # host = input("IP: ")
    host = "localhost"
    port = input("Port: ")
    node = ChordNode(host, port)
    node.join()

    t = threading.Thread(target=start_new_node, args=(node, host, port))
    t.daemon = True
    t.start()

    while True:
        cmd = input("-")
        if cmd == "info":
            log_node(node)
        l = cmd.split()
        if l[0] == "join":
            node.join("localhost", l[1])
        if l[0] == "get_history":
            print(node.history)

# # TESTS
# 10000 #2
# 11028 #7
# 11528 #8
# 11021 #e
# 22220 #0
