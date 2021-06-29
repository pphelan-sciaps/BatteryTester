# standard library
from enum import IntEnum
from cmd import Cmd
from datetime import datetime

# external packages

# internal packages
from .I2C import I2C, I2CError
from .I2C import RegisterMap
from .I2C import Register
from .I2C import uint8_to_uint, uint_to_uint8
from .ConnectionManager import ConnectionManager

class LTC2943(object):
    # constants
    # full scale register values from datasheet
    Q_SCALE = 0.340 * 50.0 / 4096.0 # mAh * mohm/max prescaler (what the hell is a mVh?)
    BATTERY_CAPACITY_mAh = 3500 
    CHARGE_FS = 100.0
    V_BAT_FS = 23.6
    V_SENSE_FS_mV = 60.0

    def __init__(
        self,
        i2c: I2C = None,
        address: int = 0x64,
        r_sense_mohm: float = 5.0,
        prescaler: int = 64):
        ''''''

        self._i2c = i2c
        self._address = address
        self._r_sense_mohm = 5.0
        self._prescaler = prescaler

        registers = [
            Register(0x00, 'r',  1, 0x00), # status
            Register(0x01, 'rw', 1, 0x3C), # control
            Register(0x02, 'rw', 1, 0x7F), # charge msb
            Register(0x03, 'rw', 1, 0xFF), # charge lsb
            Register(0x08, 'r',  1, 0x00), # voltage msb
            Register(0x09, 'r',  1, 0x00), # voltage lsb
            Register(0x0E, 'r',  1, 0x00), # current msb
            Register(0x0F, 'r',  1, 0x00), # current lsb
            Register(0x14, 'r',  1, 0x00), # temperature msb
            Register(0x15, 'r',  1, 0x00)  # temperature lsb
        ]
        self._reg_map = RegisterMap(
            i2c = self._i2c,
            address = self._address,
            registers=registers)
        

    # API
    # 0x00
    @property
    def status_reg(self):
        return self._reg_map.read_reg(0x00)

    @property
    def overflow(self):
        return self._reg_map.read_bit(0x00, 5)

    # TODO Register indexing
    # @property
    # def current_alert(self):
    #     return self._reg_map['0x00'][6]

    # @property
    # def charge_overflow_alert(self):
    #     return self._reg_map['0x00'][5]

    # @property
    # def temp_alert(self):
    #     return self._reg_map['0x00'][4]

    # @property
    # def charge_high_alert(self):
    #     return self._reg_map['0x00'][3]

    # @property
    # def charge_low_alert(self):
    #     return self._reg_map['0x00'][2]

    # @property
    # def voltage_alert(self):
    #     return self._reg_map['0x00'][1]

    # @property
    # def uvlo_alert(self):
    #     return self._reg_map['0x00'][3]

    # 0x01
    @property
    def config_reg(self):
        return self._reg_map.read_reg(0x01)

    @config_reg.setter
    def config_reg(self, word: int):
        self._reg_map.write_reg(0x01, word)

    # TODO Register indexing
    # @property
    # def adc_mode(self):
    #     reg_val = int(self._reg_map['0x01'].value,0)
    #     reg_val = (reg_val & 0xC0) >> 6
    #     return reg_val

    # @adc_mode.setter
    # def adc_mode(self, mode: ADCMode):

    # @property
    # def prescaler(self):
    #     return self._prescaler

    @property
    def charge(self):
        charge = {}
        msb = self._reg_map.read_reg(0x02)
        lsb = self._reg_map.read_reg(0x03)

        try:
            reg_value = uint8_to_uint(msb,lsb)
            q_lsb =  self.Q_SCALE * self._prescaler / self._r_sense_mohm
            battery_capacity = q_lsb * 0xFFFF
            charge['reg'] = reg_value
            charge['mAh'] = q_lsb * reg_value 
            charge['level'] = 100 * reg_value / 0xFFFF
        except TypeError as e:
            # charge = None
            print('comm err')
        
        return charge

    @charge.setter
    def charge(self, charge_lsbs):
        if charge_lsbs > 0xFFFF or charge_lsbs < 0:
            raise GasGaugeError(f'invalid charge value: {charge_lsbs} ({hex(charge_lsbs)}')
        else:
            msb, lsb = uint_to_uint8(charge_lsbs)
            self._reg_map.write_reg(0x02,msb,retries=5)
            self._reg_map.write_reg(0x03,lsb,retries=5)

    @property
    def charge_register(self):
        charge = self.charge
        if charge:
            return charge['reg']

    @property
    def charge_mAh(self):
        charge = self.charge
        if charge:
            return charge['mAh']

    @property
    def charge_level(self):
        charge = self.charge
        if charge:
            return charge['level']

    # @property
    # pass
    
    
    @property
    def voltage_mV(self):
        try:
            msb = self._reg_map.read_reg(0x08)
            lsb = self._reg_map.read_reg(0x09)
            reg_value = uint8_to_uint(msb,lsb)
            voltage = 1000 * self.V_BAT_FS * reg_value / 0xFFFF # register to voltage 
        except TypeError as e:
            voltage = None 
        
        return voltage

    @property
    def current_mA(self):
        msb = self._reg_map.read_reg(0x0E)
        lsb = self._reg_map.read_reg(0x0F)
        try:
            reg_value = uint8_to_uint(msb,lsb)
            i_bat_fs = self.V_SENSE_FS_mV / self._r_sense_mohm   # full scale current
            current = 1000 * i_bat_fs * (reg_value - 0x7FFF) / 0x7FFF   # reg to current
        except TypeError as e:
            current = None
        
        return current

    def control_init(self):
        self._reg_map.write_reg(0x01,0b10011010)
        _ = self.voltage_mV

    def control_auto(self):
        self._reg_map.write_reg(0x01,0b11011010)
        _ = self.voltage_mV

    def charge_init(self):
        self._reg_map.write_reg(0x02,0x19)  # the calibrated '0' point
        self._reg_map.write_reg(0x03,0x99)

    def get_all(self) -> dict:
        result = {
            'bat_timestamp'     : datetime.now(),
            'bat_timestamp_ms'  : 0,
            'bat_voltage_mV'    : self.voltage_mV,
            'bat_current_mA'    : self.current_mA,
            'bat_charge_mAh'    : self.charge_mAh,
            'bat_charge_level'  : self.charge_level,
            'bat_temp_C'        : 0
        }

        return result

    def __str__(self):
        if self.charge:
            return f'{datetime.now().strftime("%H:%M:%S")}\n'\
                f'charge: {self.charge["mAh"]:.0f} mAh '\
                    f'({self.charge["level"]:.1f}%)\n'\
                f'voltage: {self.voltage_mV:.0f} mV\n'\
                f'current: {self.current_mA:.0f} mA'
        else:
            return 'no battery connected'

class GasGaugeError(Exception):
    pass

# helper classes
class ADCMode(IntEnum):
    SLEEP = 0
    MANUAL = 1
    SCAN = 2
    AUTOMATIC = 3

# demo command line app
class DemoApp(Cmd):
    intro = 'LTC2943 demo app.  Type help or ? to list commands.\n'
    prompt = '(LTC2943) '

    def do_get_device_locations(self,args):
        print(self.conn_man.device_locations)

    def do_open_idx(self,args):
        args_list = args.split()
        idx = int(args_list[0],0)
        i2c = self.conn_man.open_connection(idx)
        self.ltc2943 = LTC2943(i2c=i2c)

    def do_read_v(self,args):
        pass

    def __init__(self):
        self.conn_man = ConnectionManager()
        self.ltc2943 = None
