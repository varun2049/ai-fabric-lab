"""SPyTest case against leaf1 (SONiC, docker-sonic-vs) over SSH.

Creates VLAN 300, adds Ethernet28 as an untagged member, verifies both through the
framework's 'show vlan config' parser, then removes them and verifies the removal.
"""
import pytest
from spytest import st
import apis.switching.vlan as vlan_obj

VID = "300"
PORT = "Ethernet28"

@pytest.fixture(scope="module", autouse=True)
def leaf1_module_hooks(request):
    global vars
    vars = st.ensure_min_topology("D1")
    yield

def test_vlan_create_member_verify_delete():
    dut = vars.D1
    if VID in [str(v) for v in vlan_obj.get_vlan_list(dut)]:
        st.log("stale VLAN %s present, removing first" % VID)
        vlan_obj.delete_vlan_member(dut, VID, PORT, tagging_mode=False, skip_error_check=True)
        vlan_obj.delete_vlan(dut, VID)
    st.log("create VLAN %s" % VID)
    if not vlan_obj.create_vlan(dut, VID):
        st.report_fail("vlan_create_fail", VID)
    st.log("add %s as untagged member" % PORT)
    if not vlan_obj.add_vlan_member(dut, VID, PORT, tagging_mode=False):
        st.report_fail("vlan_untagged_member_fail", PORT, VID)
    # verify via 'show vlan config': the framework's 'show vlan brief' template expects a
    # DHCP-helper column that community 202411 does not print (it prints Proxy ARP), so
    # that parser yields no members on this build.
    st.log("verify via show vlan config")
    if not vlan_obj.verify_vlan_config(dut, VID, untagged=[PORT]):
        st.report_fail("vlan_untagged_member_fail", PORT, VID)
    st.log("clean up and verify removal")
    vlan_obj.delete_vlan_member(dut, VID, PORT, tagging_mode=False)
    vlan_obj.delete_vlan(dut, VID)
    if VID in [str(v) for v in vlan_obj.get_vlan_list(dut)]:
        st.report_fail("vlan_delete_fail", VID)
    st.report_pass("test_case_passed")
