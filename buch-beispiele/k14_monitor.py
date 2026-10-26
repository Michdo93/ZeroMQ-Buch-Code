"""Socket monitoring: watch connection events of any socket.

get_monitor_socket() returns a PAIR socket on which libzmq reports events such
as CONNECTED, HANDSHAKE_SUCCEEDED, DISCONNECTED or CONNECT_RETRIED. Combined
with native heartbeats (ZMQ_HEARTBEAT_IVL / _TIMEOUT) a client notices a dead
server within seconds - even if no application message is in flight.
Run:  python k14_monitor.py
"""

import threading
import time

import zmq
from zmq.utils.monitor import recv_monitor_message

URL = "tcp://127.0.0.1:5667"

EVENT_NAMES = {getattr(zmq, name): name for name in dir(zmq) if name.startswith("EVENT_")}


def watch(monitor: zmq.Socket) -> None:
    t0 = time.time()
    while monitor.poll(4000):
        event = recv_monitor_message(monitor)
        name = EVENT_NAMES.get(event["event"], event["event"])
        print(f"  [{time.time() - t0:5.2f} s] {name:<28} {event['endpoint'].decode()}")
        if event["event"] == zmq.EVENT_MONITOR_STOPPED:
            break
    monitor.close()


ctx = zmq.Context()

client = ctx.socket(zmq.DEALER)
client.setsockopt(zmq.HEARTBEAT_IVL, 500)       # send a ZMTP PING every 500 ms
client.setsockopt(zmq.HEARTBEAT_TIMEOUT, 1500)  # no traffic for 1.5 s -> peer is dead
client.setsockopt(zmq.RECONNECT_IVL, 500)
monitor = client.get_monitor_socket()
watcher = threading.Thread(target=watch, args=(monitor,))
watcher.start()

client.connect(URL)  # server not running yet -> connect retries
time.sleep(1.2)

server = ctx.socket(zmq.ROUTER)
server.bind(URL)
print("server started")
time.sleep(1.0)

server.close(linger=0)
print("server stopped")
time.sleep(2.5)

client.disable_monitor()
watcher.join()
client.close(linger=0)
ctx.term()
