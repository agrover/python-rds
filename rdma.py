
import ctypes
import os
import sys
import socket
from eunuchs.sendmsg import sendmsg
from eunuchs.recvmsg import recvmsg

libc = ctypes.CDLL("libc.so.6")

class sockaddr_in(ctype.Structure):
    _fields_ = [("sin_family", ctypes.c_int),
                ("sin_port", ctypes.c_int),
                ("sin_addr", ctypes.c_ulong)]

class RdmaSocket(object):
    
    def __init__(self):
        #self.socket = libc.socket(socket.AF_INET, socket.SOCK_DGRAM, 0)
        self.socket = libc.socket(21, socket.SOCK_SEQPACKET, 0)
        #self.socket = socket.socket(21, socket.SOCK_SEQPACKET)

    def bind(self):
        print libc.bind(self.socket, 

    def fileno(self):
        return self.socket

    def sendmsg(self, **kwargs):
        return sendmsg(self.socket, **kwargs)

sock = RdmaSocket()

print sock.sendmsg(host='127.0.0.1', port=3333, data="hiya", flags=0, ancillary=[])

