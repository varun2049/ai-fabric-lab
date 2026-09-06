#!/usr/bin/env bash
# SPyTest reaches the DUT over SSH; docker-sonic-vs ships without sshd. usage: ./dut-enable-ssh.sh <container>
C=${1:-clab-p3-sonic-leaf1}
docker exec $C bash -c 'apt-get update -qq && apt-get install -y -qq openssh-server sudo >/dev/null 2>&1;
  id admin >/dev/null 2>&1 || useradd -m -s /bin/bash admin; echo "admin:YourPaSsWoRd" | chpasswd;
  usermod -aG sudo admin; echo "admin ALL=(ALL) NOPASSWD:ALL" > /etc/sudoers.d/admin;
  mkdir -p /run/sshd; pgrep -x sshd >/dev/null || /usr/sbin/sshd; echo "sshd running"'
docker inspect -f '{{range .NetworkSettings.Networks}}{{.IPAddress}}{{end}}' $C
