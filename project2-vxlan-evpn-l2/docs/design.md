# Project 2 Design Notes - VXLAN and EVPN L2 Overlay

## What this project is
An EVPN-VXLAN Layer 2 overlay built on the eBGP Clos underlay from Project 1. Two hosts
in the same subnet, sitting on different leaves, communicate as though they share a LAN,
while the fabric underneath routes everything at Layer 3.

Built in two stages so the control plane's contribution is visible:

- **Part A (`static-vxlan/`)** - raw VXLAN, no control plane. Every remote VTEP is
  configured by hand. Demonstrates flood-and-learn and its failure modes.
- **Part B (`evpn/`)** - BGP EVPN replaces the manual configuration. The same kernel
  forwarding entries are produced, but by the control plane instead of by a human.

## Topology

Inherited unchanged from Project 1: two spines, two leaves, full leaf-spine mesh.
Project 2 adds hosts and the overlay; no underlay BGP configuration was retyped.

```
        spine1 (65100)        spine2 (65100)
         10.255.0.101          10.255.0.102
           /      \              /      \
          /        \            /        \
    leaf1 (65011)          leaf2 (65012)
     10.255.0.11            10.255.0.12
      |        |             |        |
    h1(eth2) h3(eth4)      h2(eth2) h4(eth4)
```

### Addressing

| Element | Value |
|---|---|
| spine1 loopback | 10.255.0.101/32 |
| spine2 loopback | 10.255.0.102/32 |
| leaf1 loopback / VTEP | 10.255.0.11/32 |
| leaf2 loopback / VTEP | 10.255.0.12/32 |
| spine1 to leaf1 / leaf2 | 10.0.1.0/31 / 10.0.2.0/31 |
| spine2 to leaf1 / leaf2 | 10.0.11.0/31 / 10.0.12.0/31 |
| Tenant A (VNI 100) | 192.168.100.0/24 - h1 .10, h2 .20 |
| Tenant B (VNI 200) | 192.168.200.0/24 - h3 .10, h4 .20 |
| Leaf SVIs, VNI 100 | leaf1 192.168.100.1, leaf2 192.168.100.2 |
| Leaf SVIs, VNI 200 | leaf1 192.168.200.1, leaf2 192.168.200.2 |

ASNs follow RFC 7938: both spines share 65100, each leaf gets a unique ASN.

## The overlay rides on the underlay

The underlay carries only one thing the overlay needs: reachability between leaf
loopbacks. Each leaf's loopback is its VTEP address, so when leaf1 encapsulates a frame
for leaf2, the resulting outer packet is an ordinary IP packet from 10.255.0.11 to
10.255.0.12. The spines route it with the same BGP and the same FIB they used in
Project 1 - they never inspect the VXLAN header and do not know an overlay exists.

Two consequences worth stating explicitly:

1 **Project 1's ECMP still applies, now to tunnel traffic.** The encapsulated packets are
hashed across both spines like any other flow. The overlay inherits the underlay's
resilience and load balancing for free.
2 **ECMP also applies to the EVPN control plane.** Because both spines share ASN 65100,
EVPN routes arrive over both paths with identical AS_PATHs and BGP installs both as
multipath. See `three-way-correlation.md` for the `*>` and `*=` output.

The host subnets are deliberately NOT advertised into BGP. The leaf's host-facing port
is a bridge port with no IP, so from the underlay's perspective those hosts do not exist
as routable destinations - their frames only ever travel encapsulated.

## Design decisions

**Same subnet across leaves.** Project 1 put hosts in different subnets to force routing.
Project 2 puts them in the same subnet precisely to demonstrate bridging across an L3
fabric - the thing an overlay exists to provide.

**No new BGP sessions for EVPN.** The `l2vpn evpn` address-family was activated on the
existing underlay sessions. MP-BGP (RFC 4760) carries multiple address families over one
session, so the same TCP connection now carries both IPv4 routes and MAC advertisements.

**`advertise-all-vni` rather than per-VNI configuration.** FRR auto-discovers any local
VNI and derives its RD and RT automatically. Adding tenant B required no BGP
configuration change at all.

**SVIs on the leaf bridges.** Without an L3 interface on a bridged segment the leaf holds
no IP-to-MAC bindings, so its Type-2 routes are MAC-only and ARP suppression has nothing
to answer from. See `arp-suppression.md` for the measured before and after. The SVIs use
a different IP per leaf, not a shared anycast address - anycast gateways belong to the
IRB model in a later project.

**Runtime state in setup scripts.** containerlab does not persist kernel interfaces, so
bridges, VXLAN devices, suppression flags and SVIs are rebuilt by `setup-static.sh` and
`setup-evpn.sh`. Each stage rebuilds from destroy to working overlay with one script.

## What EVPN replaced

| Part A (manual) | Part B (EVPN) |
|---|---|
| `bridge fdb append 00:00:00:00:00:00 dst <remote>` typed by hand | Type-3 (IMET) route; zebra installs the same entry |
| Remote MACs learned reactively from received traffic | Type-2 (MAC/IP) routes; MACs known before any traffic |
| ARP floods to every VTEP | ARP answered locally from the EVPN neighbour table |
| No tenant separation mechanism | Route Targets filter imports per VNI |

The kernel forwarding state looks nearly identical in both stages. The difference is
provenance, which the `extern_learn` flag makes visible: entries placed by the control
plane rather than learned from traffic.

## Evidence

| Document | What it establishes |
|---|---|
| `vxlan-encapsulation.md` | Packet structure, VNI, 50-byte overhead, undecremented inner TTL |
| `flood-and-learn.md` | Manual FDB dependency, reactive learning, observed first-packet cost |
| `mtu-postmortem.md` | The 50-byte overhead as a gray failure, and the fix |
| `three-way-correlation.md` | One MAC traced across wire, BGP table, and kernel |
| `arp-suppression.md` | Suppression's dependency on IP-to-MAC bindings; 4 ARP to 0 |
| `multi-tenancy.md` | Two isolated tenants on one fabric; RT as the import filter |

Packet captures in `pcaps/`: VXLAN encapsulation, EVPN Type-3 refresh, Type-2 origination,
ARP before and after suppression.

## Concept answers

<< Write these in your own words - they are the interview rehearsal. >>

**What problem does VXLAN solve, and what does EVPN add on top of it?**

**How does BGP carry MAC addresses?** (MP-BGP, AFI 25 / SAFI 70, MP_REACH_NLRI - you have
this hand-decoded from a real capture in `three-way-correlation.md`.)

**What do Type-2 and Type-3 routes each do?** (Point at what each one replaced from
Part A.)

**What are RD and RT, and which one enforces isolation?**

**Why does VXLAN break MTU, and how is it fixed?**

**How do the overlay and underlay relate?** (Include the ECMP-on-EVPN-routes observation -
it is your own finding, not something the primer told you.)

**Given a MAC in this fabric, how would you locate it?** (The three-way correlation, in
under two minutes.)

## Limitations
- A virtual lab demonstrates control-plane and kernel forwarding behaviour. It does not
  model ASIC forwarding, buffering, or hardware convergence.
- Two leaves and four hosts. Flooding costs and isolation are demonstrated as mechanisms,
  not at a scale where their scaling behaviour is visible.
- L2 overlay only. Inter-subnet routing in the overlay (IRB, L3VNI, Type-5 routes) is out
  of scope and is the subject of the next project.
- MAC mobility (Type-2 re-advertisement with an incremented sequence number) was not
  exercised.

## How to run

```
# Part A - raw VXLAN
cd static-vxlan
sudo containerlab deploy -t topology.clab.yml
./setup-static.sh
docker exec clab-p2-static-h1 ping -c 3 192.168.100.20

# Part B - EVPN
cd evpn
sudo containerlab deploy -t topology.clab.yml
./setup-evpn.sh
docker exec clab-p2-evpn-h1 ping -c 3 192.168.100.20
docker exec clab-p2-evpn-leaf1 vtysh -c "show evpn vni"
```
