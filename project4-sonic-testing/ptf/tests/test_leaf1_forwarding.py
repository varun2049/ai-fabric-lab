"""PTF tests against leaf1 (SONiC, docker-sonic-vs) through the sink's ports.

  port 0 = Ethernet16 (Vlan100)   port 1 = Ethernet20 (Vlan100)   port 2 = Ethernet24 (Vlan110, VrfA)

L2ForwardInVlan        - a frame to a learned MAC is forwarded to that port only.
RouteBetweenVlansInVrf - a packet to the gateway is routed into Vlan110: TTL decremented,
                         source MAC rewritten to the gateway's, delivered on port 2.
"""
import time
import ptf
import ptf.testutils as tu
from ptf.base_tests import BaseTest
from scapy.all import Ether, ARP

P0, P1, P2 = 0, 1, 2
MAC0, MAC1, MAC2 = "00:aa:00:00:00:01", "00:aa:00:00:00:02", "00:aa:00:00:00:03"
GW100, H100, PEER100 = "192.168.100.1", "192.168.100.50", "192.168.100.51"
H110 = "192.168.110.50"

def poll_pkt(test, port, timeout=3):
    res = tu.dp_poll(test, port_number=port, timeout=timeout)
    pkt = getattr(res, "packet", None) if res is not None else None
    if pkt is None and isinstance(res, tuple) and len(res) >= 3:
        pkt = res[2]
    return pkt


class L2ForwardInVlan(BaseTest):
    def setUp(self):
        BaseTest.setUp(self)
        self.dataplane = ptf.dataplane_instance
        self.dataplane.flush()

    def runTest(self):
        # teach the switch that MAC1 lives on port 1 (a broadcast ARP from port 1 is learned)
        learn = tu.simple_arp_packet(eth_src=MAC1, hw_snd=MAC1, ip_snd=PEER100, ip_tgt=H100, arp_op=1)
        tu.send_packet(self, P1, learn)
        time.sleep(1)
        self.dataplane.flush()

        pkt = tu.simple_udp_packet(eth_dst=MAC1, eth_src=MAC0, ip_src=H100, ip_dst=PEER100)
        tu.send_packet(self, P0, pkt)
        tu.verify_packet(self, pkt, P1)        # forwarded unchanged to the learned port
        tu.verify_no_packet(self, pkt, P2)     # and not into the other VLAN


class RouteBetweenVlansInVrf(BaseTest):
    def setUp(self):
        BaseTest.setUp(self)
        self.dataplane = ptf.dataplane_instance
        self.dataplane.flush()

    def runTest(self):
        # 1. resolve the gateway's MAC the way a host would
        req = tu.simple_arp_packet(eth_src=MAC0, hw_snd=MAC0, ip_snd=H100, ip_tgt=GW100, arp_op=1)
        tu.send_packet(self, P0, req)
        rep = poll_pkt(self, P0)
        assert rep is not None, "no ARP reply from the gateway"
        gw_mac = Ether(rep)[ARP].hwsrc

        # 2. first routed packet makes the switch ARP for H110 on Vlan110; answer it from port 2
        ippkt = tu.simple_udp_packet(eth_dst=gw_mac, eth_src=MAC0, ip_src=H100, ip_dst=H110, ip_ttl=64)
        tu.send_packet(self, P0, ippkt)
        arp_req = None
        for _ in range(5):
            p = poll_pkt(self, P2, timeout=2)
            if p is not None and ARP in Ether(p) and Ether(p)[ARP].pdst == H110:
                arp_req = Ether(p); break
        assert arp_req is not None, "switch never ARPed for %s on Vlan110" % H110
        reply = tu.simple_arp_packet(eth_dst=arp_req.src, eth_src=MAC2, arp_op=2,
                                     hw_snd=MAC2, hw_tgt=arp_req[ARP].hwsrc,
                                     ip_snd=H110, ip_tgt=arp_req[ARP].psrc)
        tu.send_packet(self, P2, reply)
        time.sleep(1)
        self.dataplane.flush()

        # 3. the routed packet: TTL 64 -> 63, MACs rewritten, out on Vlan110's port
        tu.send_packet(self, P0, ippkt)
        expected = tu.simple_udp_packet(eth_dst=MAC2, eth_src=gw_mac, ip_src=H100, ip_dst=H110, ip_ttl=63)
        tu.verify_packet(self, expected, P2)
        tu.verify_no_packet(self, expected, P1)
