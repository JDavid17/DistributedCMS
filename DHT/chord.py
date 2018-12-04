from ckey import *
from settings import *
from network import *
from log import *
import Pyro4 
import threading


@Pyro4.expose
class ChordNode:
    def __init__(self, ip, port):

        self.next = -1
        self.finger = [None for i in range(M)]
        #TODO: Implement a separate class for chord id
        self._key = ChordKey(ip, port)
        self._successors = [None]
        self._predecessor = None
        self._running = False


    @property
    def key(self):
        return self._key

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
                log("Node {} is gone".format(suc))
        log("No successor was found for Node " + self.id)

    def find_successor(self, key):
        n = self.find_predecessor(key)
        return remote(n).successor()

    def find_predecessor(self, key):
        if self.id == self._successors[0].id:
            return self.key
        currentNode = self.key
        while True:
            with remote(currentNode) as n:
                if betweenclosedopen(key, n.id, n.successor().id): 
                    break
                currentNode = n.closest_preceding_node(key)
        return currentNode

    def closest_preceding_node(self, key):
        for i in range(len(self.finger)-1, 0, -1):
            if self.finger[i] and betweenclosedclosed(self.finger[i].id, self.id, key):
                return self.finger[i]
        return self.successor() if betweenclosedclosed(self.successor().id, self.id, key) else self.key

    def notify(self, predKey):
        if self.predecessor == None or betweenclosedclosed(predKey.id, self.predecessor.id, self.id) or not ping(self.predecessor):
            self.predecessor = predKey


    @repeat_wait(STABILIZE_WAIT)
    def stabilize(self):
        # log("+++ Stabilizing")
        # log_node(self)

        suc = self.successor()
        # log("current successor: ", str(suc))
        newsuclist = [suc]

        with remote(suc) as successorNode:
            x = successorNode.predecessor
            if self._successors[0].id == successorNode.id and betweenclosedclosed(x.id, self.id, successorNode.id): 
                newsuclist = [x]
            with remote(newsuclist[0]) as newSuccessor:
                newSuccessor.notify(self.key)

        # log("updating successors list")
        if self.id != self.successor().id:
            newsuclist += remote(newsuclist[0]).successors[:N_SUCCESSORS-1]
            self._successors = newsuclist
        # log("successorlist: ", self.successors, "\n")

    @repeat_wait(FFINGERS_WAIT)
    def fix_fingers(self):
        self.next = self.next + 1
        if self.next >= M:
            self.next = 0
        self.finger[self.next] = self.find_successor(intToKey(sumHexInt(self.id, 2**self.next) % 2**M, M))


    def start(self):
        if not self.running:
            self._running = True
            
            t = threading.Thread(target=self.fix_fingers)
            t.daemon = True
            t.start()

            t = threading.Thread(target=self.stabilize)
            t.daemon = True
            t.start()


    def shutdown(self):
        pass


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


# # TESTS
# 10000 #2
# 11028 #7
# 11528 #8
# 11021 #e
# 22220 #0