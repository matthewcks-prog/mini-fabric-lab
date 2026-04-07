# spine2: show ip bgp summary

- Return code: 0

## STDOUT

```
IPv4 Unicast Summary (VRF default):
BGP router identifier 10.255.0.12, local AS number 65100 VRF default vrf-id 0
BGP table version 8
RIB entries 5, using 960 bytes of memory
Peers 3, using 2176 bytes of memory
Peer groups 1, using 64 bytes of memory

Neighbor        V         AS   MsgRcvd   MsgSent   TblVer  InQ OutQ  Up/Down State/PfxRcd   PfxSnt Desc
10.255.0.21     4      65100        84        88        0    0    0 00:34:58            1        3 N/A
10.255.0.22     4      65100        81        86        0    0    0 00:34:44            1        3 N/A
172.16.0.3      4      65050        59        61        0    0    0 00:28:21            1        2 N/A

Total number of neighbors 3
```

## STDERR

```
```

## Notes

spine2 mirrors spine1's BGP state — symmetric dual-spine design confirmed. Both spines independently receive the default route from edge1 and independently reflect host prefixes to leaves. This provides full redundancy: if either spine fails, the other continues to carry all routes.
