# standard library
from enum import Enum, auto
from datetime import datetime, timedelta
import time
# external packages

# internal packages
from source.TestBoxIF.I2C import I2CError, I2CReadError, I2CWriteError
from source.TestBoxIF.TestBoxHalf import TestBoxHalf
from source.BatTest.TestLog import TestLog
from source.BatTest.TestLog import result_str

# test settings
test_log = None
charge_setpoint = None
charge_test_level = None

test_time = 0
test_pass = False
done = False

class FSM(object):
    """docstring for FSM"""
    def __init__(
        self,
        test_box_half: TestBoxHalf = None,
        box_id: str = ''
    ):

        self._test_box_half = test_box_half
        global test_log
        self._test_log = test_log 

        # state machine
        self._state = InitialState(self._test_box_half)

        # initialize results log
        self._start_datetime = 0

        # initialize control variables
        self._quickcharge = False
        self._flag = None

    # API
    @property
    def state_name(self):
        return self._state.__str__()

    @property
    def test_time(self):
        return str(datetime.now() - self._start_datetime).split('.')[0]


    @property
    def test_pass(self):
        global test_pass
        return test_pass

    @property
    def done(self):
        global done
        return done

    def start(
        self, 
        charge_sp: int,
        quickcharge: bool = False,
        short_test: bool = False,
        resume_test: bool = False
    ):
        global test_log
        global charge_setpoint
        global charge_test_level

        self._start_datetime = datetime.now()

        charge_setpoint = charge_sp

        if quickcharge:
            charge_setpoint = charge_sp
            self._flag = Flags.START_QUICKCHARGE
        else:
            if short_test:
                charge_test_level = 10.1
                self._flag = Flags.START_SHORT_TEST
            elif resume_test:
                charge_test_level = 100
                self._flag  = Flags.RESUME_TEST
            else:
                charge_test_level = 100
                self._flag = Flags.START_TEST

    def stop(self):
        self._flag = Flags.STOP

    def process(self):
        self._state.do()
        self._state = self._state.next(self._flag)
        self._flag = None

class States(Enum):
    ERROR = 'sERROR'
    INITIAL = 'sINITIAL'
    IDLE = 'sIDLE'
    PRECHARGE = 'sPRECHARGE'
    NO_BATTERY = 'sNO_BATTERY'
    QUICKCHARGE = 'sQUICKCHARGE'
    QUICKDISCHARGE = 'sQUICKDISCHARGE'
    PRETEST = 'sPRETEST'
    CHARGE_TEST = 'sCHARGE_TEST'
    WAIT = 'sWAIT'
    DISCHARGE_TEST = 'sDISCHARGE_TEST'
    POSTTEST = 'sPOSTTEST'

class Flags(Enum):
    START_TEST = 'start_test'
    START_SHORT_TEST = 'start_short_test'
    START_QUICKCHARGE = 'start_quickcharge'
    RESUME_TEST = 'resume_test'
    STOP = 'stop'
    CLEAR = 'clear'

# Parent objects
class State(object):

    def __init__(
        self,
        test_box_half: TestBoxHalf = None,
    ):
        self._test_box_half = test_box_half
        self._start_time = time.time()
        self._elapsed_time_s = 0
        self._last_read_time = 0

    timeout_time_s = 10
    name = 'state'

    def __str__(self):

        return f'{self.name}'

    def __repr__(self):
        return self.__str__()

    @property
    def state_time_ms(self):
        return self._elapsed_time_ms

    @property
    def result(self):
        return None    

    def do(self):
        self._elapsed_time_s = time.time() - self._start_time
        # print(self.name)

    def next(self, flag = None):
        return self

class LogState(State):

    def do(self):
        global test_log
        # self._test_box_half.gas_gauge.control_init()
        try:
            gas_gauge_data = self._test_box_half.gas_gauge.get_all()

            # result_datetime = gas_gauge_data['bat_timestamp']
            # dt = result_datetime - self._start_time
            # self._elapsed_time = dt.seconds * 1000 + dt.microseconds / 1000
            # gas_gauge_data['bat_timestamp'] = self._elapsed_time

            test_log.add_result(gas_gauge_data)
            self._last_read_time = time.time()
        except Exception as e:
            raise e
        # print(result_str(**gas_gauge_data))

    def next(self):
        pass

# Implementations
class ErrorState(State):
    name = States.ERROR.value
    def __init__(
        self,
        test_box_half: TestBoxHalf = None,
        test_log: TestLog = None,
        message = None
    ):
        super().__init__(test_box_half)
        print(message)    

    def next(self, flag = None):
        if flag == Flags.CLEAR:
            print('ERROR -> IDLE')
            return IdleState(self._test_box_half)

        return self


class InitialState(State):
    name = States.INITIAL.value
    def do(self):
        pass

    def next(self, flag = None):
        # print('FSM Start')
        return IdleState(self._test_box_half)

class IdleState(State):
    name = States.IDLE.value
    def __init__(self, test_box_half: TestBoxHalf = None):
        super().__init__(test_box_half)
        self._test_box_half.gpio.charge_enable = False
        self._test_box_half.gpio.discharge_enable = False

    def do(self):
        # check for drained battery
        try:
            gas_gauge_config = hex(self._test_box_half.gas_gauge.config_reg)
            if gas_gauge_config == '0x3c':
                self._test_box_half.gas_gauge.control_init()
                self._test_box_half.gas_gauge.charge_init()
        except:
            pass

    def next(self, flag = None):
        # print(self._test_box_half)
        if (flag == Flags.START_TEST) or (flag == Flags.START_SHORT_TEST):
            self.teardown()
            print('IDLE -> PRETEST')
            return PretestState(self._test_box_half)
            
        elif flag == Flags.START_QUICKCHARGE:
            global charge_setpoint
            self.teardown()

            if self._test_box_half.gas_gauge.charge_level < charge_setpoint:
                print('IDLE -> QUICKCHARGE')
                return QuickchargeState(self._test_box_half)

            else:
                print('IDLE -> QUICKDISCHARGE')
                return QuickdischargeState(self._test_box_half)

        elif flag == Flags.RESUME_TEST:
            self.teardown()
            print('IDLE -> CHARGE_TEST')
            return ChargeTestState(self._test_box_half)
        # default
        return self

    def teardown(self):
        global done
        global test_pass
        done = False
        test_pass = False
        self._test_box_half.gpio.led_done_enable = False
        self._test_box_half.gpio.led_error_enable = False
        self._test_box_half.gas_gauge.control_auto()


# class PrechargeState(State):
#     name = States.PRECHARGE.value
#     def __init__(
#         self,
#         test_box_half: TestBoxHalf = None,
#     ):
#         super().__init__(test_box_half)
#         self._retries = 3
#         self._test_box_half.gpio.charge_enable = True
#         self._test_box_half.gpio.led_run_enable = True
#         self._test_box_half.gas_gauge.control_init()

#     def do(self):
#         gas_gauge = self._test_box_half.gas_gauge.get_all()
#         # print(gas_gauge)

#     def next(self, flag = None):
#         try:
#             voltage_limit = self._test_box_half.gas_gauge.voltage_mV > 10000
#         except TypeError:
#             print('GAS GAUGE COMM ERROR')
#             self._test_box_half.gpio.discharge_enable = False
#             self._test_box_half.gpio.led_run_enable = False
#             return IdleState(self._test_box_half)

#         if self._retries == 0:
#             if flag == Flags.STOP:
#                 print('PRECHARGE stopped')
#                 self._test_box_half.gpio.discharge_enable = False
#                 self._test_box_half.gpio.led_run_enable = False
#             elif voltage_limit:
#                 self._test_box_half.gpio.charge_enable = False
#                 print('PRECHARGE -> CHARGE_TEST')
#                 return ChargeTestState(self._test_box_half)
#             else:
#                 print('PRECHARGE -> ERROR')
#                 self._test_box_half.gpio.charge_enable = False
#                 self._test_box_half.gpio.led_run_enable = False
#                 return ErrorState(self._test_box_half,'battery not found')
#         else:
#             self._retries -= 1
#             return self


class PretestState(State):
    name = States.PRETEST.value
    def __init__(
        self,
        test_box_half: TestBoxHalf = None,
    ):
        super().__init__(test_box_half)
        self._test_box_half.gas_gauge.control_auto()
        self._test_box_half.gpio.discharge_enable = True
        self._test_box_half.gpio.led_run_enable = True    

    def do(self):
        # self._test_box_half.gas_gauge.control_init()
        try:
            gas_gauge = self._test_box_half.gas_gauge.get_all()
            self._last_read_time = time.time()
        except I2CError:
            pass
            # self._retries += 1
            # print(self._retries)

        # print(gas_gauge)

    def next(self, flag = None):
        try:
            gas_gauge_config = self._test_box_half.gas_gauge.config_reg
            voltage = self._test_box_half.gas_gauge.voltage_mV
            voltage_lim = voltage < 5000
            self._last_read_time = time.time()
        except I2CError:
            print(f'GAS GAUGE COMM ERROR')
            gas_gauge_config = None
            voltage_lim = False
            # self._retries += 1
            # self._test_box_half.gpio.discharge_enable = False
            # self._test_box_half.gpio.led_run_enable = False
            # return IdleState(self._test_box_half)

        timeout = (time.time() - self._last_read_time) > self.timeout_time_s \
            and self._last_read_time > 0

        if flag == Flags.STOP or timeout:
            print('PRETEST stopped')
            self._test_box_half.gpio.discharge_enable = False
            self._test_box_half.gpio.led_run_enable = False
            return IdleState(self._test_box_half)
        elif gas_gauge_config == '0x3c' or voltage_lim:    
            print('PRETEST -> CHARGE_TEST')
            self._test_box_half.gpio.discharge_enable = False
            self._test_box_half.gas_gauge.control_auto()
            self._test_box_half.gas_gauge.charge_init()
            return ChargeTestState(self._test_box_half)
        return self

class ChargeTestState(LogState):
    name = States.CHARGE_TEST.value
    time_lim_h = 4
    def __init__(
        self,
        test_box_half: TestBoxHalf = None,
    ):
        super().__init__(test_box_half)
        self._test_box_half.gpio.charge_enable = True
        self._test_box_half.gpio.led_run_enable = True

        global test_log
        test_log = TestLog()

    def do(self):
        super().do()        

    def next(self, flag = None):
        global charge_test_level
        global test_log

        try:
            level_limit = self._test_box_half.gas_gauge.charge_level >= charge_test_level
            self._last_read_time = time.time()
            # current_limit = abs(self._test_box_half.gas_gauge.current_mA) < 25
        except I2CError:
            level_limit = False
            pass
            # return IdleState(self._test_box_half)

        timeout = (time.time() - self._last_read_time) > self.timeout_time_s\
            and self._last_read_time > 0

        if flag == Flags.STOP or timeout:
            self.teardown()
            print('CHARGE_TEST stopped')
            return IdleState(self._test_box_half)

        elif level_limit:
            self.teardown()
            print('CHARGE_TEST -> DISCHARGE_TEST')
            return DischargeTestState(self._test_box_half)

        elif self._elapsed_time_ms / (1000 * 60 * 60) > self.time_lim_h:
            self.teardown()
            self._test_box_half.gpio.led_error_enable = True
            print('CHARGE TEST TIMEOUT')
            return IdleState(self._test_box_half)

        return self

    def teardown(self):
        self._test_box_half.gpio.charge_enable = False
        self._test_box_half.gpio.led_run_enable = False

class WaitState(State):
    name = States.DISCHARGE_TEST.value

    def do(self):
        super().do()


class DischargeTestState(LogState):
    name = States.DISCHARGE_TEST.value
    time_lim_h = 1
    def __init__(
        self,
        test_box_half: TestBoxHalf = None,
    ):
        super().__init__(test_box_half)
        self._test_box_half.gpio.discharge_enable = True
        self._current_lim_debounce = 0

        global test_log
        self._state_start_time = time.time()

    def do(self):
        super().do()
        self._test_box_half.gpio.led_run_enable ^= 1  

    def next(self, flag = None):
        global test_log

        current_limit = False
        discharged = False
        try:
            # level_limit = self._test_box_half.gas_gauge.charge_level <= charge_setpoint
            if abs(self._test_box_half.gas_gauge.current_mA) < 25:
                self._current_lim_debounce += 1
            else:
                self._current_lim_debounce = 0
            current_limit = self._current_lim_debounce > 10

            discharged = self._test_box_half.gas_gauge.config_reg == 0x3C
            self._last_read_time = time.time()
        except I2CError:
            pass
            # self.teardown()
            # print('GAS GAUGE COMM ERROR')
            # return IdleState(self._test_box_half)

        state_time = (time.time() - self._state_start_time)/(60 * 60)

        timeout = (time.time() - self._last_read_time) > self.timeout_time_s\
            and self._last_read_time > 0

        if flag == Flags.STOP or timeout:
            self.teardown()
            print('DISCHARGE_TEST stopped')
            return IdleState(self._test_box_half)

        elif current_limit or discharged:
            self.teardown()
            print('DISCHARGE_TEST -> POSTTEST')
            return PostTestState(self._test_box_half)

        elif state_time > self.time_lim_h:
            self.teardown()
            print('DISCHARGE TEST TIMEOUT')
            return IdleState(self._test_box_half)

        return self

    def teardown(self):
        self._test_box_half.gpio.discharge_enable = False
        self._test_box_half.gpio.led_run_enable = False

class QuickchargeState(LogState):
    name = States.QUICKCHARGE.value
    def __init__(
        self,
        test_box_half: TestBoxHalf = None,
    ):
        super().__init__(test_box_half)
        self._test_box_half.gpio.charge_enable = True
        self._test_box_half.gpio.led_run_enable = True

    def next(self, flag = None):
        global charge_setpoint

        try:
            level_limit = self._test_box_half.gas_gauge.charge_level >= charge_setpoint
            self._last_read_time = time.time()
        except I2CError:
            level_limit = False
            # print('GAS GAUGE COMM ERROR')
            # self._test_box_half.gpio.charge_enable = False
            # self._test_box_half.gpio.led_run_enable = False
            # return IdleState(self._test_box_half)

        # current_limit = abs(self._test_box_half.gas_gauge.current_mA) < 25

        timeout = (time.time() - self._last_read_time) > self.timeout_time_s\
            and self._last_read_time > 0

        if flag == Flags.STOP or timeout:
            print('QUICKCHARGE stopped')
            self._test_box_half.gpio.charge_enable = False
            self._test_box_half.gpio.led_run_enable = False
            return IdleState(self._test_box_half)
        elif level_limit: # or current_limit:
            print('QUICKCHARGE done')
            self._test_box_half.gpio.charge_enable = False
            self._test_box_half.gpio.led_run_enable = False
            self._test_box_half.gpio.led_done_enable = True
            global done
            done = True
            return IdleState(self._test_box_half)

        return self


class QuickdischargeState(LogState):
    name = States.QUICKDISCHARGE.value
    def __init__(
        self,
        test_box_half: TestBoxHalf = None,
    ):
        super().__init__(test_box_half)
        # self._test_box_half.gas_gauge.control_init()
        self._test_box_half.gpio.discharge_enable = True

    def next(self, flag = None):
        global charge_setpoint

        self._test_box_half.gpio.led_run_enable ^= 1

        try:
            level_limit = self._test_box_half.gas_gauge.charge_level <= charge_setpoint
            # current_limit = abs(self._test_box_half.gas_gauge.current_mA) < 25
            discharged = self._test_box_half.gas_gauge.config_reg == 0x3C
            self._last_read_time = time.time()
        except I2CReadError:
            return self

        timeout = (time.time() - self._last_read_time) > self.timeout_time_s\
            and self._last_read_time > 0

        if flag == Flags.STOP or timeout:
            print('QUICKCHARGE stopped')
            self._test_box_half.gpio.discharge_enable = False
            self._test_box_half.gpio.led_run_enable = False
            return IdleState(self._test_box_half)
        elif level_limit or discharged:
            print('QUICKCHARGE done')
            self._test_box_half.gpio.discharge_enable = False
            self._test_box_half.gpio.led_run_enable = False
            self._test_box_half.gpio.led_done_enable = True
            global done
            done = True
            return IdleState(self._test_box_half)

        return self

class PostTestState(State):
    name = States.POSTTEST.value
    def __init__(
        self,
        test_box_half: TestBoxHalf = None,
    ):
        super().__init__(test_box_half)
        self._test_box_half.gas_gauge.control_init()
        self._test_box_half.gas_gauge.charge_init()
        self._test_box_half.gpio.charge_enable = True

        global test_log
        global test_pass
        test_pass = test_log.test_pass()

    def do(self):
        # gas_gauge = self._test_box_half.gas_gauge.get_all()
        # print(gas_gauge)
        global test_pass
        if test_pass:
            self._test_box_half.gpio.led_done_enable ^= 1
        else:
            self._test_box_half.gpio.led_error_enable ^= 1

    def next(self, flag = None):
        global charge_setpoint

        if flag == Flags.STOP:
            print('CHARGE_TEST stopped')
            self._test_box_half.gpio.charge_enable = False
            return IdleState(self._test_box_half)
        if self._test_box_half.gas_gauge.charge_level > charge_setpoint:
            print('TEST DONE')
            self._test_box_half.gas_gauge.control_init()
            self._test_box_half.gpio.charge_enable = False
            
            global test_pass
            if test_pass:
                self._test_box_half.gpio.led_done_enable = True
            else:
                self._test_box_half.gpio.led_error_enable = True

            return IdleState(self._test_box_half)
        return self

# class State(State):
#     name = States.PRECHARGE.value
