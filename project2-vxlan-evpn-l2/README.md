# Project 2 - VXLAN and EVPN Layer 2 Overlay

An EVPN-VXLAN L2 overlay built on the eBGP Clos underlay from
[Project 1](../project1-clos-underlay/). Hosts in the same subnet, attached to different
leaves, communicate as though they share a LAN while the fabric routes everything at
Layer 3 underneath.

Built in two stages to make the control plane's contribution visible:

- **`static-vxlan/`** - raw VXLAN with no control plane. Remote VTEPs configured by
  hand, MAC locations learned reactively from traffic (flood-and-learn).
- **`evpn/`** - BGP EVPN replaces the manual configuration. The same kernel forwarding
  entries appear, installed by Type-2 and Type-3 routes instead of by a human. Two
  isolated tenants (VNI 100 / VNI 200) share the fabric.

## What this proves

Given any MAC in the fabric, it can be located in three places: as a Type-2 route in
the BGP table (with its RD and RT), as an `extern_learn` entry in the kernel FDB, and
inside an MP_REACH_NLRI update on the wire (AFI 25 / SAFI 70, NLRI hand-decoded from
hex where tcpdump's dissector stopped). That trace - control plane to kernel to wire -
is [the flagship document](docs/three-way-correlation.md).

Also demonstrated and measured:

- VXLAN encapsulation: outer/inner structure, the 50-byte overhead, undecremented inner
  TTL proving L2 bridging
- The MTU trap the 50-byte overhead causes, reproduced and fixed
- Flood-and-learn's fragility: connectivity depending on one hand-typed FDB entry, and
  a multi-second first-packet penalty observed after rebuild
- ARP suppression's dependency on IP-to-MAC bindings: with a pure L2 bridge it does
  nothing (measured 4 ARPs crossing the fabric); with an SVI added, 0
- Multi-tenant isolation: two VNIs with overlapping host addresses on one fabric,
  separated by per-VNI bridges and Route Target import filtering

## Layout

```
project2-vxlan-evpn-l2/
  static-vxlan/          Part A - topology, configs, setup-static.sh
  evpn/                  Part B - topology, configs, setup-evpn.sh
  docs/                  evidence documents and design notes
  pcaps/                 raw captures referenced by the docs
```

## Documentation

Start with [docs/design.md](docs/design.md) - architecture, addressing, design
decisions, and what EVPN replaced from Part A.

Evidence documents, in reading order:

1. [vxlan-encapsulation.md](docs/vxlan-encapsulation.md) - the packet, layer by layer
2. [flood-and-learn.md](docs/flood-and-learn.md) - why raw VXLAN doesn't scale
3. [mtu-postmortem.md](docs/mtu-postmortem.md) - the 50-byte overhead as a gray failure
4. [three-way-correlation.md](docs/three-way-correlation.md) - one MAC across wire,
   control plane, and kernel (flagship)
5. [arp-suppression.md](docs/arp-suppression.md) - the SVI dependency, measured
6. [multi-tenancy.md](docs/multi-tenancy.md) - VNI isolation and Route Targets

## How to run

Requires containerlab and Docker. Each stage is self-contained.

```
# Part A - raw VXLAN
cd static-vxlan
sudo containerlab deploy -t topology.clab.yml
./setup-static.sh
docker exec clab-p2-static-h1 ping -c 3 192.168.100.20
sudo containerlab destroy -t topology.clab.yml --cleanup

# Part B - EVPN, two tenants
cd ../evpn
sudo containerlab deploy -t topology.clab.yml
./setup-evpn.sh
docker exec clab-p2-evpn-h1 ping -c 3 192.168.100.20      # tenant A across leaves
docker exec clab-p2-evpn-h3 ping -c 3 192.168.200.20      # tenant B across leaves
docker exec clab-p2-evpn-leaf1 vtysh -c "show evpn vni"   # both VNIs, MACs, ARPs
```

The setup scripts exist because containerlab does not persist kernel interfaces -
bridges, VXLAN devices, ARP suppression flags and SVIs are rebuilt on every deploy.
Captures were taken with the host's tcpdump run inside a container's network namespace
(`ip netns exec`), since the FRR image ships no capture tools.

## Limitations

A virtual lab demonstrates control-plane and kernel forwarding behaviour, not ASIC
forwarding, buffering, or hardware convergence. Two leaves and four hosts show the
mechanisms (flooding cost, isolation) rather than their behaviour at scale. The overlay
is L2-only; inter-subnet routing (IRB, L3VNI, Type-5) is the next project. MAC mobility
was not exercised.
