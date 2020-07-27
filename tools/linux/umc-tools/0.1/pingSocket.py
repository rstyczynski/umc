#!/usr/bin/env python2

import socket
import time
import datetime
import time as pytime
import csv
import sys
import getopt

from time import gmtime, strftime

class Unbuffered(object):
   def __init__(self, stream):
       self.stream = stream
   def write(self, data):
       self.stream.write(data)
       self.stream.flush()
   def writelines(self, datas):
       self.stream.writelines(datas)
       self.stream.flush()
   def __getattr__(self, attr):
       return getattr(self.stream, attr)
   

writer = csv.writer(sys.stdout, delimiter=',')

def getStats(targetSystem, targetPort):
    resolv=-1
    resolvFull=-1
    connect=-1
    send=-1
    response=-1
    close=-1
    addressStr='n/a'
    addressFullStr='n/a'
    responseStr='n/a'
    errorStr='OK'
    #
    try:
        s = socket.socket(socket.AF_INET, monitor_transport) 
        s.settimeout(2)
        #
        start_time = time.time()
        addressFullStr=socket.getaddrinfo(targetSystem, targetPort)
        ms = (time.time() - start_time ) * 1000
        resolvFull=ms
        #
        start_time = time.time()
        addressStr =  socket.gethostbyname(targetSystem) 
        ms = (time.time() - start_time ) * 1000
        resolv=ms

        # TCP
        if (monitor_transport == socket.SOCK_STREAM):
            start_time = time.time()
            s.connect((addressStr , targetPort))
            ms = (time.time() - start_time ) * 1000
            connect=ms
            #
            start_time = time.time()
            s.sendall("GET / HTTP/1.1\r\nHost: " + targetSystem + "\r\n\r\n")
            #s.sendall("\n")
            ms = (time.time() - start_time ) * 1000
            send=ms
            #
            start_time = time.time()
            responseStr = s.recv(4096)
            ms = (time.time() - start_time ) * 1000
            response=ms
            if makeResponseShort:
                responseStr = responseStr[:10]
            #
            start_time = time.time()
            s.close
            ms = (time.time() - start_time ) * 1000
            close=ms

        # UDP
        if (monitor_transport == socket.SOCK_DGRAM):
            start_time = time.time()
            socket.sendto('Hello!', (addressStr, targetPort))
            ms = (time.time() - start_time ) * 1000
            connect=ms

    except Exception as ex:
        errorStr = str(ex)
    #
    #
    if(timestamp): 
        now = datetime.datetime.now()
        writer.writerow([now.strftime('%d-%m-%Y' + timedelimiter + '%H:%M:%S'), strftime("%z", gmtime()), str(int(pytime.time())), system, source, 
                                      targetSystem, targetPort, addressStr, addressFullStr, resolv, resolvFull, connect, send, response, close, responseStr, errorStr])
    else:
        writer.writerow([targetSystem, targetPort, addressStr, addressFullStr, resolv, resolvFull, connect, send, response, close, 
                     responseStr, errorStr])

    
def printStats(monitor_subsystems, monitor_count, monitor_interval):
    
    if not noheader: printHeader()
    #
    for cnt in range(0, monitor_count):
        for targetFull in monitor_subsystems:
            targetSystem, targetPortStr = targetFull.split(':')   
            targetPort = int(targetPortStr)
            #
            getStats(targetSystem, targetPort)
            #
            time.sleep(monitor_interval)

def printHeader():
    if(timestamp): 
        header=globalheader.split(delimiter)
        header.extend(['targetName', 'targetPort', 'address', 'dnsInfo', 'resolve', 'resolveFull', 'connect', 'send', 'response', 'close',
            'response', 'error'
            ])                 
        writer.writerow(header)  
    else:
        writer.writerow([
            'targetName', 'targetPort', 'address', 'dnsInfo', 'resolve', 'resolveFull', 'connect', 'send', 'response', 'close',
            'response', 'error'
            ])  
#
def printRawHeader():
    printHeader()
#
def usage():
	print "TODO"

#
#
#
monitor_subsystem = 'oracle.com:80'
monitor_subsystems = ['oracle.com:80','google.com:80']
monitor_count = 10
monitor_interval = 5
delimiter = ','
timedelimiter = ' '
system = socket.gethostname()
source = 'net'
globalheader = 'datetime' + delimiter + 'timezone' + delimiter + 'timestamp' + delimiter + 'system' + delimiter + 'source'
timestamp = False
notbuffered = False
noheader=False
printrawheader=False

makeResponseShort = True

#
try:
    opts, args = getopt.getopt( sys.argv[1:], 's:p:u:c:d:h', ['server=','port=','ulr=', 'count=','delay=','transport=', 'subsystem=','subsystems=','help', 'helpInternal', 'timedelimiter=','delimiter=','system=','source=', 'globalheader=', 'noheader', 'timestamp', 'notbuffered', 'printrawheader', 'longResponse'] )
except getopt.GetoptError, err:
    print str(err)
    usage()
    sys.exit(2)
	
for opt, arg in opts:
    if opt in ('--help'):
        usage()
        sys.exit(2)
    elif opt in ('-c', '--count'):
        monitor_count = int(arg)
    elif opt in ('-d', '--delay'):
        monitor_interval = int(arg)
    elif opt in ('--subsystems'):
        monitor_subsystems = arg.split(',')
    elif opt in ('--subsystem'):
        monitor_subsystems = arg
    elif opt in ('--transport'):
        if(arg == "udp"):
            monitor_transport = socket.SOCK_DGRAM
        else:
            monitor_transport = socket.SOCK_STREAM
    elif opt in ('--longResponse'):
        makeResponseShort = False
    elif opt in ('--timedelimiter'):
        timedelimiter = arg
    elif opt in ('--delimiter'):
        delimiter = arg
        globalheader = 'datetime' + delimiter + 'timezone' + delimiter + 'timestamp' + delimiter + 'system' + delimiter + 'source'
    elif opt in ('--system'):
        system = arg
    elif opt in ('--source'):
        source = arg
    elif opt in ('--globalheader'):
        globalheader = arg
    elif opt in ('--noheader'):
        noheader = True
    elif opt in ('--printrawheader'):
        printrawheader=True
    elif opt in ('--timestamp'):
        timestamp = True
    elif opt in ('--notbuffered'):
        notbuffered = True
        output = Unbuffered(sys.stdout)
    else:
        usage()
        sys.exit(2)
        
if printrawheader==True:
    printRawHeader()
else:
    printStats(monitor_subsystems, monitor_count, monitor_interval)
