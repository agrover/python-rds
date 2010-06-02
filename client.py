
import rdma
import pickle
import mmap
import os

sock = rdma.RdmaSocket()

sock.bind("10.1.3.98", 7777)

f = open("test.file", "r+w")
f.write("x")
f.flush()

mapping = mmap.mmap(f.fileno(), 1, prot=mmap.PROT_WRITE, flags=mmap.MAP_PRIVATE)

mapping.resize(8192)

cookie = sock.get_mr(mapping)

cmd = dict(filename="kernel-2.6.18-128.1.16.0.1.el5.x86_64.rpm",
           cookie=cookie,
           offset=0,
           length=8192)

sock.sendmsg(host="10.1.3.98", port=6666, data=pickle.dumps(cmd))

print sock.recvmsg()

mapping.close()

