
# Convergence/Resilience Test

leaf1 has two ECMP paths to h2 (via spine1 and spine2). We start a continuous ping from h1 to h2, the cut the link from leaf1 to spine1 mid stream, 
observe the routing table, and then restore the link.

## Results
```
=== 1. BEFORE: route to h2 (expect TWO next-hops) ===
Routing entry for 192.168.12.0/24
  Known via "bgp", distance 20, metric 0, best
  Last update 00:02:56 ago
  * 10.0.1.0, via eth1, weight 1
  * 10.0.11.0, via eth3, weight 1


=== 2. Start continuous ping in background ===
[1] 5506

=== 3. CUT leaf1<->spine1 link ===

=== 4. DURING failure: route to h2 (expect ONE next-hop — via spine2 only) ===
Routing entry for 192.168.12.0/24
  Known via "bgp", distance 20, metric 0, best
  Last update 00:00:02 ago
    10.0.1.0, via eth1 inactive, weight 1
  * 10.0.11.0, via eth3, weight 1


=== 5. RESTORE link ===
[1]+  Done                    docker exec clab-p1-mini-h1 ping -c 40 -i 0.2 192.168.12.10 > /tmp/ping2.log 2>&1

AFTER restore: route to h2 
Routing entry for 192.168.12.0/24
  Known via "bgp", distance 20, metric 0, best
  Last update 00:00:02 ago
  * 10.0.1.0, via eth1, weight 1
  * 10.0.11.0, via eth3, weight 1

Traffic: 40 packets transmitted, 40 received, 0% packet loss, time 8107ms
```
## Conclusion
Cutting the spine1 link immediately marked its next hop inactive in leaf1s route table
While the spine2 next hop stayed active. This proves leaf1 detects the failure and updates forwarding (two paths to one). 
Because ECMP pre installs both paths, this failure only requires deactivating the dead next hop, not computing a new route.

```
echo "=== 1. BEFORE: route to h2 (expect TWO next-hops) ==="
docker exec clab-p1-mini-leaf1 vtysh -c "show ip route 192.168.12.0/24"

echo ""
echo "=== 2. Start continuous ping in background ==="
docker exec clab-p1-mini-h1 ping -c 40 -i 0.2 192.168.12.10 > /tmp/ping2.log 2>&1 &

sleep 3
echo ""
echo "=== 3. CUT leaf1<->spine1 link ==="
docker exec clab-p1-mini-leaf1 ip link set eth1 down
sleep 2

echo ""
echo "=== 4. DURING failure: route to h2 (expect ONE next-hop — via spine2 only) ==="
docker exec clab-p1-mini-leaf1 vtysh -c "show ip route 192.168.12.0/24"

sleep 2
echo ""
echo "=== 5. RESTORE link ==="
docker exec clab-p1-mini-leaf1 ip link set eth1 up
sleep 3

echo ""
echo "=== 6. AFTER restore: route to h2 (expect TWO next-hops again) ==="
docker exec clab-p1-mini-leaf1 vtysh -c "show ip route 192.168.12.0/24"

wait
echo ""
echo "=== 7. PING RESULT (traffic survived?) ==="
grep -E "packets transmitted|packet loss" /tmp/ping2.log

