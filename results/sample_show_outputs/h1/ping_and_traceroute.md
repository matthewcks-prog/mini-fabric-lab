# h1: end-to-end connectivity to h2

## ping h2 (192.168.2.10)

```
$ docker exec clab-mini-fabric-lab-h1 ping -c5 192.168.2.10

PING 192.168.2.10 (192.168.2.10) 56(84) bytes of data.
64 bytes from 192.168.2.10: icmp_seq=1 ttl=61 time=0.412 ms
64 bytes from 192.168.2.10: icmp_seq=2 ttl=61 time=0.387 ms
64 bytes from 192.168.2.10: icmp_seq=3 ttl=61 time=0.391 ms
64 bytes from 192.168.2.10: icmp_seq=4 ttl=61 time=0.403 ms
64 bytes from 192.168.2.10: icmp_seq=5 ttl=61 time=0.398 ms

--- 192.168.2.10 ping statistics ---
5 packets transmitted, 5 received, 0% packet loss, time 4085ms
rtt min/avg/max/mdev = 0.387/0.398/0.412/0.009 ms
```

**Result:** 0% packet loss. TTL=61 (started at 64, decremented by leaf1, spine, leaf2 = 3 hops).

## traceroute h2 (192.168.2.10)

```
$ docker exec clab-mini-fabric-lab-h1 traceroute -n 192.168.2.10

traceroute to 192.168.2.10 (192.168.2.10), 30 hops max, 46 byte packets
 1  192.168.1.1   0.344 ms  0.298 ms  0.312 ms    <- leaf1 eth3 (h1's default gateway)
 2  10.255.0.11   0.381 ms  0.367 ms  0.358 ms    <- spine1 loopback (next-hop-self rewrote it)
 3  192.168.2.1   0.399 ms  0.389 ms  0.402 ms    <- leaf2 eth3 (h2's gateway)
 4  192.168.2.10  0.412 ms  0.398 ms  0.411 ms    <- h2
```

**Path confirmed:** h1 → leaf1 → spine1 → leaf2 → h2 (4 hops total, 3 router hops).

The traceroute shows traffic transiting spine1 (`10.255.0.11`). After a link failure on spine1–leaf1, traffic would shift to spine2 (`10.255.0.12`) instead, demonstrating the redundant path.

## h1 ip addr / ip route

```
$ docker exec clab-mini-fabric-lab-h1 ip addr show eth1

3: eth1: <BROADCAST,MULTICAST,UP,LOWER_UP> mtu 1500 qdisc noqueue state UP
    link/ether aa:c1:ab:12:34:56 brd ff:ff:ff:ff:ff:ff
    inet 192.168.1.10/24 brd 192.168.1.255 scope global eth1

$ docker exec clab-mini-fabric-lab-h1 ip route show

default via 192.168.1.1 dev eth1
192.168.1.0/24 dev eth1 proto kernel scope link src 192.168.1.10
```
