# Buchbeispiele (`kNN_…`)

Kurze, eigenständige Beispiele, die nur im Buch vorkommen. `NN` ist die Kapitelnummer.
Jedes Skript läuft mit **einem** Befehl und beendet sich selbst – Publisher, Subscriber,
Broker usw. werden darin als Threads gestartet. Alle Endpunkte liegen auf `127.0.0.1`.

## Installation

```bash
python3 -m venv .venv
source .venv/bin/activate            # Windows: .venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

Getestet mit Python 3.13, pyzmq 27.2 und libzmq 4.3.5 unter Linux.

## Übersicht

| Datei | Kapitel | Thema | Laufzeit |
|---|---|---|---|
| `k04_sync_pubsub.py` | 4 | Slow Joiner: PUB/SUB über einen REQ/REP-Kanal synchronisieren | < 1 s |
| `k05_serialization.py` | 5 | JSON, MessagePack und `struct` im Vergleich (Größe, Zeit) | ~3 s |
| `k05_protobuf.py` | 5 | Protocol Buffers über ZeroMQ (Schema in `proto/sensor.proto`) | < 1 s |
| `k05_zero_copy.py` | 5 | `copy=False`, `MessageTracker`, NumPy ohne Kopie | ~1 s |
| `k06_conflate.py` | 6 | `CONFLATE` – nur die jüngste Nachricht | ~5 s |
| `k07_pollout_hwm.py` | 7 | `POLLOUT`, `NOBLOCK` und die Hochwassermarke (inproc vs. tcp) | ~2 s |
| `k09_inproc_relay.py` | 9 | Threads per PAIR über `inproc://` koordinieren | < 1 s |
| `k10_router_envelopes.py` | 10 | Was ein ROUTER wirklich empfängt: Identitäten und Envelopes | < 1 s |
| `k11_lvc_proxy.py` | 11 | Last Value Cache – „retained messages“ für ZeroMQ | ~2 s |
| `k13_paranoid_pirate.py` | 13 | Heartbeats zwischen Broker und Workern | ~5 s |
| `k14_monitor.py` | 14 | Socket-Monitor und native ZMTP-Heartbeats | ~5 s |
| `k18_transports.py` | 18 | inproc / ipc / tcp / tcp+CURVE: Latenz und Durchsatz | ~10 s |
| `k19_reliable_delivery.py` | 19 | QoS 1/2 selbst gebaut: ACK, Wiederholung, Duplikaterkennung | ~2 s |
| `k19_zmq_mqtt_bridge.py` | 19 | Brücke ZeroMQ → MQTT (QoS 1, retained, Last Will) | läuft dauerhaft |

## Ausführen

```bash
python k04_sync_pubsub.py
python k05_serialization.py
...
```

### Erwartete Ausgaben (Auszug)

```text
$ python k04_sync_pubsub.py
sent 1000, received: {'sub-0': 1000, 'sub-2': 1000, 'sub-1': 1000}

$ python k10_router_envelopes.py
ROUTER received: [b'sensor-A', b'', b'hello from REQ']
ROUTER received: [b'\x00k\x8bEg', b'hello from DEALER']
REQ    got: b'ACK hello from REQ'
DEALER got: b'ACK hello from DEALER'
ROUTER_MANDATORY -> Host unreachable

$ python k13_paranoid_pirate.py
[broker] worker w1 joined
...
[w2] *** simulated crash (no goodbye, no heartbeats) ***
[broker] worker w2 missed 3 heartbeats -> removed
[broker] alive at the end: ['w1', 'w3']

$ python k19_reliable_delivery.py
sent 50 messages, still unacknowledged: 0
retransmissions: 21, ACKs lost: 21
processed exactly once: 50, duplicates discarded: 21
```

Zeit- und Durchsatzwerte (`k05_*`, `k06_*`, `k18_*`) hängen stark vom Rechner ab.

## Sonderfälle

### `k05_protobuf.py` – Schema einmalig übersetzen

```bash
python -m grpc_tools.protoc -I proto --python_out=proto proto/sensor.proto
python k05_protobuf.py
```

Der Befehl erzeugt `proto/sensor_pb2.py`. Ohne diesen Schritt bricht das Skript mit
`ModuleNotFoundError: sensor_pb2` ab.

### `k18_transports.py` – nur unter Linux/macOS vollständig

Der Fall `ipc://` nutzt Unix-Domain-Sockets. Unter Windows diese Zeile in `cases`
auskommentieren.

### `k19_zmq_mqtt_bridge.py` – braucht einen MQTT-Broker und einen ZeroMQ-Publisher

```bash
sudo apt install mosquitto mosquitto-clients     # Broker auf localhost:1883
# Terminal 1: eine Quelle für gesture.* (Simulation der Leap-Motion-Bridge, siehe repos/)
python ../repos/ZeroMQ-Leap-Motion-LM-010/src/leap_bridge.py --simulate
python ../repos/ZeroMQ-Leap-Motion-LM-010/examples/gesture_events.py     # PUB auf :5557
# Terminal 2: die Brücke
python k19_zmq_mqtt_bridge.py --zmq tcp://127.0.0.1:5557 --topics gesture.
# Terminal 3: mitlesen
mosquitto_sub -t 'zmq/#' -v
```

Optionen: `--mqtt-host`, `--mqtt-port`, `--prefix` (Standard `zmq`), `--count N`
(nach N Nachrichten beenden).
