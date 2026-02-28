import os

from machine import Timer

from bluetooth import Bluetooth
from display import Display, NeoPixel
from motor import Drive, DriveState
from ranging import Infrared, Sonar
from remote import Remote
from sensors import Battery, Temperature
from sound import Buzzer

DRIVE_STATES = {
    DriveState.STOP: "Stopped",
    DriveState.BACKWARD: "Backwards",
    DriveState.FORWARD: "Forwards",
    DriveState.BRAKE: "Braked",
    DriveState.LEFT: "Left",
    DriveState.RIGHT: "Right",
}


class Board:
    """Class to handle all board components."""

    def __init__(self) -> None:
        # Motors
        self.drive = Drive()
        # Display
        self.display = Display()
        self.neopixel = NeoPixel()
        # Ranging
        self.infrared = Infrared()
        self.sonar = Sonar()
        # Sound
        self.buzzer = Buzzer()
        # Sensors
        self.battery = Battery()
        self.temperature = Temperature()
        # Control
        self.bluetooth = Bluetooth()
        self.remote = Remote()

    def display_information(self) -> None:
        """Show board information on screen."""
        self.display.fill(0x0000)
        self.display.show()
        for index, text in enumerate(
            (
                f"Board: {os.uname().machine}",
                f"State: {DRIVE_STATES[self.drive.state]}",
                f"Speed: {round(self.drive.speed)}%",
                f"Distance: {self.sonar.get_distance_mm():.1f}mm",
                f"Battery: {self.battery.percentage:.1f}% ({self.battery.voltage:.1f}V)",
                f"Temperature: {self.temperature.celsius:.1f}C",
            )
        ):
            self.display.text(text, 5, 5 + (index * 10), 0xFFFF)
        self.display.show()


class PicoGo(Board):
    """Class to handle the PicoGo mobile robot."""

    def __init__(
        self, default_speed: float = 50, allow_collisions: bool = False
    ) -> None:
        """Initialise board and internal components."""
        super().__init__()
        self._timers = []
        self._callbacks = []
        self.default_speed = self.drive.speed = default_speed
        self.allow_collisions = allow_collisions

    def register(self) -> None:
        """Register callbacks and timers for handling board."""
        self._timers.extend(
            [
                Timer(
                    mode=Timer.PERIODIC,
                    period=5000,
                    callback=lambda _: self.display_information(),
                ),
            ]
        )
        self._callbacks.append(
            lambda board: board.bluetooth.callback(
                board, default_speed=board.default_speed
            )
        )
        self._callbacks.append(
            lambda board: board.remote.callback(
                board, default_speed=board.default_speed
            )
        )
        self._callbacks.append(
            lambda board: not board.allow_collisions
            and board.infrared.any
            and board.drive.state == DriveState.FORWARD
            and board.drive.brake()
        )

    def unregister(self) -> None:
        """Unregister callbacks and timers."""
        for timer in self._timers:
            timer.deinit()
        self._callbacks.clear()

    def start(self) -> None:
        """Start main loop."""
        self.register()
        try:
            while True:
                for callback in self._callbacks:
                    callback(self)
        except KeyboardInterrupt:
            self.unregister()
