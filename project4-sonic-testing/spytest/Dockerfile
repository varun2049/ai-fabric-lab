# SPyTest runner, derived from the framework's own containers/keysight-ubuntu18/Dockerfile:
# ubuntu:focal for Python 3.8 (pytest 4.6 cannot run on 3.10) and its curated spytest.txt, minus the Keysight/IxNetwork
# installer and lint/docs tooling that a test run does not import.
FROM ubuntu:focal
ENV DEBIAN_FRONTEND=noninteractive TZ=UTC
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential git python3 python3-dev python3-pip python3-setuptools \
    iputils-ping snmp openssh-client sshpass && rm -rf /var/lib/apt/lists/*
COPY reqs.txt /tmp/reqs.txt
RUN pip3 install --no-cache-dir -r /tmp/reqs.txt
WORKDIR /spytest
