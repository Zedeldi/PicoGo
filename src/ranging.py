import utime
from machine import Pin


class Sonar:
    """Control an HC-SR04 ultrasonic ranging module."""

    SPEED_OF_SOUND = 343  # m/s

    def __init__(
        self,
        echo: Pin = Pin(15, Pin.IN),
        trigger: Pin = Pin(14, Pin.OUT),
        pulse_length_us: int = 10,
    ) -> None:
        """Initialise sonar instance."""
        self.echo = echo
        self.trigger = trigger
        self.pulse_length_us = pulse_length_us
        self.echo.off()
        self.trigger.off()

    def get_duration_us(self) -> int:
        """Return duration in microseconds from sending ultrasonic pulse to returning."""
        self.trigger.on()
        utime.sleep_us(self.pulse_length_us)
        self.trigger.off()
        while self.echo.value() == 0:
            pass
        start = utime.ticks_us()
        while self.echo.value() == 1:
            pass
        end = utime.ticks_us()
        return end - start

    def get_distance_mm(self) -> float:
        """Return distance in millimetres from object."""
        duration = self.get_duration_us()
        # total mm: metres * 1000 = duration * (m/ms)
        distance = (duration * (self.SPEED_OF_SOUND / 1000)) / 2
        return distance


class Infrared:
    """Read ST188 reflective photointerrupters with LM393 differential comparator."""

    def __init__(self, left: Pin = Pin(3, Pin.IN), right: Pin = Pin(2, Pin.IN)) -> None:
        """Initialise infrared instance."""
        self._left = left
        self._right = right

    @property
    def left(self) -> bool:
        """Return whether left infrared sensor is triggered."""
        return self._left.value() == 0

    @property
    def right(self) -> bool:
        """Return whether right infrared sensor is triggered."""
        return self._right.value() == 0

    @property
    def any(self) -> bool:
        """Return whether any infrared sensor is triggered."""
        return self.left or self.right

    @property
    def all(self) -> bool:
        """Return whether both infrared sensors are triggered."""
        return self.left and self.right
