# cedargrove_sdcard.py
import board
import busio
import digitalio
import storage
import adafruit_sdcard
from adafruit_bitmapsaver import save_pixels

class SDCard:
    def __init__(self):
        """Instantiate and test for SD card."""
        self._spi = busio.SPI(board.SCK, MOSI=board.MOSI, MISO=board.MISO)
        self._sd_cs = digitalio.DigitalInOut(board.SD_CS)
        self._has_card = False
        try:
            self._sdcard = adafruit_sdcard.SDCard(self._spi, self._sd_cs)
            self._vfs = storage.VfsFat(self._sdcard)
            storage.mount(self._vfs, '/sd')
            print('SD card found')
            self._has_card = True
        except OSError as error:
            print('SD card NOT found: ', error)

    @property
    def has_card(self):
        """True if SD card inserted."""
        return self._has_card

    def screenshot(self):
        if self._has_card:
            print('Taking Screenshot...', end='')
            save_pixels('/sd/screenshot.bmp')
            print(' Screenshot stored')
        else:
            print('SCREENSHOT: NO SD CARD')

    def read_config(self):
        """Read configuration text file from SD card."""
        pass

    def write_config(self):
        """Write configuration text file to SD card."""
        pass
