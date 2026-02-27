import utime
from machine import Pin


class Buzzer(Pin):
    """Handle the buzzer device."""

    def __init__(self, pin_id: int = 4) -> None:
        super().__init__(pin_id, Pin.OUT)

    def beep(self, time_ms: int = 150) -> None:
        """Sound the beeper for the given amount of milliseconds."""
        self.on()
        utime.sleep_ms(time_ms)
        self.off()
