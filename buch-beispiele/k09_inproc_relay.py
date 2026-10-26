"""Thread coordination with PAIR sockets over inproc:// ("relay race").

Instead of locks, events or condition variables, threads signal each other
with messages. Each step waits for the previous one and passes on the baton.
This is the zguide "mtrelay" idea - it scales to any message-driven design.
Run:  python k09_inproc_relay.py
"""

import threading
import time

import zmq


def step1(ctx: zmq.Context) -> None:
    out = ctx.socket(zmq.PAIR)
    out.connect("inproc://step2")
    print("step 1: loading configuration ...")
    time.sleep(0.3)
    out.send(b"config loaded")
    out.close()


def step2(ctx: zmq.Context) -> None:
    inp = ctx.socket(zmq.PAIR)
    inp.bind("inproc://step2")
    threading.Thread(target=step1, args=(ctx,)).start()
    print("step 2: waiting for step 1")
    print("step 2: got", inp.recv())
    time.sleep(0.3)
    out = ctx.socket(zmq.PAIR)
    out.connect("inproc://step3")
    out.send(b"hardware ready")
    inp.close()
    out.close()


def main() -> None:
    ctx = zmq.Context.instance()
    inp = ctx.socket(zmq.PAIR)
    inp.bind("inproc://step3")
    threading.Thread(target=step2, args=(ctx,)).start()
    print("main  : waiting for step 2")
    print("main  : got", inp.recv(), "-> start service")
    inp.close()
    ctx.term()


if __name__ == "__main__":
    main()
