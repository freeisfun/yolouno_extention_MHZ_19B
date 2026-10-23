"""
MH-Z19B CO2 sensor (Winsen) - MicroPython driver for Yolo:Bit / OhStem App

Based on "MH-Z19_MicroPython" by Florian "overflo" Bittner (12/2020), MIT license
https://github.com/overflo23/MH-Z19_MicroPython

Changes compared with the original library:
  - UART pins can be chosen (the original used the default UART pins, which on
    ESP32 are connected to the flash chip and cannot be used on Yolo:Bit)
  - checksum is truncated to 8 bit (the original gave 256 instead of 0)
  - input buffer is flushed before every request, the reply is searched for the
    0xFF 0x86 header and the checksum is verified
  - added: zero calibration, auto calibration (ABC), measuring range, span
    calibration, warm-up check, short cache so several blocks can read the
    sensor in the same loop without hammering the UART
  - added: simple module level functions used by the OhStem App blocks

Wiring (sensor -> Yolo:Bit):  Vin -> 5V,  GND -> GND,
                              RX  -> TX pin chosen in the block,
                              TX  -> RX pin chosen in the block
"""

from machine import UART
import time

__all__ = [
    "MHZ19B", "mhz19",
    "mhz19b_init", "mhz19b_co2", "mhz19b_temp", "mhz19b_ready",
    "mhz19b_calibrate_zero", "mhz19b_auto_calibrate", "mhz19b_set_range",
]

CMD_READ = 0x86   # read CO2 concentration
CMD_ZERO = 0x87   # zero point calibration (400 ppm)
CMD_SPAN = 0x88   # span point calibration
CMD_ABC = 0x79    # automatic baseline correction on/off
CMD_RANGE = 0x99  # detection range 2000 / 5000 ppm

WARMUP_MS = 180000  # the sensor needs about 3 minutes after power on

CO2_ERROR = -1      # returned by read_co2() when no valid answer was received
TEMP_ERROR = -99    # returned by read_temp() when no valid answer was received


def _to_pin(p):
    """Accept a Yolo:Bit pin (pin14), a machine.Pin or a GPIO number."""
    if p is None:
        return None
    if hasattr(p, "pin"):  # Yolo:Bit pin object wraps a machine.Pin in .pin
        return p.pin
    return p


class MHZ19B:
    def __init__(self, uart_no=1, tx=None, rx=None, min_interval=1000):
        self.uart_no = uart_no
        self.tx = _to_pin(tx)
        self.rx = _to_pin(rx)
        self.min_interval = min_interval  # ms, readings newer than this are reused
        self.ppm = 0
        self.temp = 0
        self.co2status = 0
        self._last = None
        self.uart = None
        self._t0 = time.ticks_ms()  # power-on time, used for the warm-up check
        self.start()

    # ---- UART handling (same names as the original library) -----------------
    def start(self):
        if self.tx is not None and self.rx is not None:
            self.uart = UART(self.uart_no, baudrate=9600, bits=8, parity=None,
                             stop=1, tx=self.tx, rx=self.rx, timeout=100)
        else:
            self.uart = UART(self.uart_no, 9600)
            self.uart.init(9600, bits=8, parity=None, stop=1, timeout=100)

    def stop(self):
        self._flush()
        self.uart.deinit()

    def _flush(self):
        n = 0
        while self.uart.any() and n < 10:
            self.uart.read()
            n += 1

    # ---- frame helpers --------------------------------------------------------
    @staticmethod
    def _checksum(frame):
        s = 0
        for i in range(1, 8):
            s += frame[i]
        return ((~(s & 0xFF)) + 1) & 0xFF

    def crc8(self, a):
        # name kept from the original library
        return self._checksum(a)

    def _build(self, cmd, b3=0, b4=0, b5=0, b6=0, b7=0):
        frame = bytearray([0xFF, 0x01, cmd, b3, b4, b5, b6, b7, 0])
        frame[8] = self._checksum(frame)
        return frame

    def _request(self, cmd):
        """Send a read command and return the verified 9 byte answer or None."""
        self._flush()
        self.uart.write(self._build(cmd))
        time.sleep_ms(100)
        data = self.uart.read()
        if not data:
            return None
        for i in range(len(data) - 8):
            if data[i] == 0xFF and data[i + 1] == cmd:
                resp = data[i:i + 9]
                if self._checksum(resp) == resp[8]:
                    return resp
        return None

    def _send(self, frame):
        """Send a command that has no answer (calibration, settings)."""
        self._flush()
        self.uart.write(frame)

    # ---- measuring ------------------------------------------------------------
    def get_data(self):
        """Ask the sensor once. Fills ppm / temp / co2status. Returns 1 or 0."""
        resp = self._request(CMD_READ)
        if resp is None:
            return 0
        self.ppm = resp[2] * 256 + resp[3]
        self.temp = resp[4] - 40
        self.co2status = resp[5]
        self._last = time.ticks_ms()
        return 1

    def update(self, force=False, retries=3):
        """Refresh the values (max. once per min_interval). True if values are valid."""
        if (not force) and self._last is not None:
            if time.ticks_diff(time.ticks_ms(), self._last) < self.min_interval:
                return True
        for _ in range(retries):
            if self.get_data():
                return True
            time.sleep_ms(50)
        return False

    def read_co2(self):
        """CO2 in ppm, or -1 if the sensor did not answer."""
        if self.update():
            return self.ppm
        return CO2_ERROR

    def read_temp(self):
        """Sensor temperature in degC (not accurate), or -99 on error."""
        if self.update():
            return self.temp
        return TEMP_ERROR

    def is_ready(self):
        """True once the 3 minute warm-up time is over."""
        return time.ticks_diff(time.ticks_ms(), self._t0) >= WARMUP_MS

    # ---- calibration / settings -----------------------------------------------
    def calibrate_zero(self):
        """Zero point = 400 ppm. Keep the sensor ~20 min in fresh outdoor air first."""
        self._send(self._build(CMD_ZERO))

    def set_auto_calibrate_zero(self, on=True):
        """Automatic baseline correction (needs a daily drop to ~400 ppm)."""
        self._send(self._build(CMD_ABC, 0xA0 if on else 0x00))

    def set_range(self, ppm):
        """Detection range, 2000 or 5000 ppm."""
        if ppm not in (2000, 5000):
            raise ValueError("range must be 2000 or 5000")
        self._send(self._build(CMD_RANGE, 0, 0, 0, ppm >> 8, ppm & 0xFF))

    def calibrate_span(self, ppm=2000):
        """Span point (advanced, needs a known gas concentration, 2000 ppm recommended)."""
        self._send(self._build(CMD_SPAN, ppm >> 8, ppm & 0xFF))


# Name used by the original library
mhz19 = MHZ19B


# ---------------------------------------------------------------------------
# Module level functions: these are what the OhStem App blocks generate.
# ---------------------------------------------------------------------------
_sensor = None


def _need():
    if _sensor is None:
        raise RuntimeError("Dung khoi 'khoi tao cam bien CO2 MH-Z19B' truoc")
    return _sensor


def mhz19b_init(tx, rx, uart_no=1):
    global _sensor
    if _sensor is not None:
        try:
            _sensor.stop()
        except Exception:
            pass
    _sensor = MHZ19B(uart_no, tx, rx)
    return _sensor


def mhz19b_co2():
    return _need().read_co2()


def mhz19b_temp():
    return _need().read_temp()


def mhz19b_ready():
    return _need().is_ready()


def mhz19b_calibrate_zero():
    _need().calibrate_zero()


def mhz19b_auto_calibrate(on):
    _need().set_auto_calibrate_zero(on)


def mhz19b_set_range(ppm):
    _need().set_range(int(ppm))
