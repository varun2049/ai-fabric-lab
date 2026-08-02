# ARP Suppression - Project 2 Part B

## What this shows

EVPN lets a leaf answer ARP locally instead of flooding it across the fabric, using the
IP-to-MAC bindings it learns from Type-2 routes. This lab demonstrates that the
`neigh_suppress on` flag alone is not sufficient - the leaf must also have an L3
interface (SVI) on the bridged segment, because that is what causes it to hold and
advertise IP-to-MAC bindings at all. Both configurations were measured under an
identical test.

## Result

| Configuration           | ARP packets | ICMP packets | Total captured |
|-------------------------|-------------|--------------|----------------|
| L2-only bridge (no SVI) | 4           | 6            | 10             |
| With SVI on br100       | 0           | 6            | 6              |

Identical procedure both times: flush both host ARP caches, ping h1 to h2 three times,
capture `udp port 4789` on all leaf1 interfaces. ARP flooding eliminated; ICMP unchanged,
so data-plane forwarding is unaffected. Evidence for every figure is below.

## Configuration A - L2-only bridge
`neigh_suppress on` set on vxlan100 on both leaves, br100 with no IP address.

```
tcpdump: data link type LINUX_SLL2
tcpdump: listening on any, link-type LINUX_SLL2 (Linux cooked v2), snapshot length 262144
^C10 packets captured
10 packets received by filter
0 packets dropped by kernel
```

Traffic generated in a second terminal while that capture ran:

```
PING 192.168.100.20 (192.168.100.20) 56(84) bytes of data.
64 bytes from 192.168.100.20: icmp_seq=1 ttl=64 time=0.402 ms
64 bytes from 192.168.100.20: icmp_seq=2 ttl=64 time=0.267 ms
64 bytes from 192.168.100.20: icmp_seq=3 ttl=64 time=0.405 ms

--- 192.168.100.20 ping statistics ---
3 packets transmitted, 3 received, 0% packet loss, time 2029ms
rtt min/avg/max/mdev = 0.267/0.358/0.405/0.064 ms
```

ARP count and contents:

```
reading from file /tmp/arp-before-svi.pcap, link-type LINUX_SLL2 (Linux cooked v2), snapshot length 262144
Warning: interface names might be incorrect
4
```

```
reading from file /tmp/arp-before-svi.pcap, link-type LINUX_SLL2 (Linux cooked v2), snapshot length 262144
Warning: interface names might be incorrect
ARP, Request who-has 192.168.100.20 tell 192.168.100.10, length 28
ARP, Reply 192.168.100.20 is-at aa:c1:ab:01:72:0b, length 28
ARP, Request who-has 192.168.100.10 tell 192.168.100.20, length 28
ARP, Reply 192.168.100.10 is-at aa:c1:ab:62:49:f7, length 28
```

The capture filter was `udp port 4789`, so every packet in the file was
VXLAN-encapsulated. These four ARP lines are the inner frames - they were wrapped and
carried across the fabric. Both directions ARPed because both host caches were flushed.

ICMP count in the same file:

```
reading from file /tmp/arp-before-svi.pcap, link-type LINUX_SLL2 (Linux cooked v2), snapshot length 262144
Warning: interface names might be incorrect
6
```

## Why a pure L2 bridge cannot suppress
`show evpn vni` shows leaf1 holding zero ARP entries - no IP-to-MAC bindings exist:

```
VNI        Type VxLAN IF              # MACs   # ARPs   # Remote VTEPs  Tenant VRF                           
100        L2   vxlan100              2        0        1               default                              
```

The Type-2 route on the wire (see three-way-correlation.md) shows the same thing:

```
    0x0000:  0019 4604 0aff 000b 0002 2100 010a ff00
    0x0010:  0b00 0200 0000 0000 0000 0000 0000 0000
    0x0020:  0030 aac1 ab62 49f7 0000 0064
```

Reading the NLRI: `0030` is the 48-bit MAC length, `aac1 ab62 49f7` the MAC, and the
`00` immediately following is IP-address-length = 0. A MAC-only advertisement.

Without an L3 interface on the segment, the leaf kernel maintains no neighbour table for
it, so FRR has no IP-to-MAC bindings to advertise or to answer from. Suppression is
enabled but has no data to work with, so ARP falls through to the flood path built by
the Type-3 routes.

## Configuration B - add an SVI
An SVI (Switch Virtual Interface) is an IP address on the bridge itself, making the leaf
a participant on the subnet rather than only a mover of frames. A different IP per leaf -
NOT a shared anycast address, which is the IRB model and belongs to a later project.

```
docker exec clab-p2-evpn-leaf1 ip addr add 192.168.100.1/24 dev br100
docker exec clab-p2-evpn-leaf2 ip addr add 192.168.100.2/24 dev br100
docker exec clab-p2-evpn-leaf1 ping -c 2 -I br100 192.168.100.10
docker exec clab-p2-evpn-leaf2 ping -c 2 -I br100 192.168.100.20
```

The pings force each leaf to ARP for its own local host, which populates the neighbour
table. After that:

```
VNI        Type VxLAN IF              # MACs   # ARPs   # Remote VTEPs  Tenant VRF                           
100        L2   vxlan100              2        2        1               default                              
```

```
Number of ARPs (local and remote) known for this VNI: 2
Flags: I=local-inactive, P=peer-active, X=peer-proxy
Neighbor        Type   Flags State    MAC               Remote ES/VTEP                 Seq #'s
192.168.100.10  local        active   aa:c1:ab:62:49:f7                                0/0
192.168.100.20  remote       active   aa:c1:ab:01:72:0b 10.255.0.12                    0/0
```

`# ARPs` moved from 0 to 2. The remote entry is the significant one: leaf1 knows h2's
IP-to-MAC binding and which VTEP it sits behind, learned from a Type-2 route - not from
observing an ARP. This is what leaf1 answers from.

## Configuration B measured
Same procedure, same filter:

```
tcpdump: data link type LINUX_SLL2
tcpdump: listening on any, link-type LINUX_SLL2 (Linux cooked v2), snapshot length 262144
^C6 packets captured
6 packets received by filter
0 packets dropped by kernel
```

ARP count - zero:

```
reading from file /tmp/arp-after-svi.pcap, link-type LINUX_SLL2 (Linux cooked v2), snapshot length 262144
Warning: interface names might be incorrect
0
```

ICMP count - unchanged at 6:

```
reading from file /tmp/arp-after-svi.pcap, link-type LINUX_SLL2 (Linux cooked v2), snapshot length 262144
Warning: interface names might be incorrect
6
```

Connectivity check:

```
PING 192.168.100.20 (192.168.100.20) 56(84) bytes of data.
64 bytes from 192.168.100.20: icmp_seq=1 ttl=64 time=0.130 ms
64 bytes from 192.168.100.20: icmp_seq=2 ttl=64 time=0.420 ms
64 bytes from 192.168.100.20: icmp_seq=3 ttl=64 time=0.425 ms

--- 192.168.100.20 ping statistics ---
3 packets transmitted, 3 received, 0% packet loss
```

## What was proven
1 ARP suppression depends on IP-to-MAC bindings, not just the `neigh_suppress` flag.
Those bindings require an L3 interface on the bridged segment.
2 With an SVI present, `# ARPs` went 0 to 2 and the remote binding was learned from a
Type-2 route rather than from observed traffic.
3 ARP packets crossing the fabric went 4 to 0 under an identical test procedure.
4 ICMP stayed at 6 in both captures, so the reduction is in broadcast traffic only -
forwarding is unaffected.

## Limitation
Measured on a two-leaf lab with two hosts, so the absolute numbers are small. The point
is directional: flooded ARP scales with fabric size and host count, local suppression
does not. This lab demonstrates the mechanism, not that scaling.

## Raw capture files
pcaps/arp-before-svi.pcap
pcaps/arp-after-svi.pcap

## Commands used

```
# capture - host tcpdump run inside leaf1's netns because the FRR image has no tcpdump.
# -i any because ECMP may hash the encapsulated ARP onto either uplink.
# -Z root stops tcpdump dropping privileges, which fails on an existing root-owned file.
sudo ip netns exec clab-p2-evpn-leaf1 tcpdump -i any -n -Z root \
  -w /tmp/arp-before-svi.pcap udp port 4789

# trigger, in a SECOND terminal while the capture runs
docker exec clab-p2-evpn-h1 ip neigh flush all
docker exec clab-p2-evpn-h2 ip neigh flush all
docker exec clab-p2-evpn-h1 ping -c 3 192.168.100.20

# add the SVI
docker exec clab-p2-evpn-leaf1 ip addr add 192.168.100.1/24 dev br100
docker exec clab-p2-evpn-leaf2 ip addr add 192.168.100.2/24 dev br100
docker exec clab-p2-evpn-leaf1 ping -c 2 -I br100 192.168.100.10
docker exec clab-p2-evpn-leaf2 ping -c 2 -I br100 192.168.100.20

# verification
docker exec clab-p2-evpn-leaf1 vtysh -c "show evpn vni"
docker exec clab-p2-evpn-leaf1 vtysh -c "show evpn arp-cache vni 100"
sudo tcpdump -r /tmp/arp-before-svi.pcap -n | grep -ci arp
sudo tcpdump -r /tmp/arp-after-svi.pcap -n | grep -ci arp
sudo tcpdump -r /tmp/arp-before-svi.pcap -n | grep -ci icmp
sudo tcpdump -r /tmp/arp-after-svi.pcap -n | grep -ci icmp
```
