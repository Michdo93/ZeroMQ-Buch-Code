"""Last Value Cache (LVC) proxy - "retained messages" for ZeroMQ PUB/SUB.

The proxy remembers the last message of every topic. When a NEW subscriber
subscribes to a topic, the XPUB socket reports the subscription (b"\\x01topic")
and the proxy immediately sends the cached value. A late joiner therefore
knows the current state at once - the ZeroMQ equivalent of MQTT's
"retained" flag.

XPUB_VERBOSE=1 forwards every subscription, not only the first one per topic,
so the second, third, ... subscriber also gets the cached value.
Run:  python k11_lvc_proxy.py
"""

import threading
import time

import zmq

FRONT = "tcp://127.0.0.1:5665"  # publishers connect
BACK = "tcp://127.0.0.1:5666"   # subscribers connect


def lvc_proxy(stop: threading.Event) -> None:
    ctx = zmq.Context.instance()
    xsub = ctx.socket(zmq.XSUB)
    xpub = ctx.socket(zmq.XPUB)
    xpub.setsockopt(zmq.XPUB_VERBOSE, 1)
    xsub.bind(FRONT)
    xpub.bind(BACK)
    xsub.send(b"\x01")  # XSUB: subscribe to everything from the publishers
    cache = {}
    poller = zmq.Poller()
    poller.register(xsub, zmq.POLLIN)
    poller.register(xpub, zmq.POLLIN)
    while not stop.is_set():
        events = dict(poller.poll(100))
        if xsub in events:
            topic, value = xsub.recv_multipart()
            cache[topic] = value
            xpub.send_multipart([topic, value])
        if xpub in events:
            event = xpub.recv()
            if event[0] == 1:  # subscription
                topic = event[1:]
                for cached_topic, value in cache.items():
                    if cached_topic.startswith(topic):
                        xpub.send_multipart([cached_topic, value])
    xsub.close(linger=0)
    xpub.close(linger=0)


def main() -> None:
    stop = threading.Event()
    threading.Thread(target=lvc_proxy, args=(stop,)).start()
    ctx = zmq.Context.instance()

    pub = ctx.socket(zmq.PUB)
    pub.connect(FRONT)
    time.sleep(0.3)
    pub.send_multipart([b"livingroom/light", b"ON"])
    pub.send_multipart([b"livingroom/temperature", b"21.5"])
    pub.send_multipart([b"kitchen/window", b"OPEN"])
    time.sleep(0.3)

    # A subscriber that starts AFTER the values were published:
    late = ctx.socket(zmq.SUB)
    late.connect(BACK)
    late.setsockopt(zmq.SUBSCRIBE, b"livingroom/")
    while late.poll(500):
        print("late subscriber got retained value:", late.recv_multipart())

    stop.set()
    time.sleep(0.2)
    pub.close(linger=0)
    late.close(linger=0)
    ctx.term()


if __name__ == "__main__":
    main()
