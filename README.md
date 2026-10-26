# From Zero to Hero – ZeroMQ in Python meistern · Begleitcode

Michael Christian Dörflinger · Stand: Oktober 2026

Dieses Archiv enthält **alle Codebeispiele des Buchs**:

```text
ZeroMQ-Buch-Code/
├── README.md                ← diese Datei
├── buch-beispiele/          ← kurze Beispiele, die nur im Buch vorkommen (k04_… bis k19_…)
│   ├── README.md
│   ├── requirements.txt
│   └── proto/sensor.proto
└── repos/                   ← Snapshots der GitHub-Repositorys (getestet, Stand des Buchs)
    ├── ZeroMQ-Examples/
    ├── ZeroMQ-Camera-Control/
    ├── ZeroMQ-Walkie-Talkie/
    ├── ZeroMQ-Task-Pipeline/
    ├── Python-Concurrency-Patterns/
    ├── ZeroMQ-Concurrency-Patterns/
    ├── ZeroMQ-OOP-Patterns/
    ├── ZeroMQ-Cross-Language-CPP-Python/
    ├── ZeroMQ-Advanced-Examples/
    ├── ZeroMQ-Leap-Motion-LM-010/
    └── ZeroMQ-Kinect-v1-Xbox-360/
```

Jeder Ordner hat eine eigene `README.md` mit Installation, Startreihenfolge und
erwarteter Ausgabe. Die aktuellen Fassungen der Repositorys liegen unter
<https://github.com/Michdo93>.

## Schnellstart

```bash
sudo apt install python3 python3-venv      # Ubuntu/Debian
python3 -m venv .venv
source .venv/bin/activate                  # Windows: .venv\Scripts\Activate.ps1
pip install pyzmq
python -c "import zmq; print(zmq.__version__, zmq.zmq_version(), zmq.has('curve'))"
```

Die Wheels von pyzmq enthalten libzmq und libsodium (CURVE). Eine Systeminstallation
von libzmq ist nur für die C++-Beispiele nötig.

Zusätzliche Pakete je nach Kapitel:

| Bereich | Installation |
|---|---|
| Buchbeispiele | `pip install -r buch-beispiele/requirements.txt` |
| Webcam, Kamera, Pipeline | `pip install opencv-python numpy flask` |
| Mikrofon, Walkie-Talkie | `pip install sounddevice numpy` (+ `sudo apt install libportaudio2`) |
| MQTT-Vergleich, Brücke | `pip install paho-mqtt psutil` und `sudo apt install mosquitto` |
| C++ ↔ Python | `sudo apt install build-essential cmake pkg-config libzmq3-dev cppzmq-dev nlohmann-json3-dev` |
| Leap Motion | Ultraleap Gemini + `leapc-python-bindings` (oder `--simulate`) |
| Kinect v1 | `libfreenect` + Python-Wrapper (oder `--simulate`) |

Die Ordner `ZeroMQ-Concurrency-Patterns`, `ZeroMQ-OOP-Patterns`,
`ZeroMQ-Cross-Language-CPP-Python`, `ZeroMQ-Advanced-Examples`,
`ZeroMQ-Leap-Motion-LM-010` und `ZeroMQ-Kinect-v1-Xbox-360` bringen jeweils eine
eigene `requirements.txt` mit.

## Kapitel → Code

| Kapitel | Thema | Code |
|---|---|---|
| 2 | Installation, Hallo Welt | `repos/ZeroMQ-Examples/` (`response_server.py`, `request_client.py`) |
| 4 | Die vier Grundmuster | `repos/ZeroMQ-Examples/`, `buch-beispiele/k04_sync_pubsub.py` |
| 5 | Nachrichtenformate, Zero-Copy | `buch-beispiele/k05_*.py`, `proto/sensor.proto` |
| 6 | Bild und Ton, CONFLATE | `repos/ZeroMQ-Examples/` (`webcam_*`, `microphone_*`), `buch-beispiele/k06_conflate.py` |
| 7 | Polling, Zeitlimits, HWM | `buch-beispiele/k07_pollout_hwm.py` |
| 8 | Drei Praxisprojekte | `repos/ZeroMQ-Camera-Control/`, `repos/ZeroMQ-Walkie-Talkie/`, `repos/ZeroMQ-Task-Pipeline/` |
| 9 | Threads, Prozesse, asyncio | `repos/Python-Concurrency-Patterns/`, `repos/ZeroMQ-Concurrency-Patterns/`, `buch-beispiele/k09_inproc_relay.py` |
| 10 | ROUTER, DEALER, Envelopes | `buch-beispiele/k10_router_envelopes.py`, `repos/ZeroMQ-OOP-Patterns/03-oop-worker-node/` |
| 11 | XPUB/XSUB, Last Value Cache | `repos/ZeroMQ-Concurrency-Patterns/03-multi-pub-multi-sub/`, `buch-beispiele/k11_lvc_proxy.py` |
| 12 | Objektorientiertes Design | `repos/ZeroMQ-OOP-Patterns/` |
| 13 | Zuverlässigkeit (Piraten) | `buch-beispiele/k13_paranoid_pirate.py`, `repos/ZeroMQ-OOP-Patterns/01-oop-req-rep/client.py` |
| 14 | Monitoring, Fehlersuche | `buch-beispiele/k14_monitor.py` |
| 15 | C++ und Python | `repos/ZeroMQ-Cross-Language-CPP-Python/` |
| 16 | Sicherheit (ZAP, PLAIN, CURVE) | `repos/ZeroMQ-Advanced-Examples/01-…` bis `05-…` |
| 17 | systemd-Dienst | `repos/ZeroMQ-Advanced-Examples/06-systemd-deployment/` |
| 18 | Performance | `buch-beispiele/k18_transports.py` |
| 19 | ZeroMQ vs. MQTT | `repos/ZeroMQ-Advanced-Examples/07-mqtt-comparison/`, `buch-beispiele/k19_*.py` |
| 20 | Leap Motion und Kinect | `repos/ZeroMQ-Leap-Motion-LM-010/`, `repos/ZeroMQ-Kinect-v1-Xbox-360/` |

## Allgemeine Hinweise

- **Ports:** Viele Repository-Beispiele nutzen Port 5555. Immer nur ein Beispiel
  gleichzeitig starten oder den Port per Option bzw. `ZMQ_ENDPOINT` ändern.
  Belegte Ports zeigt `ss -tlnp | grep 55`.
- **Beenden:** Alle Dienste reagieren auf `Strg+C` bzw. `SIGTERM` und räumen
  Sockets und Kontext geordnet auf.
- **Ohne Hardware:** Leap-Motion- und Kinect-Bridge haben einen Schalter `--simulate`
  mit identischem Nachrichtenformat; alle Verbraucher (Monitor, Gesten, Viewer,
  Präsenz) lassen sich damit ohne Geräte ausprobieren.
- **Sicherheit:** Passwörter und Schlüssel in den Beispielen sind Platzhalter
  (`change-me`). Geheime CURVE-Schlüssel (`*.key_secret`) niemals weitergeben.
- **Messwerte:** Alle Zeit- und Durchsatzangaben im Buch sind Richtwerte eines
  einzelnen Rechners.

## Lizenz und Haftung

Der Code ist als Lehrmaterial gedacht. Die Lizenzen der einzelnen Repositorys gelten
entsprechend ihrer jeweiligen Angaben auf GitHub. Nutzung auf eigene Verantwortung.
