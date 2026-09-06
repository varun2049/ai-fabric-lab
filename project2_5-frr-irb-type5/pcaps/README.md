# Captures

| File | Taken on | Contains |
|---|---|---|
| `irb-l3vni-routed.pcap` | leaf1 uplinks | h1 to h2 across subnets: traffic on VNI 1000 with the leaves' router MACs as the inner Ethernet header and inner TTL decremented; also the stretched-subnet return path switching from VNI 100 (bridged) to VNI 1000 (routed) once the host route exists (`irb-explained.md`) |
