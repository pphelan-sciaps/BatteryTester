# standard library
from enum import Enum, auto

# external packages

# internal packages
from source.TestBoxIF.TestBoxHalf import TestBoxHalf
from source.BatTest.TestLog import TestLog

# globals

test_log = None
charge_setpoint = None

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
    def start(self, charge_sp: int, quickcharge: bool):
        global test_log
        test_log = TestLog()
        global charge_setpoint
        charge_setpoint = charge_sp
        if quickcharge:
            self._flag = Flags.START_QUICKCHARGE
        else:
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
    DISCHARGE_TEST = 'sDISCHARGE_TEST'
    POSTTEST = 'sPOSTTEST'

class Flags(Enum):
    START_TEST = 'start_test'
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
        return self.name

    def __repr__(self):
        return self.__str__

    @property
    def result(self):
        return None    

    def do(self):
        print(self.name)

    def next(self, flag = None):
        return self

class LogState(State):

    def do(self):
        global test_log
        self._test_box_half.gas_gauge.control_init()
        result = self._test_box_half.gas_gauge.get_all()
        test_log.new_result(
            voltage_mV   = result['voltage_mV'],
            current_mA   = result['current_mA'],
            charge_mAh   = result['charge_mAh'],
            charge_level = result['charge_level'],
            temp_C = result['temp_C']
        )
        print(test_log.last)

# Implementations
class ErrorState(State):
    def __init__(
        self,
        test_box_half: TestBoxHalf = None,
        test_log: TestLog = None,
        message = None
    ):
        super().__init__(test_box_half)
        print(message)

    name = States.ERROR

    def next(self, flag = None):
        if flag == Flags.CLEAR:
            print('ERROR -> IDLE')
            return IdleState(self._test_box_half)

        return self


class InitialState(State):
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
        if flag == Flags.START_TEST:
            if self._test_box_half.gas_gauge.voltage_mV > 10000:
                print('IDLE -> PRETEST')
                return PretestState(self._test_box_half)
            else:
                print('IDLE -> PRECHARGE')
                return PrechargeState(self._test_box_half)
        elif flag == Flags.START_QUICKCHARGE:
            global charge_setpoint
            if self._test_box_half.gas_gauge.charge_level < charge_setpoint:
                print('IDLE -> QUICKCHARGE')
                return QuickchargeState(self._test_box_half)
            else:
                print('IDLE -> QUICKDISCHARGE')
                return QuickdischargeState(self._test_box_half)
        # default
        return self


class PrechargeState(State):
    def __init__(
        self,
        test_box_half: TestBoxHalf = None,
    ):
        super().__init__(test_box_half)
        self._retries = 3
        self._test_box_half.gpio.charge_enable = True
        self._test_box_half.gas_gauge.control_init()

    name = States.PRECHARGE.value

    def do(self):
        gas_gauge = self._test_box_half.gas_gauge.get_all()
        print(gas_gauge)

    def next(self, flag = None):
        if self._retries == 0:
            if self._test_box_half.gas_gauge.voltage_mV > 10000:
                self._test_box_half.gpio.charge_enable = False
                print('PRECHARGE -> CHARGE_TEST')
                return ChargeTestState(self._test_box_half)
            else:
                return ErrorState(
                    self._test_box_half,
                    'battery not found')
        else:
                self._retries -= 1
                return self


class PretestState(State):
    def __init__(
        self,
        test_box_half: TestBoxHalf = None,
    ):
        super().__init__(test_box_half)
        self._test_box_half.gpio.discharge_enable = True

    name = States.PRETEST.value

    def do(self):
        # self._test_box_half.gas_gauge.control_init()
        gas_gauge = self._test_box_half.gas_gauge.get_all()
        print(gas_gauge)

    def next(self, flag = None):
        if flag == Flags.STOP:
            print('PRETEST stopped')
            self._test_box_half.gpio.charge_enable = False
            return IdleState(self._test_box_half)
        elif self._test_box_half.gas_gauge.voltage_mV < 10000:
            print('PRETEST -> CHARGE_TEST')
            self._test_box_half.gpio.discharge_enable = False
            return ChargeTestState(self._test_box_half)
        return self

class ChargeTestState(LogState):
    def __init__(
        self,
        test_box_half: TestBoxHalf = None,
    ):
        super().__init__(test_box_half)
        self._test_box_half.gas_gauge.control_init()
        self._test_box_half.gas_gauge.charge_init()
        self._test_box_half.gpio.charge_enable = True

    def do(self):
        super().do()        

    def next(self, flag = None):
        if flag == Flags.STOP:
            print('CHARGE_TEST stopped')
            self._test_box_half.gpio.charge_enable = False
            return IdleState(self._test_box_half)
        if self._test_box_half.gas_gauge.charge_level >= 100:
            print('CHARGE_TEST -> DISCHARGE_TEST')
            self._test_box_half.gpio.charge_enable = False
            return DischargeTestState(self._test_box_half)
        return self

class DischargeTestState(LogState):
    def __init__(
        self,
        test_box_half: TestBoxHalf = None,
    ):
        super().__init__(test_box_half)
        self._test_box_half.gpio.discharge_enable = True

    def do(self):
        super().do()  

    def next(self, flag = None):
        if flag == Flags.STOP:
            print('DISCHARGE_TEST stopped')
            self._test_box_half.gpio.dicharge_enable = False
            return IdleState(self._test_box_half)
        elif self._test_box_half.gas_gauge.voltage_mV < 10000:
            print('DISCHARGE_TEST -> POSTTEST')
            self._test_box_half.gpio.discharge_enable = False
            return PostTestState(self._test_box_half)
        return self

class QuickchargeState(LogState):
    def __init__(
        self,
        test_box_half: TestBoxHalf = None,
    ):
        super().__init__(test_box_half)
        self._test_box_half.gas_gauge.control_init()
        self._test_box_half.gpio.charge_enable = True

    def next(self, flag = None):
        global charge_setpoint

        if flag == Flags.STOP:
            print('QUICKCHARGE stopped')
            self._test_box_half.gpio.charge_enable = False
            return IdleState(self._test_box_half)
        elif self._test_box_half.gas_gauge.charge_level >= charge_setpoint:
            print('QUICKCHARGE done')
            self._test_box_half.gpio.charge_enable = False
            return IdleState(self._test_box_half)

        return self


class QuickdischargeState(LogState):
    def __init__(
        self,
        test_box_half: TestBoxHalf = None,
    ):
        super().__init__(test_box_half)
        self._test_box_half.gas_gauge.control_init()
        self._test_box_half.gpio.discharge_enable = True

    def next(self, flag = None):
        global charge_setpoint

        if flag == Flags.STOP:
            print('QUICKCHARGE stopped')
            self._test_box_half.gpio.discharge_enable = False
            return IdleState(self._test_box_half)
        elif self._test_box_half.gas_gauge.charge_level <= charge_setpoint:
            print('QUICKCHARGE done')
            self._test_box_half.gpio.discharge_enable = False
            return IdleState(self._test_box_half)

        return self

class PostTestState(State):
    def __init__(
        self,
        test_box_half: TestBoxHalf = None,
    ):
        super().__init__(test_box_half)
        self._test_box_half.gas_gauge.control_init()
        self._test_box_half.gpio.charge_enable = True

    def do(self):
        gas_gauge = self._test_box_half.gas_gauge.get_all()
        print(gas_gauge)

    def next(self, flag = None):
        if flag == Flags.STOP:
            print('CHARGE_TEST stopped')
            self._test_box_half.gpio.charge_enable = False
            return IdleState(self._test_box_half)
        if self._test_box_half.gas_gauge.voltage_mV > 12500:
            print('TEST DONE')
            self._test_box_half.gpio.charge_enable = False
            return IdleState(self._test_box_half)
        return self

# class State(State):
#     name = States.PRECHARGE.value
