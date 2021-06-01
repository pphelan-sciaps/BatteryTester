# standard library
from cmd import Cmd
import threading
from time import sleep

# external packages

# internal packages
from source.BatTest.BatteryTest import BatteryTest
from source.TestBoxIF.I2C import I2C
from source.TestBoxIF.ConnectionManager import ConnectionManager 
from source.TestBoxIF.TestBoxHalf import TestBoxHalf

class TestManager(object):
    """docstring for TestManager"""
    def __init__(self):
        self._bat_tests = []
        self._conn_man = ConnectionManager()

        # start IO loop thread
        self._event = threading.Event()
        t = threading.Thread(target=self.step_thread, daemon=True)
        t.start()

    @property
    def device_locations(self):
        return self._conn_man.device_locations

    def open_connection(self, idx: int):
        i2c = I2C(self._conn_man.open_connection(idx))
        bat_test = BatteryTest(i2c)
        self._bat_tests.append(bat_test)

    def bat_test(self, test_num: int = 0):
        try:
            return self._bat_tests[test_num]
        except IndexError:
            print('Invalid box index')

    def step_thread(self):
        while not self._event.isSet():
            for test in self._bat_tests:
                try:
                    test.process()
                except Exception as e:
                    raise e

            try:
                self._event.wait(1)
            except KeyboardInterrupt:
                self._event.set()
                break
