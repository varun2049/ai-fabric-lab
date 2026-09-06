# Flood and Learn - Why Raw VXLAN Does Not Scale - Project 2 Part A

## Evidence: the overlay depends on one manual entry
Raw VXLAN has no control plane. leaf 1 reaches leaf 2 because of a hand
configured FDB entry

00:00:00:00:00:00 dst 10.255.0.12 self permanent

Flushing it broke the connectivity immediately (ping h1 -> h2): 

3 packets transmitted, 0 received, 100% packet loss

Restoring it fixed it (0% loss). 

3 packets transmitted, 3 received, 0% packet loss

Nothing discovered the remote VTEP, it only worked because it was typed in.

## Learning is reactive, and incomplete

After traffic:

aa:c1:ab:17:ba:87 master br100
00:00:00:00:00:00 dst 10.255.0.12 self permanent

The bridge learned the MAC is out the vxlan100 port, but the VXLAN layer has no
`dst` for it (`nolearning`), so frames are still flooded rather than sent directly.

## Observed cost of flood-and-learn

Both stages were rebuilt from scratch (`containerlab destroy` then `deploy`, then the
stage's setup script), and h1 pinged h2 immediately. Part A, raw VXLAN:

```
PING 192.168.100.20 (192.168.100.20) 56(84) bytes of data.
64 bytes from 192.168.100.20: icmp_seq=1 ttl=64 time=2042 ms
64 bytes from 192.168.100.20: icmp_seq=2 ttl=64 time=1025 ms
64 bytes from 192.168.100.20: icmp_seq=3 ttl=64 time=2.10 ms

--- 192.168.100.20 ping statistics ---
3 packets transmitted, 3 received, 0% packet loss, time 2040ms
rtt min/avg/max/mdev = 2.101/1022.985/2041.620/832.631 ms, pipe 3
```

Part B, EVPN, same test:

```
PING 192.168.100.20 (192.168.100.20) 56(84) bytes of data.
64 bytes from 192.168.100.20: icmp_seq=1 ttl=64 time=1.07 ms
64 bytes from 192.168.100.20: icmp_seq=2 ttl=64 time=0.344 ms
64 bytes from 192.168.100.20: icmp_seq=3 ttl=64 time=0.449 ms

--- 192.168.100.20 ping statistics ---
3 packets transmitted, 3 received, 0% packet loss, time 2020ms
rtt min/avg/max/mdev = 0.344/0.622/1.073/0.321 ms
```

Under flood-and-learn the first two packets sat queued for seconds while the ARP flooded
to the remote VTEP and the reply came back, and only by the third packet - once the FDB
was populated - did latency settle at 2 ms. Under EVPN there is no such delay: h2's MAC
was already installed from a Type-2 route before any traffic was sent, so the first
packet forwards directly.

Caveat: this is three pings on a two-leaf lab, not a controlled benchmark, and BGP
session establishment immediately after deploy may contribute to the first-packet time.
It is reported as observed behaviour consistent with flood-and-learn's reactive
discovery, not as a measurement of it.

## Why this doesn't scale
- Every remote VTEP must be manually configured on every leaf, and redone on change.
- BUM traffic floods to all VTEPs, and cost grows with fabric size
- MAC locations are learned reactively from traffic, never advertised in advance
- Host moves leave stale entries until they age out.
- ARP floods the entire fabric - no leaf can answer for a remote host

## What EVPN fixes (Part B)
VTEPs advertise MAC/IP bindings over MP-BGP, leaves are told where hosts live,
remote VTEPs are discovered automatically (no static FDB), and ARP is suppressed locally.
