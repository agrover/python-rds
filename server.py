
import rdma
import pickle
import mmap
import os

sock = rdma.RdmaSocket()

sock.bind("10.1.3.98", 6666)

os.chdir(os.path.expanduser("~/"))

user_token = 1337

while (True):
    pickled_cmd, sender, flags, ancillary = sock.recvmsg()
    cmd = pickle.loads(pickled_cmd)
    print cmd

    offset = cmd["offset"]
    length = cmd["length"]

    f = open(cmd["filename"], "rb")

    m = mmap.mmap(f.fileno(), 0, flags=mmap.MAP_PRIVATE) # mmap whole file

    sock.rdma_sendmsg(m[offset:offset+length], cmd["cookie"],
                      offset, length, user_token, host=sender[0],
                      port=sender[1], data="here it is")



