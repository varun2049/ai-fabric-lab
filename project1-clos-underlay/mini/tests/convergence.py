#!/usr/bin/env python3
"""Measure data-plane outage during a fabric failure.

One long-lived ping (10ms interval, -D timestamps) runs inside h1 for the
whole window; a failure is injected mid-stream. The largest wall-clock gap
between consecutive replies is the outage.

Uses a single ping process rather than one subprocess per probe: the latter
had a ~90ms jitter floor, larger than the outages being measured.
"""
import subprocess, time, re, argparse

H1, TARGET, INTERVAL = "clab-p1-mini-h1", "192.168.12.10", 0.01

def measure(action, restore, fail_at=5, restore_at=20, total=30):
    n = int(total / INTERVAL)
    p = subprocess.Popen(
        ["docker","exec",H1,"ping","-D","-i",str(INTERVAL),"-c",str(n),"-W","1",TARGET],
        stdout=subprocess.PIPE, stderr=subprocess.DEVNULL, text=True)
    t0 = time.time()
    time.sleep(fail_at)
    subprocess.run(action, capture_output=True)
    print(f"  [{time.time()-t0:5.2f}s] failure injected")
    time.sleep(restore_at - fail_at)
    subprocess.run(restore, capture_output=True)
    print(f"  [{time.time()-t0:5.2f}s] restored")
    out, _ = p.communicate(timeout=total+60)

    reps = [(float(m.group(1)), int(m.group(2))) for m in
            (re.match(r'\[(\d+\.\d+)\].*icmp_seq=(\d+)', l) for l in out.splitlines()) if m]
    if len(reps) < 2:
        print("  no replies parsed"); return None
    base = reps[0][0]
    gaps = [(reps[i+1][0]-reps[i][0], reps[i][0]-base) for i in range(len(reps)-1)]
    worst, when = max(gaps)
    print(f"  replies {len(reps)}/{n}   worst gap {worst*1000:.0f} ms at t={when:.2f}s")
    return worst

if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("scenario", choices=["link","node"])
    ap.add_argument("--spine", default="spine1")
    ap.add_argument("--trials", type=int, default=3)
    a = ap.parse_args()
    c = f"clab-p1-mini-{a.spine}"
    if a.scenario == "link":
        iface = "eth1" if a.spine == "spine1" else "eth3"
        act = ["docker","exec","clab-p1-mini-leaf1","ip","link","set",iface,"down"]
        res = ["docker","exec","clab-p1-mini-leaf1","ip","link","set",iface,"up"]
    else:
        act, res = ["docker","pause",c], ["docker","unpause",c]

    print(f"scenario={a.scenario} target={a.spine} trials={a.trials}")
    r = []
    for i in range(a.trials):
        print(f"trial {i+1}:")
        v = measure(act, res)
        if v: r.append(v)
        time.sleep(20)
    if r:
        print(f"\n{a.scenario}: outages(ms) = {[round(x*1000) for x in r]}  "
              f"median={sorted(r)[len(r)//2]*1000:.0f} ms")
