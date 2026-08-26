# Symmetric IRB - Project 2.5

## What this shows
The overlay from Project 2 could only bridge: hosts in different subnets could not
communicate even within one tenant. This lab adds routing between subnets, distributed
across the leaves (every leaf is the gateway), while tenants stay isolated. The model is
EVPN symmetric IRB (RFC 9135): route at the ingress leaf, route again at the egress
leaf, over a per-tenant L3VNI.

## Design

| | Tenant A | Tenant B |
|---|---|---|
| Subnets | 192.168.100.0/24 (leaf1, stretched to leaf2), 192.168.101.0/24 (leaf2 only) | 192.168.200.0/24 (leaf1), 192.168.201.0/24 (leaf2) |
| VRF / kernel table | tenantA / 1001 | tenantB / 1002 |
| L3VNI | 1000 (br1000/vxlan1000) | 2000 (br2000/vxlan2000) |
| Gateways | anycast: same IP per subnet, same MAC everywhere (00:00:5e:00:01:01) | same |

Router MACs are per-leaf (aa:bb:cc:00:00:11 / :12), set on each L3VNI's bridge and vxlan
device. Hosts now have default routes - the thing Project 2's hosts deliberately lacked.

Subnet 101 exists ONLY on leaf2. leaf1 has no br101, so it cannot bridge toward that
subnet under any circumstances - it must route via the L3VNI. The topology makes
symmetric IRB unfakeable, and makes asymmetric IRB (which requires every VNI on every
leaf) impossible by construction.

## Symmetric vs asymmetric

| | Asymmetric | Symmetric (built here) |
|---|---|---|
| Ingress leaf | routes + bridges onto the destination L2VNI | routes into the L3VNI |
| Egress leaf | bridges only | routes again |
| Inner dest MAC on wire | destination host's MAC | egress leaf's router MAC |
| Every leaf needs | every VNI, every SVI, every host's ARP | local VNIs + one L3VNI per tenant |

## Evidence 1 - routing works, and the TTL proves it

```
PING 192.168.101.10 (192.168.101.10) 56(84) bytes of data.
64 bytes from 192.168.101.10: icmp_seq=2 ttl=62 time=0.449 ms
64 bytes from 192.168.101.10: icmp_seq=3 ttl=62 time=0.158 ms
```

ttl=62: two routing hops inside the overlay (leaf1 routed, leaf2 routed). Project 2's
captures showed inner ttl=64 - proof of bridging. Same field, opposite verdict.

## Evidence 2 - the wire (pcaps/irb-l3vni-routed.pcap)

```
10.255.0.11.42789 > 10.255.0.12.4789: VXLAN, flags [I] (0x08), vni 1000
aa:bb:cc:00:00:11 > aa:bb:cc:00:00:12, ethertype IPv4, length 98: (ttl 63)
    192.168.100.10 > 192.168.101.10: ICMP echo request
```

Three claims in one packet: the traffic rides the L3VNI (1000, not 100 or 101); the
inner MACs are the two leaves' ROUTER MACs - neither belongs to a host, exactly like
classic routing hands a packet to a next-hop router; and the inner TTL is already
decremented once by the ingress leaf.

## Evidence 3 - stretched subnets have two return paths

In the same capture, the first reply came back bridged over VNI 100 (ttl 63 at h1), the
rest symmetric over VNI 1000 (ttl 62). Packet count: 5 packets on vni 1000, 2 on vni 100.

Cause: subnet 100 is stretched, so leaf2 holds two valid routes back to h1 - its own
connected 192.168.100.0/24 (route locally, bridge across the L2VNI) and h1's /32 host
route from a MAC+IP Type-2 (route via the L3VNI). h1's Type-2 had aged out (the ~5min
lifecycle from Project 2), so reply 1 used the connected /24; the ARP exchange
re-triggered the Type-2, the /32 arrived, and longest-prefix-match flipped the return
to symmetric. Return-path symmetry on stretched subnets depends on host-route presence.

## Evidence 4 - tenant isolation, now three layers deep

```
VRF tenantB:
C>* 192.168.200.0/24 is directly connected, br200
B>* 192.168.201.0/24 [20/0] via 10.255.0.12, br2000 onlink
B>* 192.168.201.10/32 [20/0] via 10.255.0.12, br2000 onlink
```

Tenant B routes across leaves (h3 to h4, ttl=62) through its own L3VNI, and its table
contains no tenant A subnet. Cross-tenant pings fail with 100% loss - and unlike
Project 2, those packets now genuinely reach the leaf (hosts have gateways) and die on
a VRF lookup miss. Isolation is enforced by separate bridges (L2), separate RTs
(control plane), and now separate VRFs + L3VNIs (L3).

## Design note - why the gateway MAC is not advertised
`advertise-svi-ip` is excluded deliberately: it advertises SVI MAC/IPs as Type-2 host
routes and exists for designs with unique per-leaf SVI addresses. With an anycast
gateway, every leaf owns the same MAC locally; advertising it as a host MAC creates
ownership conflict between the leaves. Anycast gateway MACs must stay local-only.

## Limitation
Two leaves, one stretched subnet. MAC mobility (host moves between leaves) is not
exercised. Return-path behaviour on stretched subnets is observed and explained but not
exhaustively characterised.

## Commands used

```
# reachability + isolation
docker exec clab-p25-irb-h1 ping -c 3 192.168.101.10
docker exec clab-p25-irb-h3 ping -c 2 192.168.201.10
docker exec clab-p25-irb-h3 ping -c 2 -W 2 192.168.101.10
docker exec clab-p25-irb-leaf1 vtysh -c "show ip route vrf tenantA"
docker exec clab-p25-irb-leaf1 vtysh -c "show ip route vrf tenantB"

# capture
sudo ip netns exec clab-p25-irb-leaf1 tcpdump -i any -n -Z root \
  -w /tmp/irb-l3vni.pcap udp port 4789
sudo tcpdump -r /tmp/irb-l3vni.pcap -n -e -vv | head -12
```
