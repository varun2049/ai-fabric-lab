#!/usr/bin/env bash
# Run sonic-swss DVS tests from the runner container against docker-sonic-vs.
# usage: ./run-dvs.sh <pytest args>   e.g. ./run-dvs.sh -v test_vlan.py
exec docker run --rm -it --privileged --net=host --pid=host \
  -v /var/run/docker.sock:/var/run/docker.sock \
  -v /var/run/redis-vs:/var/run/redis-vs \
  -v /var/run/netns:/var/run/netns \
  -v ~/src/sonic-swss/tests:/tests -v ~/netlab/project4-sonic-testing/tests:/tests/local -w /tests \
  --entrypoint python3 swss-test-runner -m pytest "$@"
