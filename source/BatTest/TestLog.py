# standard library
from __future__ import annotations
from enum import Enum
import time
from datetime import datetime, timedelta
import csv
import sys

# external packages

# internal packages

# constants
csv_headers = [
    'Time elapsed',
    'Time elapsed (ms)',
    'Bat Voltage (mV)',
    'Bat Current (mA)',
    'Bat Charge (mAh)',
    'Bat Charge level (%)',
    'Bat Temp (C)'
]

result_keys = [
    'bat_timestamp',
    'bat_timestamp_ms',
    'bat_voltage_mV',
    'bat_current_mA',
    'bat_charge_mAh',
    'bat_charge_level',
    'bat_temp_C'
]


class TestLog(object):
    def __init__(self, fname: str = None, load: bool = False):
        self._results = []
        self._start_datetime = datetime.now()
        self._t_elapsed_ms = 0


        # test phase markers
        self._prechrg_start_idx = -1
        self._const_i_start_idx = -1
        self._const_v_start_idx = -1
        self._dischrg_start_idx = -1

        if fname:
            self._fname = fname
        else:
            self._fname = f'test_results\\battery_test_' \
                f'{self._start_datetime.strftime("%Y-%m-%d_%H-%M-%S")}.csv'

        if load:
            # load from existing file
            self.csv_read_all()
        else:
            # start log file
            self.csv_header_write()

        

    def add_result(self, result_dict):
        # elapsed time in HH:MM:SS.ms and ms
        result_datetime = result_dict['bat_timestamp']
        dt = result_datetime - self._start_datetime
        self._t_elapsed_ms = dt.seconds * 1000 + dt.microseconds / 1000
        result_dict['bat_timestamp'] = self._t_elapsed_ms

        result_row = [str(dt), *result_dict.values()]

        self._results.append(result_dict)
        with open(self._fname, 'a', newline='') as file:
            writer = csv.writer(file)
            writer.writerow(result_row)

    def csv_header_write(self):
        with open(self._fname, 'w', newline='') as file:
            writer = csv.writer(file)
            writer.writerow([self._fname])
            writer.writerow(['BatMan test results'])
            writer.writerow(csv_headers)  

    def csv_read_all(self):
        with open(self._fname, 'r', newline='') as file:
            # clear result list
            self._results = []

            # number of data columns
            num_cols = len(csv_headers)

            reader = csv.reader(file)
            for row in reader:
                # find header row
                if len(row) == num_cols and row != csv_headers:
                    result = dict(zip(result_keys, row))
                    self._results.append(result)

    def test_pass(self):
        # split test into phases
        result_prev = {}
        for result in self._results:
            current = result.get('bat_current')
            current_prev = result_prev.get('bat_current', 0)
            # precharge

    def test_time(self):
        return str(timedelta(milliseconds = self._t_elapsed_ms))   

    @property
    def last(self):
        if self._results:
            return self._results[-1]
        else:
            return None

def result_str(**kwargs):
    result_string = ''

    for description, measurement in zip(csv_headers,kwargs.values()):
        if not result_string:
            result_string += f'{description} - {measurement}\n'
        else:
            result_string += f'  {description} - {measurement:.1f}\n'

    return result_string
    
if __name__ == "__main__":
    fname = sys.argv[1]
    test_log = TestLog(fname,load=True)
    print(test_log._results)
    

# class Result(object):
#     def __init__(self, **kwargs
#     ):

#         self._result_dict = kwargs

#     def __str__(self):
#         string = f'{time.strftime("%H:%M:%S",time.localtime())}, ' + \
#         f'{self.voltage_mV:.0f}, ' + \
#         f'{self.current_mA:.0f}, ' + \
#         f'{self.charge_mAh:.0f}, ' + \
#         f'{self.charge_level:.1f}, ' + \
#         f'{self.temp_C:.0f}'

#         return string

