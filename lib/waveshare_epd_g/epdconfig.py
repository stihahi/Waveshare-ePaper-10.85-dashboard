# Bridge to Waveshare's prebuilt DEV_Config library for the 10.85inch e-Paper (G).
# Unlike the black/white driver it bit-bangs the chip selects itself, so SPI
# and GPIO go through the native library instead of spidev/gpiozero.
import ctypes
import os
import struct
import time

CS_M_PIN = 8
CS_S_PIN = 7
DC_PIN = 25
RST_PIN = 17
BUSY_PIN = 24

LIBRARY_DIR = os.path.dirname(os.path.realpath(__file__))
DEVICE_MODEL_PATH = '/proc/device-tree/model'


def _is_raspberry_pi_5():
    try:
        with open(DEVICE_MODEL_PATH) as model:
            return 'Raspberry Pi 5' in model.read()
    except OSError:
        return False


def _library_path():
    pointer_bits = struct.calcsize('P') * 8
    gpio_backend = 'w' if _is_raspberry_pi_5() else 'b'
    return os.path.join(LIBRARY_DIR, f'DEV_Config_{pointer_bits}_{gpio_backend}.so')


_native = ctypes.CDLL(_library_path())


def digital_write(pin, value):
    _native.DEV_Digital_Write(pin, value)


def digital_read(pin):
    return _native.DEV_Digital_Read(pin)


def spi_write_byte(value):
    _native.DEV_SPI_SendData(value)


def spi_write_bytes(data):
    _native.DEV_SPI_SendData_nByte((ctypes.c_ubyte * len(data)).from_buffer_copy(data), ctypes.c_ulong(len(data)))


def delay_ms(milliseconds):
    time.sleep(milliseconds / 1000.0)


class ModuleInitError(RuntimeError):
    pass


def module_init():
    if _native.DEV_ModuleInit() != 0:
        raise ModuleInitError("DEV_ModuleInit failed (bcm2835_init could not map GPIO)")


def module_exit():
    _native.DEV_ModuleExit()
    # Waveshare's DEV_ModuleExit never unmaps /dev/gpiomem; each unreleased
    # init leaks 32MB of address space until mmap fails on 32-bit Pis.
    _native.bcm2835_close()
