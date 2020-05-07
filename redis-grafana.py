#!/usr/bin/env python

import socket
import sys
import time
import json
import os

#------------------------settings-------------------------
CARBON_SERVER = 'your.server.here'
CARBON_PORT = 2003
REDIS_SERVER = 'localhost'
REDIS_PORT = 6379
REDIS_PASSWORD = 'password'
STATS_TMP_FILE = '/tmp/redis.json'
#---------------------------------------------------------
metric_server = 'undefined'

f = open('/etc/hostname', 'r')
metric_server = f.read().strip();
f.close()


COUNTERS = [
    'connected_clients',
    'blocked_clients',
    'used_memory',
    'used_memory_rss'
]

DIFF_COUNTERS = [
    'total_connections_received',
    'total_commands_processed',
    'total_net_input_bytes',
    'total_net_output_bytes',
    'keyspace_hits',
    'keyspace_misses',
]

def linesplit(socket):
    buffer = socket.recv(4096)
    buffering = True
    while buffering:
        if "\n" in buffer:
            (line, buffer) = buffer.split("\n", 1)
            if(line == "\r"):
                buffering = False
            yield line
        else:
            more = socket.recv(4096)
            if not more:
                buffering = False
            else:
                buffer += more
    if buffer:
        yield buffer

def send_metrics(m):
    if (len(m)>0):
        timestamp = int(time.time())
        message = "";
        for mes in m:
            message = message + mes + " "+ str(timestamp) + "\n"
        sock = socket.socket()
        sock.connect((CARBON_SERVER, CARBON_PORT))
        sock.sendall(message)
        sock.close()

s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
s.connect((REDIS_SERVER, int(REDIS_PORT)))
s.send("INFO\n")
stats = {}
metrics = []
stats['counters'] = {}
stats['diff_counters'] = {}
stats['keyspaces'] = {}
for line in linesplit(s):
    if 'Authentication required' in line:
	s.send("AUTH "+REDIS_PASSWORD+"\n")
	s.send("INFO\n")
    if 'invalid password' in line:
	print line
	s.close()
	exit()
    if '# Clients' in line:
        for l in line.split("\n"):
	    if ':keys' in l:
                (keyspace, kstats) = l.split(':')
		stats['keyspaces'][keyspace] = {}
                for ks in kstats.split(','):
                    (n, v) = ks.split('=')
    		    stats['keyspaces'][keyspace][n] = v.rstrip()
	    elif ':' in l:
        	(name, value) = l.split(':')
		if (name in COUNTERS):
		    stats['counters'][name] = value.rstrip()
		if (name in DIFF_COUNTERS):
		    stats['diff_counters'][name] = value.rstrip()
        
s.close()
for metric in stats['counters']:
    metrics.append("host."+metric_server+".redis."+metric+" "+str(stats['counters'][metric]))
for metric in stats['keyspaces']:
    metrics.append("host."+metric_server+".redis."+metric+".keys "+str(stats['keyspaces'][metric]['keys']))
if os.path.isfile(STATS_TMP_FILE):
    old_data = json.load( open( STATS_TMP_FILE ) )
    for metric in old_data:
	metrics.append("host."+metric_server+".redis."+metric+" "+str(int(stats['diff_counters'][metric]) - int(old_data[metric])))


send_metrics(metrics)

json.dump( stats['diff_counters'], open( STATS_TMP_FILE, 'w' ) )
