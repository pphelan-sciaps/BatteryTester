# Main class for battery test
# system utilities
import sys
import traceback
import configparser

# package modules
import PackageLogger
from TestResult import TestResult

# version info


if __name__ == '__main__':
	# test limits
	config = configparser.ConfigParser()
	config.read('BatteryTest.ini')

	# logger
	logger_name = 'BatteryTest'

	# build file names
	fname = sys.argv[1]
    fname_in = fname
    fname_out = os.path.splitext(fname)[0] + '.csv'

	# build test results from file
	test = TestResult(fname=fname_in, logger_name=logger_name)

	# export test results to csv
	test.TestResult_to_csv(fname_out)

	# compare with test limits
	errors = 0

	limits = config['test_limits_prechrg']
	if test.prechrg_mV_min() < limits[min_v_lim_mV]
