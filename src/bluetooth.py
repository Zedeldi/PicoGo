import ujson
from machine import UART

import board


class Bluetooth(UART):
    """Handle Bluetooth connectivity."""

    BAUDRATE = 115200

    def __init__(self) -> None:
        """Initialise UART instance."""
        super().__init__(0, self.BAUDRATE)

    def callback(
        self,
        board: board.Board,
        speed_increment: float = 10,
        default_speed: float = 50,
    ) -> None:
        """Control board with Bluetooth."""
        if not self.any():
            return
        try:
            data = ujson.loads(self.read())
        except ValueError:
            return

        drive = data.get("drive")
        if drive == "forward":
            board.drive.forward()
        elif drive == "backward":
            board.drive.backward()
        elif drive == "left":
            board.drive.left()
        elif drive == "right":
            board.drive.right()
        elif drive == "stop":
            board.drive.stop()
        elif drive == "brake":
            board.drive.brake()

        speed = data.get("speed")
        if speed == "default":
            board.drive.speed = default_speed
        elif speed == "increase":
            board.drive.speed += speed_increment
        elif speed == "decrease":
            board.drive.speed -= speed_increment
        elif isinstance(speed, int) or isinstance(speed, float):
            board.drive.speed = float(speed)

        buzzer = data.get("buzzer")
        if buzzer == "toggle":
            board.buzzer.toggle()
        elif buzzer == "on":
            board.buzzer.on()
        elif buzzer == "off":
            board.buzzer.off()
