#!/usr/bin/env python3
"""Measure BGP failure DETECTION time: failure injected -> peer leaves Established.

This is the quantity BFD changes. Without BFD, bgpd waits out the hold timer.
With BFD, sub-second liveness detection reports the peer down immediately.
Failure is 'docker pause': the peer stops responding while its interfaces stay
up, which is precisely the case hold timers exist to cover.
"""
import subprocess, time, json, argparse

def established(node, peer):
    r = subprocess.run(
        ["docker","exec",f"clab-p1-mini-{node}","vtysh","-c","show bgp summary json"],
        capture_output=True, text=True)
    try:
        d = json.loads(r.stdout[r.stdout.index("{"):])
        return d["ipv4Unicast"]["peers"][peer]["state"] == "Established"
    except Exception:
        return None

def trial(node, peer, target, timeout=30):
    while established(node, peer) is not True:
        time.sleep(1)
    subprocess.run(["docker","pause",target], capture_output=True)
    t0 = time.time()
    detected = None
    while time.time() - t0 < timeout:
        if established(node, peer) is False:
            detected = time.time() - t0
            break
        time.sleep(0.05)
    subprocess.run(["docker","unpause",target], capture_output=True)
    return detected

if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--node", default="leaf1")
    ap.add_argument("--peer", default="10.0.11.0")   # spine2's /31 end
    ap.add_argument("--target", default="clab-p1-mini-spine2")
    ap.add_argument("--trials", type=int, default=3)
    a = ap.parse_args()

    print(f"detection time: {a.node} detecting {a.target} ({a.peer}) down")
    res = []
    for i in range(a.trials):
        d = trial(a.node, a.peer, a.target)
        print(f"  trial {i+1}: {d:.2f} s" if d else f"  trial {i+1}: NOT DETECTED")
        if d: res.append(d)
        time.sleep(15)
    if res:
        print(f"\ndetection(s) = {[round(x,2) for x in res]}  "
              f"median={sorted(res)[len(res)//2]:.2f} s")
