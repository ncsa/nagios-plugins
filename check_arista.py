#!/usr/bin/env python
# Author: Jon Schipp <jonschipp@gmail.com, jschipp@illinois.edu>
import sys
import os
import argparse
import imp
import filecmp
import time
from jsonrpclib import Server

# Nagios exit codes
nagios_ok       = 0
nagios_warning  = 1
nagios_critical = 2
nagios_unknown  = 3

# Build accepted check type options for argparse
status_checks=['protocol_status', 'interface_status', 'duplex_status', 'bandwidth_status']
rate_checks=['input_rate', 'output_rate']
other_checks=['dumbno', 'link_status', 'traffic_status']
all_checks = status_checks + rate_checks + other_checks

fail   = nagios_ok

# Create dictionaries to minimize code
direction_map = {
  'input_rate':  'inBitsRate',
  'output_rate': 'outBitsRate',
}

interface_map = {
  'input_rate':  '9/1-24',
  'output_rate': '3/1-16',
}

status_map = {
  'interface_status': 'interfaceStatus',
  'protocol_status':  'lineProtocolStatus',
  'duplex_status':    'duplex',
  'bandwidth_status': 'bandwidth',
}

status_msg = {
  '0':  'OK',
  '1':  'WARNING',
  '2':  'CRITICAL',
  '3':  'UNKNOWN',
}

def cred_usage():
  doc = '''
  Could not open file! Does it exist?

  A file containing the API credentials should be read in using ``-f <file>''
  Its contents should be formatted like this:

  user = 'aristauser'
  password = 'aasldfjasdlfjafajdfalsdfj'
  '''[1:]
  return doc


# interface going down - one is flapping (LinkStatusChanges tracks number of status changes by incrementing - we want to know if it's changing)
# tap ports on line cards 9-10 - we want input metrics, graph them

# notes
# line card 9 - 10gb ports
# line card 10 - 100gb ports (2 up currently)
# line card 3/1-16 we want output statistics


def check_rate(switch, direction, interfaces, skip):
    response = switch.runCmds( 1, ["show interfaces Ethernet" + interfaces] )
    ifs = response[0]["interfaces"]
    d={}
    rc=[]
    for p,info in ifs.items():
      if p in skip:
        continue
      if info["description"] is None:
        continue
      rate = info["interfaceStatistics"].get(direction, 0)  / (1000**2)
      d[p] = [rate, threshold(rate)]
    for nic in d:
      msg=d[nic][1]
      rc.append(msg)
      print status_msg[str(msg)] + ':', nic, "Mbps: %.2f" % d[nic][0]
    exit(max(rc))

def check_status(switch, option, devices, skip):
    status_type=str(option)
    crit_items=["connected", "up", "duplexFull", 10000000000]
    response = switch.runCmds( 1, ["show interfaces"])
    ifs = response[0]["interfaces"]
    fail = nagios_ok
    for p,info in ifs.items():
      if p in skip:
        continue
      if status_type == "bandwidth":
        bw=crit_items[-1]
        if int(info[status_type]) < bw:
          print "CRITICAL: %s Bandwidth: %dGbps" % (p, info[status_type] / (1000**3))
          fail = nagios_critical
          continue
        else: continue
      if devices != "None":
        if p in devices:
          if info[status_type] not in crit_items:
            fail = nagios_critical
            print "CRITICAL: %s %s" % (p, info[status_type])
            continue
          else: print "SUCCESS: %s %s" % (p, info[status_type])
        else: continue
      if devices == "None":
        if info["description"] is None:
          continue
        if status_type not in info:
          continue
        if info[status_type] not in crit_items:
          fail = nagios_critical
          print "CRITICAL: %s  %s" % (p, info[status_type])
    if fail == 0: print "SUCCESS: %s check successful" % status_type
    exit(fail)

def check_traffic_status(switch, skip):
    response = switch.runCmds( 1, ["show interfaces"])
    ifs = response[0]["interfaces"]
    fail = 0
    for p,info in ifs.items():
      if p in skip:
        continue
      if info["description"] is None:
        continue
      if info["lineProtocolStatus"] == "notPresent":
        continue
      if info["interfaceStatus"] == "notconnect":
        continue
      in_traffic = info["interfaceStatistics"]["inPktsRate"]
      out_traffic = info["interfaceStatistics"]["outPktsRate"]
      if in_traffic == 0 and out_traffic == 0:
        print "CRITICAL: %s In: %s Out: %s" % (p, in_traffic, out_traffic)
        fail=1
    if fail == 1:
      return nagios_critical
    else:
      print "SUCCESS: Traffic is being processed by all connected interfaces"
      return nagios_ok

def check_dumbno(switch, skip):
    path    = '/tmp/%s' % os.path.basename(sys.argv[0]) + '-dumbno.state'
    current = path + '.current'
    old     = path + '.old'
    response = switch.runCmds( 1, ["enable", "show ip access-lists"] )
    acl_lists = response[1]["aclList"]
    rules=[]
    for list in acl_lists:
      name = list["name"]
      if name in skip:
        continue
      for rule in list["sequence"]:
        if "permit" in rule["text"]:
          continue
        line = name + " - " + rule["text"]
        rules.append(line)
    if os.path.isfile(current):
      os.rename(current, old)
    save_file(rules, current)
    compare_file(current, old)

def check_link_status(switch, skip):
    path    = '/tmp/%s' % os.path.basename(sys.argv[0]) + '-flap.state'
    current = path + '.current'
    old     = path + '.old'
    key = "lastStatusChangeTimestamp"
    response = switch.runCmds( 1, ["show interfaces"])
    ifs = response[0]["interfaces"]
    data=[]
    for p,info in ifs.items():
      if p in skip:
        continue
      if key not in info:
        continue
      print p, info[key]
    if os.path.isfile(current):
      os.rename(current, old)
    save_file(data, current)
    compare_file(current, old)

def compare_file(current, old):
  if not os.path.isfile(current):
    print "First run, waiting to create history"
    exit(nagios_unknown)
  if not os.path.isfile(old):
    exit(nagios_unknown)
  if filecmp.cmp(current, old):
    print "CRITICAL: Entries haven't changed"
    exit(nagios_critical)
  else:
    print "SUCCESS: Entries rules have changed"
    exit(nagios_ok)

def save_file(data, path):
  file = "\n".join(data)
  try:
    f = open(path, 'w+')
    f.write(file)
    f.close()
  except IOError:
    print "Unable to open file for writing"
    exit(nagios_unknown)

def threshold(value):
  if value >= crit:
    return nagios_critical
  elif value >= warn:
    return nagios_warning
  else:
    return nagios_ok

def arguments():
  global crit
  global warn

  parser = argparse.ArgumentParser(description='Check Arista stats')
  parser.add_argument("-s", "--skip",     type=str, help="Items to skip from check")
  parser.add_argument("-d", "--device",   type=str, help="Devices to check (def: all) (sep: ,) e.g. Ethernet1/1/3")
  parser.add_argument("-T", "--type",     type=str, help="Type of check", choices=all_checks)
  parser.add_argument("-H", "--host",     type=str, help="<host:port> e.g. arista.company.org:443", required=True)
  parser.add_argument("-f", "--filename", type=str, help="Filename that contains API credentials", required=True)
  parser.add_argument("-c", "--critical", type=int, help="Critical value in Mbps")
  parser.add_argument("-w", "--warning",  type=int, help="Warning value in Mbps")
  args = parser.parse_args()

  option = args.type
  host = args.host
  filename = args.filename
  crit = args.critical
  warn = args.warning

  if args.skip:
    skip = args.skip.split(",")
  else:
    skip = "None"
  if args.device:
    devices = args.device.split(",")
  else:
    devices = "None"

  return(option, host, filename, devices, skip)

def get_creds(filename):
  try:
    f = open(filename, "r")
    creds = imp.load_source('data', '', f)
    f.close()
    return creds
  except IOError:
    print cred_usage()
    exit(nagios_unknown)

def main():
  option, host, filename, devices, skip = arguments()
  creds = get_creds(filename)

  url    = 'https://' + creds.user + ':' + creds.password + host + '/command-api'
  switch = Server(url)

  if option == "dumbno":
    check_dumbno(switch, skip)
  elif option == "traffic_status":
    check_traffic_status(switch, skip)
  elif option == "link_status":
    check_link_status(switch, skip)
  elif option in status_checks:
    option  =  status_map[option]
    check_status(switch, option, devices, skip)
  elif option in rate_checks:
    direction  =  direction_map[option]
    interfaces =  interface_map[option]
    check_rate(switch, direction, interfaces, skip)
  else:
    print "Invalid option"
    exit(nagios_unknown)

if __name__ == "__main__":
  main()
