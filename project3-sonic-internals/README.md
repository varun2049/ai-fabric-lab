# Project 3 - SONiC Internals

The [Project 2.5](../project2_5-frr-irb-type5/) fabric rebuilt with SONiC leaves, then
examined from the inside: configuration changes followed through SONiC's pipeline -
CONFIG_DB, the manager daemons, the kernel, APPL_DB, orchagent, ASIC_DB, syncd, and the
resulting SAI call - with the orchagent source that produced each recorded call read
and annotated. Two Python tools capture and export that state.

Platform: `docker-sonic-vs` (community 202411) in containerlab, with FRR spines.

## What this proves

- **Configuration traced to the SAI call.** A VLAN, a BGP route, an EVPN-learned MAC
  and a VNI mapping are each read verbatim at every layer of the pipeline, ending at
  the line in `sairedis.rec` where syncd was instructed to program the switch. SONiC's
  design requires these copies to agree; the first layer that disagrees identifies the
  responsible daemon.
- **Network state in SAI terms.** A remote MAC becomes an `FDB_ENTRY` installed
  `STATIC` with an `ENDPOINT_IP`; an ECMP route becomes a `ROUTE_ENTRY` keyed by
  virtual router and prefix; an L3VNI becomes a `VNI_TO_VIRTUAL_ROUTER_ID` map entry;
  each tenant VRF becomes its own `VIRTUAL_ROUTER` object.
- **The code behind the calls.** `VxlanTunnelMapOrch::addOperation`,
  `VxlanVrfMapOrch::addOperation` and `FdbOrch::addFdbEntry` in `sonic-swss` are read
  to the lines that set each attribute observed in the recording - including why an
  L2 VNI produces a single decapsulation map entry while an L3VNI produces both
  directions.
- **The pipeline in reverse.** A VNI mapping removed at CONFIG_DB is observed
  disappearing from every layer, with the same object ID at both ends of its lifecycle.
- **Symmetric IRB and Type-5 routing from tables alone.** `ttl=62` across leaves,
  cross-tenant traffic failing on a VRF lookup miss, and the VRF route carrying its
  VNI and router MAC as next-hop attributes in APPL_DB.

## Documentation

1. [docs/orientation.md](docs/orientation.md) - daemons, databases with ids read from
   the node, a VLAN traced to its SAI call
2. [docs/fabric.md](docs/fabric.md) - design, the mapping from Linux kernel
   configuration to CONFIG_DB tables, routed-overlay proofs
3. [docs/sonic-internals-trace.md](docs/sonic-internals-trace.md) (flagship) - a route
   in four places, a remote MAC in five, a VNI map in five, the deliberate removal,
   annotated orchagent code

## Tools

- `tools/sonic_snapshot.py <container>` - captures a node's state in one command: all
  five Redis databases as JSON, kernel tables, FRR views, process list, recording and
  syslog tails.
- `tools/counters_exporter.py <container>...` - serves `COUNTERS_DB` port statistics
  as Prometheus metrics at `:9108/metrics` (`sonic_port_stat{node,port,stat}`).

Both read SONiC through its native `swsscommon` API. See [tools/README.md](tools/README.md).

## Layout

```
project3-sonic-internals/
  lab/        topology.clab.yml, configs/<leaf>/{config_db.json,bgpd.conf}, setup-fabric.sh
  docs/       evidence documents
  tools/      snapshot and exporter
```

## How to run

Requires Docker, containerlab, and a `docker-sonic-vs` image (x86-64).

```
cd lab
sudo containerlab deploy -t topology.clab.yml
./setup-fabric.sh                                   # waits for ports, loads tables, starts bgpd
docker exec clab-p3-sonic-h1 ping -c 3 192.168.101.10        # expect ttl=62
docker exec clab-p3-sonic-leaf1 vtysh -c "show evpn vni"
python3 ../tools/sonic_snapshot.py clab-p3-sonic-leaf1
python3 ../tools/counters_exporter.py clab-p3-sonic-leaf1 clab-p3-sonic-leaf2
```

Each SONiC leaf has 32 links (four in use, the remainder to a sink node): the virtual
switch backs every port it initializes with a container interface, and orchagent
defers VLAN programming until all ports have initialized. Configuration is applied
with `config load` (a merge) once ports are ready. This image has no `bgpcfgd`, so FRR
is configured directly from `bgpd.conf` and the L3VNI bindings are applied via `vtysh`.

## Scope

Virtual-platform behaviour, not pipeline defects: `show mac` omits the tunnel entries
ASIC_DB holds; the EVPN tunnel reports `operstatus down` in STATE_DB while forwarding
works; a leaf's own `eth2` endpoint MAC appears in the VLAN; port counter polling is
off until `FLEX_COUNTER_TABLE` enables it. Anycast gateway is not configured - each
gateway resides on one leaf, and the design does not require it. Nothing below the SAI
call (buffers, QoS, line-rate forwarding) can be demonstrated on this platform.
