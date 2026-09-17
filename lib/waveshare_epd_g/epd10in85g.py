# Driver for the Waveshare 10.85inch e-Paper (G) (black/white/yellow/red).
# Command sequences follow Waveshare's official epd10in85g.py. The panel has no
# partial refresh: every display() is a full, flashing refresh.
import logging

from . import epdconfig

logger = logging.getLogger(__name__)

BUSY_POLL_MS = 20

INIT_SEQUENCE = (
    (0x4D, (0x78,)),
    (0xE0, (0x01,)),
    (0xE5, (0x08,)),
    (0xA2, (0x01,)),
    (0x00, (0x2F, 0x21)),
    (0xA2, (0x02,)),
    (0x00, (0x2F, 0x21)),
    (0xA2, (0x00,)),
    (0x01, (0x07, 0x00)),
    (0x06, (0x0D, 0x12, 0x30, 0x20, 0x19, 0x3D, 0x0C)),
    (0x30, (0x08,)),
    (0x50, (0x37,)),
    (0x61, (0x02, 0xA8, 0x01, 0xE0)),  # resolution per controller: 680x480
    (0x65, (0x00, 0x00, 0x00, 0x00)),
    (0xE3, (0x88,)),
    (0xE9, (0x01,)),
    (0xB8, (0xB5,)),
)
POWER_ON = 0x04
POWER_OFF = 0x02
DEEP_SLEEP = 0x07
DEEP_SLEEP_CHECK_CODE = 0xA5
DATA_START_TRANSMISSION = 0x10
DISPLAY_REFRESH = 0x12


class EPD:
    def init(self):
        epdconfig.module_init()
        self._reset()
        self._wait_until_idle()
        self._select_both()
        for command, data in INIT_SEQUENCE:
            self._send(command, data)
        epdconfig.delay_ms(200)
        self._send(POWER_ON)
        epdconfig.delay_ms(500)
        self._wait_until_idle()
        self._release_both()

    def display(self, frame):
        self._transmit_to(epdconfig.CS_M_PIN, frame.master)
        self._transmit_to(epdconfig.CS_S_PIN, frame.slave)
        self._select_both()
        self._send(DISPLAY_REFRESH, (0x00,))
        self._release_both()
        self._wait_until_idle()

    def sleep(self):
        self._select_both()
        self._send(POWER_OFF, (0x00,))
        epdconfig.delay_ms(100)
        self._send(DEEP_SLEEP, (DEEP_SLEEP_CHECK_CODE,))
        self._release_both()
        epdconfig.delay_ms(2000)
        epdconfig.module_exit()

    def _reset(self):
        for level, wait_ms in ((1, 200), (0, 2), (1, 200)):
            epdconfig.digital_write(epdconfig.RST_PIN, level)
            epdconfig.delay_ms(wait_ms)

    def _wait_until_idle(self):
        logger.debug("waiting for BUSY release")
        epdconfig.delay_ms(100)
        while epdconfig.digital_read(epdconfig.BUSY_PIN) == 0:
            epdconfig.delay_ms(BUSY_POLL_MS)
        logger.debug("BUSY released")

    def _transmit_to(self, chip_select_pin, pixels):
        epdconfig.digital_write(chip_select_pin, 0)
        self._send(DATA_START_TRANSMISSION)
        epdconfig.digital_write(epdconfig.DC_PIN, 1)
        epdconfig.spi_write_bytes(pixels)
        self._release_both()

    def _send(self, command, data=()):
        epdconfig.digital_write(epdconfig.DC_PIN, 0)
        epdconfig.spi_write_byte(command)
        epdconfig.digital_write(epdconfig.DC_PIN, 1)
        for value in data:
            epdconfig.spi_write_byte(value)

    def _select_both(self):
        self._set_both_chip_selects(0)

    def _release_both(self):
        self._set_both_chip_selects(1)

    def _set_both_chip_selects(self, level):
        epdconfig.digital_write(epdconfig.CS_M_PIN, level)
        epdconfig.digital_write(epdconfig.CS_S_PIN, level)
