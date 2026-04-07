#!/bin/sh
ip link set eth1 up
ip addr replace 192.168.1.10/24 dev eth1
ip route replace default via 192.168.1.1 dev eth1
