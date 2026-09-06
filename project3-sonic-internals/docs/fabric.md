# The Fabric on SONiC - Project 3

## What this shows
Project 2.5's design - eBGP Clos underlay, EVPN-VXLAN overlay, two routed tenants with
symmetric IRB - rebuilt with SONiC leaves. Every kernel command from the FRR labs
becomes a CONFIG_DB table row; the pipeline turns those rows into kernel state and SAI
objects. Same proofs, table-driven.

## Design

| | Tenant A | Tenant B |
|---|---|---|
| VRF / L3VNI | VrfA / 1000 (Vlan1000) | VrfB / 2000 (Vlan2000) |
| Subnets | Vlan100 192.168.100.0/24 (leaf1, stretched to leaf2), Vlan101 192.168.101.0/24 (leaf2) | Vlan200 192.168.200.0/24 (leaf1), Vlan201 192.168.201.0/24 (leaf2) |
| Hosts | h1 .100.10 (leaf1 Ethernet4), h2 .101.10 (leaf2 Ethernet4) | h3 .200.10 (leaf1 Ethernet12), h4 .201.10 (leaf2 Ethernet12) |

Underlay unchanged from Project 1: leaf ASNs 65011/65012, spines 65100, loopbacks
10.255.0.11/.12 as VTEPs, FRR spines. Subnet 101 exists only on leaf2, so leaf1 can
reach it only by routing over the L3VNI. Each subnet's gateway lives on one leaf;
anycast gateway is not used (see Scope).

## FRR lab to SONiC: what each command became

| Project 2.5 (kernel command) | Project 3 (CONFIG_DB) |
|---|---|
| `ip link add br100 type bridge` | `VLAN\|Vlan100` |
| `ip link set eth2 master br100` | `VLAN_MEMBER\|Vlan100\|Ethernet4` |
| `ip link add vxlan100 ... local 10.255.0.11` | `VXLAN_TUNNEL\|vtep1` (src_ip) + `VXLAN_TUNNEL_MAP\|vtep1\|map_100_Vlan100` |
| `bridge link set dev vxlan100 neigh_suppress on` | `SUPPRESS_VLAN_NEIGH\|Vlan100` |
| `ip addr add 192.168.100.1/24 dev br100` | `VLAN_INTERFACE\|Vlan100\|192.168.100.1/24` |
| `ip link add tenantA type vrf table 1001` | `VRF\|VrfA` |
| `ip link set br100 master tenantA` | `VLAN_INTERFACE\|Vlan100` field `vrf_name: VrfA` |
| `br1000` + `vxlan1000` (L3VNI devices) | `VLAN\|Vlan1000` + `VXLAN_TUNNEL_MAP` vni 1000 + `VLAN_INTERFACE\|Vlan1000` in VrfA |
| FRR `vrf tenantA / vni 1000` | `VRF\|VrfA` field `vni: 1000` (plus the same zebra stanza) |
| FRR `advertise-all-vni`, VRF BGP instances | unchanged - FRR is FRR inside SONiC |

SONiC gives each L3VNI its own VLAN with an address-less SVI bound to the VRF; the VNI
is mapped to that VLAN like any other. Everything is loaded with `config load`, which
merges into the running CONFIG_DB. On this image bgpd is started after the tables are
loaded and reads `/etc/frr/bgpd.conf`.

## Evidence

**VRFs and VNIs as SONiC sees them**
```
show vrf
VRF    Interfaces
VrfA   Vlan100
       Vlan1000
VrfB   Vlan200
       Vlan2000

show evpn vni
VNI        Type VxLAN IF              # MACs   # ARPs   # Remote VTEPs  Tenant VRF
200        L2   vtep1-200             2        0        0               VrfB
100        L2   vtep1-100             2        0        1               VrfA
1000       L3   vtep1-1000            1        1        n/a             VrfA
2000       L3   vtep1-2000            1        1        n/a             VrfB
```

**The routed path, layer by layer (leaf1 to subnet 101)**
```
vtysh: show ip route vrf VrfA
B>* 192.168.101.0/24 [20/0] via 10.255.0.12, Vlan1000 onlink

vtysh: show bgp l2vpn evpn route type prefix
 *> [5]:[0]:[24]:[192.168.101.0]
                    RT:65012:1000 ET:8 Rmac:02:42:ac:14:14:06

APPL_DB: hgetall 'ROUTE_TABLE:VrfA:192.168.101.0/24'
nexthop 10.255.0.12   ifname Vlan1000   vni_label 1000   router_mac 02:42:ac:14:14:06   protocol bgp

ASIC_DB: keys '*ROUTE_ENTRY*' | grep 192.168.101
ASIC_STATE:SAI_OBJECT_TYPE_ROUTE_ENTRY:{"dest":"192.168.101.0/24","switch_id":"oid:0x21000000000000","vr":"oid:0x3000000000630"}
ASIC_STATE:SAI_OBJECT_TYPE_ROUTE_ENTRY:{"dest":"192.168.101.10/32","switch_id":"oid:0x21000000000000","vr":"oid:0x3000000000630"}
```
The Type-5 carries the L3 route-target and leaf2's router MAC (on SONiC, the system
MAC). APPL_DB carries the VNI and router MAC as next-hop attributes for routeorch. The
ASIC_DB entries sit in VrfA's own virtual router (`vr ...630`, not the default VRF's),
with the /24 from the Type-5 and the /32 host route from h2's Type-2 coexisting.

**The proofs**
```
h1 ping 192.168.101.10        64 bytes from 192.168.101.10: icmp_seq=1 ttl=62
h3 ping 192.168.201.10        3 packets transmitted, 3 received, 0% packet loss
h3 ping 192.168.101.10        2 packets transmitted, 0 received, 100% packet loss
```
ttl=62: routed at both leaves through the L3VNI. Cross-tenant packets reach the leaf
and die on a VRF lookup miss.

## What was proven
1 The Project 2.5 design runs on SONiC from CONFIG_DB tables plus FRR config, with no
kernel commands typed.
2 Symmetric IRB, Type-5 propagation, and three-layer tenant isolation behave
identically on SONiC and on FRR/Linux.
3 The routed path is visible at every layer: FRR, APPL_DB (with VNI and router MAC),
ASIC_DB (in the tenant's virtual router).

## Limitations
Anycast gateway (identical IP and MAC on every leaf) is not configured: the community
image's static-anycast-gateway support was not confirmed for this build, and the design
does not require it. Virtual-platform quirks are listed in
[sonic-internals-trace.md](sonic-internals-trace.md).

## Reproduce
```
cd lab
sudo containerlab deploy -t topology.clab.yml
./setup-fabric.sh
docker exec clab-p3-sonic-h1 ping -c 3 192.168.101.10     # expect ttl=62
```
