
import ctypes
import os
import sys
import socket
import errno
from eunuchs.sendmsg import sendmsg
from eunuchs.recvmsg import recvmsg
import rdmahelper

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

#ctypes.sizeof isn't working, so we have to "know" this value.
SIN_SIZE=16

libc = ctypes.CDLL("libc.so.6", use_errno=True)

class in_addr(ctypes.Structure):
    _fields_ = [("s_addr", ctypes.c_char * 4)]

class sockaddr_in(ctypes.Structure):
    _fields_ = [("sin_family", ctypes.c_uint16),
                ("sin_port", ctypes.c_uint16),
                ("sin_addr", in_addr)]

class rds_cookie(ctypes.Structure):
    _fields_ = [("cookie", ctypes.c_uint64)]

class rds_iovec(ctypes.Structure):
    _fields_ = [("addr", ctypes.c_uint64),
                ("bytes", ctypes.c_uint64)]

class rds_get_mr_args(ctypes.Structure):
    _fields_ = [("vec", rds_iovec),
                ("cookie_addr", ctypes.c_uint64),
                ("flags", ctypes.c_uint64)]

class rds_free_mr_args(ctypes.Structure):
    _fields_ = [("cookie", ctypes.c_uint64),
                ("flags", ctypes.c_uint64)]

class rds_rdma_args(ctypes.Structure):
    _fields_ = [("cookie", ctypes.c_uint64),
                ("remote_vec", rds_iovec),
                ("local_vec_addr", ctypes.c_uint64),
                ("nr_local", ctypes.c_uint64),
                ("flags", ctypes.c_uint64),
                ("user_token", ctypes.c_uint32)]

class rds_rdma_notify(ctypes.Structure):
    _fields_ = [("user_token", ctypes.c_uint64),
                ("status", ctypes.c_int32)]

class RdmaSocket(object):
    
    def __init__(self):
        self.socket = libc.socket(PF_RDS, socket.SOCK_SEQPACKET, 0)

    def bind(self, port, addr):
        sin = sockaddr_in(socket.AF_INET, socket.htons(port),
                        (socket.inet_aton(addr),))
        # can't get size of x (yuck) but we know it's 16
        ret = libc.bind(self.socket, ctypes.addressof(sin), SIN_SIZE)
        if ret == -1:
            raise IOError(errno.errorcode[ctypes.get_errno()])
        else:
            self.bound = True
        return ret

    def fileno(self):
        return self.socket

    def sendmsg(self, **kwargs):
        if not self.bound:
            return -errno.ENOTCONN
        return sendmsg(self.socket, **kwargs)

    def _setsockopt(self, optname, value, length):
        ret = libc.setsockopt(self.socket, SOL_RDS, optname,
                               ctypes.addressof(value), length)
        if ret == -1:
            raise IOError(errno.errorcode[ctypes.get_errno()])

    def cancel_sent_to(self, addr, port):
        """cancel all messages in queue for given addr and port"""
        sin = sockaddr_in(socket.AF_INET, socket.htons(port),
                        (socket.inet_aton(addr),))
        self._setsockopt(RDS_CANCEL_SENT_TO, sin, SIN_SIZE)

    def get_mr(self, obj, offset, length):
        cookie = rds_cookie(0)

        obj_addr, obj_length = rdmahelper.get_buffer_info(obj)
        obj_addr += offset
        obj_length = min(length, obj_length - offset)

        args = rds_get_mr_args((obj_addr, obj_length), ctypes.addressof(cookie), 0)
        self._setsockopt(RDS_GET_MR, args, ctypes.sizeof(args))
        print cookie.cookie
        return cookie.cookie

sock = RdmaSocket()

sock.bind(6666, '127.0.0.1')

import mmap

m = mmap.mmap(-1, 1222)

cookie = sock.get_mr(m, 10, 100)


#print sock.sendmsg(host='127.0.0.1', port=3333, data="hiya", flags=0, ancillary=[])

#print sock.sendmsg(host='127.0.0.1', port=3333, data="hiya",
#                   ancillary=[
#        (SOL_IP, IP_PKTINFO, (10, #interface index
#                              '0.0.0.0',
#                              '255.255.255.255',
#                              )),])
