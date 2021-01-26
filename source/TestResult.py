# Object to handle test result storage and basic operations
# system utilities
import sys
import os
import errno
import traceback
import logging
from collections import deque

# helper modules
from PackageLogger import get_logger

# constants
PRECHRG_END_VFB_THRESH_mV = 1550*235/30  # VFB = Vbat(mV) * 30k/(205k + 30k)
DISCHRG_I_THRESH_mA = -50


class TestResult():
    def __init__(self,fname='',logger_name='BatteryTest'):
        # open log
        self.logger = get_logger(logger_name)

        # intialize vars
        self.clear_test_results()        

        # load data from log file
        if fname != '':
            self.log_to_TestResult(fname)

    # calculate stats
    def get_all_stats(self):
        stats = {}

        stats['prechrg_time']   = self.prechrg_time()
        stats['prechrg_mV_min'] = self.prechrg_mV_min()
        stats['prechrg_mV_max'] = self.prechrg_mV_max()
        stats['prechrg_mV_avg'] = self.prechrg_mV_avg()
        stats['prechrg_mA_min'] = self.prechrg_mA_min()
        stats['prechrg_mA_max'] = self.prechrg_mA_max()
        stats['prechrg_mA_avg'] = self.prechrg_mA_avg()

        stats['const_i_time']   = self.const_i_time()
        stats['const_i_mV_min'] = self.const_i_mV_min()
        stats['const_i_mV_max'] = self.const_i_mV_max()
        stats['const_i_mV_avg'] = self.const_i_mV_avg()
        stats['const_i_mA_min'] = self.const_i_mA_min()
        stats['const_i_mA_max'] = self.const_i_mA_max()
        stats['const_i_mA_avg'] = self.const_i_mA_avg()

        stats['const_v_time']   = self.const_v_time()
        stats['const_v_mV_min'] = self.const_v_mV_min()
        stats['const_v_mV_max'] = self.const_v_mV_max()
        stats['const_v_mV_avg'] = self.const_v_mV_avg()
        stats['const_v_mA_min'] = self.const_v_mA_min()
        stats['const_v_mA_max'] = self.const_v_mA_max()
        stats['const_v_mA_avg'] = self.const_v_mA_avg()

        stats['chrg_time'] = self.chrg_time()

        stats['dischrg_time']   = self.dischrg_time()
        stats['dischrg_mV_min'] = self.dischrg_mV_min()
        stats['dischrg_mV_max'] = self.dischrg_mV_max()
        stats['dischrg_mV_avg'] = self.dischrg_mV_avg()
        stats['dischrg_mA_min'] = self.dischrg_mA_min()
        stats['dischrg_mA_max'] = self.dischrg_mA_max()
        stats['dischrg_mA_avg'] = self.dischrg_mA_avg()

        return stats


    # precharge phase
    def prechrg_time(self):
        return self.phase_time(self.prechrg_start, self.prechrg_end)

    def prechrg_mV_min(self):
        return self.phase_min(self.prechrg_start, self.prechrg_end, 'voltage')

    def prechrg_mV_max(self):
        return self.phase_max(self.prechrg_start, self.prechrg_end, 'voltage')

    def prechrg_mV_avg(self):
        return self.phase_avg(self.prechrg_start, self.prechrg_end, 'voltage')

    def prechrg_mA_min(self):
        return self.phase_min(self.prechrg_start, self.prechrg_end, 'current')

    def prechrg_mA_max(self):
        return self.phase_max(self.prechrg_start, self.prechrg_end, 'current')

    def prechrg_mA_avg(self):
        return self.phase_avg(self.prechrg_start, self.prechrg_end, 'current')

    # constant current phase
    def const_i_time(self):
        return self.phase_time(self.const_i_start, self.const_i_end)

    def const_i_mV_min(self):
        return self.phase_min(self.const_i_start, self.const_i_end, 'voltage')

    def const_i_mV_max(self):
        return self.phase_max(self.const_i_start, self.const_i_end, 'voltage')

    def const_i_mV_avg(self):
        return self.phase_avg(self.const_i_start, self.const_i_end, 'voltage')

    def const_i_mA_min(self):
        return self.phase_min(self.const_i_start, self.const_i_end, 'current')

    def const_i_mA_max(self):
        return self.phase_max(self.const_i_start, self.const_i_end, 'current')

    def const_i_mA_avg(self):
        return self.phase_avg(self.const_i_start, self.const_i_end, 'current')

    # constant voltage phase
    def const_v_time(self):
        return self.phase_time(self.const_v_start, self.chrg_end)

    def const_v_mV_min(self):
        return self.phase_min(self.const_v_start, self.chrg_end, 'voltage')

    def const_v_mV_max(self):
        return self.phase_max(self.const_v_start, self.chrg_end, 'voltage')

    def const_v_mV_avg(self):
        return self.phase_avg(self.const_v_start, self.chrg_end, 'voltage')

    def const_v_mA_min(self):
        return self.phase_min(self.const_v_start, self.chrg_end, 'current')

    def const_v_mA_max(self):
        return self.phase_max(self.const_v_start, self.chrg_end, 'current')

    def const_v_mA_avg(self):
        return self.phase_avg(self.const_v_start, self.chrg_end, 'current')

    # complete charge time
    def chrg_time(self):
        return self.prechrg_time() + self.const_i_time() + self.const_v_time()

    # discharge phase
    def dischrg_time(self):
        return self.phase_time(self.dischrg_start, self.dischrg_end)

    def dischrg_mV_min(self):
        return self.phase_min(self.dischrg_start, self.dischrg_end, 'voltage')

    def dischrg_mV_max(self):
        return self.phase_max(self.dischrg_start, self.dischrg_end, 'voltage')

    def dischrg_mV_avg(self):
        return self.phase_avg(self.dischrg_start, self.dischrg_end, 'voltage')

    def dischrg_mA_min(self):
        return self.phase_min(self.dischrg_start, self.dischrg_end, 'current')

    def dischrg_mA_max(self):
        return self.phase_max(self.dischrg_start, self.dischrg_end, 'current')

    def dischrg_mA_avg(self):
        return self.phase_avg(self.dischrg_start, self.dischrg_end, 'current')

    def clear_test_results(self):
        self.test_result_list = []
        self.prechrg_start = -1  # indecies for charge phase
        self.prechrg_end   = -1
        self.const_i_start = -1
        self.const_i_end   = -1
        self.const_v_start = -1
        self.chrg_end      = -1
        self.dischrg_start = -1
        self.dischrg_end   = -1

    def phase_time(self, start_idx, stop_idx):
        try:
            # ignore if phase not found
            if start_idx < 0 or stop_idx < 0:
                return 0

            t_start = self.test_result_list[start_idx]['time'][0]
            t_stop = self.test_result_list[stop_idx]['time'][0]
            return t_stop - t_start
        except (IndexError, KeyError):
            self.logger.error(traceback.format_exc())
            return None

    def phase_min(self, start_idx, stop_idx, stat=''):
        stats = self.phase_stat_list(start_idx, stop_idx, stat)
        return min(stats)

    def phase_max(self, start_idx, stop_idx, stat=''):
        stats = self.phase_stat_list(start_idx, stop_idx, stat)
        return max(stats)

    def phase_avg(self, start_idx, stop_idx, stat=''):
        stats = self.phase_stat_list(start_idx, stop_idx, stat)
        return int(sum(stats)/len(stats))

    def phase_stat_list(self, start_idx, stop_idx, stat=''):
        try:
            # ignore if phase not found
            if start_idx < 0 or stop_idx < 0:
                return [0]

            # get stat list for phase
            test_results = self.test_result_list[start_idx:stop_idx]
            stats = [test_result[stat][0] for test_result in test_results]

            return stats
        except (IndexError, KeyError, ValueError):
            test.logger.error(traceback.format_exc())
            return [0]


    # file operations
    def log_to_TestResult(self,fname):
        # clear test results
        self.clear_test_results()

        # check for valid file name
        if len(fname) < 5:
            self.logger.warning(
                'Filename not long valid, please choose another file'
            )
            return None

        # read and process log file
        try:
            # current differential for end of constant current
            num_i_samples = 5
            prev_currents = deque([],num_i_samples)

            with open(fname) as f:
                i = 0
                for line in f.readlines():

                    # skip line if not status
                    split_line = line.split(', ')
                    if len(split_line) != 5:
                        continue

                    # parse status line
                    sample = self.parse_status_line(split_line)

                    # start of precharge
                    if (sample['voltage'][0] < PRECHRG_END_VFB_THRESH_mV
                        and sample['current'][0] > 0
                        and self.prechrg_start < 0
                    ):
                        self.prechrg_start = i
                        msg = 'precharge start idx: {}'\
                            .format(self.prechrg_start)
                        self.logger.debug(msg)


                    # precharge to constant current
                    if (sample['voltage'][0] >= PRECHRG_END_VFB_THRESH_mV
                        and sample['current'][0] > 0
                        and self.prechrg_end
                        and self.const_i_start < 0
                    ):
                        self.prechrg_end = i - 1
                        self.const_i_start = i
                        msg = 'constant current start idx: {}'\
                            .format(self.const_i_start)
                        self.logger.debug(msg)

                    # constant i to constant v
                    # end of constant current when current decreasing
                    # debounced with rolling samples
                    prev_currents.append(sample['current'])
                    di_dt = [
                        prev_currents[n][0]-prev_currents[n-1][0]
                        for n
                        in range(1,len(prev_currents))]

                    if (
                        all(j < 0 for j in di_dt)
                        and self.const_i_end < 0
                        and self.const_v_start < 0
                    ):
                        self.const_i_end = i - num_i_samples - 1
                        self.const_v_start = i - num_i_samples
                        msg = 'constant voltage start idx: {}'\
                            .format(self.const_v_start)
                        self.logger.debug(msg)

                    # end of charge
                    if (
                        sample['capacity_native'][0] == '0xFFFF'
                        and self.chrg_end < 0
                    ):
                        self.chrg_end = i
                        msg = 'charge complete idx: {}'.format(self.chrg_end)
                        self.logger.debug(msg)

                    # start of discharge
                    if (
                        sample['current'][0] <= DISCHRG_I_THRESH_mA
                        and self.dischrg_start < 0
                    ):
                        self.dischrg_start = i
                        msg = 'discharge start idx: {}'.format(self.chrg_end)
                        self.logger.debug(msg)

                    # test result index
                    i += 1

                    # add to results list
                    self.test_result_list.append(sample)

            # end of discharge
            self.dischrg_end = i-1      

        except FileNotFoundError as e:
            self.logger.warning('File not found, please choose another file')


    def TestResult_to_csv(self,fname):
        # column headers
        lines = []
        header = []

        # stat header
        line = self.csv_stats_header()
        lines.append(line)

        # summary lines
        stats = self.get_all_stats()

        line = self.csv_stats_line('prechrg')
        lines.append(line)

        line = self.csv_stats_line('const_i')
        lines.append(line)

        line = self.csv_stats_line('const_v')
        lines.append(line)

        line = self.csv_stats_line('chrg')
        lines.append(line)

        line = self.csv_stats_line('dischrg')
        lines.append(line)

        lines.append('\n')

        # results header
        line = self.csv_results_header()
        lines.append(line)

        # result lines
        for test_result in self.test_result_list:
            lines.append(self.csv_results_line(test_result))

        # write to csv
        with open(fname,'w') as f:
            f.writelines(lines)

    def csv_stats_header(self):
        line  = 'Phase,'
        line += 'Duration (min),'
        line += 'Imin (mA),'
        line += 'Imax (mA),'
        line += 'Iavg (mA),'
        line += 'Vmin (mV),'
        line += 'Vmax (mV),'
        line += 'Vavg (mV)\n'
        return line

    def csv_stats_line(self, phase=''):
        # check for valid phase name
        phases = {'prechrg', 'const_v', 'const_i', 'chrg', 'dischrg'}
        if phase not in phases:
            self.logger.error('Invalid phase name: ' + phase)

        # stats based on phase name
        if phase != 'chrg':
            measurement_names = ['time', 'mA', 'mV']
        else:
            measurement_names = ['time']

        # build stat line

        stats = self.get_all_stats()
        try:
            line = '{} phase,'.format(phase)
            # loop through each measurment type
            for measurement_name in measurement_names:
                if measurement_name == 'time':
                    key = '{}_time'.format(phase)
                    line += '{},'.format(stats[key])
                # each stat for non time measurements    
                else:
                    for stat_type in ['min', 'max', 'avg']:
                        key = '{}_{}_{}'.format(
                            phase,
                            measurement_name,
                            stat_type)
                        line += '{},'.format(stats[key])
            line += '\n'
            return line
        except (KeyError, ValueError):
            self.logger.error(traceback.format_exc())
            self.logger.error('Unable to get stat')
            return ''

    def csv_results_header(self):
        line  = 'time (min),'
        line += 'temp (C),'
        line += 'voltage (mV),'
        line += 'current (mA),'
        line += 'capacity (mAh),'
        line += 'capacity (%),'
        line += 'capacity (raw),'
        line += 'state\n'
        return line

    def csv_results_line(self,test_result):
        measurement_names = ['time','temp','voltage','current','capacity_mAh',
            'capacity_percent','capacity_native']

        # result lines
        line = ''
        for measurement_name in measurement_names:
            line += '{},'.format(test_result[measurement_name][0])
        line += '\n'
        self.logger.debug(line)

        return line

    # sample test result
    # '25 min - 36C, 14993mV, 1060mA, 799mAh, 22% (0x3960) STATE_CHARGING'
    def parse_status_line(self,line):
        test_result = {}
        
        time_and_temp = line[0].split(' - ')
        test_result['time'] = (int(time_and_temp[0][:-4]),)
        test_result['temp'] = (int(time_and_temp[1][:-1]),)
        test_result['voltage'] = (int(line[1][:-2]),)
        test_result['current'] = (int(line[2][:-2]),)
        test_result['capacity_mAh'] = (int(line[3][:-3]),)
        status = line[4].split(' ')          
        test_result['capacity_percent'] = (int(status[0][:-1]),)
        test_result['capacity_native'] = (status[1][1:-1],)
        test_result['status'] = (status[2],)   
        
        self.logger.debug('parsing status line: {}'.format(test_result))
        
        return test_result    

        
# main for testing     
if __name__ =='__main__':
    # build file names
    fname = sys.argv[1]
    fname_in = fname
    fname_out = os.path.splitext(fname)[0] + '.csv'

    # remove old debug log if exists
    logger_name = 'TestResult'
    try:
        fname = logger_name + '.log'
        os.remove(fname)
    except OSError as e:    
        if e.errno != errno.ENOENT: # ignore file doesnt exist
            test.logger.error(traceback.format_exc())
            sys.exit()

    # new test results from serial log file
    test = TestResult(fname = fname_in, logger_name = logger_name)
    test.logger.debug('TestResult CSV import test\n')

    # export test results to csv
    test.TestResult_to_csv(fname_out)

    # calculate test results
    test.logger.info('TestResult statistics:')
    test.logger.info('Precharge phase:')
    test.logger.info('Duration: {} min'.format(test.prechrg_time()))
    test.logger.info('Voltage min: {} mV'.format(test.prechrg_mV_min()))
    test.logger.info('Voltage max: {} mV'.format(test.prechrg_mV_max()))
    test.logger.info('Voltage max: {} mV'.format(test.prechrg_mV_avg()))
    test.logger.info('Current min: {} mA'.format(test.prechrg_mA_min()))
    test.logger.info('Current max: {} mA'.format(test.prechrg_mA_max()))
    test.logger.info('Current max: {} mA\n'.format(test.prechrg_mA_avg()))

    test.logger.info('Constant current phase:')
    test.logger.info('Duration: {} min'.format(test.const_i_time()))
    test.logger.info('Voltage min: {} mV'.format(test.const_i_mV_min()))
    test.logger.info('Voltage max: {} mV'.format(test.const_i_mV_max()))
    test.logger.info('Voltage avg: {} mV'.format(test.const_i_mV_avg()))
    test.logger.info('Current min: {} mA'.format(test.const_i_mA_min()))
    test.logger.info('Current max: {} mA'.format(test.const_i_mA_max()))
    test.logger.info('Current avg: {} mA\n'.format(test.const_i_mA_avg()))

    test.logger.info('Constant voltage phase:')
    test.logger.info('Duration: {} min'.format(test.const_v_time()))
    test.logger.info('Voltage min: {} mV'.format(test.const_v_mV_min()))
    test.logger.info('Voltage max: {} mV'.format(test.const_v_mV_max()))
    test.logger.info('Voltage max: {} mV'.format(test.const_v_mV_avg()))
    test.logger.info('Current min: {} mA'.format(test.const_v_mA_min()))
    test.logger.info('Current max: {} mA'.format(test.const_v_mA_max()))
    test.logger.info('Current max: {} mA\n'.format(test.const_v_mA_avg()))

    test.logger.info('Discharge phase:')
    test.logger.info('Duration: {} min'.format(test.dischrg_time()))
    test.logger.info('Duration: {} min'.format(test.dischrg_time()))
    test.logger.info('Voltage min: {} mV'.format(test.dischrg_mV_min()))
    test.logger.info('Voltage max: {} mV'.format(test.dischrg_mV_max()))
    test.logger.info('Voltage max: {} mV'.format(test.dischrg_mV_avg()))
    test.logger.info('Current min: {} mA'.format(test.dischrg_mA_min()))
    test.logger.info('Current max: {} mA'.format(test.dischrg_mA_max()))
    test.logger.info('Current max: {} mA\n'.format(test.dischrg_mA_avg()))