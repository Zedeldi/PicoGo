from collections import namedtuple

from machine import PWM, Pin

MotorControls = namedtuple("MotorControls", ("speed", "forward", "backward"))
MotorGroup = namedtuple("MotorGroup", ("left", "right"))


class MotorState:
    """Enumeration of motor states."""

    STOP = 0
    BACKWARD = 1
    FORWARD = 2
    BRAKE = 3


class DriveState(MotorState):
    """Enumeration of drive states."""

    LEFT = 4
    RIGHT = 5


class Motor:
    """Base class for motor devices."""

    SPEED_FREQ = 1000

    def __init__(self, controls: MotorControls) -> None:
        self.controls = controls
        self.controls.speed.freq(self.SPEED_FREQ)

    @property
    def state(self) -> int:
        """Return state of motor."""
        return (self.controls.forward.value() << 1) + self.controls.backward.value()

    @property
    def speed(self) -> float:
        """Return current speed of PWM as a percentage."""
        return (self.controls.speed.duty_u16() * 100) / 0xFFFF

    @speed.setter
    def speed(self, speed: float) -> None:
        """Set speed of PWM as a percentage."""
        if speed < 0:
            speed = 0
        elif speed > 100:
            speed = 100
        self.controls.speed.duty_u16(int(speed * 0xFFFF / 100))

    def forward(self, speed: float | None = None) -> None:
        """Set motor to drive forwards at specified speed."""
        if speed is not None:
            self.speed = speed
        self.controls.forward.on()
        self.controls.backward.off()

    def backward(self, speed: float | None = None) -> None:
        """Set motor to drive backwards at specified speed."""
        if speed is not None:
            self.speed = speed
        self.controls.forward.off()
        self.controls.backward.on()

    def stop(self) -> None:
        """Stop motor."""
        self.controls.forward.off()
        self.controls.backward.off()

    def brake(self) -> None:
        """Apply short brake."""
        self.controls.forward.on()
        self.controls.backward.on()


class Drive:
    """Handle a group of motors to provide drive."""

    def __init__(self):
        """Initialise drive instance with motors."""
        self.motors = MotorGroup(
            left=Motor(
                MotorControls(
                    speed=PWM(Pin(16)),
                    forward=Pin(17, Pin.OUT),
                    backward=Pin(18, Pin.OUT),
                )
            ),
            right=Motor(
                MotorControls(
                    speed=PWM(Pin(21)),
                    forward=Pin(20, Pin.OUT),
                    backward=Pin(19, Pin.OUT),
                )
            ),
        )
        self.stop()

    @property
    def state(self) -> int:
        """Return state of drive."""
        left, right = self.motors.left.state, self.motors.right.state
        # Forward, backward, stop or brake
        if left == right:
            return left
        # Left
        elif left == MotorState.BACKWARD or right == MotorState.FORWARD:
            return DriveState.LEFT
        # Right
        elif left == MotorState.FORWARD or right == MotorState.BACKWARD:
            return DriveState.RIGHT
        # Stop/brake
        return DriveState.STOP

    @property
    def speed(self) -> float:
        """Return average speed of all motor as a percentage."""
        return sum(motor.speed for motor in self.motors) / len(self.motors)

    @speed.setter
    def speed(self, speed: float) -> None:
        """Set speed of all motors as a percentage."""
        for motor in self.motors:
            motor.speed = speed

    def forward(self, speed: float | None = None) -> None:
        """Drive all motors forwards at specified speed."""
        for motor in self.motors:
            motor.forward(speed)

    def backward(self, speed: float | None = None) -> None:
        """Drive all motors backwards at specified speed."""
        for motor in self.motors:
            motor.backward(speed)

    def left(self, speed: float | None = None) -> None:
        """Turn left at specified speed."""
        self.motors.right.forward(speed)
        self.motors.left.backward(speed)

    def right(self, speed: float | None = None) -> None:
        """Turn right at specified speed."""
        self.motors.left.forward(speed)
        self.motors.right.backward(speed)

    def stop(self) -> None:
        """Stop all motors."""
        for motor in self.motors:
            motor.stop()

    def brake(self) -> None:
        """Apply short brake to all motors."""
        for motor in self.motors:
            motor.brake()
