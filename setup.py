from distutils.core import setup, Extension

rdma = Extension('rdmahelper',
                    sources = ['rdmahelpermodule.c'])

setup (name = 'RDMA Helper',
       version = '1.0',
       description = 'RDMA Helper module',
       ext_modules = [rdma])
