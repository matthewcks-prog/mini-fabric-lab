# leaf1: show ip bgp summary

- Return code: 0

## STDOUT

```
IPv4 Unicast Summary (VRF default):
BGP router identifier 10.255.0.21, local AS number 65100 VRF default vrf-id 0
BGP table version 5
RIB entries 3, using 576 bytes of memory
Peers 2, using 1448 bytes of memory

Neighbor        V         AS   MsgRcvd   MsgSent   TblVer  InQ OutQ  Up/Down State/PfxRcd   PfxSnt Desc
10.255.0.11     4      65100        92        87        0    0    0 00:35:14            3        1 N/A
10.255.0.12     4      65100        88        84        0    0    0 00:34:58            3        1 N/A

Total number of neighbors 2
```

## STDERR

```
```

## Notes

leaf1 peers only with the two spines (RR clients do not peer with each other):
- Receiving 3 prefixes from each spine: `192.168.2.0/24` (leaf2 subnet), `0.0.0.0/0` (default from edge), and `192.168.1.0/24` (own subnet, reflected back — BGP loop prevention means this is not re-advertised)
- Sending 1 prefix to each spine: `192.168.1.0/24` (the `network 192.168.1.0/24` statement in leaf1's BGP config)
