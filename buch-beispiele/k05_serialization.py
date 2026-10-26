"""Compare serialisation formats for the same sensor record.

JSON (text), MessagePack (binary, schemaless) and struct (binary, fixed
layout). Prints the encoded size and the encode+decode time per message.
Run:  pip install msgpack   then   python k05_serialization.py
"""

import json
import struct
import timeit

import msgpack

record = {"sensor_id": 17, "timestamp": 1792842244.4403, "temperature": 21.53,
          "humidity": 48.2, "battery": 0.87}

LAYOUT = struct.Struct("<Hdfff")  # uint16, float64, 3 x float32 = 22 bytes


def with_json():
    return json.loads(json.dumps(record).encode())


def with_msgpack():
    return msgpack.unpackb(msgpack.packb(record))


def with_struct():
    raw = LAYOUT.pack(record["sensor_id"], record["timestamp"], record["temperature"],
                      record["humidity"], record["battery"])
    return LAYOUT.unpack(raw)


sizes = {
    "JSON": len(json.dumps(record).encode()),
    "MessagePack": len(msgpack.packb(record)),
    "struct": LAYOUT.size,
}
for name, func in (("JSON", with_json), ("MessagePack", with_msgpack), ("struct", with_struct)):
    t = min(timeit.repeat(func, number=20000, repeat=3)) / 20000 * 1e6
    print(f"{name:<12} {sizes[name]:4d} bytes   {t:6.2f} us encode+decode")
