
import ctypes
import os
import sys
import socket
import errno
from eunuchs.sendmsg import sendmsg
from eunuchs.recvmsg import recvmsg

PF_RDS=21
SOL_RDS=276

# sockopts
RDS_CANCEL_SENT_TO=1
RDS_GET_MR=2
RDS_FREE_MR=3
RDS_RECVERR=5
RDS_CONG_MONITOR=6
RDS_GET_MR_FOR_DEST=7

# cmsg types
RDS_CMSG_RDMA_ARGS=1
RDS_CMSG_RDMA_DEST=2
RDS_CMSG_RDMA_MAP=3
RDS_CMSG_RDMA_STATUS=4
RDS_CMSG_CONG_UPDATE=5


libc = ctypes.CDLL("libc.so.6", use_errno=True)

class in_addr(ctypes.Structure):
    _fields_ = [("s_addr", ctypes.c_char * 4)]

class sockaddr_in(ctypes.Structure):
    _fields_ = [("sin_family", ctypes.c_uint16),
                ("sin_port", ctypes.c_uint16),
                ("sin_addr", in_addr)]

class 

class RdmaSocket(object):
    
    def __init__(self):
        self.socket = libc.socket(PF_RDS, socket.SOCK_SEQPACKET, 0)

    def bind(self, port, addr):
        x = sockaddr_in(socket.AF_INET, socket.htons(port),
                        (socket.inet_aton(addr),))
        # can't get size of x (yuck) but we know it's 16
        ret = libc.bind(self.socket, ctypes.addressof(x), 16)
        if ret == -1:
            print "bind error: ", errno.errorcode[ctypes.get_errno()]
        return ret

    def fileno(self):
        return self.socket

    def sendmsg(self, **kwargs):
        return sendmsg(self.socket, **kwargs)

sock = RdmaSocket()

sock.bind(6666, '127.0.0.1')

#print sock.sendmsg(host='127.0.0.1', port=3333, data="hiya", flags=0, ancillary=[])

print sock.sendmsg(host='127.0.0.1', port=3333, data="hiya", flags=0,
                   ancillary=[
        (SOL_IP, IP_PKTINFO, (10, #interface index
                              '0.0.0.0',
                              '255.255.255.255',
                              )),])
