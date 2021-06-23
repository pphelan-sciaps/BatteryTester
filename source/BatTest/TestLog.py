# standard library
from __future__ import annotations
from enum import Enum
import time
from datetime import datetime, timedelta
import csv
import sys
from collections import deque

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

prechrg_lims = {
    'i_min' : 210,
    'i_max' : 390,
    'v_min' : 7000,
    'v_max' : 12267
}

const_i_lims = {
    'i_min' : 900,
    'i_max' : 1200,
    'v_min' : 12016,
    'v_max' : 16779
}

const_v_lims = {
    'i_min' : 100,
    'i_max' : 1159,
    'v_min' : 16121,
    'v_max' : 16779
}

dischrg_lims = {
    'i_min' : -5649,
    'i_max' : -1928,
    'v_min' : 7000,
    'v_max' : 16779
}

test_lims = [prechrg_lims, const_i_lims, const_v_lims, dischrg_lims]

PRECHRG_END_VFB_THRESH_mV = 1550*235/30  # VFB = Vbat(mV) * 30k/(205k + 30k)
DISCHRG_I_THRESH_mA = -50


class TestLog(object):
    def __init__(
        self,
        fname: str = None,
        load: bool = False,
        box_id: str = ''):

        self._results = []
        self._t_elapsed_ms = 0

        self._box_id = box_id

        # test phase markers
        self._prechrg_start_idx = -1
        self._const_i_start_idx = -1
        self._const_v_start_idx = -1
        self._dischrg_start_idx = -1


        if fname:
            self._fname = fname
        else:
            self._fname = f'test_results\\battery_test_' \
                f'box_{self._box_id}_'\
                f'{datetime.now().strftime("%Y-%m-%d_%H-%M-%S")}.csv'

        if load:
            # load from existing file
            self.csv_read_all()
        else:
            # start log file
            self.csv_header_write()

        

    def add_result(self, result_dict):
        # elapsed time in HH:MM:SS.ms and ms
        # result_datetime = result_dict['bat_timestamp']
        # dt = result_datetime - self._start_datetime
        # self._t_elapsed_ms = dt.seconds * 1000 + dt.microseconds / 1000
        # result_dict['bat_timestamp'] = self._t_elapsed_ms

        result_row = [*result_dict.values()]

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
            for str_row in reader:
                if len(str_row) != len(csv_headers):
                    continue

                row = []
                
                # convert string to values
                for i,val in enumerate(str_row):
                    try:
                        val = float(val)
                    except:
                        pass
                    row.append(val)
                result = dict(zip(result_keys, row))
                self._results.append(result)

    def test_pass(self):
        # find phase boundries
        current_prev = 0

        i_avg = 0
        i_avg_samples = 0
        i_rolling_avg_deque = deque([None] * 10, maxlen=10)
        const_i_currents_mA = []

        i_discharge_deque = deque([0] * 5, maxlen=5)

        for i, result in enumerate(self._results):
            if '' in result.values():
                continue

            global csv_headers
            if i < len(csv_headers):
                continue

            current = result.get('bat_current_mA', 0)
            voltage = result.get('bat_voltage_mV', 0)
            charge  = result.get('charge_level', 0)

            if self._prechrg_start_idx < 0:
                if current > 0 and current_prev < 0:
                    self._prechrg_start_idx = i
                    print(f'prechrg start {i}')
                current_prev = current

            # start of constant current
            if voltage > PRECHRG_END_VFB_THRESH_mV and self._const_i_start_idx < 0:
                self._const_i_start_idx = i
                print(f'const i start {i}')

            # start of constant voltage
            if self._const_i_start_idx > 0 and self._const_v_start_idx < 0:
                # find average current
                i_avg = (i_avg_samples * i_avg + current)/(i_avg_samples + 1)                
                i_avg_samples += 1

                # rolling average current
                try:
                    i_rolling_avg_deque.append(current)
                    i_rolling_avg = sum(i_rolling_avg_deque)/len(i_rolling_avg_deque)
                except TypeError:
                    i_rolling_avg = i_avg

                if i_avg - i_rolling_avg > 10:
                    self._const_v_start_idx = i
                    print(f'const v start {i}')
            # start of discharge
            if self._const_v_start_idx > 0 and self._dischrg_start_idx < 0:
                if all([current < 0 for current in i_discharge_deque]):
                    self._dischrg_start_idx = i
                    print(f'dischrg start {i}')
                    break
                i_discharge_deque.append(current)

        # split result into charge phases
        try:
            test_phases = [
                self._results[self._prechrg_start_idx+10:self._const_i_start_idx-10],
                self._results[self._const_i_start_idx+10:self._const_v_start_idx-10],
                self._results[self._const_v_start_idx+10:self._dischrg_start_idx-10],
                self._results[self._dischrg_start_idx+50:-3]
            ]
        except IndexError:
            print('unable to split into phases')
            return False

        global test_lims
        errors = 0

        for i, (phase, limit) in enumerate(zip(test_phases, test_lims)):
            # print(phase)
            i_results = [result.get('bat_current_mA',None) for result in phase]
            v_results = [result.get('bat_voltage_mV',None) for result in phase]

            i_stats = self.calc_stats(i_results)
            v_stats = self.calc_stats(v_results)
            
            try:
                if i_stats['min'] < limit['i_min']:
                    print(f'i_lim min {i} {i_stats}')
                    errors += 1
                if i_stats['max'] > limit['i_max']:
                    print(f'i_lim max {i} {i_stats}')
                    errors += 1
                if v_stats['min'] < limit['v_min']:
                    print(f'v_lim min {i} {v_stats}')
                    errors += 1
                if v_stats['max'] > limit['v_max']:
                    print(f'v_lim max {i} {v_stats}')
                    errors += 1
            except TypeError:
                errors += 1

        return errors == 0

    def calc_stats(self,measurement_list):
        stats = {}
        try:
            stats['min'] = min(measurement_list)
            stats['max'] = max(measurement_list)
            stats['avg'] = sum(measurement_list)/len(measurement_list)
            return stats
        except:
            print(measurement_list)

    # @property
    # def test_time(self):
    #     test_time = datetime.fromtimestamp(self._t_elapsed_ms/1000).strftime("%H:%M:%S")
    #     print(self._t_elapsed_ms)
    #     print(test_time)
    #     1/0
    #     return test_time

    # @property
    # def test_time_h(self):
    #     return self._t_elapsed_ms/(1000 * 60 * 60)   

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
    print(test_log.test_pass())
    

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

