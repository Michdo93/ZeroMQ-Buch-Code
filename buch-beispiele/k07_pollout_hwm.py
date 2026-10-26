"""POLLIN, POLLOUT, NOBLOCK and the high-water mark (HWM).

A PUSH socket without connected peer (or whose peers are full) cannot send:
  * send()                 would block forever
  * send(flags=NOBLOCK)    raises zmq.Again
  * poll(POLLOUT)          tells us beforehand whether sending is possible

The HWM limits the number of messages ZeroMQ queues per peer. With inproc://
the limit is exact (SNDHWM + RCVHWM). With tcp:// the kernel's socket buffers
come on top - for tiny messages that can be hundreds of thousands more.
Run:  python k07_pollout_hwm.py
"""

import time

import zmq


def fill_and_drain(transport: str) -> None:
    ctx = zmq.Context()
    push = ctx.socket(zmq.PUSH)
    push.setsockopt(zmq.SNDHWM, 5)
    push.bind(transport)

    writable = bool(push.poll(100, zmq.POLLOUT))
    try:
        push.send(b"x", flags=zmq.NOBLOCK)
        blocked = False
    except zmq.Again:
        blocked = True
    print(f"{transport:<26} no peer: POLLOUT={writable}, send(NOBLOCK) raised zmq.Again={blocked}")

    pull = ctx.socket(zmq.PULL)
    pull.setsockopt(zmq.RCVHWM, 5)
    pull.connect(transport)
    time.sleep(0.2)

    sent = 0
    while push.poll(100, zmq.POLLOUT):  # send until all queues are full
        push.send(b"x" * 10, flags=zmq.NOBLOCK)
        sent += 1
    received = 0
    while pull.poll(100, zmq.POLLIN):
        pull.recv()
        received += 1
    print(f"{'':<26} peer never reads: {sent} messages fit in, {received} drained,"
          f" writable again: {bool(push.poll(100, zmq.POLLOUT))}")
    push.close(linger=0)
    pull.close(linger=0)
    ctx.term()


fill_and_drain("inproc://hwm-demo")
fill_and_drain("tcp://127.0.0.1:5664")
