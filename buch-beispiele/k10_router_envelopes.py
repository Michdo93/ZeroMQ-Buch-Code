"""What a ROUTER socket really receives - identities and envelopes.

* From a REQ peer:    [identity, b"", payload]   (REQ adds the empty delimiter)
* From a DEALER peer: [identity, payload]        (DEALER adds nothing)
* Identity: random 5 bytes, or the value set with zmq.IDENTITY (ROUTING_ID).
* Replying = sending the identity as the first frame.
* ROUTER_MANDATORY: unknown identities raise an error instead of being
  silently discarded.
Run:  python k10_router_envelopes.py
"""

import zmq

ctx = zmq.Context()
router = ctx.socket(zmq.ROUTER)
router.setsockopt(zmq.ROUTER_MANDATORY, 1)
router.bind("inproc://router")

req = ctx.socket(zmq.REQ)
req.setsockopt(zmq.IDENTITY, b"sensor-A")  # readable identity
req.connect("inproc://router")

dealer = ctx.socket(zmq.DEALER)  # automatic random identity
dealer.connect("inproc://router")

req.send(b"hello from REQ")
dealer.send(b"hello from DEALER")

for _ in range(2):
    frames = router.recv_multipart()
    print("ROUTER received:", frames)
    identity, payload = frames[0], frames[-1]
    reply_envelope = frames[:-1]  # everything up to the payload
    router.send_multipart(reply_envelope + [b"ACK " + payload])

print("REQ    got:", req.recv())
print("DEALER got:", dealer.recv())

try:
    router.send_multipart([b"unknown-peer", b"", b"nobody home"])
except zmq.ZMQError as exc:
    print("ROUTER_MANDATORY ->", exc)

for s in (req, dealer, router):
    s.close(linger=0)
ctx.term()
