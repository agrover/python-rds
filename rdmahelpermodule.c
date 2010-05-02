
#include <Python.h>

static PyObject *
rdma_get_buffer_info(PyObject *self, PyObject *args)
{
	char *ptr;
	Py_ssize_t len;
	unsigned long long addr_as_u64;

	if (!PyArg_ParseTuple(args, "w#", &ptr, &len))
		return NULL;

	addr_as_u64 = (unsigned long)ptr;

	return Py_BuildValue("Kn", addr_as_u64, len);
}

static PyMethodDef rdma_methods[] = {
	{"get_buffer_info",  rdma_get_buffer_info, METH_VARARGS,
	 "Object -> (address, length)"},
	 {NULL, NULL, 0, NULL}        /* Sentinel */
};

PyMODINIT_FUNC
initrdmahelper(void)
{
	Py_InitModule("rdmahelper", rdma_methods);
}
