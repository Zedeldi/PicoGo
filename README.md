# PicoGo

[![GitHub license](https://img.shields.io/github/license/Zedeldi/PicoGo?style=flat-square)](https://github.com/Zedeldi/PicoGo/blob/master/LICENSE) [![GitHub last commit](https://img.shields.io/github/last-commit/Zedeldi/PicoGo?style=flat-square)](https://github.com/Zedeldi/PicoGo/commits) [![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg?style=flat-square)](https://github.com/psf/black)

Micropython project to control the [PicoGo Mobile Robot from Waveshare](https://www.waveshare.com/picogo.htm).

## Description

Components are implemented within their relevant module, and instantiated within
a `Board` instance to handle the PicoGo as a whole unit.

Callback methods, e.g. remote control, obstacle handling, etc., are registered
with the `PicoGo` instance, which will be called each iteration of the main loop.

Please note that there are some differences between product versions, e.g.:

>  The ADC chips are different in the V1 and V2 versions, the tracking demos are not compatible, but the function effects are the same.

This project is designed for a V2 board. For support with other versions, see [resources](#resources).

## Installation

After flashing the MicroPython firmware to the Pico, copy the `src` directory with `rshell`, etc. and reboot.

## Resources

### PicoGo

 - [Waveshare Wiki](https://www.waveshare.com/wiki/PicoGo)
 - [Jokymon/mypico_go](https://github.com/Jokymon/mypico_go) ([Documentation](https://jokymon.github.io/mypico_go/index.html))

### Display

 - [russhughes/st7789py_mpy](https://github.com/russhughes/st7789py_mpy) (based on [devbis/st7789py_mpy](https://github.com/devbis/st7789py_mpy))

## License

`PicoGo` is licensed under the [MIT Licence](https://mit-license.org/) for everyone to use, modify and share freely.

This project is distributed in the hope that it will be useful, but without any warranty.

## Donate

If you found this project useful, please consider donating. Any amount is greatly appreciated! Thank you :smiley:

[![PayPal](https://www.paypalobjects.com/webstatic/mktg/Logo/pp-logo-150px.png)](https://paypal.me/ZackDidcott)
