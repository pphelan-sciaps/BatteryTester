# standard library

# extenal packages

# internal packages
from source.TestBoxIF.I2C import I2C
from source.TestBoxIF.TestBoxHalf import TestBoxHalf
from source.BatTest.TestLog import TestLog
from source.BatTest.FSM import FSM

class BatteryTest(object):
    """docstring for BatteryTest"""
    def __init__(
        self,
        i2c: I2C = None,
        usb_id = None):

        self._i2c = i2c

        self._if_board = TestBoxHalf(i2c,usb_id)
        self._fsm = FSM(self._if_board)
        self._result = None
        self._charge_setpoint = 100
        self._status = None

    # API
    @property
    def if_board(self):
        return self._if_board

    @property
    def test_log(self):
        return self._fsm._test_log

    @property
    def state_name(self):
        return self._fsm.state_name

    @property
    def test_time(self):
        if self.test_log:
            return self.test_log.test_time

    @property
    def done(self):
        return self._fsm.done

    def start_test(self, charge_setpoint: int = 35, short_test: bool = False):
        self._fsm.start(
            charge_setpoint,
            quickcharge=False,
            short_test = short_test)

    def start_quickcharge(self, charge_setpoint: int = 100):
        self._fsm.start(charge_setpoint,quickcharge=True)

    def stop(self):
        self._fsm.stop()

    def process(self):
        self._fsm.process()


    # helper methods
