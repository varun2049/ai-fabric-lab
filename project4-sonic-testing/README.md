# Project 4 - Testing SONiC with SONiC's Frameworks

The Project 3 fabric validated with the three test frameworks the SONiC ecosystem
uses - DVS tests for the control plane, PTF for the data plane, SPyTest end to end -
each run against `docker-sonic-vs` (community 202411) with the upstream suites, and
each extended with tests written here.

## What this proves

- **Control plane, in the community's own harness.** 16 upstream DVS tests across
  VLAN, VXLAN and EVPN pass against this image, plus two original tests that assert
  tunnel-map behaviour read directly from `orchagent/vxlanorch.cpp`.
- **Data plane, with PTF.** Two cases inject traffic into leaf1 and assert forwarding
  byte for byte - L2 delivery to a learned MAC, and routing between VLANs in a VRF with
  TTL decrement and MAC rewrite.
- **End to end, with SPyTest.** A VLAN lifecycle driven over SSH through the
  framework's API modules and verified through its parsed `show` output, on a
  community build the framework was not written for.
- **Testbeds as engineering.** Each framework runs from a small container with its
  requirements pinned and its reasons documented, reproducible from a clone.

## Documentation
[docs/testing-notes.md](docs/testing-notes.md) - what each framework tests, the tests
written, results, and how the frameworks were run on community SONiC.

## Layout
```
project4-sonic-testing/
  runner/   DVS harness runner (Dockerfile, run-dvs.sh)
  tests/    original DVS tests
  ptf/      PTF runner, run-ptf.sh, tests/
  spytest/  SPyTest runner, testbed, tests/, upstream-fixes.patch, helper scripts
  docs/     testing-notes.md
```

## How to run
See the Reproduce section of the notes. Requires Docker, the Project 3 lab for PTF and
SPyTest, `sonic-swss` (branch 202411) and `sonic-mgmt` (spytest) checked out under `~/src`.

## Scope
Everything runs on the virtual switch, so data-plane assertions cover forwarding
decisions, not line-rate behaviour. LAG-related DVS tests need the `team` kernel
module, absent on this host. The three frameworks are exercised at the depth of one
representative case each beyond the upstream suites.
