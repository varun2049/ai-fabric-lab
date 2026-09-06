#!/usr/bin/env python3
"""counters_exporter.py - expose SONiC port counters as Prometheus metrics.

Reads COUNTERS_DB from one or more SONiC containers (COUNTERS_PORT_NAME_MAP, then each
port's COUNTERS:oid hash) and serves them at /metrics as
sonic_port_stat{node,port,stat}. Each scrape reads live values.

usage: counters_exporter.py <container> [<container> ...] [--port 9108]
"""
import argparse, json, subprocess
from http.server import HTTPServer, BaseHTTPRequestHandler

READ_PY = r"""
import json
try:
    from swsscommon.swsscommon import SonicV2Connector
    db = SonicV2Connector(use_unix_socket_path=True); db.connect("COUNTERS_DB")
    m = db.get_all("COUNTERS_DB", "COUNTERS_PORT_NAME_MAP") or {}
    print(json.dumps({p: (db.get_all("COUNTERS_DB", "COUNTERS:" + oid) or {}) for p, oid in m.items()}))
except ImportError:
    import redis
    r = redis.Redis(unix_socket_path="/var/run/redis/redis.sock", db=2, decode_responses=True)
    m = r.hgetall("COUNTERS_PORT_NAME_MAP")
    print(json.dumps({p: r.hgetall("COUNTERS:" + oid) for p, oid in m.items()}))
"""

def read(container):
    r = subprocess.run(["docker", "exec", container, "python3", "-c", READ_PY],
                       capture_output=True, text=True, timeout=60)
    return json.loads(r.stdout) if r.returncode == 0 and r.stdout.strip() else {}

def render(containers):
    out = ["# HELP sonic_port_stat SAI port statistic read from COUNTERS_DB",
           "# TYPE sonic_port_stat counter"]
    for c in containers:
        node = c.rsplit("-", 1)[-1]
        for port, stats in sorted(read(c).items()):
            for k, v in sorted(stats.items()):
                if k.startswith("SAI_PORT_STAT_") and v.lstrip("-").isdigit():
                    out.append(f'sonic_port_stat{{node="{node}",port="{port}",stat="{k}"}} {v}')
    return "\n".join(out) + "\n"

def serve(containers, port):
    class H(BaseHTTPRequestHandler):
        def do_GET(self):
            body = render(containers).encode() if self.path == "/metrics" else b"see /metrics\n"
            self.send_response(200); self.send_header("Content-Type", "text/plain"); self.end_headers()
            self.wfile.write(body)
        def log_message(self, *a): pass
    print(f"serving /metrics on :{port} for {', '.join(containers)}")
    HTTPServer(("0.0.0.0", port), H).serve_forever()

if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("containers", nargs="+")
    ap.add_argument("--port", type=int, default=9108)
    a = ap.parse_args()
    serve(a.containers, a.port)
