from socket import *
import os
import sys
import struct
import time
import select
import binascii

ICMP_ECHO_REQUEST = 8

def checksum(string):
    csum = 0
    countTo = (len(string) // 2) * 2
    count = 0

    while count < countTo:
        thisVal = ord(string[count+1]) * 256 + ord(string[count])
        csum = csum + thisVal
        csum = csum & 0xffffffff
        count = count + 2
        
    if countTo < len(string):
        csum = csum + ord(string[len(string) - 1])
        csum = csum & 0xffffffff
        
    csum = (csum >> 16) + (csum & 0xffff)
    csum = csum + (csum >> 16)
    answer = ~csum
    answer = answer & 0xffff
    answer = answer >> 8 | (answer << 8 & 0xff00)
    return answer

def receiveOnePing(mySocket, ID, timeout, destAddr):
    timeLeft = timeout
    while 1:
        startedSelect = time.time()
        whatReady = select.select([mySocket], [], [], timeLeft)
        howLongInSelect = (time.time() - startedSelect)
        if whatReady[0] == []: # Timeout
            return "Request timed out."

        timeReceived = time.time()
        recPacket, addr = mySocket.recvfrom(1024)
        
        icmpHeader = recPacket[20:28]
        type, code, checksum, packetID, seq = struct.unpack("bbHHh", icmpHeader)
        getTime = struct.unpack("d", recPacket[28:36])[0]

        print("ICMP Header: "), type, code, checksum, packetID, seq

        if((type == 0) and (code == 0) and (packetID == ID)):
            rtt = timeReceived - getTime
            return rtt
        
        timeLeft = timeLeft - howLongInSelect

        if timeLeft <= 0:
            return "Request timed out."
        
def sendOnePing(mySocket, destAddr, ID):
    # Header is type (8), code (8), checksum (16), id (16), sequence (16)
    # Make a dummy header with a 0 checksum
    myChecksum = 0

    # struct -- Interpret strings as packed binary data
    header = struct.pack("bbHHh", ICMP_ECHO_REQUEST, 0, myChecksum, ID, 1)
    data = struct.pack("d", time.time())

    # Calculate the checksum on the data and the dummy header.
    myChecksum = checksum(str(header + data))

    # Get the right checksum, and put in the header
    if sys.platform == 'darwin':
        myChecksum = htons(myChecksum) & 0xffff
    else:
        myChecksum = htons(myChecksum)

    header = struct.pack("bbHHh", ICMP_ECHO_REQUEST, 0, myChecksum, ID, 1)
    packet = header + data

    # AF_INET address must be tuple, not str
    # Both LISTS and TUPLES consist of a number of objects
    # which can be referenced by their position number within the object.
    mySocket.sendto(packet, (destAddr, 1))

def ping(host, timeout=1):
    dest = gethostbyname(host)
    print("Pinging " + dest + " using Python:")
    print("")

    icmp = getprotobyname("icmp")
    myID = os.getpid() & 0xFFFF # Return the current process id

    # Send ping requests to a server separated by approximately a second
    while 1:
        mySocket = socket(AF_INET, SOCK_RAW, icmp)
        sendOnePing(mySocket, dest, myID)
        delay = receiveOnePing(mySocket, myID, timeout, dest)
        print(delay)
        mySocket.close()
        time.sleep(1)
    return delay
ping("203.205.251.178", 1)
