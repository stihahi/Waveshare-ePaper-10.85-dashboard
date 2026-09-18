import os
import sys
import unittest
from types import SimpleNamespace
from unittest import mock

PROJECT_DIR = os.path.dirname(os.path.dirname(os.path.realpath(__file__)))
sys.path.insert(0, os.path.join(PROJECT_DIR, 'lib'))

with mock.patch('ctypes.CDLL'):
    from waveshare_epd_g import epd10in85g, epdconfig

INIT_OK = 0
INIT_FAILED = 1
BUSY_RELEASED = 1


def fake_native():
    native = mock.MagicMock()
    native.DEV_ModuleInit.return_value = INIT_OK
    native.DEV_Digital_Read.return_value = BUSY_RELEASED
    return native


def blank_frame():
    return SimpleNamespace(master=b'\x55', slave=b'\x55')


class NativeTestCase(unittest.TestCase):
    def setUp(self):
        self.native = fake_native()
        for patcher in (mock.patch.object(epdconfig, '_native', self.native),
                        mock.patch.object(epdconfig, 'delay_ms')):
            patcher.start()
            self.addCleanup(patcher.stop)


class ModuleInitTest(NativeTestCase):
    def test_raises_when_native_init_fails(self):
        self.native.DEV_ModuleInit.return_value = INIT_FAILED
        with self.assertRaises(epdconfig.ModuleInitError):
            epdconfig.module_init()

    def test_succeeds_when_native_init_succeeds(self):
        epdconfig.module_init()
        self.native.DEV_ModuleInit.assert_called_once_with()


class ModuleExitTest(NativeTestCase):
    def test_unmaps_gpio_after_driving_pins_low(self):
        epdconfig.module_exit()
        self.assertEqual([name for name, _, _ in self.native.method_calls],
                         ['DEV_ModuleExit', 'bcm2835_close'])


class ShowTest(NativeTestCase):
    def test_releases_module_after_refresh(self):
        epd10in85g.EPD().show(blank_frame())
        self.native.bcm2835_close.assert_called_once_with()

    def test_releases_module_when_transfer_fails(self):
        self.native.DEV_SPI_SendData_nByte.side_effect = RuntimeError('spi failure')
        with self.assertRaises(RuntimeError):
            epd10in85g.EPD().show(blank_frame())
        self.native.bcm2835_close.assert_called_once_with()

    def test_skips_panel_io_and_release_when_init_fails(self):
        self.native.DEV_ModuleInit.return_value = INIT_FAILED
        with self.assertRaises(epdconfig.ModuleInitError):
            epd10in85g.EPD().show(blank_frame())
        self.native.DEV_Digital_Write.assert_not_called()
        self.native.DEV_ModuleExit.assert_not_called()


if __name__ == '__main__':
    unittest.main()
