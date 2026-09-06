# VXLAN Encapsulation Evidence - Project 2 Part A

## What this shows
The Raw VXLAN (no control plane) tunnels a Layer-2 frame across the L3 underlay.
h1 (192.168.100.10) and h2 (192.168.100.20) are on the same subnet but different
leaves. So their traffic is bridged across the fabric inside VXLAN tunnels.

## The packet
Each captured packet is two nested packets:
-Outer: 10.255.0.11 > 10.255.0.12 on UDP dport 4789 = this is the leaf1 loopback to leaf2
 loopback (VTEPs). The underlay only sees this and spines route leaf to leaf.
-VXLAN header: vni 100 = the virtual network ID.
-Inner: 192.168.100.10 > 192.168.100.20 ICMP = this is the real h1 to h2 ping, wrapped inside.

## What the capture reveals
1 Overhead: outer length 134, inner length 84 = which give 134-84 = 50 bytes of VXLAN/UDP/IP 
overhead. 
2 Inner TTL =64 which is undecremented. The hosts believe they are on the same LAN (bridged L2),
even though the outer packet crossed the routed fabric.

## How the packet got here (no control plane)
h1 ARPs for h2, the broadcast floods out of the leaf1's bridge, and the static FDB
entry (00:00:00:00:00:00 dst 10.255.0.12) sends it out the VXLAN tunnel to leaf2, which then
decapsulates and delivers to h2. Reachability was NOT advertised, leaf1 floods the remote VTEP
because it was manually told to. EVPN replaces this flood and learn behavior in Part B of Project 2.

## Raw capture file
pcaps/vxlan.pcap 

## Raw capture output

```
reading from file /tmp/vxlan.pcap, link-type EN10MB (Ethernet), snapshot length 262144
07:45:22.692644 IP (tos 0x0, ttl 64, id 44095, offset 0, flags [none], proto UDP (17), length 134)
    10.255.0.11.35444 > 10.255.0.12.4789: [udp sum ok] VXLAN, flags [I] (0x08), vni 100
IP (tos 0x0, ttl 64, id 26620, offset 0, flags [DF], proto ICMP (1), length 84)
    192.168.100.10 > 192.168.100.20: ICMP echo request, id 19572, seq 1, length 64
07:45:22.692933 IP (tos 0x0, ttl 63, id 244, offset 0, flags [none], proto UDP (17), length 134)
    10.255.0.12.35444 > 10.255.0.11.4789: [udp sum ok] VXLAN, flags [I] (0x08), vni 100
IP (tos 0x0, ttl 64, id 9491, offset 0, flags [none], proto ICMP (1), length 84)
    192.168.100.20 > 192.168.100.10: ICMP echo reply, id 19572, seq 1, length 64
07:45:23.753404 IP (tos 0x0, ttl 64, id 44525, offset 0, flags [none], proto UDP (17), length 134)
    10.255.0.11.35444 > 10.255.0.12.4789: [udp sum ok] VXLAN, flags [I] (0x08), vni 100
IP (tos 0x0, ttl 64, id 26740, offset 0, flags [DF], proto ICMP (1), length 84)
    192.168.100.10 > 192.168.100.20: ICMP echo request, id 19572, seq 2, length 64
07:45:23.753520 IP (tos 0x0, ttl 63, id 1144, offset 0, flags [none], proto UDP (17), length 134)
    10.255.0.12.35444 > 10.255.0.11.4789: [udp sum ok] VXLAN, flags [I] (0x08), vni 100
IP (tos 0x0, ttl 64, id 10214, offset 0, flags [none], proto ICMP (1), length 84)
    192.168.100.20 > 192.168.100.10: ICMP echo reply, id 19572, seq 2, length 64
07:45:24.776386 IP (tos 0x0, ttl 64, id 45102, offset 0, flags [none], proto UDP (17), length 134)
    10.255.0.11.35444 > 10.255.0.12.4789: [udp sum ok] VXLAN, flags [I] (0x08), vni 100
IP (tos 0x0, ttl 64, id 26940, offset 0, flags [DF], proto ICMP (1), length 84)
    192.168.100.10 > 192.168.100.20: ICMP echo request, id 19572, seq 3, length 64
07:45:24.776562 IP (tos 0x0, ttl 63, id 1232, offset 0, flags [none], proto UDP (17), length 134)
    10.255.0.12.35444 > 10.255.0.11.4789: [udp sum ok] VXLAN, flags [I] (0x08), vni 100
IP (tos 0x0, ttl 64, id 10434, offset 0, flags [none], proto ICMP (1), length 84)
    192.168.100.20 > 192.168.100.10: ICMP echo reply, id 19572, seq 3, length 64
07:45:25.797261 IP (tos 0x0, ttl 64, id 45120, offset 0, flags [none], proto UDP (17), length 134)
    10.255.0.11.35444 > 10.255.0.12.4789: [udp sum ok] VXLAN, flags [I] (0x08), vni 100
IP (tos 0x0, ttl 64, id 27017, offset 0, flags [DF], proto ICMP (1), length 84)
    192.168.100.10 > 192.168.100.20: ICMP echo request, id 19572, seq 4, length 64
07:45:25.797449 IP (tos 0x0, ttl 63, id 1662, offset 0, flags [none], proto UDP (17), length 134)
    10.255.0.12.35444 > 10.255.0.11.4789: [udp sum ok] VXLAN, flags [I] (0x08), vni 100
IP (tos 0x0, ttl 64, id 10852, offset 0, flags [none], proto ICMP (1), length 84)
    192.168.100.20 > 192.168.100.10: ICMP echo reply, id 19572, seq 4, length 64
07:45:26.825453 IP (tos 0x0, ttl 64, id 45352, offset 0, flags [none], proto UDP (17), length 134)
    10.255.0.11.35444 > 10.255.0.12.4789: [udp sum ok] VXLAN, flags [I] (0x08), vni 100
IP (tos 0x0, ttl 64, id 27373, offset 0, flags [DF], proto ICMP (1), length 84)
    192.168.100.10 > 192.168.100.20: ICMP echo request, id 19572, seq 5, length 64
07:45:26.825653 IP (tos 0x0, ttl 63, id 2389, offset 0, flags [none], proto UDP (17), length 134)
    10.255.0.12.35444 > 10.255.0.11.4789: [udp sum ok] VXLAN, flags [I] (0x08), vni 100
IP (tos 0x0, ttl 64, id 11116, offset 0, flags [none], proto ICMP (1), length 84)
    192.168.100.20 > 192.168.100.10: ICMP echo reply, id 19572, seq 5, length 64
07:45:27.849257 IP (tos 0x0, ttl 64, id 45995, offset 0, flags [none], proto UDP (17), length 134)
    10.255.0.11.35444 > 10.255.0.12.4789: [udp sum ok] VXLAN, flags [I] (0x08), vni 100
IP (tos 0x0, ttl 64, id 27601, offset 0, flags [DF], proto ICMP (1), length 84)
    192.168.100.10 > 192.168.100.20: ICMP echo request, id 19572, seq 6, length 64
07:45:27.849405 IP (tos 0x0, ttl 63, id 2888, offset 0, flags [none], proto UDP (17), length 134)
    10.255.0.12.35444 > 10.255.0.11.4789: [udp sum ok] VXLAN, flags [I] (0x08), vni 100
IP (tos 0x0, ttl 64, id 12007, offset 0, flags [none], proto ICMP (1), length 84)
    192.168.100.20 > 192.168.100.10: ICMP echo reply, id 19572, seq 6, length 64
07:45:28.040510 IP (tos 0x0, ttl 64, id 46088, offset 0, flags [none], proto UDP (17), length 78)
    10.255.0.11.35924 > 10.255.0.12.4789: [udp sum ok] VXLAN, flags [I] (0x08), vni 100
ARP, Ethernet (len 6), IPv4 (len 4), Request who-has 192.168.100.20 tell 192.168.100.10, length 28
07:45:28.040578 IP (tos 0x0, ttl 63, id 3068, offset 0, flags [none], proto UDP (17), length 78)
    10.255.0.12.35924 > 10.255.0.11.4789: [udp sum ok] VXLAN, flags [I] (0x08), vni 100
ARP, Ethernet (len 6), IPv4 (len 4), Request who-has 192.168.100.10 tell 192.168.100.20, length 28
07:45:28.040727 IP (tos 0x0, ttl 64, id 46089, offset 0, flags [none], proto UDP (17), length 78)
    10.255.0.11.35924 > 10.255.0.12.4789: [udp sum ok] VXLAN, flags [I] (0x08), vni 100
ARP, Ethernet (len 6), IPv4 (len 4), Reply 192.168.100.10 is-at aa:c1:ab:e7:ff:ed (oui Unknown), length 28
07:45:28.040740 IP (tos 0x0, ttl 63, id 3069, offset 0, flags [none], proto UDP (17), length 78)
    10.255.0.12.35924 > 10.255.0.11.4789: [udp sum ok] VXLAN, flags [I] (0x08), vni 100
ARP, Ethernet (len 6), IPv4 (len 4), Reply 192.168.100.20 is-at aa:c1:ab:17:ba:87 (oui Unknown), length 28
07:45:28.869299 IP (tos 0x0, ttl 64, id 46565, offset 0, flags [none], proto UDP (17), length 134)
    10.255.0.11.35444 > 10.255.0.12.4789: [udp sum ok] VXLAN, flags [I] (0x08), vni 100
IP (tos 0x0, ttl 64, id 28145, offset 0, flags [DF], proto ICMP (1), length 84)
    192.168.100.10 > 192.168.100.20: ICMP echo request, id 19572, seq 7, length 64
07:45:28.869489 IP (tos 0x0, ttl 63, id 3308, offset 0, flags [none], proto UDP (17), length 134)
    10.255.0.12.35444 > 10.255.0.11.4789: [udp sum ok] VXLAN, flags [I] (0x08), vni 100
IP (tos 0x0, ttl 64, id 12380, offset 0, flags [none], proto ICMP (1), length 84)
    192.168.100.20 > 192.168.100.10: ICMP echo reply, id 19572, seq 7, length 64
07:45:29.893311 IP (tos 0x0, ttl 64, id 46792, offset 0, flags [none], proto UDP (17), length 134)
    10.255.0.11.35444 > 10.255.0.12.4789: [udp sum ok] VXLAN, flags [I] (0x08), vni 100
IP (tos 0x0, ttl 64, id 28559, offset 0, flags [DF], proto ICMP (1), length 84)
    192.168.100.10 > 192.168.100.20: ICMP echo request, id 19572, seq 8, length 64
07:45:29.893462 IP (tos 0x0, ttl 63, id 4269, offset 0, flags [none], proto UDP (17), length 134)
    10.255.0.12.35444 > 10.255.0.11.4789: [udp sum ok] VXLAN, flags [I] (0x08), vni 100
IP (tos 0x0, ttl 64, id 13023, offset 0, flags [none], proto ICMP (1), length 84)
    192.168.100.20 > 192.168.100.10: ICMP echo reply, id 19572, seq 8, length 64
```
