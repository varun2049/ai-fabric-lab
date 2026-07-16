# Project 1 — eBGP Leaf-Spine Clos Underlay

A data-center fabric built with FRRouting and containerlab: two spines, two
leaves, eBGP everywhere, ECMP across spines. Demonstrates the underlay that
VXLAN/EVPN overlays ride on (Projects 2+).

## Topology

    spine1 (AS65100)   spine2 (AS65100)
       |    \           /    |
       |     \         /     |
    leaf1 (AS65011)  leaf2 (AS65012)
       |                 |
      h1                h2
  192.168.11.10     192.168.12.10

Every leaf connects to every spine. Spines share one ASN (RFC 7938 Tier-1);
each leaf has a unique ASN.

## Addressing

- spine1: AS65100, lo 10.255.0.101, eth1->leaf1 10.0.1.0/31, eth2->leaf2 10.0.2.0/31
- spine2: AS65100, lo 10.255.0.102, eth1->leaf1 10.0.11.0/31, eth2->leaf2 10.0.12.0/31
- leaf1:  AS65011, lo 10.255.0.11, eth1->spine1, eth3->spine2, eth2->h1 (192.168.11.1)
- leaf2:  AS65012, lo 10.255.0.12, eth1->spine1, eth3->spine2, eth2->h2 (192.168.12.1)

## Run it

    sudo containerlab deploy -t topology.clab.yml
    docker exec clab-p1-mini-spine1 vtysh -c "show bgp summary"
    docker exec clab-p1-mini-h1 ping 192.168.12.10
    sudo containerlab destroy -t topology.clab.yml --cleanup

## What this demonstrates

- eBGP Clos underlay (RFC 7938): eBGP on every leaf-spine link, unique leaf ASNs,
  shared spine ASN so ECMP paths have identical AS_PATHs.
- ECMP: leaf installs two equal paths to each remote host subnet. Traffic spread
  depends on 5-tuple entropy — see docs/ecmp-evidence.md.
- Resilience: cutting a spine link marks its next-hop inactive; the pre-installed
  second path keeps forwarding — see docs/convergence-evidence.md.

## Concepts

BGP as DC underlay, eBGP vs iBGP, /31 point-to-point links, loopback router IDs,
ECMP and 5-tuple hashing, control plane (bgpd/Loc-RIB) vs data plane (kernel FIB),
failure convergence.
