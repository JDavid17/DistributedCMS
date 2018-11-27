import Pyro4
import threading
import hashlib
import time
from ckey import *
from settings import *
from network import *


def repeat_wait(waitTime):
    def decorator(func):
        def inner(self, *args, **kwargs):
            while True:
                try:
                    func(self, *args, **kwargs)
                except Exception:
                    pass
                time.sleep(waitTime)
            return

        return inner

    return decorator


@Pyro4.expose
class Chord:
    def __init__(self, ip, port):

        self.next = -1
        self.finger = [None for i in range(M)]
        # TODO: Implement a separate class for chord id
        self._id = hashlib.sha1(str(ip + ":" + str(port)).encode('utf-8')).hexdigest()[:int(M / 4)]
        self._successors = [""]
        self._predecessor = ""
        self._running = False

    @property
    def id(self):
        return self._id

    @id.setter
    def id(self, value):
        self._id = value

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

    def get(self, key):
        if betweenclosedopen(key, self.predecessor, self.id):
            # Return the stored value corresponding to key
            pass
        return remote(self.find_successor(key)).get(key)

    def set(self, key, value):
        if betweenclosedopen(key, self.predecessor, self.id):
            # Store the value corresponding to key
            pass
        return remote(self.find_successor(key)).set(key)

    def join(self, node=None):
        if not node:
            self._successors[0] = self.predecessor = self.id
        else:
            with remote(node) as gatewayNode:
                self.predecessor = None
                if gatewayNode.id == gatewayNode.successor():
                    self._successors[0] = node
                    self.predecessor = node
                    gatewayNode.successors = [self.id]
                    gatewayNode.predecessor = self.id

                    gatewayNode.start()
                else:
                    self._successors[0] = gatewayNode.find_successor(self.id)
            self.start()

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
        if self.id == self._successors[0]:
            return self.id
        currentNode = self.id
        while True:
            with remote(currentNode) as n:
                if betweenclosedopen(key, n.id, n.successor()):
                    break
                currentNode = n.closest_preceding_node(key)
        return currentNode

    def closest_preceding_node(self, key):
        for i in range(len(self.finger) - 1, 0, -1):
            if self.finger[i] and betweenclosedclosed(self.finger[i], self.id, key):
                return self.finger[i]
        return self.successor() if betweenclosedclosed(self.successor(), self.id, key) else self.id

    def notify(self, node):
        if self.predecessor is None or betweenclosedclosed(node, self.predecessor, self.id) or not ping(
                self.predecessor):
            self.predecessor = node

    @repeat_wait(STABILIZE_WAIT)
    def stabilize(self):
        log("+++ Stabilizing")
        log_node(self)

        suc = self.successor()
        log("current successor: ", suc)
        newsuclist = [suc]

        with remote(suc) as successorNode:
            x = successorNode.predecessor
            if self._successors[0] == successorNode.id and betweenclosedclosed(x, self.id, successorNode.id):
                newsuclist = [x]
            with remote(newsuclist[0]) as newSuccessor:
                newSuccessor.notify(self.id)

        if self.id != self.successor():
            newsuclist += remote(newsuclist[0]).successors[:N_SUCCESSORS - 1]
            self._successors = newsuclist
        log("successorlist: ", self.successors, "\n")

    @repeat_wait(FFINGERS_WAIT)
    def fix_fingers(self):
        self.next = self.next + 1
        if self.next >= M:
            self.next = 0
        self.finger[self.next] = self.find_successor(intToKey(sumHexInt(self.id, 2 ** self.next) % 2 ** M, M))

    def start(self):
        if not self.running:
            t = threading.Thread(target=self.fix_fingers)
            t.daemon = True
            t.start()

            t = threading.Thread(target=self.stabilize)
            t.daemon = True
            t.start()


def log(*args):
    print(*args)


def start_new_node(node, ip, port):
    with Pyro4.Daemon(host=host, port=int(port)) as daemon:
        uri = daemon.register(node)
        Pyro4.locateNS().register(node.id, uri)
        print("daemon started for Node " + node.id)
        daemon.requestLoop()


def log_node(node):
    print(
        "Node ID: {} Pred: {} Fingers: {} SucList: {}".format(node.id, node.predecessor, node.finger, node.successors))


if __name__ == "__main__":
    host = input("IP: ")
    port = input("Port: ")
    node = Chord(host, port)
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
            node.join(l[1])
            print("Joining node %s:" % l[1])

        # # TESTS
# 10000 #2
# 11028 #7
# 11528 #8
# 11021 #e
# 22220 #0
