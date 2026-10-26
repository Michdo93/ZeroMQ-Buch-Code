"""MQTT-like QoS built on ZeroMQ: acknowledgements, retransmission, dedup.

QoS 1 ("at least once")  = sequence number + ACK + retransmit on timeout
QoS 2 ("exactly once")   = QoS 1 + duplicate detection on the receiver

The sender (DEALER) keeps every unacknowledged message in `pending` and
retransmits after ACK_TIMEOUT. The receiver (ROUTER) acknowledges each
sequence number and remembers which ones it has already processed, so a
retransmitted duplicate is acknowledged again but not processed twice.

To prove that it works, the receiver deliberately "loses" 30 % of all ACKs.
Run:  python k19_reliable_delivery.py
"""

import json
import random
import threading
import time

import zmq

URL = "tcp://127.0.0.1:5668"
ACK_TIMEOUT = 0.2
MESSAGES = 50


def receiver(stop: threading.Event, stats: dict) -> None:
    sock = zmq.Context.instance().socket(zmq.ROUTER)
    sock.bind(URL)
    seen = set()  # processed sequence numbers (per sender in real life)
    while not stop.is_set():
        if not sock.poll(100):
            continue
        identity, raw = sock.recv_multipart()
        msg = json.loads(raw)
        if msg["seq"] in seen:
            stats["duplicates"] += 1  # QoS 2: do not process again ...
        else:
            seen.add(msg["seq"])
            stats["processed"] += 1   # ... business logic would run here
        if random.random() < 0.3:
            stats["acks_lost"] += 1   # simulate a lost ACK
            continue
        sock.send_multipart([identity, json.dumps({"ack": msg["seq"]}).encode()])
    sock.close(linger=0)


class ReliableSender:
    def __init__(self, url: str):
        self.sock = zmq.Context.instance().socket(zmq.DEALER)
        self.sock.connect(url)
        self.next_seq = 0
        self.pending = {}  # seq -> (message bytes, last send time)
        self.retransmissions = 0

    def send(self, payload: dict) -> None:
        raw = json.dumps({"seq": self.next_seq, "payload": payload}).encode()
        self.pending[self.next_seq] = (raw, time.time())
        self.sock.send(raw)
        self.next_seq += 1

    def service(self, timeout: float = 0.05) -> None:
        """Process ACKs and retransmit everything that timed out."""
        while self.sock.poll(int(timeout * 1000)):
            ack = json.loads(self.sock.recv())["ack"]
            self.pending.pop(ack, None)
        now = time.time()
        for seq, (raw, sent_at) in list(self.pending.items()):
            if now - sent_at > ACK_TIMEOUT:
                self.sock.send(raw)
                self.pending[seq] = (raw, now)
                self.retransmissions += 1

    def close(self) -> None:
        self.sock.close(linger=0)


def main() -> None:
    random.seed(1)
    stop = threading.Event()
    stats = {"processed": 0, "duplicates": 0, "acks_lost": 0}
    rx = threading.Thread(target=receiver, args=(stop, stats))
    rx.start()

    sender = ReliableSender(URL)
    for i in range(MESSAGES):
        sender.send({"switch": "light", "state": i % 2})
        sender.service(timeout=0.005)
    deadline = time.time() + 10
    while sender.pending and time.time() < deadline:
        sender.service()

    stop.set()
    rx.join()
    print(f"sent {MESSAGES} messages, still unacknowledged: {len(sender.pending)}")
    print(f"retransmissions: {sender.retransmissions}, ACKs lost: {stats['acks_lost']}")
    print(f"processed exactly once: {stats['processed']}, duplicates discarded: {stats['duplicates']}")
    sender.close()
    zmq.Context.instance().term()


if __name__ == "__main__":
    main()
