# Three-Way Correlation - Project 2 Part B

## What this shows
One MAC address (`aa:c1:ab:62:49:f7` = h1, attached to leaf1) traced through three
independent layers at the same time: the BGP update on the wire, the Type-2 route
in leaf2's control plane, and the FDB entry in leaf2's kernel. There are NO static FDB
entries anywhere in this lab. Every forwarding entry below was placed by BGP EVPN.


## How the capture was triggered
h1's bridge entry on leaf1 had aged out after -5 minutes idle, so leaf1 had withdrawn
its Type-2. Pinging from h1 forced leaf1 to re-learn the MAC and originate a fresh
Type-2, captured live. The FRR image has no tcpdump, so the host's tcpdump was run
inside leaf1's network namespace.

## Leg 1 - the wire (pcaps/evpn-type2-birth.pcap)

```
	Update Message (2), length: 104
	  Multi-Protocol Reach NLRI (14), length: 44, Flags [OE]: 
	    AFI: VPLS (25), SAFI: EVPN (70)
	    no AFI 25 / SAFI 70 decoder
	    0x0000:  0019 4604 0aff 000b 0002 2100 010a ff00
	    0x0010:  0b00 0200 0000 0000 0000 0000 0000 0000
	    0x0020:  0030 aac1 ab62 49f7 0000 0064
	  Origin (1), length: 1, Flags [T]: IGP
	    0x0000:  00
	  AS Path (2), length: 6, Flags [TE]: 65011 
	    0x0000:  0201 0000 fdf3
	  Extended Community (16), length: 16, Flags [OT]: 
	    encapsulation (0x030c), Flags [none]: Tunnel type: VXLAN
	    target (0x0002), Flags [none]: 65011:100 (= 0.0.0.100)
```

AFI 25 / SAFI 70 is MP-BGP carrying EVPN. tcpdump has no EVPN NLRI decoder, so the 
hex codes by hand:

- `0002` = route type 2 (MAC/IP Advertisement)
- `0001 0aff000b 0002` = Route Distinguisher 10.255.0.11:2
- `0030` = 48-bit MAC length
- `aac1 ab62 49f7` = the MAC itself, on the wire
- `00` = IP address length 0 (MAC-only route, no IP advertised)
- `0000 64` = VNI 100
- `target 65011:100` = the Route Target remote leaves import on


A second copy appears with AS Path `65100 65011`, sent by spine1 BACK to leaf1
(source 10.0.1.0). leaf1 discards it: its own ASN 65011 is already in the
AS_PATH. BGP's loop prevention from Project 1, operating on EVPN routes, visible
on the wire.

## Leg 2 - leaf2's control plane

```
Route Distinguisher: 10.255.0.11:2
 *>  [2]:[0]:[48]:[aa:c1:ab:62:49:f7]
                    10.255.0.11(spine1)      0 65100 65011 i
                    RT:65011:100 ET:8
 *=  [2]:[0]:[48]:[aa:c1:ab:62:49:f7]
                    10.255.0.11(spine2)      0 65100 65011 i
                    RT:65011:100 ET:8
```

Same MAC, same RD, same RT as the wire capture - this is that message, received and
installed. The next hop is leaf1's loopback, not the spine it arrived from: spines
relay EVPN routes without rewriting the next hop, so the tunnel runs leaf to leaf.

Two paths, `*>` via spine1 and `*=` via spine2. Both spines share ASN 65100, so the
AS_PATHs are identical and BGP installs both. The Project 1 ECMP design is
load-balancing EVPN route distribution itself, not just data traffic.

## Leg 3 - leaf2's kernel

```
aa:c1:ab:62:49:f7 extern_learn master br100
aa:c1:ab:62:49:f7 dst 10.255.0.11 self extern_learn
```

`extern_learn` means installed by the control plane (zebra), not learned from traffic.
Two entries doing two jobs: the bridge entry says "exit via port vxlan100", the VXLAN
entry says "tunnel it to VTEP 10.255.0.11". This is what packets actually forward on.

## The chain

```
h1 speaks
  -> leaf1 learns MAC on eth2
  -> bgpd originates Type-2
  -> UPDATE crosses the fabric            (Leg 1)
  -> leaf2 imports it via RT 65011:100    (Leg 2)
  -> zebra installs the FDB entry         (Leg 3)
  -> traffic to h1 tunnels straight to 10.255.0.11, no flooding
```

In Part A this knowledge could only come from flooding traffic and learning from the
replies. Here leaf2 was told, before ever receiving a frame from h1.

## What was proven
1 The same MAC, RD and RT appear across wire, BGP table and kernel - byte for byte.
2 Forwarding state originates in BGP, not data-plane learning (`extern_learn`, and no
static entries exist).
3 MAC advertisements are dynamic: they age out with bridge learning and are
re-originated when the host speaks. This capture is a re-origination event.

## Raw capture file
pcaps/evpn-type2-birth.pcap

## Commands used

```
# capture - host tcpdump borrowed into leaf1's netns (FRR image has no tcpdump)
sudo ip netns exec clab-p2-evpn-leaf1 tcpdump -i eth1 -w /tmp/type2-birth.pcap tcp port 179

# trigger - aged-out MAC forces a fresh Type-2 on next traffic
docker exec clab-p2-evpn-h1 ping -c 3 192.168.100.20

# legs 2 and 3
docker exec clab-p2-evpn-leaf2 vtysh -c "show bgp l2vpn evpn route type macip"
docker exec clab-p2-evpn-leaf2 bridge fdb show dev vxlan100
```
