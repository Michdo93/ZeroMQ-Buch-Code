"""Kapitel 18: Transporte, Nachrichtengröße und CURVE im Vergleich.

Misst Round-Trip-Latenz (REQ/REP) und Durchsatz (PUSH/PULL) für
inproc, ipc und tcp sowie tcp mit CURVE-Verschlüsselung.
Nur ein Richtwert - die Zahlen hängen stark von Rechner und Python ab.
"""

import statistics
import threading
import time

import zmq

ROUNDTRIPS = 2000
MESSAGES = 100_000


def make_pair(ctx, kind_a, kind_b, endpoint, curve):
    a, b = ctx.socket(kind_a), ctx.socket(kind_b)
    if curve:
        server_pub, server_sec = zmq.curve_keypair()
        client_pub, client_sec = zmq.curve_keypair()
        a.curve_server, a.curve_secretkey, a.curve_publickey = True, server_sec, server_pub
        b.curve_serverkey, b.curve_publickey, b.curve_secretkey = server_pub, client_pub, client_sec
    a.bind(endpoint)
    b.connect(endpoint)
    return a, b


def roundtrip(endpoint, curve=False, size=64):
    ctx = zmq.Context()
    rep, req = make_pair(ctx, zmq.REP, zmq.REQ, endpoint, curve)

    def echo():
        for _ in range(ROUNDTRIPS + 100):
            rep.send(rep.recv())

    t = threading.Thread(target=echo)
    t.start()
    payload = b"x" * size
    samples = []
    for i in range(ROUNDTRIPS + 100):
        t0 = time.perf_counter()
        req.send(payload)
        req.recv()
        if i >= 100:  # warm-up
            samples.append((time.perf_counter() - t0) * 1e6)
    t.join()
    rep.close(); req.close(); ctx.term()
    return statistics.median(samples)


def throughput(endpoint, curve=False, size=64):
    messages = MESSAGES if size <= 1024 else MESSAGES // 20  # large frames: 5000 x 64 kB
    ctx = zmq.Context()
    pull, push = make_pair(ctx, zmq.PULL, zmq.PUSH, endpoint, curve)
    payload = b"x" * size
    push.send(b"start"); pull.recv()          # connection is up

    def sink():
        for _ in range(messages):
            pull.recv()

    t = threading.Thread(target=sink)
    t0 = time.perf_counter()
    t.start()
    for _ in range(messages):
        push.send(payload)
    t.join()
    elapsed = time.perf_counter() - t0
    push.close(); pull.close(); ctx.term()
    return messages / elapsed, messages * size / elapsed / 1e6


def main():
    cases = [
        ("inproc", "inproc://bench", False),
        ("ipc", "ipc:///tmp/zmq-bench.ipc", False),
        ("tcp", "tcp://127.0.0.1:5610", False),
        ("tcp + CURVE", "tcp://127.0.0.1:5611", True),
    ]
    print(f"pyzmq {zmq.__version__} / libzmq {zmq.zmq_version()}")
    print(f"{'Transport':<12} {'RTT 64 B':>10} {'msg/s 64 B':>12} {'MB/s 64 kB':>11}")
    for name, ep, curve in cases:
        rtt = roundtrip(ep, curve)
        rate, _ = throughput(ep, curve, 64)
        _, mbps = throughput(ep, curve, 65536)
        print(f"{name:<12} {rtt:>7.1f} us {rate:>12,.0f} {mbps:>11,.0f}")


if __name__ == "__main__":
    main()
