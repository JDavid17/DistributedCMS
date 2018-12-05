M = 4  # 2^M size of Chord ring

N_SUCCESSORS = 3  # Number of successors to keep track of

CON_RETRIES = 3  # Number of times to attemp a reconnection to a peer

STABILIZE_WAIT = .5  # Time to wait between each stabilization call (seconds)

FFINGERS_WAIT = .5  # Time to wait between each fix fingers call (seconds)

DISTRIBUTE_WAIT = 1  # Time to wait between each data distribution routine (seconds)

REPLICATE_WAIT = 1  # Time to wait between each data replication routine (seconds)

CHECK_REP_WAIT = 1  # Time to wait to check replicated data (seconds)

MERGE_WAIT = 1  # Time to wait to check for posible merge (seconds)
