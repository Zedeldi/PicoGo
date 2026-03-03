import rp2
import utime
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
        self.num_sensors = num_sensors
        self.calibrated_min = [0] * self.num_sensors
        self.calibrated_max = [1023] * self.num_sensors
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

    def analog_read(self):
        """
        Read the sensor values into an array.

        There *MUST* be space for as many values as there were sensors specified
        in the constructor.

        Example usage:
        unsigned int sensor_values[8];9
        sensors.read(sensor_values);
        The values returned are a measure of the reflectance in abstract units,
        with higher values corresponding to lower reflectance (e.g. a black
        surface or a void).
        """
        value = [0] * (self.num_sensors + 1)

        # Read each channel AD value
        for j in range(0, self.num_sensors + 1):
            self.cs.value(0)
            # set channel
            self.sm.put(j << 28)
            # get last channel value
            value[j] = self.sm.get() & 0xFFF
            self.cs.value(1)
            value[j] >>= 2
        utime.sleep_ms(2)
        return value[1:]

    def calibrate(self):
        """
        Read the sensors 10 times and use the results for calibration.

        The sensor values are not returned; instead, the maximum and minimum
        values found over time are stored internally and used for the
        read_calibrated method.
        """
        max_sensor_values = [0] * self.num_sensors
        min_sensor_values = [0] * self.num_sensors
        for j in range(0, 10):
            sensor_values = self.analog_read()
            for i in range(0, self.num_sensors):
                # set the max we found this time
                if (j == 0) or max_sensor_values[i] < sensor_values[i]:
                    max_sensor_values[i] = sensor_values[i]
                # set the min we found this time
                if (j == 0) or min_sensor_values[i] > sensor_values[i]:
                    min_sensor_values[i] = sensor_values[i]
        # record the min and max calibration values
        for i in range(0, self.num_sensors):
            if min_sensor_values[i] > self.calibrated_min[i]:
                self.calibrated_min[i] = min_sensor_values[i]
            if max_sensor_values[i] < self.calibrated_max[i]:
                self.calibrated_max[i] = max_sensor_values[i]

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
        for i in range(0, self.num_sensors):
            denominator = self.calibrated_max[i] - self.calibrated_min[i]
            if denominator != 0:
                value = (sensor_values[i] - self.calibrated_min[i]) * 1000 / denominator
            if value < 0:
                value = 0
            elif value > 1000:
                value = 1000
            sensor_values[i] = int(value)
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
        sensor_values = self.read_calibrated()
        avg = 0
        sum = 0
        on_line = 0
        for i in range(0, self.num_sensors):
            value = sensor_values[i]
            if white_line:
                value = 1000 - value
            # keep track of whether we see the line at all
            if value > 200:
                on_line = 1
            # only average in values that are above a noise threshold
            if value > 50:
                avg += value * (i * 1000)
                # this is for the weighted total,
                sum += value
                # this is for the denominator
        if on_line != 1:
            # If it last read to the left of center, return 0.
            if self.last_value < (self.num_sensors - 1) * 1000 / 2:
                # print("left")
                self.last_value = 0
            # If it last read to the right of center, return the max.
            else:
                # print("right")
                self.last_value = (self.num_sensors - 1) * 1000
        else:
            self.last_value = avg / sum
        return int(self.last_value), sensor_values
