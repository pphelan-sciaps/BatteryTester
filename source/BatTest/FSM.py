# standard library
from enum import Enum, auto

# external packages

# internal packages
from source.TestBoxIF.TestBoxHalf import TestBoxHalf
from source.BatTest.TestLog import TestLog
from source.BatTest.TestLog import result_str

# test settings
test_log = None
charge_setpoint = None
charge_test_level = None

done = False

class FSM(object):
    """docstring for FSM"""
    def __init__(
        self,
        test_box_half: TestBoxHalf = None,
    ):

        self._test_box_half = test_box_half
        global test_log
        self._test_log = test_log 

        # state machine
        self._state = InitialState(self._test_box_half)

        # initialize results log

        # initialize control variables
        self._quickcharge = False
        self._flag = None

    # API
    @property
    def state_name(self):
        return self._state.__str__()

    @property
    def done(self):
        global done
        return done

    def start(
        self, 
        charge_sp: int,
        quickcharge: bool,
        short_test: bool = False
    ):
        global test_log
        global charge_setpoint
        global charge_test_level

        charge_setpoint = charge_sp

        if quickcharge:
            charge_setpoint = charge_sp
            self._flag = Flags.START_QUICKCHARGE
        else:
            if short_test:
                charge_test_level = 10.1
                self._flag = Flags.START_SHORT_TEST
            else:
                charge_test_level = 100
                self._flag = Flags.START_TEST
            test_log = TestLog()

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
    DISCHARGE_TEST = 'sDISCHARGE_TEST'
    POSTTEST = 'sPOSTTEST'

class Flags(Enum):
    START_TEST = 'start_test'
    START_SHORT_TEST = 'start_short_test'
    START_QUICKCHARGE = 'start_quickcharge'
    STOP = 'stop'
    CLEAR = 'clear'

# Parent objects
class State(object):

    def __init__(
        self,
        test_box_half: TestBoxHalf = None,
    ):
        self._test_box_half = test_box_half

    name = 'state'
    def __str__(self):

        return f'{self.name}'

    def __repr__(self):
        return self.__str__()

    @property
    def result(self):
        return None    

    def do(self):
        pass
        # print(self.name)

    def next(self, flag = None):
        return self

class LogState(State):

    def do(self):
        global test_log
        # self._test_box_half.gas_gauge.control_init()
        gas_gauge_data = self._test_box_half.gas_gauge.get_all()
        try:
            test_log.add_result(gas_gauge_data)
        except:
            pass
        # print(result_str(**gas_gauge_data))

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
    def do(self):
        # print(self.name)
        # self._test_box_half.gas_gauge.control_init()
        pass

    def next(self, flag = None):
        # print(self._test_box_half)
        global done
        if (flag == Flags.START_TEST) or (flag == Flags.START_SHORT_TEST):
            done = False
            self._test_box_half.gpio.led_done_enable = False

            if self._test_box_half.gas_gauge.voltage_mV > 10000:
                print('IDLE -> PRETEST')
                return PretestState(self._test_box_half)
            else:
                print('IDLE -> PRECHARGE')
                return PrechargeState(self._test_box_half)
        elif flag == Flags.START_QUICKCHARGE:
            global charge_setpoint
            done = False
            self._test_box_half.gpio.led_done_enable = False
            
            if self._test_box_half.gas_gauge.charge_level < charge_setpoint:
                print('IDLE -> QUICKCHARGE')
                return QuickchargeState(self._test_box_half)
            else:
                print('IDLE -> QUICKDISCHARGE')
                return QuickdischargeState(self._test_box_half)
        # default
        return self


class PrechargeState(State):
    name = States.PRECHARGE.value
    def __init__(
        self,
        test_box_half: TestBoxHalf = None,
    ):
        super().__init__(test_box_half)
        self._retries = 3
        self._test_box_half.gpio.charge_enable = True
        self._test_box_half.gpio.led_run_enable = True
        self._test_box_half.gas_gauge.control_init()

    def do(self):
        gas_gauge = self._test_box_half.gas_gauge.get_all()
        # print(gas_gauge)

    def next(self, flag = None):
        try:
            voltage_limit = self._test_box_half.gas_gauge.voltage_mV > 10000
        except TypeError:
            print('GAS GAUGE COMM ERROR')
            self._test_box_half.gpio.discharge_enable = False
            self._test_box_half.gpio.led_run_enable = False
            return IdleState(self._test_box_half)

        if self._retries == 0:
            if flag == Flags.STOP:
                print('PRECHARGE stopped')
                self._test_box_half.gpio.discharge_enable = False
                self._test_box_half.gpio.led_run_enable = False
            elif voltage_limit:
                self._test_box_half.gpio.charge_enable = False
                print('PRECHARGE -> CHARGE_TEST')
                return ChargeTestState(self._test_box_half)
            else:
                self._test_box_half.gpio.charge_enable = False
                self._test_box_half.gpio.led_run_enable = False
                return ErrorState(self._test_box_half,'battery not found')
        else:
            self._retries -= 1
            return self


class PretestState(State):
    name = States.PRETEST.value
    def __init__(
        self,
        test_box_half: TestBoxHalf = None,
    ):
        super().__init__(test_box_half)
        self._test_box_half.gpio.discharge_enable = True
        self._test_box_half.gpio.led_run_enable = True
    

    def do(self):
        # self._test_box_half.gas_gauge.control_init()
        gas_gauge = self._test_box_half.gas_gauge.get_all()
        # print(gas_gauge)

    def next(self, flag = None):
        try:
            voltage_limit = self._test_box_half.gas_gauge.voltage_mV < 10000
        except TypeError:
            print('GAS GAUGE COMM ERROR')
            self._test_box_half.gpio.discharge_enable = False
            self._test_box_half.gpio.led_run_enable = False
            return IdleState(self._test_box_half)

        if flag == Flags.STOP:
            print('PRETEST stopped')
            self._test_box_half.gpio.discharge_enable = False
            self._test_box_half.gpio.led_run_enable = False
            return IdleState(self._test_box_half)
        elif voltage_limit:
            print('PRETEST -> CHARGE_TEST')
            self._test_box_half.gpio.discharge_enable = False
            return ChargeTestState(self._test_box_half)
        return self

class ChargeTestState(LogState):
    name = States.CHARGE_TEST.value
    def __init__(
        self,
        test_box_half: TestBoxHalf = None,
    ):
        super().__init__(test_box_half)
        self._test_box_half.gas_gauge.control_init()
        self._test_box_half.gas_gauge.charge_init()
        self._test_box_half.gpio.charge_enable = True
        self._test_box_half.gpio.led_run_enable = True

    def do(self):
        super().do()        

    def next(self, flag = None):
        global charge_test_level

        try:
            level_limit = self._test_box_half.gas_gauge.charge_level >= charge_test_level
            # current_limit = abs(self._test_box_half.gas_gauge.current_mA) < 25
        except TypeError:
            print('GAS GAUGE COMM ERROR')
            self._test_box_half.gpio.charge_enable = False
            self._test_box_half.gpio.led_run_enable = False
            return IdleState(self._test_box_half)

        if flag == Flags.STOP:
            print('CHARGE_TEST stopped')
            self._test_box_half.gpio.charge_enable = False
            self._test_box_half.gpio.led_run_enable = False
            return IdleState(self._test_box_half)
        if level_limit:
            print('CHARGE_TEST -> DISCHARGE_TEST')
            self._test_box_half.gpio.charge_enable = False
            self._test_box_half.gpio.led_run_enable = False
            return DischargeTestState(self._test_box_half)
        return self

class DischargeTestState(LogState):
    name = States.DISCHARGE_TEST.value
    def __init__(
        self,
        test_box_half: TestBoxHalf = None,
    ):
        super().__init__(test_box_half)
        self._test_box_half.gpio.discharge_enable = True

    def do(self):
        super().do()
        self._test_box_half.gpio.led_run_enable ^= 1  

    def next(self, flag = None):
        try:
            level_limit = self._test_box_half.gas_gauge.charge_level <= charge_setpoint
            current_limit = abs(self._test_box_half.gas_gauge.current_mA) < 25
            discharged = self._test_box_half.gas_gauge.config_reg == 0x3C
        except TypeError:
            print('GAS GAUGE COMM ERROR')
            self._test_box_half.gpio.discharge_enable = False
            self._test_box_half.gpio.led_run_enable = False
            return IdleState(self._test_box_half)

        if flag == Flags.STOP:
            print('DISCHARGE_TEST stopped')
            self._test_box_half.gpio.dicharge_enable = False
            self._test_box_half.gpio.led_run_enable = False
            return IdleState(self._test_box_half)
        elif level_limit or current_limit or discharged:
            print('DISCHARGE_TEST -> POSTTEST')
            self._test_box_half.gpio.discharge_enable = False
            self._test_box_half.gpio.led_run_enable = False
            return PostTestState(self._test_box_half)
        return self

class QuickchargeState(LogState):
    name = States.QUICKCHARGE.value
    def __init__(
        self,
        test_box_half: TestBoxHalf = None,
    ):
        super().__init__(test_box_half)
        self._test_box_half.gas_gauge.control_init()
        self._test_box_half.gpio.charge_enable = True
        self._test_box_half.gpio.led_run_enable = True

    def next(self, flag = None):
        global charge_setpoint

        try:
            level_limit = self._test_box_half.gas_gauge.charge_level >= charge_setpoint
        except TypeError:
            print('GAS GAUGE COMM ERROR')
            self._test_box_half.gpio.charge_enable = False
            self._test_box_half.gpio.led_run_enable = False
            return IdleState(self._test_box_half)

        # current_limit = abs(self._test_box_half.gas_gauge.current_mA) < 25

        if flag == Flags.STOP:
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

        level_limit = self._test_box_half.gas_gauge.charge_level <= charge_setpoint
        # current_limit = abs(self._test_box_half.gas_gauge.current_mA) < 25
        discharged = self._test_box_half.gas_gauge.config_reg == 0x3C

        if flag == Flags.STOP:
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
        self._test_box_half.gpio.charge_enable = True

    def do(self):
        gas_gauge = self._test_box_half.gas_gauge.get_all()
        # print(gas_gauge)

    def next(self, flag = None):
        global charge_setpoint

        if flag == Flags.STOP:
            print('CHARGE_TEST stopped')
            self._test_box_half.gpio.charge_enable = False
            return IdleState(self._test_box_half)
        if self._test_box_half.gas_gauge.charge_level > charge_setpoint:
            print('TEST DONE')
            self._test_box_half.gpio.charge_enable = False
            self._test_box_half.gpio.led_done_enable = True
            global done
            done = True
            return IdleState(self._test_box_half)
        return self

# class State(State):
#     name = States.PRECHARGE.value
