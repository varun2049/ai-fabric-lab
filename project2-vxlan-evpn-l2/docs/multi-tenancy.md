# Multi-Tenant Isolation - Project 2 Part B

## What this shows
Two tenants sharing one physical fabric with no reachability between them. VNI 100 and
VNI 200 ride the same spines, the same links, and the same BGP sessions, yet neither
tenant's MAC addresses ever appear in the other's forwarding tables. Isolation comes
from separate bridges in the kernel and differing Route Targets in BGP - not from
filtering anywhere in the fabric.

## Design

| Property | Tenant A | Tenant B |
|---|---|---|
| VNI | 100 | 200 |
| Subnet | 192.168.100.0/24 | 192.168.200.0/24 |
| Hosts | h1 .10 (leaf1), h2 .20 (leaf2) | h3 .10 (leaf1), h4 .20 (leaf2) |
| Leaf port | eth2 | eth4 |
| Bridge / VXLAN dev | br100 / vxlan100 | br200 / vxlan200 |
| SVI (leaf1 / leaf2) | 192.168.100.1 / .2 | 192.168.200.1 / .2 |

Both tenants deliberately use the same host addresses (.10 and .20). Overlapping tenant
address space is normal in multi-tenant fabrics, and it makes the isolation test
unambiguous.

No FRR configuration was changed to add tenant B. `advertise-all-vni` causes FRR to
auto-discover any local VNI and originate EVPN routes for it, deriving the RD and RT
automatically.

## Both tenants work across leaves

```
PING 192.168.100.20 (192.168.100.20) 56(84) bytes of data.
64 bytes from 192.168.100.20: icmp_seq=1 ttl=64 time=0.155 ms
64 bytes from 192.168.100.20: icmp_seq=2 ttl=64 time=0.384 ms

--- 192.168.100.20 ping statistics ---
2 packets transmitted, 2 received, 0% packet loss, time 1054ms
rtt min/avg/max/mdev = 0.155/0.269/0.384/0.114 ms
PING 192.168.200.20 (192.168.200.20) 56(84) bytes of data.
64 bytes from 192.168.200.20: icmp_seq=1 ttl=64 time=0.172 ms
64 bytes from 192.168.200.20: icmp_seq=2 ttl=64 time=0.403 ms

--- 192.168.200.20 ping statistics ---
2 packets transmitted, 2 received, 0% packet loss, time 1041ms
rtt min/avg/max/mdev = 0.172/0.287/0.403/0.115 ms
```

Both VNIs are present and independently converged on leaf1:

```
VNI        Type VxLAN IF              # MACs   # ARPs   # Remote VTEPs  Tenant VRF                           
200        L2   vxlan200              2        2        1               default                              
100        L2   vxlan100              2        2        1               default                              
```

## No cross-tenant reachability

```
PING 192.168.200.10 (192.168.200.10) 56(84) bytes of data.

--- 192.168.200.10 ping statistics ---
2 packets transmitted, 0 received, 100% packet loss, time 1042ms

PING 192.168.100.10 (192.168.100.10) 56(84) bytes of data.

--- 192.168.100.10 ping statistics ---
2 packets transmitted, 0 received, 100% packet loss, time 1017ms
```

These pings are consistent with isolation but are not by themselves proof of it: the
hosts have no route to the other subnet and no default gateway, so the packets never
left the host. The control-plane evidence below is the actual proof.

## The proof - separate MAC tables

leaf1 holds two independent forwarding tables, one per VNI:

```
Number of MACs (local and remote) known for this VNI: 2
Flags: N=sync-neighs, I=local-inactive, P=peer-active, X=peer-proxy
MAC               Type   Flags Intf/Remote ES/VTEP            VLAN  Seq #'s
aa:c1:ab:2a:21:89 local        eth2                                 0/0
aa:c1:ab:54:16:4d remote       10.255.0.12                          0/0
```

```
Number of MACs (local and remote) known for this VNI: 2
Flags: N=sync-neighs, I=local-inactive, P=peer-active, X=peer-proxy
MAC               Type   Flags Intf/Remote ES/VTEP            VLAN  Seq #'s
aa:c1:ab:2d:e8:02 local        eth4                                 0/0
aa:c1:ab:ae:94:4e remote       10.255.0.12                          0/0
```

VNI 100 contains only h1 and h2's MACs; VNI 200 only h3 and h4's. No MAC appears in
both, even though every route for both tenants crossed the same two BGP sessions.

## The mechanism - Route Targets

```
Route Distinguisher: 10.255.0.11:2
                    ET:8 RT:65011:100
                    ET:8 RT:65011:100
                    ET:8 RT:65011:100
Route Distinguisher: 10.255.0.11:3
                    ET:8 RT:65011:200
                    ET:8 RT:65011:200
                    ET:8 RT:65011:200
Route Distinguisher: 10.255.0.12:2
                    RT:65012:100 ET:8
                    RT:65012:100 ET:8
                    RT:65012:100 ET:8
                    RT:65012:100 ET:8
                    RT:65012:100 ET:8
                    RT:65012:100 ET:8
Route Distinguisher: 10.255.0.12:3
                    RT:65012:200 ET:8
                    RT:65012:200 ET:8
                    RT:65012:200 ET:8
                    RT:65012:200 ET:8
                    RT:65012:200 ET:8
                    RT:65012:200 ET:8
```

Four RD/RT pairs, one per leaf per VNI. FRR derives both automatically: the RT is
`ASN:VNI`, and the RD is `router-id:index` where the index is a per-VNI counter (VNI 100
got 2, VNI 200 got 3) - the RD only needs to be unique, while the RT carries the VNI
identity.

Two distinct mechanisms enforce the separation:

1 **Kernel - separate bridges.** br100 and br200 are independent broadcast domains. A
frame entering br100 can only leave through a port enslaved to br100. eth2 is in br100,
eth4 in br200, and no path exists between them.
2 **Control plane - Route Targets.** Every route crosses every BGP session; the spines
relay all four RTs without inspecting them. Each leaf imports a route into a VNI only
when the RT matches. This is what keeps tenant B's MACs out of tenant A's tables.

## What was proven
1 A single fabric carries two isolated L2 segments with overlapping host addressing.
2 Adding a tenant required no BGP configuration change - `advertise-all-vni` discovered
VNI 200 and derived its RD and RT automatically.
3 Each VNI maintains its own MAC table with no cross-population, despite both tenants'
routes traversing identical BGP sessions.
4 RTs differ per VNI (`65011:100` vs `65011:200`), which is the import filter that
enforces control-plane separation.

## Limitation
Isolation here is between two L2VNIs in the default VRF. Isolation between routed
tenants (separate VRFs, L3VNIs, and inter-subnet routing) is a different mechanism and
is out of scope for this project.

## Commands used

```
# reachability
docker exec clab-p2-evpn-h1 ping -c 2 192.168.100.20
docker exec clab-p2-evpn-h3 ping -c 2 192.168.200.20
docker exec clab-p2-evpn-h1 ping -c 2 -W 2 192.168.200.10
docker exec clab-p2-evpn-h3 ping -c 2 -W 2 192.168.100.10

# control plane
docker exec clab-p2-evpn-leaf1 vtysh -c "show evpn vni"
docker exec clab-p2-evpn-leaf1 vtysh -c "show evpn mac vni 100"
docker exec clab-p2-evpn-leaf1 vtysh -c "show evpn mac vni 200"
docker exec clab-p2-evpn-leaf1 vtysh -c "show bgp l2vpn evpn" | grep -E "RT:|Route Distinguisher"
```
