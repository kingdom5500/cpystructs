import _ctypes
import ctypes
import os

# should we just import * ?
from ctypes import (
    c_char, c_char_p, c_double, c_int, c_int64,
    c_long, c_size_t, c_ssize_t, c_uint, c_uint32,
    c_uint64, c_ulong, c_void_p, CFUNCTYPE,
    POINTER, py_object, Structure
)

# TODO: do we want separate "typedefs" for non-standard
# types in cpython like Py_ssize_t and Py_hash_t? Maybe.

__all__ = [
    "PyAsyncMethods",
    "PyBufferProcs",
    "PyBytesObject",
    "PyCoreConfig",
    "PyErr_StackItem",
    "PyFloatObject",
    "PyGetSetDef",
    "PyInterpreterState",
    "PyListObject",
    "PyLongObject",
    "PyMappingMethods",
    "PyMemberDef",
    "PyMethodDef",
    "PyNumberMethods",
    "PyObject",
    "PySequenceMethods",
    "PyThreadState",
    "PyTupleObject",
    "PyTypeObject",
    "PyVarObject",
    "Py_buffer",
]


class _PyStruct(Structure):
    """
    A basic subclass of ctypes.Structure which gives a simple
    class method for defining the fields after declaration.
    Also provides basic methods for interacting with objects.
    """

    @classmethod
    def set_fields(cls, **fields):
        temp = []
        for name, typ in fields.items():
            if typ is not None:
                temp.append((name, typ))

        cls._fields_ = tuple(temp)

    @classmethod
    def from_object(cls, obj):
        return cls.from_address(id(obj))

    @classmethod
    def field_offset(cls, field):
        """
        Find how many bytes are before a field. At least for
        now, this will not check if the given field name is
        in the struct. If a name is passed which isn't in the
        struct, this will fall through to the end and return
        the total size of the struct. For now.
        """

        total = 0
        for name, ctype in cls._fields_:
            if name == field:
                break

            total += ctypes.sizeof(ctype)

        return total

    def field_address(self, field):
        offset = self.field_offset(field)
        addr = ctypes.addressof(self)
        return addr + offset

    def get_object(self):
        ptr = c_void_p(ctypes.addressof(self))
        return ctypes.cast(ptr, py_object).value

    def as_type(self, struct_type):
        return struct_type.from_address(
            ctypes.addressof(self)
        )


# we're forward-declaring these structs for two reasons.
# 1 - to avoid postponed references to not-yet-defined structs.
# 2 - to avoid circular imports with the `_funcs.py` script
class PyObject(_PyStruct): ...
class PyVarObject(_PyStruct): ...
class PyTypeObject(_PyStruct): ...
class PyAsyncMethods(_PyStruct): ...
class PyNumberMethods(_PyStruct): ...
class PySequenceMethods(_PyStruct): ...
class PyMappingMethods(_PyStruct): ...
class PyBufferProcs(_PyStruct): ...
class PyMethodDef(_PyStruct): ...
class PyMemberDef(_PyStruct): ...
class Py_buffer(_PyStruct): ...
class PyGetSetDef(_PyStruct): ...
class PyFloatObject(_PyStruct): ...

class PyLongObject(_PyStruct):
    @property
    def ob_digit(self):
        size = self.ob_base.ob_size
        array = c_uint32 * size
        return ctypes.cast(self._ob_digit, array)

class PyListObject(_PyStruct):
    @property
    def ob_item(self):
        size = self.ob_base.ob_size
        ptr = POINTER(POINTER(PyObject) * size)  # PyObject **
        return ctypes.cast(self._ob_item, ptr)

class PyTupleObject(_PyStruct):
    @property
    def ob_item(self):
        size = self.ob_base.ob_size
        array = POINTER(PyObject) * size

        address = self.field_address("_ob_item")
        return array.from_address(address)

class PyBytesObject(_PyStruct):
    @property
    def ob_sval(self):
        size = self.ob_base.ob_size
        array = c_char * (size + 1)

        address = self.field_address("_ob_sval")
        return array.from_address(address)

class PyErr_StackItem(_PyStruct): ...
class PyCoreConfig(_PyStruct): ...
class PyThreadState(_PyStruct): ...
class PyInterpreterState(_PyStruct): ...

# all structs have been defined, so now we can import the func types
from ._funcs import *

PyObject.set_fields(
    ob_refcount=c_ssize_t,
    ob_type=POINTER(PyTypeObject),
)

PyVarObject.set_fields(
    ob_base=PyObject,
    ob_size=c_ssize_t,
)

PyTypeObject.set_fields(
    ob_base=PyVarObject,
    tp_name=c_char_p,
    tp_basicsize=c_ssize_t,
    tp_itemsize=c_ssize_t,

    tp_dealloc=destructor,
    tp_print=printfunc,
    tp_getattr=getattrfunc,
    tp_setattr=setattrfunc,
    tp_as_async=POINTER(PyAsyncMethods),
    tp_repr=reprfunc,

    tp_as_number=POINTER(PyNumberMethods),
    tp_as_sequence=POINTER(PySequenceMethods),
    tp_as_mapping=POINTER(PyMappingMethods),

    tp_hash=hashfunc,
    tp_call=ternaryfunc,
    tp_str=reprfunc,
    tp_getattro=getattrofunc,
    tp_setattro=setattrofunc,

    tp_as_buffer=POINTER(PyBufferProcs),
    tp_flags=c_ulong,
    tp_doc=c_char_p,

    tp_traverse=traverseproc,
    tp_clear=inquiry,
    tp_richcompare=richcmpfunc,
    tp_weaklistoffset=c_ssize_t,

    tp_iter=getiterfunc,
    tp_iternext=iternextfunc,

    tp_methods=POINTER(PyMethodDef),
    tp_members=POINTER(PyMemberDef),
    tp_getset=POINTER(PyGetSetDef),
    tp_base=POINTER(PyTypeObject),
    tp_dict=POINTER(PyObject),

    tp_descr_get=descrgetfunc,
    tp_descr_set=descrsetfunc,
    tp_dictoffset=c_ssize_t,
    tp_init=initproc,
    tp_alloc=allocfunc,
    tp_new=newfunc,
    tp_free=freefunc,
    tp_is_gc=inquiry,
    tp_bases=POINTER(PyObject),
    tp_mro=POINTER(PyObject),
    tp_cache=POINTER(PyObject),
    tp_subclasses=POINTER(PyObject),
    tp_weaklist=POINTER(PyObject),

    tp_version_tag=c_uint,
    tp_finalize=destructor,
)

PyAsyncMethods.set_fields(
    am_await=unaryfunc,
    am_aiter=unaryfunc,
    am_anext=unaryfunc,
)

PyNumberMethods.set_fields(
    nb_add=binaryfunc,
    nb_subtract=binaryfunc,
    nb_multiply=binaryfunc,
    nb_remainder=binaryfunc,
    nb_divmod=binaryfunc,
    nb_power=ternaryfunc,
    nb_negative=unaryfunc,
    nb_positive=unaryfunc,
    nb_absolute=unaryfunc,
    nb_bool=inquiry,
    nb_invert=unaryfunc,
    nb_lshift=binaryfunc,
    nb_rshift=binaryfunc,
    nb_and=binaryfunc,
    nb_xor=binaryfunc,
    nb_or=binaryfunc,
    nb_int=unaryfunc,
    nb_reserved=c_void_p,
    nb_float=unaryfunc,

    nb_inplace_add=binaryfunc,
    nb_inplace_subtract=binaryfunc,
    nb_inplace_multiply=binaryfunc,
    nb_inplace_remainder=binaryfunc,
    nb_inplace_power=ternaryfunc,
    nb_inplace_lshift=binaryfunc,
    nb_inplace_rshift=binaryfunc,
    nb_inplace_and=binaryfunc,
    nb_inplace_xor=binaryfunc,
    nb_inplace_or=binaryfunc,

    nb_floor_divide=binaryfunc,
    nb_true_divide=binaryfunc,
    nb_inplace_floor_divide=binaryfunc,
    nb_inplace_true_divide=binaryfunc,

    nb_index=unaryfunc,

    nb_matrix_multiply=binaryfunc,
    nb_inplace_matrix_multiply=binaryfunc,
)

PySequenceMethods.set_fields(
    sq_length=lenfunc,
    sq_concat=binaryfunc,
    sq_repeat=ssizeargfunc,
    sq_item=ssizeargfunc,
    was_sq_slice=c_void_p,
    sq_ass_item=ssizeobjargproc,
    was_sq_ass_slice=c_void_p,
    sq_contains=objobjproc,

    sq_inplace_concat=binaryfunc,
    sq_inplace_repeat=ssizeargfunc,
)

PyMappingMethods.set_fields(
    mp_length=lenfunc,
    mp_subscript=binaryfunc,
    mp_ass_subscript=objobjargproc,
)

PyBufferProcs.set_fields(
    bf_getbuffer=getbufferproc,
    bf_releasebuffer=releasebufferproc,
)

Py_buffer.set_fields(
    buf=c_void_p,
    obj=POINTER(PyObject),
    len=c_ssize_t,
    itemsize=c_ssize_t,

    readonly=c_int,
    ndim=c_int,
    format=c_char_p,
    shape=POINTER(c_ssize_t),
    strides=POINTER(c_ssize_t),
    suboffsets=POINTER(c_ssize_t),
    internal=c_void_p
)

PyGetSetDef.set_fields(
    name=c_char_p,
    get=getter,
    set=setter,
    doc=c_char_p,
    closure=c_void_p,
)

PyLongObject.set_fields(
    ob_base=PyVarObject,
    # `ob_digit` is replaced with `c_uint32[ob_size]` when accessed
    _ob_digit=c_void_p,
)

PyListObject.set_fields(
    ob_base=PyVarObject,
    # `ob_item` is replaced with `PyObject **` when accessed
    _ob_item=c_void_p,
    allocated=c_ssize_t,
)

PyFloatObject.set_fields(
    ob_base=PyObject,
    ob_fval=c_double
)

PyTupleObject.set_fields(
    ob_base=PyVarObject,
    # `ob_item` is replaced with `PyObject*[ob_size]` when accessed
    _ob_item=c_void_p
)

PyBytesObject.set_fields(
    ob_base=PyVarObject,
    ob_shash=c_ssize_t,
    # `ob_sval` is replaced with `char[ob_size]` when accessed
    _ob_sval=c_void_p
)

PyErr_StackItem.set_fields(
    exc_type=POINTER(PyObject),
    exc_value=POINTER(PyObject),
    exc_traceback=POINTER(PyObject),

    previous_item=POINTER(PyErr_StackItem)
)

PyCoreConfig.set_fields(
    isolated=c_int,
    use_environment=c_int,
    _init_main=c_int,
)

HAVE_DLOPEN = hasattr(_ctypes, "dlopen")
HAVE_FORK = hasattr(os, "fork")

PyInterpreterState.set_fields(
    next=POINTER(PyInterpreterState),
    tstate_head=POINTER(PyThreadState),

    id=c_int64,
    id_refcount=c_int64,
    requires_idref=c_int,
    id_mutex=c_void_p,  # PyThread_type_lock

    finalizing=c_int,

    modules=POINTER(PyObject),
    modules_by_index=POINTER(PyObject),
    sysdict=POINTER(PyObject),
    builtins=POINTER(PyObject),
    importlib=POINTER(PyObject),

    check_interval=c_int,

    num_threads=c_long,
    pythread_stacksize=c_size_t,

    codec_search_path=POINTER(PyObject),
    codec_search_cache=POINTER(PyObject),
    codec_error_registry=POINTER(PyObject),
    codecs_initialized=c_int,
    fscodec_initialized=c_int,

    core_config=PyCoreConfig,
    dlopenflags=c_int if HAVE_DLOPEN else None,

    dict=POINTER(PyObject),
    builtins_copy=POINTER(PyObject),
    import_func=POINTER(PyObject),

    eval_frame=PyFrameEvalFunction,

    co_extra_user_count=c_ssize_t,
    co_extra_freefuncs=freefunc * 255,

    before_forkers = POINTER(PyObject) if HAVE_FORK else None,
    after_forkers_parent = POINTER(PyObject) if HAVE_FORK else None,
    after_forkers_child = POINTER(PyObject) if HAVE_FORK else None,

    pyexitfunc = CFUNCTYPE(None, py_object),
    pyexitmodule = POINTER(PyObject),

    tstate_next_unique_id = c_uint64
)

PyThreadState.set_fields(
    prev=POINTER(PyThreadState),
    next=POINTER(PyThreadState),
    interp=POINTER(PyInterpreterState),

    frame=c_void_p,  # TODO: pointer to frame struct
    recursion_depth=c_int,
    overflowed=c_char,
    recursion_critical=c_char,
    stackcheck_counter=c_int,

    tracing=c_int,
    use_tracing=c_int,

    c_profilefunc=Py_tracefunc,
    c_tracefunc=Py_tracefunc,
    c_profileobj=POINTER(PyObject),
    c_traceobj=POINTER(PyObject),

    curexc_type=POINTER(PyObject),
    curexc_value=POINTER(PyObject),
    curexc_traceback=POINTER(PyObject),

    exc_state=PyErr_StackItem,
    exc_info=PyErr_StackItem,

    dict=POINTER(PyObject),

    gilstate_counter=c_int,

    async_exc=POINTER(PyObject),
    thread_id=c_ulong,

    trash_delete_nesting=c_int,
    trash_delete_later=POINTER(PyObject),

    on_delete=CFUNCTYPE(None, c_void_p),
    on_delete_data=c_void_p,

    coroutine_origin_tracking_depth=c_int,

    coroutine_wrapper=POINTER(PyObject),
    in_coroutine_wrapper=c_int,

    async_gen_firstiter=POINTER(PyObject),
    async_gen_finalizer=POINTER(PyObject),

    context=POINTER(PyObject),
    context_ver=c_uint64,

    id=c_uint64
)