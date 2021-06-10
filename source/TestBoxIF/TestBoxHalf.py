# standard library

# external packages

# internal
from .I2C import I2C
from .GPIO import GPIO
from .LTC2943 import LTC2943

class TestBoxHalf(object):
    """docstring for TestBoxHalf"""
    # device config

    def __init__(
        self,
        i2c: I2C = None,
        usb_id = None):

        self._i2c = i2c
        self._gas_gauge = LTC2943(i2c=i2c)
        self._gpio = GPIO(i2c=i2c)
        self._usb_id = usb_id

    @property
    def gas_gauge(self):
        return self._gas_gauge

    @property
    def gpio(self):
        return self._gpio

    @property
    def usb_id(self):
        return self._usb_id
    
    @property
    def battery_present(self):
        return self.gas_gauge.status_reg is not None

