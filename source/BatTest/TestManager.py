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
    def __init__(self, threaded = False):
        self._bat_tests = []
        self._conn_man = ConnectionManager()
        self._device_locations = []
        self._threaded = threaded

        # start IO loop thread
        if self._threaded:
            self._event = threading.Event()
            t = threading.Thread(target=self.step_thread, daemon=True)
            t.start()

    @property
    def device_locations(self):
        self._device_locations = self._conn_man.device_locations
        return self._device_locations

    def open_connection(self, idx: int):
        box_id = self.device_locations[idx]
        i2c = I2C(self._conn_man.open_connection(idx))
        bat_test = BatteryTest(i2c, box_id)
        self._bat_tests.append(bat_test)

    def close_connection(self):
        if self._bat_tests:
            self._bat_tests[0].stop()
            del self._bat_tests[0]

    def bat_test(self, test_num: int = 0):
        try:
            return self._bat_tests[test_num]
        except IndexError:
            print('Invalid box index')

    def step(self):
        for test in self._bat_tests:
            try:
                test.process()
            except Exception as e:
                raise e

    def step_thread(self):
        while not self._event.isSet():
            self.step()

            try:
                self._event.wait(1)
            except KeyboardInterrupt:
                self._event.set()
                break
