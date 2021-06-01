# standard library

# extenal packages

# internal packages
from source.TestBoxIF.I2C import I2C
from source.TestBoxIF.TestBoxHalf import TestBoxHalf
from source.BatTest.TestLog import TestLog
from source.BatTest.FSM import FSM

class BatteryTest(object):
    """docstring for BatteryTest"""
    def __init__(self, i2c: I2C = None):
        self._i2c = i2c
        self._if_board = TestBoxHalf(i2c)
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
        return self._fsm.test_log

    def start_test(self, charge_setpoint: int = 35):
        self._fsm.start(charge_setpoint,quickcharge=False)

    def start_quickcharge(self, charge_setpoint: int = 100):
        self._fsm.start(charge_setpoint,quickcharge=True)

    def stop(self):
        self._fsm.stop()

    def process(self):
        self._fsm.process()

    # helper methods
