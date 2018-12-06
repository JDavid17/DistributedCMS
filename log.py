def log(*args):
    print(*args)

def log_node(node):
    print("Node ID: {} Pred: {} Fingers: {} SucList: {}".format(node.id, node.predecessor, node.finger, node.successors))
