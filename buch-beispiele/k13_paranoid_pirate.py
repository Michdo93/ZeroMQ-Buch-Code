"""Heartbeating between broker and workers (simplified "Paranoid Pirate").

Problem: a load-balancing broker keeps a list of idle workers. If a worker
process crashes or its host loses power, the broker would happily keep
sending jobs into the void.

Solution: broker and workers exchange small HEARTBEAT messages. A worker
that stays silent for LIVENESS * INTERVAL is considered dead and removed;
a worker that loses its broker reconnects with exponential back-off.

This compact demo starts a broker and three workers as threads, kills one
worker after two seconds and shows how the broker reacts.
Run:  python k13_paranoid_pirate.py
"""

import threading
import time
from collections import OrderedDict

import zmq

BACKEND = "inproc://workers"
HEARTBEAT = b"\x01"
READY = b"\x02"
INTERVAL = 0.5  # seconds between heartbeats
LIVENESS = 3    # missed heartbeats until "dead"


def broker(stop: threading.Event) -> None:
    sock = zmq.Context.instance().socket(zmq.ROUTER)
    sock.bind(BACKEND)
    workers = OrderedDict()  # identity -> expiry time
    next_beat = time.time() + INTERVAL
    while not stop.is_set():
        if sock.poll(int(INTERVAL * 1000)):
            identity, msg = sock.recv_multipart()
            if identity not in workers:
                print(f"[broker] worker {identity.decode()} joined")
            workers[identity] = time.time() + INTERVAL * LIVENESS
        now = time.time()
        if now >= next_beat:
            for identity in workers:
                sock.send_multipart([identity, HEARTBEAT])
            next_beat = now + INTERVAL
        for identity, expiry in list(workers.items()):
            if expiry < now:
                print(f"[broker] worker {identity.decode()} missed {LIVENESS} heartbeats -> removed")
                del workers[identity]
    print(f"[broker] alive at the end: {[w.decode() for w in workers]}")
    sock.close(linger=0)


def worker(name: str, crash_after: float, stop: threading.Event) -> None:
    sock = zmq.Context.instance().socket(zmq.DEALER)
    sock.setsockopt_string(zmq.IDENTITY, name)
    sock.connect(BACKEND)
    sock.send(READY)
    start = time.time()
    while not stop.is_set():
        if crash_after and time.time() - start > crash_after:
            print(f"[{name}] *** simulated crash (no goodbye, no heartbeats) ***")
            break
        if sock.poll(int(INTERVAL * 1000)):
            sock.recv()  # heartbeat (or job) from the broker
        sock.send(HEARTBEAT)
    sock.close(linger=0)


def main() -> None:
    stop = threading.Event()
    threads = [threading.Thread(target=broker, args=(stop,))]
    threads += [threading.Thread(target=worker, args=(f"w{i}", 2.0 if i == 2 else 0, stop)) for i in range(1, 4)]
    for t in threads:
        t.start()
    time.sleep(5)
    stop.set()
    for t in threads:
        t.join()
    zmq.Context.instance().term()


if __name__ == "__main__":
    main()
