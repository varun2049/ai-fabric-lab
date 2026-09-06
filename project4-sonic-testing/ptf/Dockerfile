# PTF runner: attaches to the sink container's network namespace, where 28 of leaf1's
# ports terminate, and injects/expects packets on them.
# ptf depends on netifaces (a C extension) - build tools are installed for pip and removed after.
FROM python:3.11-slim
RUN apt-get update && apt-get install -y --no-install-recommends iproute2 tcpdump gcc python3-dev \
    && pip install --no-cache-dir ptf scapy \
    && apt-get purge -y gcc python3-dev && apt-get autoremove -y && rm -rf /var/lib/apt/lists/*
ENTRYPOINT ["ptf"]
