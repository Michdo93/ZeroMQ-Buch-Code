"""Zero-copy sending of large NumPy arrays.

send(copy=True)  : pyzmq copies the buffer into a libzmq message.
send(copy=False) : libzmq references the Python buffer directly. The buffer
                   must not be modified until libzmq is done with it ->
                   track=True returns a MessageTracker that tells us when.
On the receiving side recv(copy=False) returns a zmq.Frame whose .buffer
can be wrapped by numpy.frombuffer without another copy.
Run:  python k05_zero_copy.py
"""

import time

import numpy as np
import zmq

ctx = zmq.Context()
tx = ctx.socket(zmq.PAIR)
rx = ctx.socket(zmq.PAIR)
tx.bind("inproc://frames")
rx.connect("inproc://frames")

frame = np.random.randint(0, 255, (1080, 1920, 3), dtype=np.uint8)  # ~6 MB "Full-HD image"
N = 200

for copy in (True, False):
    t0 = time.perf_counter()
    for _ in range(N):
        tracker = tx.send(frame, copy=copy, track=not copy)
        msg = rx.recv(copy=False)
        image = np.frombuffer(msg.buffer, dtype=np.uint8).reshape(frame.shape)
    dt = (time.perf_counter() - t0) / N * 1e3
    assert np.array_equal(image, frame)
    if not copy:
        # The tracker only completes when EVERY reference to the message is
        # gone - also the receiving Frame and the NumPy view on it.
        del image, msg
        tracker.wait()  # now it would be safe to modify `frame`
    print(f"copy={copy!s:<5}  {dt:6.2f} ms per 6 MB frame  ({frame.nbytes / 2**20 / dt * 1e3:7.0f} MiB/s)")

tx.close()
rx.close()
ctx.term()
