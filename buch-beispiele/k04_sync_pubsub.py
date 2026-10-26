"""Slow joiner solved: synchronise PUB and SUB before sending.

The publisher waits until N subscribers have reported "ready" via a separate
REQ/REP channel. Only then it starts publishing - no message gets lost.
Run:  python k04_sync_pubsub.py
"""

import threading
import time

import zmq

PUB_URL = "tcp://127.0.0.1:5661"
SYNC_URL = "tcp://127.0.0.1:5662"
SUBSCRIBERS = 3
MESSAGES = 1000


def subscriber(ctx: zmq.Context, name: str, results: dict) -> None:
    sub = ctx.socket(zmq.SUB)
    sub.connect(PUB_URL)
    sub.setsockopt(zmq.SUBSCRIBE, b"")
    # The subscription travels asynchronously to the publisher. A short wait
    # makes sure it has arrived before we announce "ready".
    time.sleep(0.2)
    sync = ctx.socket(zmq.REQ)
    sync.connect(SYNC_URL)
    sync.send(b"ready")
    sync.recv()
    count = 0
    while sub.recv() != b"END":
        count += 1
    results[name] = count
    sub.close()
    sync.close()


def main() -> None:
    ctx = zmq.Context()
    pub = ctx.socket(zmq.PUB)
    # Default SNDHWM is 1000: a burst of 1001 messages would make PUB silently
    # DROP the rest - including our END marker. 0 = no limit for this demo.
    pub.setsockopt(zmq.SNDHWM, 0)
    pub.bind(PUB_URL)
    sync = ctx.socket(zmq.REP)
    sync.bind(SYNC_URL)

    results = {}
    threads = [threading.Thread(target=subscriber, args=(ctx, f"sub-{i}", results)) for i in range(SUBSCRIBERS)]
    for t in threads:
        t.start()

    for _ in range(SUBSCRIBERS):  # wait for all "ready" messages
        sync.recv()
        sync.send(b"")
    for i in range(MESSAGES):
        pub.send(f"update {i}".encode())
    pub.send(b"END")

    for t in threads:
        t.join()
    print(f"sent {MESSAGES}, received: {results}")
    pub.close()
    sync.close()
    ctx.term()


if __name__ == "__main__":
    main()
