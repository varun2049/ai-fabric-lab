# Captures

| File | Taken on | Contains |
|---|---|---|
| `vxlan.pcap` | leaf1 uplinks, Part A | An h1 to h2 ping encapsulated in VXLAN: outer IP/UDP 4789, VNI 100, inner frame with undecremented TTL (`vxlan-encapsulation.md`) |
| `evpn-refresh-type3-only.pcap` | leaf1-spine1 BGP session | Steady-state EVPN: Type-3 routes only, no MAC advertisements |
| `evpn-type2-birth.pcap` | leaf1-spine1 BGP session | The UPDATE originating h1's Type-2 after its MAC aged out; NLRI decoded by hand in `three-way-correlation.md` |
| `arp-before-svi.pcap` | all leaf1 interfaces, `udp port 4789` | 4 ARP requests crossing the fabric with suppression on but no SVI (`arp-suppression.md`) |
| `arp-after-svi.pcap` | all leaf1 interfaces, `udp port 4789` | 0 ARP requests after adding the SVI; ICMP unchanged |

All captures were taken with the host's tcpdump run inside a container's network
namespace (`ip netns exec`), as the FRR image ships no capture tools.
