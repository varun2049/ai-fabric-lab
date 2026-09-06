#!/usr/bin/env bash
# usage: ./run-spytest.sh [extra spytest args]   e.g. ./run-spytest.sh --noop
exec docker run --rm -it --net=host \
  -v ~/src/sonic-mgmt/spytest:/spytest \
  -v "$(pwd)/testbed_leaf1.yaml:/spytest/testbeds/testbed_leaf1.yaml" \
  -v "$(pwd)/tests:/spytest/tests/local" \
  -v "$(pwd)/logs:/spytest/logs" \
  spytest-runner python3 bin/spytest \
    --testbed-file testbeds/testbed_leaf1.yaml --logs-path logs \
    --skip-tgen --skip-init-config --skip-load-config base --skip-init-checks --feature-group master "$@"
