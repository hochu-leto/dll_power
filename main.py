import ctypes
from ctypes import *
from pprint import pprint

"""
typedef struct {
		_u32 id;
		_u8 data[8];
		_u8 len;
		_u16 flags;            /* bit 0 - RTR, 2 - EFF */
		_u32 ts;
	} canmsg_t;
	"""


class Buffer(Structure):
    _fields_ = [
        ('id', ctypes.c_int32),
        ('data', ctypes.c_int8 * 8),
        ('len', ctypes.c_int8),
        ('flags', ctypes.c_int16),
        ('ts', ctypes.c_int32)
    ]


class Cw(Structure):
    _fields_ = [
        ('chan', ctypes.c_int8),
        ('wflags', ctypes.c_int8),
        ('rflags', ctypes.c_int8)
    ]


array_cw = Cw * 2
cw = array_cw((0, 0x1 | 0x4, 0), (1, 0x1 | 0x4, 0))
buffer = Buffer()
lib = cdll.LoadLibrary(r"C:\Program Files (x86)\CHAI-2.14.0\x64\chai.dll")
lib.CiInit()
open_canal = lib.CiOpen(0, 0x2 | 0x4)
while open_canal < 0:
    open_canal = lib.CiOpen(0, 0x2 | 0x4)
lib.CiSetBaud(0, 0x03, 0x1c)
lib.CiStart(0)
ret = 0
lib.CiWaitEvent.argtypes = [ctypes.POINTER(array_cw), ctypes.c_int32, ctypes.c_int16]
can_read = 0
old_id = 0
while can_read >= 0:
    while not ret:
        ret = lib.CiWaitEvent(ctypes.pointer(cw), 1, 1000)  # timeout = 1000 миллисекунд

    can_read = lib.CiRead(0, ctypes.pointer(buffer), 1)
    if old_id != buffer.id:
        print(hex(buffer.id), end='    ')
        for i in range(buffer.len):
            print(hex(buffer.data[i]), end=' ')
        print()
    old_id = buffer.id
lib.CiStop(0)

lib.CiClose(0)
