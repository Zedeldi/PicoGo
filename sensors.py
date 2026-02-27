from machine import ADC, Pin


class Battery(ADC):
    """Get battery voltage and charge percentage."""

    def __init__(self, pin: Pin = Pin(26)) -> None:
        super().__init__(pin)

    @property
    def voltage(self) -> float:
        """Return voltage of battery."""
        return self.read_u16() * 3.3 / 65535 * 2

    @property
    def percentage(self) -> float:
        """Return percentage charge of battery."""
        percentage = (self.voltage - 3) * 100 / 1.2
        if percentage < 0:
            percentage = 0
        if percentage > 100:
            percentage = 100
        return percentage


class Temperature(ADC):
    """Get chip temperature."""

    def __init__(self, channel: int = 4) -> None:
        super().__init__(channel)

    @property
    def celsius(self) -> float:
        """Return temperature in degree Celsius."""
        reading = self.read_u16() * 3.3 / (65535)
        return 27 - (reading - 0.706) / 0.001721
