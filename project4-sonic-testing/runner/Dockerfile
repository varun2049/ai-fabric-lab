# Runner for the sonic-swss DVS test harness.
# Built FROM the DUT image so the host-side swsscommon bindings match the switch exactly.
FROM docker-sonic-vs:latest
RUN pip install --no-cache-dir --break-system-packages docker pytest flaky redis distro
# The harness runs 'modprobe team' unconditionally; this kernel (WSL2) has no team module.
# The shim lets the session start; LAG tests will fail, everything else runs.
RUN printf '#!/bin/sh\nexit 0\n' > /sbin/modprobe && chmod +x /sbin/modprobe
# Some tests parse the host distro version with StrictVersion (expects "X.Y");
# Debian reports "12", which fails to parse. Report "12.0" so the check works.
RUN sed -i 's/^VERSION_ID=.*/VERSION_ID="12.0"/' /etc/os-release
# The harness shells out to the docker CLI (e.g. docker inspect) as well as using the SDK.
# Install the static client only; the host's daemon is reached via the mounted socket.
RUN apt-get update && apt-get install -y --no-install-recommends curl ca-certificates ethtool iproute2 util-linux && \
    curl -fsSL https://download.docker.com/linux/static/stable/x86_64/docker-27.3.1.tgz \
    | tar xz --strip-components=1 -C /usr/local/bin docker/docker && \
    rm -rf /var/lib/apt/lists/*
ENTRYPOINT ["/bin/bash"]
