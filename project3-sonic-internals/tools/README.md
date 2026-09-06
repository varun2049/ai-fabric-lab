# Tools

Two Python tools that read SONiC through its own `swsscommon` API, run from the host
against a container. No dependencies beyond Python 3 and Docker.

## sonic_snapshot.py - capture a node's state

```
python3 sonic_snapshot.py clab-p3-sonic-leaf1
CONFIG_DB       333 keys
APPL_DB         226 keys
ASIC_DB        1567 keys
STATE_DB        174 keys
COUNTERS_DB      19 keys
bundle: snapshots/clab-p3-sonic-leaf1-20260906-072136
```

The bundle:

```
APPL_DB.json  ASIC_DB.json  CONFIG_DB.json  COUNTERS_DB.json  STATE_DB.json
kernel.txt        ip addr/route, bridge fdb, ip neigh, per-VRF routes
frr.txt           bgp summary, evpn vni, l2vpn evpn summary, routes in all VRFs
processes.txt     supervisorctl status
sairedis.rec.tail swss.rec.tail syslog.tail   (last 200 lines; --lines N)
```

Every Redis database is dumped as `{key: {field: value}}`, so the layer-by-layer
comparison in the trace docs can be done offline with a diff or a script. Use it before
and after a change, or when opening a ticket: the ASIC_DB dump plus the recording tail
is what a vendor asks for.

## counters_exporter.py - port counters as Prometheus metrics

```
python3 counters_exporter.py clab-p3-sonic-leaf1 clab-p3-sonic-leaf2 --port 9108
curl -s localhost:9108/metrics | head
sonic_port_stat{node="leaf1",port="Ethernet0",stat="SAI_PORT_STAT_IF_IN_OCTETS"} 1436489
sonic_port_stat{node="leaf1",port="Ethernet0",stat="SAI_PORT_STAT_IF_OUT_OCTETS"} 1318852
sonic_port_stat{node="leaf1",port="Ethernet100",stat="SAI_PORT_STAT_IF_IN_OCTETS"} 0
```

Reads `COUNTERS_PORT_NAME_MAP` to resolve port names to SAI object IDs, then each
port's `COUNTERS:oid:...` hash, on every scrape. Ethernet0 above carries the underlay
BGP session; Ethernet100 is unused. Counter polling must be enabled
(`FLEX_COUNTER_TABLE|PORT`, included in the leaf configs; `counterpoll port enable`
on a running node) - without it COUNTERS_DB holds only the name maps.

Point a Prometheus `scrape_config` at `:9108` and the fabric's per-port counters graph
in Grafana with no agent on the switch.
