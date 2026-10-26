"""Bridge: fast ZeroMQ edge network -> MQTT broker (e.g. for openHAB).

ZeroMQ carries the high-rate raw data between the processes on the edge
device; only the condensed, slow events are forwarded to MQTT, where
openHAB, Node-RED or Home Assistant pick them up - including QoS and
retained messages for the dashboard.

    ZeroMQ PUB  "gesture.*", "presence.*"  --->  bridge  --->  MQTT  zmq/gesture/..., retained

Requirements: pip install paho-mqtt, a broker on localhost:1883
Run:  python k19_zmq_mqtt_bridge.py --zmq tcp://127.0.0.1:5557 --topics gesture. presence.
"""

import argparse
import json

import paho.mqtt.client as mqtt
import zmq


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--zmq", action="append", default=None, help="ZeroMQ PUB endpoint(s) to subscribe to")
    parser.add_argument("--topics", nargs="+", default=["gesture.", "presence."])
    parser.add_argument("--mqtt-host", default="localhost")
    parser.add_argument("--mqtt-port", type=int, default=1883)
    parser.add_argument("--prefix", default="zmq")
    parser.add_argument("--count", type=int, default=0, help="stop after N messages (0 = endless)")
    args = parser.parse_args()

    client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2, client_id="zmq-bridge")
    client.will_set(f"{args.prefix}/bridge/online", "false", qos=1, retain=True)  # Last Will
    client.connect(args.mqtt_host, args.mqtt_port)
    client.loop_start()
    client.publish(f"{args.prefix}/bridge/online", "true", qos=1, retain=True)

    ctx = zmq.Context()
    sub = ctx.socket(zmq.SUB)
    for endpoint in args.zmq or ["tcp://127.0.0.1:5557"]:
        sub.connect(endpoint)
    for topic in args.topics:
        sub.setsockopt_string(zmq.SUBSCRIBE, topic)

    forwarded = 0
    try:
        while args.count == 0 or forwarded < args.count:
            topic, payload = sub.recv_multipart()[:2]
            mqtt_topic = f"{args.prefix}/" + topic.decode().replace(".", "/")
            # events are rare and important -> QoS 1 and retained for dashboards
            client.publish(mqtt_topic, payload, qos=1, retain=True)
            forwarded += 1
            print(f"{topic.decode():<16} -> {mqtt_topic:<24} {json.loads(payload)}")
    except KeyboardInterrupt:
        pass
    finally:
        client.publish(f"{args.prefix}/bridge/online", "false", qos=1, retain=True).wait_for_publish(2)
        client.loop_stop()
        client.disconnect()
        sub.close(linger=0)
        ctx.term()


if __name__ == "__main__":
    main()
