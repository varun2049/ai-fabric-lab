# Project 2.5 - EVPN Symmetric IRB + Type-5 Routes

A routed overlay built on the [Project 2](../project2-vxlan-evpn-l2/) EVPN fabric.
Hosts in different subnets, attached to different leaves, communicate through
distributed routing - every leaf is the gateway - while tenants remain fully isolated.
The model is EVPN symmetric IRB (RFC 9135) with Type-5 prefix routes (RFC 9136).

What Project 2 could not do: its overlay only bridged. A tenant with two subnets had
no path between them, and the leaf SVIs were not gateways. This project adds per-tenant
VRFs, anycast gateways (same IP and MAC on every leaf), a per-tenant L3VNI as the
routing plane between leaves, and prefix advertisement over EVPN.

## What this proves

- **Symmetric IRB on the wire**: routed traffic rides the L3VNI (vni 1000) with the
  two leaves' router MACs as the inner Ethernet header - neither inner MAC belongs to
  a host - and the inner TTL decremented at each routing hop. Hosts see `ttl=62`
  (two overlay routing hops), where Project 2's bridged captures showed `ttl=64`.
  Same field, opposite proof.
- **The topology makes it unfakeable**: subnet 101 exists only on leaf2, so leaf1 has
  no bridge for it and can only reach it by routing over the L3VNI.
- **Type-5 prefix routes** carrying the L3 route-target (derived from the L3VNI) and
  the originator's router MAC as extended communities, installed into the tenant VRF
  over the L3VNI SVI - with ECMP via both spines.
- **Host routes and prefix routes coexist**: a /32 from a MAC+IP Type-2 appears the
  moment a host transmits and wins by longest-prefix-match; the /24 Type-5 covers the
  silent-host case.
- **Stretched subnets have two return paths**: replies use the connected subnet
  (bridged) until the host route exists, then flip to symmetric via the L3VNI -
  captured mid-transition.
- **Isolation, three layers deep**: separate bridges (L2), separate route-targets
  (control plane), separate VRFs and L3VNIs (L3). Cross-tenant packets now genuinely
  reach the leaf and die on a VRF lookup miss.

## Layout

```
project2_5-frr-irb-type5/
  lab/                   topology, configs, setup-irb.sh
  docs/                  evidence documents
  pcaps/                 raw captures referenced by the docs
```

## Documentation

1. [irb-explained.md](docs/irb-explained.md) - symmetric vs asymmetric IRB, the
   design, the TTL and wire evidence, the return-path finding
2. [type5-evidence.md](docs/type5-evidence.md) - Type-5 anatomy, VRF installation,
   host/prefix route coexistence

## How to run

Requires containerlab and Docker.

```
cd lab
sudo containerlab deploy -t topology.clab.yml
./setup-irb.sh
docker exec clab-p25-irb-h1 ping -c 3 192.168.101.10        # tenant A, routed across leaves (expect ttl=62)
docker exec clab-p25-irb-h3 ping -c 2 -W 2 192.168.101.10   # cross-tenant (expect 100% loss)
docker exec clab-p25-irb-leaf1 vtysh -c "show ip route vrf tenantA"
```

The setup script builds what containerlab does not persist: VRFs, bridges, VXLAN
devices, anycast gateway addresses, and the per-tenant L3VNI devices carrying each
leaf's router MAC.

## Limitations

Two leaves, one stretched subnet; mechanisms rather than scale. MAC mobility is not
exercised. All Type-5s are redistributed connected subnets - external and summarised
prefixes (the border-leaf case) are not. The anycast gateway MAC is deliberately not
advertised (`advertise-svi-ip` is for unique per-leaf SVI designs; with anycast, the
gateway MAC must remain local-only).
