"""Virtual field sensor nodes (PIR + microphone dB + tree vibration) for WildGuard AI.

Usage:
  python sensor_sim.py                      # 6 nodes, random normal activity + random events
  python sensor_sim.py --scenario logging   # force an illegal-logging event on node-2
  python sensor_sim.py --scenario poaching  # force motion + engine noise on node-4
"""
import argparse
import math
import random
import time

import requests

CENTER = (21.9497, 88.8958)   # Sundarbans National Park
RADIUS_KM = 25


def make_nodes(n):
    nodes = []
    for i in range(n):
        ang = 2 * math.pi * i / n
        r = RADIUS_KM * 0.6 / 111.32
        nodes.append({
            "node_id": f"node-{i + 1}",
            "lat": round(CENTER[0] + r * math.cos(ang), 5),
            "lon": round(CENTER[1] + r * math.sin(ang) / math.cos(math.radians(CENTER[0])), 5),
            "battery": 100.0,
        })
    return nodes


def normal_reading(node):
    return {"motion": random.random() < 0.01,
            "sound_db": round(random.gauss(45, 6), 1),     # forest ambience
            "vibration": round(abs(random.gauss(0.05, 0.03)), 2)}


def logging_event():
    return {"motion": True, "sound_db": round(random.uniform(88, 105), 1),
            "vibration": round(random.uniform(0.65, 0.95), 2)}


def poaching_event():
    return {"motion": True, "sound_db": round(random.uniform(76, 84), 1),
            "vibration": round(random.uniform(0.05, 0.2), 2)}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--url", default="http://localhost:8000/api/sensors/reading")
    ap.add_argument("--nodes", type=int, default=6)
    ap.add_argument("--interval", type=float, default=3.0)
    ap.add_argument("--scenario", choices=["random", "logging", "poaching"], default="random")
    args = ap.parse_args()

    nodes = make_nodes(args.nodes)
    print(f"Simulating {len(nodes)} nodes -> {args.url}  (Ctrl+C to stop)")
    tick = 0
    while True:
        tick += 1
        for idx, node in enumerate(nodes):
            reading = normal_reading(node)
            if args.scenario == "logging" and idx == 1:
                reading = logging_event()
            elif args.scenario == "poaching" and idx == 3:
                reading = poaching_event()
            elif args.scenario == "random" and random.random() < 0.02:
                reading = random.choice([logging_event, poaching_event])()

            node["battery"] = max(0.0, round(node["battery"] - 0.01, 2))
            payload = {**node, **reading, "sound_db": max(0, reading["sound_db"])}
            try:
                res = requests.post(args.url, json=payload, timeout=5).json()
                flag = " <-- ALERT: " + ", ".join(a["category"] for a in res["alerts"]) if res["alerts"] else ""
                print(f"[{tick:04}] {node['node_id']}: motion={payload['motion']!s:5} "
                      f"sound={payload['sound_db']:5} dB vib={payload['vibration']}{flag}")
            except requests.RequestException as e:
                print(f"Backend not reachable: {e}")
        time.sleep(args.interval)


if __name__ == "__main__":
    main()
