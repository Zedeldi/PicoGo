import rp2
from machine import Pin


@rp2.asm_pio(
    out_shiftdir=0,
    autopull=True,
    pull_thresh=12,
    autopush=True,
    push_thresh=12,
    sideset_init=(rp2.PIO.OUT_LOW),
    out_init=rp2.PIO.OUT_LOW,
)
def spi_cpha0():
    """PIO assembly for sensor control."""
    out(pins, 1).side(0x0)[1]  # noqa: F821
    in_(pins, 1).side(0x1)[1]  # noqa: F821


class Sensor:
    """Class to store sensor data."""

    MINIMUM_VALUE = 0
    MAXIMUM_VALUE = 1023

    def __init__(self) -> None:
        """Initialise sensor instance."""
        self.minimum = self.MINIMUM_VALUE
        self.maximum = self.MAXIMUM_VALUE


class Sensors(list):
    """Class to handle multiple sensors."""

    def __init__(self, num_sensors: int) -> None:
        """Initialise calibration instance."""
        super().__init__(Sensor() for _ in range(num_sensors))


class Tracking:
    """Class to handle infrared tracking."""

    def __init__(
        self,
        num_sensors: int = 5,
        clock: Pin = Pin(6, Pin.OUT),
        address: Pin = Pin(7, Pin.OUT),
        data: Pin = Pin(27, Pin.IN),
        cs: Pin = Pin(28, Pin.OUT),
    ) -> None:
        """Initialise instance and state machine."""
        self.sensors = Sensors(num_sensors)
        self.last_value = 0.0
        self.clock = clock
        self.address = address
        self.data = data
        self.cs = cs
        self.cs.value(1)
        self.sm = rp2.StateMachine(
            1,
            spi_cpha0,
            freq=4 * 200000,
            sideset_base=self.clock,
            out_base=self.address,
            in_base=self.data,
        )
        self.sm.active(1)

    def analog_read(self) -> list[int]:
        """
        Read the sensor values and return as a list.

        The values returned are a measure of the reflectance in abstract units,
        with higher values corresponding to lower reflectance (e.g. a black
        surface or a void).

        The StateMachine returns the value of the last selected channel/sensor,
        e.g. when index = 3, the 2nd sensor value will get appended.
        """
        values = []
        # Read each channel AD value
        for index in range(len(self.sensors) + 1):
            self.cs.value(0)
            # set channel
            self.sm.put(index << 28)
            # get last channel value
            values.append((self.sm.get() & 0xFFF) >> 2)
            self.cs.value(1)
        return values[1:]

    def calibrate(self, iterations: int = 10) -> None:
        """
        Read the sensors multiple times and use the results for calibration.

        The sensor values are not returned; instead, the maximum and minimum
        values found over time are stored internally and used for the
        read_calibrated method.
        """
        min_sensor_values = [0] * len(self.sensors)
        max_sensor_values = [0] * len(self.sensors)
        for iteration in range(iterations):
            sensor_values = self.analog_read()
            for index, value in enumerate(sensor_values):
                # set the min we found this time
                if (iteration == 0) or min_sensor_values[index] > value:
                    min_sensor_values[index] = value
                # set the max we found this time
                if (iteration == 0) or max_sensor_values[index] < value:
                    max_sensor_values[index] = value
        # record the min and max calibration values
        for index, values in enumerate(zip(min_sensor_values, max_sensor_values)):
            sensor = self.sensors[index]
            minimum, maximum = values
            # minimum and maximum should converge each calibration
            if minimum > sensor.minimum:
                sensor.minimum = minimum
            if maximum < sensor.maximum:
                sensor.maximum = maximum

    def read_calibrated(self):
        """
        Return values calibrated to a value between 0 and 1000.

        0 corresponds to the minimum value read by calibrate and 1000
        corresponds to the maximum value. Calibration values are
        stored separately for each sensor, so that differences in the
        sensors are accounted for automatically.
        """
        value = 0
        sensor_values = self.analog_read()
        for index, value in enumerate(sensor_values):
            sensor = self.sensors[index]
            denominator = sensor.maximum - sensor.minimum
            if denominator != 0:
                value = (value - sensor.minimum) * 1000 / denominator
            if value < 0:
                value = 0
            elif value > 1000:
                value = 1000
            sensor_values[index] = int(value)
        return sensor_values

    def read_line(self, white_line: bool = False):
        """
        Return an estimated position of the robot with respect to a line.

        Operates the same as read calibrated, but also returns an estimated
        position of the robot with respect to a line. The estimate is made
        using a weighted average of the sensor indices multiplied by 1000, so
        that a return value of:
         - 0 indicates that the line is directly below sensor 0
         - 1000 indicates that the line is directly below sensor 1
         - 2000 indicates that the line is directly below sensor 2000, etc.
        Intermediate values indicate that the line is between two sensors.

        The formula is:

        0 * value0 + 1000 * value1 + 2000 * value2 + ...
        ------------------------------------------------
               value0  +  value1  +  value2 + ...

        By default, this function assumes a dark line (high values) surrounded
        by white (low values). If your line is light on black, set the optional
        second argument white_line to true. In this case, each sensor value
        will be replaced by (1000 - value) before averaging.
        """
        avg = 0
        total = 0
        on_line = False
        sensor_values = self.read_calibrated()
        for index, value in enumerate(sensor_values):
            if white_line:
                value = 1000 - value
            # keep track of whether we see the line at all
            if value > 200:
                on_line = True
            # only average in values that are above a noise threshold
            if value > 50:
                avg += value * (index * 1000)
                # this is for the weighted total,
                total += value
                # this is for the denominator
        if not on_line:
            # If it last read to the left of center, return 0.
            if self.last_value < (len(self.sensors) - 1) * 1000 / 2:
                self.last_value = 0
            # If it last read to the right of center, return the max.
            else:
                self.last_value = (len(self.sensors) - 1) * 1000
        else:
            self.last_value = avg / total
        return int(self.last_value), sensor_values
