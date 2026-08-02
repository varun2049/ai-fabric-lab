# MTU Postmortem: VXLAN Overhead Gray Failure — Project 2 Part A

## Symptom
Small pings succeed, large frames fail. Monitoring looks healthy while real
application traffic breaks.

    1400-byte ping: 2 transmitted, 2 received, 0% packet loss
    1472-byte ping: 2 transmitted, 0 received, 100% packet loss
    From 192.168.100.20 icmp_seq=1 Frag needed and DF set (mtu = 1450)

## Cause
VXLAN adds ~50 bytes (outer IP + UDP + VXLAN header), measured directly in the
packet capture: outer length 134 vs inner length 84 = 50 bytes.

With the underlay at MTU 1500, the largest inner frame that fits is 1500 - 50 =
1450 — exactly the value the kernel reported. A 1472-byte payload (1500 inner)
exceeds it and is dropped.

## Fix — must be applied at EVERY layer
Raising only the underlay links was not enough; the first attempt still failed:

    (underlay raised to 9500, vxlan100 still 1500)
    ping: local error: message too long, mtu=1450

Required changes:
- underlay links (leaf uplinks + spine links): mtu 9500
- VXLAN interface (vxlan100): mtu 9000
- bridge (br100): mtu 9000
- flush the endpoint's cached path MTU: ip route flush cache

Result after full fix:

    1472-byte ping: 2 transmitted, 2 received, 0% packet loss

## Takeaways
- Any overlay adds header overhead the underlay must accommodate. Running VXLAN
  on a default 1500 underlay silently breaks full-size frames.
- The fix must cover every layer in the path (underlay, VXLAN interface, bridge).
  Missing one leaves the failure in place.
- Endpoints cache path MTU. Clients keep failing after the network is corrected
  until that cache clears — a common reason MTU incidents appear "unfixed."
