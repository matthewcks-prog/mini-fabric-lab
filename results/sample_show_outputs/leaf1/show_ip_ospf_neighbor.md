# leaf1: show ip ospf neighbor

- Return code: 0

## STDOUT

```
Neighbor ID     Pri State           Up Time         Dead Time Address         Interface                        RXmtL RqstL DBsmL
10.255.0.11       1 Full/-          5m14s             38.901s 10.0.0.0        eth1:10.0.0.0                        0     0     0
10.255.0.12       1 Full/-          5m10s             36.224s 10.0.0.4        eth2:10.0.0.4                        0     0     0
```

## STDERR

```
```

## Notes

leaf1 has OSPF adjacencies to both spines:
- spine1 (`10.255.0.11`) via eth1 (10.0.0.0/31 link)
- spine2 (`10.255.0.12`) via eth2 (10.0.0.4/31 link)

Both are in `Full` state — LSA exchange is complete and routing tables are synchronized. The `-` for DR role confirms point-to-point operation (no DR/BDR election).
