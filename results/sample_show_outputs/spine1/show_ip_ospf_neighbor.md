# spine1: show ip ospf neighbor

- Return code: 0

## STDOUT

```
Neighbor ID     Pri State           Up Time         Dead Time Address         Interface                        RXmtL RqstL DBsmL
10.255.0.21       1 Full/-          5m12s             34.123s 10.0.0.1        eth1:10.0.0.0                        0     0     0
10.255.0.22       1 Full/-          5m09s             31.456s 10.0.0.3        eth2:10.0.0.2                        0     0     0
```

## STDERR

```
```

## Notes

Both spine1–leaf1 and spine1–leaf2 links show state `Full/-`. The `-` indicates no DR/BDR role (expected for point-to-point interfaces). Both adjacencies have been stable for ~5 minutes.
