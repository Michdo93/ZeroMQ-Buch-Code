"""Pub-Sub "last message only": ZMQ_CONFLATE.

A fast sensor publishes 100 values per second, a slow consumer needs 0.5 s
per value. Without CONFLATE the consumer works through an ever older backlog;
with CONFLATE it always gets the most recent value.
CONFLATE keeps exactly one message per socket and does NOT support
multipart messages.
Run:  python k06_conflate.py
"""

import threading
import time

import zmq

URL = "tcp://127.0.0.1:5663"


def publisher(stop: threading.Event) -> None:
    pub = zmq.Context.instance().socket(zmq.PUB)
    pub.bind(URL)
    i = 0
    while not stop.is_set():
        pub.send_string(f"{i} {time.time():.3f}")
        i += 1
        time.sleep(0.01)  # 100 Hz
    pub.close(linger=0)


def consumer(conflate: bool) -> None:
    sub = zmq.Context.instance().socket(zmq.SUB)
    if conflate:
        sub.setsockopt(zmq.CONFLATE, 1)  # must be set BEFORE connect
    sub.setsockopt(zmq.SUBSCRIBE, b"")
    sub.connect(URL)
    time.sleep(0.3)
    for _ in range(4):
        seq, ts = sub.recv_string().split()
        print(f"  conflate={conflate!s:<5} value #{seq:>4}  age {1000 * (time.time() - float(ts)):6.0f} ms")
        time.sleep(0.5)  # slow processing
    sub.close(linger=0)


stop = threading.Event()
threading.Thread(target=publisher, args=(stop,), daemon=True).start()
time.sleep(0.2)
consumer(conflate=False)
consumer(conflate=True)
stop.set()
time.sleep(0.1)
zmq.Context.instance().term()
