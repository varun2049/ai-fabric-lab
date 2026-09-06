#!/usr/bin/env python3
"""sonic_snapshot.py - capture a SONiC node's state into a timestamped bundle.

Dumps each Redis database (CONFIG/APPL/ASIC/STATE/COUNTERS) as JSON, kernel network
state, FRR views, the process list, and the tails of the SAI/swss recordings and
syslog. One command, one directory: the evidence to attach to a ticket.

usage: sonic_snapshot.py <container> [--lines 200] [--out snapshots]
"""
import argparse, json, os, subprocess, time

DBS = {"CONFIG_DB": 4, "APPL_DB": 0, "ASIC_DB": 1, "STATE_DB": 6, "COUNTERS_DB": 2}

DUMP_PY = r"""
import json, sys
name = sys.argv[1]
try:
    from swsscommon.swsscommon import SonicV2Connector
    db = SonicV2Connector(use_unix_socket_path=True); db.connect(name)
    print(json.dumps({k: db.get_all(name, k) for k in (db.keys(name, "*") or [])}))
except ImportError:
    import redis
    n = {"APPL_DB": 0, "ASIC_DB": 1, "COUNTERS_DB": 2, "CONFIG_DB": 4, "STATE_DB": 6}[name]
    r = redis.Redis(unix_socket_path="/var/run/redis/redis.sock", db=n, decode_responses=True)
    print(json.dumps({k: r.hgetall(k) for k in r.scan_iter()}))
"""

def sh(c, cmd, timeout=120):
    r = subprocess.run(["docker", "exec", c, "bash", "-c", cmd],
                       capture_output=True, text=True, timeout=timeout)
    return r.stdout + (r.stderr if r.returncode else "")

def dump_db(c, name, n):
    r = subprocess.run(["docker", "exec", c, "python3", "-c", DUMP_PY, name],
                       capture_output=True, text=True, timeout=300)
    if r.returncode == 0 and r.stdout.strip():
        return json.loads(r.stdout)
    out = {}                                  # fallback: plain redis-cli, alternating field/value lines
    for k in sh(c, f'redis-cli -n {n} keys "*"').split("\n"):
        k = k.strip()
        if not k:
            continue
        lines = [l for l in sh(c, f'redis-cli -n {n} hgetall "{k}"').split("\n") if l != ""]
        out[k] = dict(zip(lines[0::2], lines[1::2]))
    return out

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("container")
    ap.add_argument("--lines", type=int, default=200)
    ap.add_argument("--out", default="snapshots")
    a = ap.parse_args()
    d = os.path.join(a.out, f"{a.container}-{time.strftime('%Y%m%d-%H%M%S')}")
    os.makedirs(d, exist_ok=True)

    for name, n in DBS.items():
        data = dump_db(a.container, name, n)
        json.dump(data, open(f"{d}/{name}.json", "w"), indent=1, sort_keys=True)
        print(f"{name:12s} {len(data):6d} keys")

    kernel = "\n".join(f"### {c}\n{sh(a.container, c)}" for c in [
        "ip -br addr", "ip route", "bridge fdb show", "ip neigh",
        "for v in $(ip -br link show type vrf | awk '{print $1}'); do echo \"-- vrf $v\"; ip route show vrf $v; done"])
    open(f"{d}/kernel.txt", "w").write(kernel)

    frr = sh(a.container, 'vtysh -c "show bgp summary" -c "show evpn vni" '
                          '-c "show bgp l2vpn evpn summary" -c "show ip route vrf all" 2>/dev/null')
    open(f"{d}/frr.txt", "w").write(frr)
    open(f"{d}/processes.txt", "w").write(sh(a.container, "supervisorctl status"))
    for f in ("sairedis.rec", "swss.rec"):
        open(f"{d}/{f}.tail", "w").write(sh(a.container, f"tail -n {a.lines} /var/log/swss/{f}"))
    open(f"{d}/syslog.tail", "w").write(sh(a.container, f"tail -n {a.lines} /var/log/syslog"))
    print(f"bundle: {d}")

if __name__ == "__main__":
    main()
