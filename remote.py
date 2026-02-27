import utime
from machine import Pin

import board


class Key:
    """Enumeration of remote control keys."""

    CHANNEL_DOWN = 0x45
    CHANNEL = 0x46
    CHANNEL_UP = 0x47
    PREVIOUS = 0x44
    NEXT = 0x40
    PLAY_PAUSE = 0x43
    VOLUME_DOWN = 0x7
    VOLUME_UP = 0x15
    EQ = 0x9
    NUMBER_0 = 0x16
    NUMBER_100_PLUS = 0x19
    NUMBER_200_PLUS = 0xD
    NUMBER_1 = 0xC
    NUMBER_2 = 0x18
    NUMBER_3 = 0x5E
    NUMBER_4 = 0x8
    NUMBER_5 = 0x1C
    NUMBER_6 = 0x5A
    NUMBER_7 = 0x42
    NUMBER_8 = 0x52
    NUMBER_9 = 0x4A


class Remote(Pin):
    """
    Class to handle infrared remote control.

    A pin value of 1 equals silence; 0 equals data.
    """

    def __init__(self, pin_id: int = 5) -> None:
        super().__init__(pin_id, Pin.IN)

    def get_key(self):
        """Get key code from IR sensor."""
        if self.value() == 1:  # No data
            return None

        count = 0
        while (self.value() == 0) and (count < 100):  # 9ms - AGC
            count += 1
            utime.sleep_us(100)
        if count < 10:
            return None
        count = 0
        while (self.value() == 1) and (count < 50):  # 4.5ms - Silence
            count += 1
            utime.sleep_us(100)
        idx = 0
        cnt = 0
        data = [0, 0, 0, 0]  # 8-bit address and command
        for i in range(0, 32):  # 32 bits
            count = 0
            while (self.value() == 0) and (count < 10):  # 0.56ms
                count += 1
                utime.sleep_us(100)
            count = 0
            while (self.value() == 1) and (count < 20):  # 0: 0.56ms
                count += 1  # 1: 1.69ms
                utime.sleep_us(100)
            if count > 7:
                data[idx] |= 1 << cnt
            if cnt == 7:
                cnt = 0
                idx += 1
            else:
                cnt += 1
        if data[0] + data[1] == 0xFF and data[2] + data[3] == 0xFF:  # check
            return data[2]
        else:
            return "repeat"

    def callback(
        self,
        board: board.Board,
        speed_increment: float = 10,
        default_speed: float = 50,
    ) -> None:
        """Control board with remote control."""
        key = self.get_key()
        if key is None:
            return
        elif key == Key.NUMBER_0:
            board.drive.brake()
        elif key == Key.NUMBER_2:
            board.drive.forward()
        elif key == Key.NUMBER_4:
            board.drive.left()
        elif key == Key.NUMBER_5:
            board.drive.stop()
        elif key == Key.NUMBER_6:
            board.drive.right()
        elif key == Key.NUMBER_8:
            board.drive.backward()
        elif key == Key.EQ:
            board.drive.speed = default_speed
        elif key == Key.VOLUME_UP:
            board.drive.speed += speed_increment
        elif key == Key.VOLUME_DOWN:
            board.drive.speed -= speed_increment
        elif key == Key.PLAY_PAUSE:
            board.buzzer.toggle()
