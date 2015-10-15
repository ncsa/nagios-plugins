# nagios-plugins
Nagios plugins

### check_arista.py

A file containing the API credentials should be read in using `-f <file>`. Its contents should be formatted like this:
```
user = 'aristauser'
password = 'aasldfjasdlfjafajdfalsdfj'
```

Note: Interfaces that do not have a description are skipped for many of the checks.

Check for Mbps rate on input (use `-T output_rate` to test output):
```
./arista.py -f credentials-for-arista.txt -H arista.local -T input_rate -c 1000 -w 500
OK: Ethernet9/18 Mbps: 0.01
OK: Ethernet9/19 Mbps: 0.00
OK: Ethernet9/12 Mbps: 0.00
OK: Ethernet9/13 Mbps: 0.00
OK: Ethernet9/10 Mbps: 0.00
OK: Ethernet9/11 Mbps: 0.00
OK: Ethernet9/16 Mbps: 0.00
OK: Ethernet9/17 Mbps: 2.58
OK: Ethernet9/14 Mbps: 0.00
OK: Ethernet9/15 Mbps: 0.00
OK: Ethernet9/24 Mbps: 0.71
OK: Ethernet9/23 Mbps: 11.74
OK: Ethernet9/22 Mbps: 5.82
OK: Ethernet9/21 Mbps: 175.00
OK: Ethernet9/20 Mbps: 0.00
OK: Ethernet9/8 Mbps: 2.87
OK: Ethernet9/9 Mbps: 0.01
OK: Ethernet9/1 Mbps: 0.00
OK: Ethernet9/2 Mbps: 0.00
WARNING: Ethernet9/3 Mbps: 529.00
OK: Ethernet9/4 Mbps: 9.24
OK: Ethernet9/5 Mbps: 55.80
OK: Ethernet9/6 Mbps: 0.58
OK: Ethernet9/7 Mbps: 0.47
```

Make sure traffic is being processed on all interfaces who are connectd, up, and have description.
```
python arista.py -f credentials-for-arista.txt -H arista.local -T traffic_status
SUCCESS: Traffic is being processed by all connected interfaces
```

Alert on interfaces connected at less than 10Gbps, skipping known slower links.
```
arista.py -f credentials-for-arista.txt -H arista.local --skip Management1/1,Management1/2,Ethernet9/42 -T bandwidth_status
SUCCESS: bandwidth check successful
```

Alert if dumbno rules haven't changed - might mean that flow shunting is no longer working.
```
./arista.py -f credentials-for-arista.txt -H arista.local -T dumbno
CRITICAL: Dumbno rules haven't changed
```

Check line protocol status for a single interface:
```
./arista.py -f credentials-for-arista.txt -H arista.local --device Ethernet3/11 -T protocol_status
SUCCESS: Ethernet3/11 up
SUCCESS: lineProtocolStatus check successful
```

Check if links are not connected at full duplex for connected and up interfaces:
```
arista.py -f credentials-for-arista.txt -H arista.local --skip Management1/2 -T duplex_status
SUCCESS: duplex check successful
```

Check if interfaces are connected:
```
arista.py -f credentials-for-arista.txt -H arista.local --device Ethernet3/11,Ethernet3/12 -T interface_status
SUCCESS: Ethernet3/11 connected
SUCCESS: Ethernet3/12 connected
SUCCESS: interfaceStatus check successful
```

Check line protocol status for all interfaces except those explicitly skipped:
`./arista.py -f credentials-for-arista.txt -H arista.local --skip Ethernet3/20,Ethernet3/23,Ethernet3/22 -T protocol_status`

### check_crashplan_backup.py

A file containing the API credentials should be read in using `-f <file>`. Its contents should be formatted like this:
```
user = 'crashplanuser'
password = 'aasldfjasdlfjafajdfalsdfj'
```

Check if backup has been completed in last 48 hours for host:
```
./check_crashplan_backup.py -f /root/crashplan-credentials.txt -H crashplan.local:4285 -d www1.local
CRITICAL: www1.local: LastCompleteBackup: Aug 20, 2015 12:25:56 AM
```

Check if backup has been completed in last 48 hours for all hosts:
```
./check_crashplan_backup.py -f /root/crashplan-credentials.txt -H crashplan.local:4285
CRITICAL: host1.local: LastCompleteBackup: Aug 20, 2015 11:15:02 AM
CRITICAL: host2.local: LastCompleteBackup: Aug 20, 2015 11:15:07 AM
```
