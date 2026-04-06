#!/bin/sh
set -e

ip addr flush dev eth1 || true
ip addr add 192.168.2.10/24 dev eth1
ip link set eth1 up

ip route del default 2>/dev/null || true
ip route add default via 192.168.2.1
