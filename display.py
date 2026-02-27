from collections import namedtuple

import framebuf
from machine import SPI, Pin
from neopixel import NeoPixel as BaseNeoPixel

BaseColour = namedtuple("BaseColour", ["red", "green", "blue"])


class Colour(BaseColour):
    """Implement colour helper methods."""

    @property
    def rgb565(self) -> tuple[int, int, int]:
        """Convert 24-bit RGB to RGB565 components."""
        return (self.red >> 3, self.green >> 2, self.blue >> 3)

    @property
    def rgb_24bit(self) -> int:
        """Convert 24-bit RGB components to 24-bit RGB value."""
        return (self.red << 16) | (self.green << 8) | self.blue

    @property
    def brg_16bit(self) -> int:
        """Convert 24-bit RGB components to 16-bit BRG value."""
        red, green, blue = self.rgb565
        return (blue << 11) | (red << 5) | green


class Colours:
    """Enumeration of RGB color codes."""

    BLACK = Colour(0, 0, 0)
    WHITE = Colour(255, 255, 255)
    RED = Colour(255, 0, 0)
    ORANGE = Colour(255, 150, 0)
    YELLOW = Colour(255, 255, 0)
    GREEN = Colour(0, 255, 0)
    BLUE = Colour(0, 0, 255)
    CYAN = Colour(0, 255, 255)
    PURPLE = Colour(180, 0, 255)
    MAGENTA = Colour(255, 0, 255)


class Led(Pin):
    """Handle the onboard LED."""

    def __init__(self, pin_id: int = 25) -> None:
        super().__init__(pin_id, Pin.OUT)


class NeoPixel(BaseNeoPixel):
    """Control WS2812 NeoPixel LEDs."""

    def __init__(self, pin: Pin = Pin(22), leds: int = 4):
        super().__init__(pin, leds, bpp=3, timing=1)


class DisplayCommand:
    """Enumeration of display commands."""

    NOP = 0x00
    SWRESET = 0x01
    RDDID = 0x04
    RDDST = 0x09
    SLPIN = 0x10
    SLPOUT = 0x11
    PTLON = 0x12
    NORON = 0x13
    INVOFF = 0x20
    INVON = 0x21
    DISPOFF = 0x28
    DISPON = 0x29
    CASET = 0x2A
    RASET = 0x2B
    RAMWR = 0x2C
    RAMRD = 0x2E
    PTLAR = 0x30
    VSCRDEF = 0x33
    MADCTL = 0x36
    VSCSAD = 0x37
    COLMOD = 0x3A
    RAMCTL = 0xB0
    PORCHCTL = 0xB2
    DISPCTL = 0xB6
    GATECTL = 0xB7
    VCOMSET = 0xBB
    PWRCTL1 = 0xC0
    PWRCTL2 = 0xC2
    PWRCTL3 = 0xC3
    PWRCTL4 = 0xC4
    VCOMCTL1 = 0xC6
    PWRCTLA = 0xD0
    RDID1 = 0xDA
    RDID2 = 0xDB
    RDID3 = 0xDC
    RDID4 = 0xDD
    GAMMA_CURVE_POS = 0xE0
    GAMMA_CURVE_NEG = 0xE1


class MemoryAccessMode:
    """Enumeration of memory access data control values."""

    MADCTL_MY = 0x80
    MADCTL_MX = 0x40
    MADCTL_MV = 0x20
    MADCTL_ML = 0x10
    MADCTL_BGR = 0x08
    MADCTL_MH = 0x04
    MADCTL_RGB = 0x00


class ColourMode:
    """Enumeration of colour modes."""

    COLOUR_MODE_65K = 0x50
    COLOUR_MODE_262K = 0x60
    COLOUR_MODE_12BIT = 0x03
    COLOUR_MODE_16BIT = 0x05
    COLOUR_MODE_18BIT = 0x06
    COLOUR_MODE_16M = 0x07


class Display(framebuf.FrameBuffer):
    """Control an ST7789 display."""

    def __init__(self, width: int = 240, height: int = 135):
        self.width = width
        self.height = height

        self.dc = Pin(8, Pin.OUT)
        self.dc.on()
        self.cs = Pin(9, Pin.OUT)
        self.cs.on()
        self.spi = SPI(
            1, 10_000_000, polarity=0, phase=0, sck=Pin(10), mosi=Pin(11), miso=None
        )
        self.rst = Pin(12, Pin.OUT)
        self.bl = Pin(13, Pin.OUT)
        self.bl.on()

        self.buffer = bytearray(self.height * self.width * 2)
        super().__init__(self.buffer, self.width, self.height, framebuf.RGB565)
        self.init_display()

    def _write(self, data: bytearray, set_dc: bool = False) -> None:
        """Handle writing data to SPI."""
        self.cs.on()
        self.dc(set_dc)
        self.cs.off()
        self.spi.write(data)
        self.cs.on()

    def write(
        self,
        *,
        command: int,
        data: bytearray | list[int] | None = None,
    ):
        """Write command and optionally data to SPI."""
        self._write(bytearray([command]))
        if data:
            if not isinstance(data, bytearray):
                data = bytearray(data)
            self._write(data, set_dc=True)

    def _set_colour_mode(self, mode: int) -> None:
        """Set colour mode of display."""
        self.write(command=DisplayCommand.COLMOD, data=[mode & 0x77])

    def init_display(self):
        """Initialise display."""
        self.rst.on()
        self.rst.off()
        self.rst.on()

        self.write(command=DisplayCommand.MADCTL, data=[0x70])
        self._set_colour_mode(ColourMode.COLOUR_MODE_16BIT)
        self.write(command=DisplayCommand.PORCHCTL, data=[0x0C, 0x0C, 0x00, 0x33, 0x33])
        self.write(command=DisplayCommand.GATECTL, data=[0x35])
        self.write(command=DisplayCommand.VCOMSET, data=[0x19])
        self.write(command=DisplayCommand.PWRCTL1, data=[0x2C])
        self.write(command=DisplayCommand.PWRCTL2, data=[0x01])
        self.write(command=DisplayCommand.PWRCTL3, data=[0x12])
        self.write(command=DisplayCommand.PWRCTL4, data=[0x20])
        self.write(command=DisplayCommand.VCOMCTL1, data=[0x0F])
        self.write(command=DisplayCommand.PWRCTLA, data=[0xA4, 0xA1])
        self.write(
            command=DisplayCommand.GAMMA_CURVE_POS,
            data=[
                0xD0,
                0x04,
                0x0D,
                0x11,
                0x13,
                0x2B,
                0x3F,
                0x54,
                0x4C,
                0x18,
                0x0D,
                0x0B,
                0x1F,
                0x23,
            ],
        )
        self.write(
            command=DisplayCommand.GAMMA_CURVE_NEG,
            data=[
                0xD0,
                0x04,
                0x0C,
                0x11,
                0x13,
                0x2C,
                0x3F,
                0x44,
                0x51,
                0x2F,
                0x1F,
                0x1F,
                0x20,
                0x23,
            ],
        )
        self.write(command=DisplayCommand.INVON)
        self.write(command=DisplayCommand.SLPOUT)
        self.write(command=DisplayCommand.DISPON)

    def show(self):
        """Write framebuffer to display."""
        self.write(command=DisplayCommand.CASET, data=[0x00, 0x28, 0x01, 0x17])
        self.write(command=DisplayCommand.RASET, data=[0x00, 0x35, 0x00, 0xBB])
        self.write(command=DisplayCommand.RAMWR, data=self.buffer)
