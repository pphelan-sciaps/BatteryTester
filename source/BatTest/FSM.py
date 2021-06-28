# standard library
import logging
from enum import Enum, auto
from datetime import datetime, timedelta
from time import sleep
# external packages

# internal packages
from source import Config
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

        self.logger = logging.getLogger('batman.BatTest.FSM.FSM')
        self.logger.info('FSM init')

        self._test_box_half = test_box_half
        global test_log
        self._test_log = test_log 

        # state machine
        self._state = IdleState(self._test_box_half)

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
        global charge_setpoint

        self._start_datetime = datetime.now()

        charge_setpoint = charge_sp

        if quickcharge:
            global charge_test_level
            charge_test_level = charge_sp
            self._flag = Flags.START_QUICKCHARGE
        else:
            if short_test:
                charge_test_level = 10.5
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
    IDLE = 'sIDLE'
    WAIT = 'sWAIT'
    NO_BATTERY = 'sNO_BATTERY'
    QUICKCHARGE = 'sQUICKCHARGE'
    QUICKDISCHARGE = 'sQUICKDISCHARGE'
    PRETEST = 'sPRETEST'
    CHARGE_TEST = 'sCHARGE_TEST'
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
    STATE_TIMEOUT_TD = timedelta.max
    READ_TIMEOUT_TD = timedelta(seconds=5)
    NAME = 'state'

    def __init__(
        self,
        test_box_half: TestBoxHalf = None,
    ):
        self.logger = logging.getLogger(f'batman.BatTest.FSM.{self.__class__.__name__}')

        self._test_box_half = test_box_half
        self._start_time = datetime.now()
        self._last_read_time = self._start_time

        self.logger.info(f'entered {self.__class__.__name__}')

    def __str__(self):
        return f'{self.NAME}'

    def __repr__(self):
        return self.__str__()

    @property
    def state_time_s(self):
        return self._elapsed_time

    @property
    def result(self):
        return None    

    # do state actions
    def do(self):
        self._elapsed_time = datetime.now() - self._start_time

    # get next state
    def next(self, flag):
        state_timeout = self._elapsed_time > self.STATE_TIMEOUT_TD

        if flag == Flags.STOP:
            self.logger.info('test stopped')
            self.teardown()
            return IdleState(self._test_box_half)
        elif state_timeout:
            self.logger.warning(f'test state timeout {self._elapsed_time}')
            self.teardown()
            self._test_box_half.gpio.led_error_enable = True
            return IdleState(self._test_box_half)    

    def teardown(self):
        self._test_box_half.gpio.charge_enable = False
        self._test_box_half.gpio.discharge_enable = False

class LogState(State):
    def __init__(self, test_box_half: TestBoxHalf = None):
        super().__init__(test_box_half)

    def do(self):
        super().do()
        global test_log
        # self._test_box_half.gas_gauge.control_init()
        try:
            gas_gauge_data = self._test_box_half.gas_gauge.get_all()
            result_datetime = gas_gauge_data['bat_timestamp']
            td = result_datetime - self._start_time
            gas_gauge_data['bat_timestamp'] = td
            gas_gauge_data['bat_timestamp_ms'] = td.seconds * 1000 + td.microseconds / 1000
            if test_log:
                test_log.add_result(gas_gauge_data)
            self._last_read_time = datetime.now()
        except I2CError as e:
            self.logger.exception(e)
        except Exception as e:
            self.logger.exception(e)
            raise e

# Implementations
# class ErrorState(State):
#     name = States.ERROR.value
#     def __init__(
#         self,
#         test_box_half: TestBoxHalf = None,
#         test_log: TestLog = None,
#         message = None
#     ):
#         super().__init__(test_box_half)
#         print(message)    

#     def next(self, flag = None):
#         if flag == Flags.CLEAR:
#             return IdleState(self._test_box_half)

        return self

class IdleState(State):
    NAME = States.IDLE.value
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
        except I2CError:
            pass

    def next(self, flag):
        if (flag == Flags.START_TEST) or (flag == Flags.START_SHORT_TEST):
            self.logger.info('starting test')
            self.teardown()
            return PretestState(self._test_box_half)
            
        elif flag == Flags.START_QUICKCHARGE:
            self.logger.info('starting quick(dis)charge')

            global test_log
            test_log = None

            global charge_setpoint
            self.teardown()

            if self._test_box_half.gas_gauge.charge_level < charge_setpoint:
                return ChargeTestState(self._test_box_half,quickcharge=True)
            else:
                return DischargeTestState(self._test_box_half,quickcharge=True)

        elif flag == Flags.RESUME_TEST:
            self.logger.info('resuming test')
            self.teardown()
            return ChargeTestState(self._test_box_half,quickcharge=True)
        # stay in state
        return self

    def teardown(self):
        global done
        global test_pass
        done = False
        test_pass = False
        self._test_box_half.gpio.led_done_enable = False
        self._test_box_half.gpio.led_error_enable = False
        self._test_box_half.gas_gauge.control_auto()

class WaitState(State):
    NAME = States.WAIT.value
    STATE_TIMEOUT_TD = timedelta(seconds=10)

    def __init__(
        self,
        test_box_half: TestBoxHalf = None,
        next_state: State = IdleState,
        charge_en = False,
        discharge_en = False
    ):
        super().__init__(test_box_half)
        self._next_state = next_state
        self._test_box_half.gpio.charge_enable = charge_en
        self._test_box_half.gpio.discharge_enable = discharge_en
    
    def next(self, flag):
        if self._elapsed_time > self.STATE_TIMEOUT_TD:
            self.logger.info('wait over')
            return self._next_state(self._test_box_half)

        default_next = super().next(flag)
        if default_next is not None:
            return default_next

        return self

class PretestState(State):
    STATE_TIMEOUT_TD = timedelta(hours=1)
    NAME = States.PRETEST.value
    DELAY = 3

    def __init__(
        self,
        test_box_half: TestBoxHalf = None,
    ):
        super().__init__(test_box_half)

        self._test_box_half.gas_gauge.control_auto()
        self._test_box_half.gpio.discharge_enable = True
        self._test_box_half.gpio.led_run_enable = True

        self._delay_count = 0   

    # def do(self):
    #     super().do()
    #     # self._test_box_half.gas_gauge.control_init()
    #     try:
    #         gas_gauge = self._test_box_half.gas_gauge.get_all()
    #         self._last_read_time = time.time()
    #     except I2CError:
    #         pass
    def do(self):
        super().do()
        if self._delay_count >= self.DELAY:
            self._test_box_half.gpio.led_run_enable ^= 1
            self._delay_count = 0;
        else:
            self._delay_count += 1

        

    def next(self, flag):
        # read from gas gauge
        try:
            gas_gauge_config = self._test_box_half.gas_gauge.config_reg
            voltage = self._test_box_half.gas_gauge.voltage_mV
            voltage_lim = voltage < 5000
            read_timeout = False
            self._last_read_time = datetime.now()
        except I2CError:
            gas_gauge_config = None
            voltage_lim = False
            delta_t = datetime.now() - self._last_read_time
            read_timeout = delta_t > self.READ_TIMEOUT_TD
    
        
        default_next = super().next(flag)

        if default_next is not None:
            return default_next
        elif read_timeout:
            self.logger.warning('i2c read timeout')
            super().teardown()
            return IdleState(self._test_box_half)
        elif gas_gauge_config == '0x3c' or voltage_lim:
            self.logger.info('battery discharged')    
            self._test_box_half.gpio.discharge_enable = False
            self._test_box_half.gpio.charge_enable = True
            self._test_box_half.gas_gauge.control_auto()
            self._test_box_half.gas_gauge.charge_init()
            return WaitState(
                self._test_box_half,
                ChargeTestState,
                charge_en = True)

        return self

class ChargeTestState(LogState):
    STATE_TIMEOUT_TD = timedelta(hours=4.5)
    NAME = States.CHARGE_TEST.value

    def __init__(
        self,
        test_box_half: TestBoxHalf = None,
        quickcharge = False
    ):
        super().__init__(test_box_half)
        self._test_box_half.gpio.charge_enable = True
        self._test_box_half.gpio.led_run_enable = True
        self._quickcharge = quickcharge

        if not quickcharge:
            global test_log
            test_log = TestLog()


    def do(self):
        super().do()        

    def next(self, flag):
        global charge_test_level

        try:
            level_limit = self._test_box_half.gas_gauge.charge_level >= charge_test_level
            read_timeout = False
            self._last_read_time = datetime.now()
            # current_limit = abs(self._test_box_half.gas_gauge.current_mA) < 25
        except I2CError:
            level_limit = False
            delta_t = datetime.now() - self._last_read_time
            read_timeout = delta_t > STATE_TIMEOUT_TD

        default_next = super().next(flag)
        if default_next is not None:
            return default_next
        elif read_timeout:
            self.logger.warning('test timeout')
            self.teardown()
            return IdleState(self._test_box_half)
        elif level_limit:
            if self._quickcharge:
                self.logger.info('quickcharge done')
                self.teardown()
                return IdleState(self._test_box_half)
            else:
                self.logger.info('wait before discharge test')
                self.teardown()
                sleep(1)
                return WaitState(
                    self._test_box_half,
                    DischargeTestState,
                    discharge_en = True)

        return self

    def teardown(self):
        self._test_box_half.gpio.charge_enable = False
        self._test_box_half.gpio.led_run_enable = False

class DischargeTestState(LogState):
    STATE_TIMEOUT_TD = timedelta(hours=1)
    NAME = States.DISCHARGE_TEST.value

    def __init__(
        self,
        test_box_half: TestBoxHalf = None,
        quickcharge = False
    ):
        super().__init__(test_box_half)
        self._test_box_half.gpio.discharge_enable = True
        self._current_lim_debounce = 0
        self._quickcharge = quickcharge
        self._state_start_time = datetime.now()

    def do(self):
        super().do()
        self._test_box_half.gpio.led_run_enable ^= 1  

    def next(self, flag):
        global charge_test_level

        try:
            # idle current (fully discharged)
            if abs(self._test_box_half.gas_gauge.current_mA) < 25:
                self._current_lim_debounce += 1
            else:
                self._current_lim_debounce = 0
            current_limit = self._current_lim_debounce > 10

            if self._quickcharge:
                level_limit = self._test_box_half.gas_gauge.charge_level <= charge_test_level
            else:
                level_limit = False

            discharged = self._test_box_half.gas_gauge.config_reg == 0x3C
            read_timeout = False

            self._last_read_time = datetime.now()
        except I2CError:
            self.logger.warning(I2CError)
            self._current_lim_debounce = 0
            current_limit = False
            level_limit = False
            discharged = False
            delta_t = datetime.now() - self._last_read_time
            read_timeout = delta_t > self.READ_TIMEOUT_TD

        default_next = super().next(flag)
        if default_next is not None:
            return default_next
        elif read_timeout:
            self.logger.warning('test timeout')
            self.teardown()
            return IdleState(self._test_box_half)
        elif current_limit or discharged or level_limit:
            if self._quickcharge:
                self.logger.info('quickcharge complete')
                self.teardown()
                return IdleState(self._test_box_half)
            else:
                self.logger.info('battery discharged')
                self.teardown()
                sleep(1)
                return WaitState(
                    self._test_box_half,
                    PostTestState,
                    charge_en = True)

        return self

    def teardown(self):
        self._test_box_half.gpio.discharge_enable = False
        self._test_box_half.gpio.led_run_enable = False

# class QuickchargeState(LogState):
#     STATE_TIMEOUT_TD = 4 * 60 * 60    # 4 hours
#     NAME = States.CHARGE_TEST.value

#     def __init__(
#         self,
#         test_box_half: TestBoxHalf = None,
#     ):
#         super().__init__(test_box_half)
#         self._test_box_half.gpio.charge_enable = True
#         self._test_box_half.gpio.led_run_enable = True

#     def next(self, flag = None):
#         global charge_setpoint

#         try:
#             level_limit = self._test_box_half.gas_gauge.charge_level >= charge_setpoint
#             self._last_read_time = time.time()
#         except I2CError:
#             level_limit = False
#             # print('GAS GAUGE COMM ERROR')
#             # self._test_box_half.gpio.charge_enable = False
#             # self._test_box_half.gpio.led_run_enable = False
#             # return IdleState(self._test_box_half)

#         # current_limit = abs(self._test_box_half.gas_gauge.current_mA) < 25

#         timeout = (time.time() - self._last_read_time) > self.timeout_time_s\
#             and self._last_read_time > 0

#         if flag == Flags.STOP or timeout:
#             # print('QUICKCHARGE stopped')
#             self._test_box_half.gpio.charge_enable = False
#             self._test_box_half.gpio.led_run_enable = False
#             return IdleState(self._test_box_half)
#         elif level_limit: # or current_limit:
#             # print('QUICKCHARGE done')
#             self._test_box_half.gpio.charge_enable = False
#             self._test_box_half.gpio.led_run_enable = False
#             self._test_box_half.gpio.led_done_enable = True
#             global done
#             done = True
#             return IdleState(self._test_box_half)

#         return self

# class QuickdischargeState(LogState):
#     name = States.QUICKDISCHARGE.value
#     def __init__(
#         self,
#         test_box_half: TestBoxHalf = None,
#     ):
#         super().__init__(test_box_half)
#         # self._test_box_half.gas_gauge.control_init()
#         self._test_box_half.gpio.discharge_enable = True

#     def next(self, flag = None):
#         global charge_setpoint

#         self._test_box_half.gpio.led_run_enable ^= 1

#         try:
#             level_limit = self._test_box_half.gas_gauge.charge_level <= charge_setpoint
#             # current_limit = abs(self._test_box_half.gas_gauge.current_mA) < 25
#             discharged = self._test_box_half.gas_gauge.config_reg == 0x3C
#             self._last_read_time = time.time()
#         except I2CReadError:
#             return self

#         timeout = (time.time() - self._last_read_time) > self.timeout_time_s\
#             and self._last_read_time > 0

#         if flag == Flags.STOP or timeout:
#             # print('QUICKCHARGE stopped')
#             self._test_box_half.gpio.discharge_enable = False
#             self._test_box_half.gpio.led_run_enable = False
#             return IdleState(self._test_box_half)
#         elif level_limit or discharged:
#             # print('QUICKCHARGE done')
#             self._test_box_half.gpio.discharge_enable = False
#             self._test_box_half.gpio.led_run_enable = False
#             self._test_box_half.gpio.led_done_enable = True
#             global done
#             done = True
#             return IdleState(self._test_box_half)

#         return self

class PostTestState(State):
    STATE_TIMEOUT_TD = timedelta(hours=4.5)
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

    def next(self, flag):
        global charge_setpoint

        if flag == Flags.STOP:
            # print('CHARGE_TEST stopped')
            self._test_box_half.gpio.charge_enable = False
            return IdleState(self._test_box_half)
        if self._test_box_half.gas_gauge.charge_level > charge_setpoint:
            # print('TEST DONE')
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
