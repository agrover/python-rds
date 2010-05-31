
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

_RDS_RDMA_READWRITE= 1  # write?
_RDS_RDMA_FENCE=     2  # use FENCE for immediate send
_RDS_RDMA_INVALIDATE=4  # invalidate R_Key after freeing MR
_RDS_RDMA_USE_ONCE=  8  # free MR after use
_RDS_RDMA_DONTWAIT=  16 # Don't wait in SET_BARRIER
_RDS_RDMA_NOTIFY_ME= 32 # Notify when operation completes
_RDS_RDMA_SILENT=    64 # Do not interrupt remote


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
        s = libc.socket(PF_RDS, socket.SOCK_SEQPACKET, 0)
        if s == -1:
            raise IOError(errno.errorcode[ctypes.get_errno()])
        else:
            self.socket = s

    def _throw_on_fail(self, func):
        result = func()
        if result == -1:
            raise IOError(errno.errorcode[ctypes.get_errno()])
        return result

    def bind(self, addr, port):
        sin = sockaddr_in(socket.AF_INET, socket.htons(port),
                        (socket.inet_aton(addr),))
        # can't get size of x (yuck) but we know it's 16
        ret = libc.bind(self.socket, ctypes.addressof(sin), SIN_SIZE)
        if ret == -1:
            raise IOError(errno.errorcode[ctypes.get_errno()])
        else:
            self.bound = True
            self.local_addr = addr
            self.local_port = port

    def close(self):
        return libc.close(self.socket)

    def fileno(self):
        return self.socket

    def getsockname(self):
        return (self.local_addr, self.local_port)

    def sendmsg(self, **kwargs):
        if not self.bound:
            return -errno.ENOTCONN
        print kwargs
        return sendmsg(self.socket, **kwargs)

    def recvmsg(self, **kwargs):
        return recvmsg(self.socket, **kwargs)

    def rdma_sendmsg(self, loc_obj, cookie, remote_offset, remote_length, user_token, **kwargs):
        if not self.bound:
            return -errno.ENOTCONN

        obj_addr, obj_length = rdmahelper.get_read_buffer_info(loc_obj)

        if obj_length != remote_length:
            raise IOError("Local and remote lengths differ (%d, %d)"
                          % (obj_length, remote_length))

        local_iovec = rds_iovec(obj_addr, obj_length)

        args = rds_rdma_args(cookie,
                             rds_iovec(remote_offset, remote_length),
                             ctypes.addressof(local_iovec),
                             1,
                             0, # flags
                             user_token)

        #self.sendmsg(ancillary=[ctypes.addressof(args)], **kwargs)
        self.sendmsg(ancillary=[(3, 4, ctypes.addressof(args))], **kwargs)

    def _setsockopt(self, optname, value, length):
        ret = libc.setsockopt(self.socket, SOL_RDS, optname,
                              value, length)
        if ret == -1:
            raise IOError(errno.errorcode[ctypes.get_errno()])

    def cancel_sent_to(self, addr, port):
        """cancel all messages in queue for given addr and port"""
        sin = sockaddr_in(socket.AF_INET, socket.htons(port),
                        (socket.inet_aton(addr),))
        self._setsockopt(RDS_CANCEL_SENT_TO, sin, SIN_SIZE)

    # TODO: re-implement in terms of _FOR_DEST
    def get_mr(self, obj, offset=0, length=None):

        if not length:
            length = len(obj)

        cookie = rds_cookie(0)

        obj_addr, obj_length = rdmahelper.get_write_buffer_info(obj)
        if length > obj_length - offset:
            raise IOError("length out of bounds")
        obj_addr += offset

        args = rds_get_mr_args((obj_addr, obj_length), ctypes.addressof(cookie), 0)
        self._setsockopt(RDS_GET_MR, ctypes.addressof(args),
                         ctypes.sizeof(args))
        return cookie.cookie

    def get_mr_for_dest(self, obj, offset, length, dest_addr):
        pass # IMPLEMENT

    def free_mr(self, cookie, flags=0):
        args = rds_free_mr_args(cookie, flags)

        self._setsockopt(RDS_FREE_MR, ctypes.addressof(args),
                         ctypes.sizeof(args))


if __name__ == "__main__":

    sock = RdmaSocket()

    sock.bind('10.1.3.98', 6666)

    import mmap

    m1 = mmap.mmap(-1, 1222)

    cookie = sock.get_mr(m, 10, 100)

    sock.free_mr(10203040)

    print cookie

#print sock.sendmsg(host='127.0.0.1', port=3333, data="hiya", flags=0, ancillary=[])

#print sock.sendmsg(host='127.0.0.1', port=3333, data="hiya",
#                   ancillary=[
#        (SOL_IP, IP_PKTINFO, (10, #interface index
#                              '0.0.0.0',
#                              '255.255.255.255',
#                              )),])
