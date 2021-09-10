import ctypes
from ctypes import *


# define ECIOK      0            /* success */
# define ECIGEN     1            /* generic (not specified) error */
# define ECIBUSY    2            /* device or resourse busy */
# define ECIMFAULT  3            /* memory fault */
# define ECISTATE   4            /* function can't be called for chip in current state */
# define ECIINCALL  5            /* invalid call, function can't be called for this object */
# define ECIINVAL   6            /* invalid parameter */
# define ECIACCES   7            /* can not access resource */
# define ECINOSYS   8            /* function or feature not implemented */
# define ECIIO      9            /* input/output error */
# define ECINODEV   10           /* no such device or object */
# define ECIINTR    11           /* call was interrupted by event */
# define ECINORES   12           /* no resources */
# define ECITOUT    13

def trying():
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

    open_canal = -1
    while open_canal < 0:
        lib.CiOpen(0, 0x2 | 0x4)
        lib.CiSetBaud(0, 0x00, 0x1c)
        open_canal = lib.CiStart(0)

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
        lib.msg_zero(ctypes.pointer(cw))

    lib.CiStop(0)

    lib.CiClose(0)


class CANMarathon:
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

    def __init__(self):
        self.lib = cdll.LoadLibrary(r"C:\Program Files (x86)\CHAI-2.14.0\x64\chai.dll")
        self.lib.CiInit()
        self.can_canal_number = 0

    def canal_open(self):
        open_canal = -1
        while open_canal < 0:
            self.lib.CiOpen(self.can_canal_number, 0x2 | 0x4)  # 0x2 | 0x4 - это приём 11bit и 29bit заголовков
            self.lib.CiSetBaud(self.can_canal_number, 0x00, 0x1c)  # 0x03, 0x1c это скорость CAN BCI_125K
            open_canal = self.lib.CiStart(self.can_canal_number)  # 0x00, 0x1c это скорость CAN BCI_500K

    def can_read(self, can_id: int):
        # can_id = ctypes.c_int32(can_id)
        array_cw = self.Cw * 1
        cw = array_cw((self.can_canal_number, 0x1 | 0x4, 0))  # 0x1 | 0x4 - это wflags - флаги интересующих нас событий
        #  = количество кадров в приемной очереди стало больше или равно значению порога + ошибка сети
        buffer = self.Buffer()
        self.lib.CiWaitEvent.argtypes = [ctypes.POINTER(array_cw), ctypes.c_int32, ctypes.c_int16]
        self.canal_open()
        ret = 0
        while True:
            while not ret:
                ret = self.lib.CiWaitEvent(ctypes.pointer(cw), 1, 1000)  # timeout = 1000 миллисекунд
            if ret > 0:
                # print(cw[0].wflags )
                if cw[0].wflags & 0x01:  # количество кадров в приемной очереди стало больше
                    # или равно значению порога
                    can_read = self.lib.CiRead(self.can_canal_number, ctypes.pointer(buffer), 1)
                    if can_read >= 0:
                        if can_id == buffer.id:  #
                            print(hex(buffer.id), end='    ')
                            for i in range(buffer.len):
                                print(hex(buffer.data[i]), end=' ')
                            print()
                            self.lib.CiStop(self.can_canal_number)
                            self.lib.CiClose(self.can_canal_number)
                            return buffer.data
                    else:
                        print('Ошибка при чтении с буфера канала ')
                    # self.lib.msg_zero(ctypes.pointer(cw))
                elif cw[0].wflags == 0x04:  # ошибка сети
                    print('ошибка сети EWL, BOFF, HOVR, SOVR, или WTOUT')
                    # здесь процедурой CiErrsGetClear надо вычислить что за ошибка

    def can_write(self, can_id: int, message: list):
        buffer = self.Buffer()
        buffer.id = ctypes.c_int32(can_id)
        j = 0
        for i in message:
            buffer.data[j] = ctypes.c_int8(i)
            j += 1
        buffer.len = len(message)
        if can_id > 0xFFF:
            buffer.flags = 2
        else:
            buffer.flags = 0
        self.lib.CiTransmit.argtypes = [ctypes.c_int8, ctypes.POINTER(self.Buffer)]
        self.canal_open()
        transmit_ok = -1
        while transmit_ok < 0:
            self.lib.CiTransmit(self.can_canal_number, ctypes.pointer(buffer))


if __name__ == "__main__":
    #  trying()
    marathon = CANMarathon()
    marathon.can_write(0x4F5, [0x00, 0x00, 0x00, 0x00, 0x6D, 0x00, 0x2B, 0x03])  # запрос у передней рулевой рейки порядок
    # передачи байт многобайтных параметров, 0x00 - прямой, 0x01 - обратный
    marathon.can_read(0x4F7)
    # while True:
    #     canid = 0x60D
    #     marathon.can_read(canid)
