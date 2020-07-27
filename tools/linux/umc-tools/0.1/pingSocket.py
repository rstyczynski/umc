#!/usr/bin/env python2

import socket
import time
import datetime
import time as pytime
import csv
import sys
import getopt
import os
import struct

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

# Source: http://code.activestate.com/recipes/576662-icmplib/
class Packet(object):

    """Creates ICMPv4 and v6 packets.
    
    header
        two-item sequence containing the type and code of the packet,
        respectively.
    version
        Automatically set to version of protocol being used or None if ambiguous.
    data
        Contains data of the packet.  Can only assign a subclass of string
        or None.

    packet
        binary representation of packet.
    
    EXAMPLE: (using Python as root)
		>>> import icmpLib
		>>> icmplib.ping('127.0.0.1')
    """

    header_table = {
                0 : (0, 4),
                #3 : (15, 4),  Overlap with ICMPv6
                3 : (15, None),
                #4 : (0, 4),  Deprecated by RFC 1812
                5 : (3, 4),
                8 : (0, 4),
                9 : (0, 4),
                10: (0, 4),
                11: (1, 4),
                12: (1, 4),
                13: (0, 4),
                14: (0, 4),
                15: (0, 4),
                16: (0, 4),
                17: (0, 4),
                18: (0, 4),

                1 : (4, 6),
                2 : (0, 6),
                #3 : (2, 6),  Overlap with ICMPv4
                #4 : (2, 6),  Type of 4 in ICMPv4 is deprecated
                4 : (2, None),
                128: (0, 6),
                129: (0, 6),
                130: (0, 6),
                131: (0, 6),
                132: (0, 6),
                133: (0, 6),
                134: (0, 6),
                135: (0, 6),
                136: (0, 6),
                137: (0, 6),
             }

    def _setheader(self, header):
        """Set type, code, and version for the packet."""
        if len(header) != 2:
            raise ValueError("header data must be in a two-item sequence")
        type_, code = header
        try:
            max_range, version = self.header_table[type_]
        except KeyError:
            raise ValueError("%s is not a valid type argument" % type_)
        else:
            if code > max_range:
                raise ValueError("%s is not a valid code value for type %s" %\
                                     (type_, code))
            self._type, self._code, self._version = type_, code, version

    header = property(lambda self: (self._type, self._code), _setheader,
                       doc="type and code of packet")

    version = property(lambda self: self._version,
                        doc="Protocol version packet is using or None if "
                            "ambiguous")

    def _setdata(self, data):
        """Setter for self.data; will only accept a string or None type."""
        if not isinstance(data, (str, bytes)) and not isinstance(data, type(None)):
            raise TypeError("value must be a subclass of string or None, "
                            "not %s" % type(data))
        self._data = data

    data = property(lambda self: self._data, _setdata,
                    doc="data contained within the packet")

    def __init__(self, header=(None, None), data=None):
        """Set instance attributes if given."""
        #XXX: Consider using __slots__
        # self._version initialized by setting self.header
        self.header = header
        self.data = data

    def __repr__(self):
        return "<ICMPv%s packet: type = %s, code = %s, data length = %s>" % \
                (self.version, self.type, self.code, len(self.data))

    def create(self):
        """Return a packet."""
        # Kept as a separate method instead of rolling into 'packet' property so
        # as to allow passing method around without having to define a lambda
        # method.
        args = [self.header[0], self.header[1], 0]
        pack_format = "!BBH"
        if self.data != None:
            pack_format += "%ss" % len(self.data)
            args.append(self.data)
        # ICMPv6 has the IP stack calculate the checksum
        # For ambiguous cases, just go ahead and calculate it just in case
        if self.version == 4 or not self.version:
            args[2] = self._checksum(struct.pack(pack_format, *args))
        return struct.pack(pack_format, *args)

    packet = property(create,
                       doc="Complete ICMP packet")

    def _checksum(self, checksum_packet):
        """Calculate checksum"""
        byte_count = len(checksum_packet)
        #XXX: Think there is an error here about odd number of bytes
        if byte_count % 2:
            odd_byte = ord(checksum_packet[-1])
            checksum_packet = checksum_packet[:-1]
        else:
            odd_byte = 0
        two_byte_chunks = struct.unpack("!%dH" % (len(checksum_packet)/2),
                                        checksum_packet)
        total = 0
        for two_bytes in two_byte_chunks:
            total += two_bytes
        else:
            total += odd_byte
        total = (total >> 16) + (total & 0xFFFF)
        total += total >> 16
        return ~total
        
    def parse(cls, packet):
        """Parse ICMP packet and return an instance of Packet"""
        string_len = len(packet) - 4 # Ignore IP header
        pack_format = "!BBH"
        if string_len:
            pack_format += "%ss" % string_len
        unpacked_packet = struct.unpack(pack_format, packet)
        type, code, checksum = unpacked_packet[:3]
        try:
            data = unpacked_packet[3]
        except IndexError:
            data = None
        return cls((type, code), data)

    parse = classmethod(parse)


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
            s = socket.socket(socket.AF_INET, monitor_transport) 
            s.settimeout(2)

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
            s = socket.socket(socket.AF_INET, monitor_transport) 
            s.settimeout(2)

            start_time = time.time()
            s.sendto('Hello!', (addressStr, targetPort))
            ms = (time.time() - start_time ) * 1000
            send=ms

            #
            start_time = time.time()
            data, server = s.recvfrom(2048)
            ms = (time.time() - start_time ) * 1000
            response=ms

        # ICMP
        if (monitor_transport == socket.SOCK_RAW):

            s = socket.socket(socket.AF_INET, monitor_transport, socket.getprotobyname('icmp'))
            s.settimeout(2)

            # connect
            start_time = time.time()
            s.connect((addressStr,22))
            ms = (time.time() - start_time ) * 1000
            connect=ms

            os.setuid(os.getuid())
            process_id = os.getpid()
            seq_num = 0
            pdata = struct.pack("!HHd", process_id, seq_num, time.time())
    
            ## send initial packet 
            base_packet = Packet((8, 0))
            base_packet.data = pdata

            start_time = time.time()
            s.send(base_packet.packet)
            ms = (time.time() - start_time ) * 1000
            send=ms

            ## recv packet
            buf = s.recv(BUFSIZE)
            ms = (time.time() - start_time ) * 1000
            response=ms

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
monitor_transport = socket.SOCK_STREAM
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
        if(arg == "icmp"):
            monitor_transport = socket.SOCK_RAW

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
