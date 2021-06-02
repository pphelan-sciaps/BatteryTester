# standard library
from __future__ import annotations
from enum import Enum
import time
from datetime import datetime
import csv

# external packages

# internal packages

class TestLog(object):
    def __init__(self, fname: str = None, ):
        self._results = []

        if fname:
            self._fname = fname
        else:
            self._fname = f'test_results\\battery_test_' \
                f'{datetime.now().strftime("%Y-%m-%d_%H-%M-%S")}.csv'

        # start log file
        self.csv_header_write()

    def new_result(
        self,
        voltage_mV: int = None,
        current_mA: int = None,
        charge_mAh: int = None,
        charge_level: int = None,
        temp_C: int = None,
    ):
    
        timestamp = f'{datetime.now().strftime("%H:%M:%S")}'    
        result = Result(
            timestamp,
            voltage_mV,
            current_mA,
            charge_mAh,
            charge_level,
            temp_C
        )

        self._results.append(result)
        self.csv_result_write(result)

    def add_result(self, result: Result = None):
        self._results.append(result)

    def csv_header_write(self):
        with open(self._fname, 'w', newline='') as file:
            writer = csv.writer(file)
            writer.writerow([self._fname])
            writer.writerow(['BatMan test results'])
            writer.writerow([
                'Timestamp',
                'Voltage (mV)',
                'Current (mA)',
                'Charge (mAh)',
                'Charge level (%)'
            ])

    def csv_result_write(self, result: Result = None, newline=""):

        with open(self._fname, 'a', newline='') as file:
            writer = csv.writer(file)
            writer.writerow(f'{result}'.split(', '))

    @property
    def last(self):
        if self._results:
            return self._results[-1]
        else:
            return Result(time.time(), 0, 0, 0, 0)
    

class Result(object):
    def __init__(
        self,
        timestamp: str,
        voltage_mV: int,
        current_mA: int,
        charge_mAh: int,
        charge_level: int,
        temp_C: int
        ):

        self.timestamp = timestamp
        self.voltage_mV = voltage_mV
        self.current_mA = current_mA
        self.charge_mAh = charge_mAh
        self.charge_level = charge_level
        self.temp_C = temp_C

    def __str__(self):
        string = f'{time.strftime("%H:%M:%S",time.localtime())}, ' + \
        f'{self.voltage_mV:.0f}, ' + \
        f'{self.current_mA:.0f}, ' + \
        f'{self.charge_mAh:.0f}, ' + \
        f'{self.charge_level:.1f}, ' + \
        f'{self.temp_C:.0f}'

        return string

