'''
'''

# standard library

# external pakcages

# internal
from .I2C import I2C
from .I2C import RegisterMap
from .I2C import Register
from .I2C import uint8_to_uint
# from .TCA9555 import TCA9555


reg_init_dict = {}

class GPIO(object):
    """docstring for GPIO"""
    def __init__(
        self,
        i2c: I2C = None,
        address: int = 0x27):
        # self.tca9555 = TCA9555(i2c=i2c, address=address)
        self._i2c = i2c
        self._address = address

        registers = [
            Register(0x00, 'r',  1, 0x00),
            Register(0x01, 'r',  1, 0x00),
            Register(0x02, 'rw', 1, 0x00),
            Register(0x03, 'rw', 1, 0x00),
            Register(0x04, 'rw', 1, 0x00),
            Register(0x05, 'rw', 1, 0x00),
            Register(0x06, 'rw', 1, 0xDA),
            Register(0x07, 'rw', 1, 0xF0)
        ]

        self._reg_map = RegisterMap(
            i2c = self._i2c,
            address = self._address,
            registers = registers)

        self._reg_map.write_all()

    def __del__(self):
        self.charge_enable = False
        self.discharge_enable = False
    
    # API
    @property
    def address(self):
        return self._address

    @property
    def input_port_word(self, port_num: int):
        if port_num == 0:
            return self._reg_map.read_reg(0x0)
        elif port_num == 1:
            return self._reg_map.read_reg(0x1)
        else:
            raise GPIOError('invalid input port')

    @property
    def output_port_word(self, port_num: int):
        if port_num == 0:
            return self._reg_map.read_reg(0x2)
        elif port_num == 1:
            return self._reg_map.read_reg(0x3)
        else:
            raise GPIOError('invalid output port')

    @property
    def battery_present(self):
        '''input for detecting inserted battery
        '''
        return not self._reg_map.read_bit(reg_addr=0x0,bit_num=7)

    @property
    def charge_enable(self):
        '''output for enabling battery charging
        '''
        return self._reg_map.read_bit(reg_addr=0x3,bit_num=0)

    @charge_enable.setter
    def charge_enable(self,enable):
        if self.discharge_enable and enable:
            raise GPIOError('cannot enable charge during discharge')
        else:
            self._reg_map.write_bit(reg_addr=0x3,bit_num=0,value=enable)

    # TODO
    # @property
    # def charge_sw_alert(self):
    #     '''input for detecting charge switch alert
    #     '''
    #     return self.tca9555.read_input_port_bit(port=0,bit=1)

    # @property
    # def charge_dmm_alert(self):
    #     '''input for detecting charge dmm alert
    #     '''
    #     return self.tca9555.read_input_port_bit(port=0,bit=4)

    # @property
    # def charge_sw_diag_en(self):
    #     '''output for enabling charge switch alerts
    #     '''
    #     return self.tca9555.read_output_port_bit(port=0,bit=2)

    # @charge_sw_diag_en.setter
    # def charge_sw_diag_en(self, enable: bool):
    #     if enable:
    #         self.tca9555.set_output_port_bit(port=0,bit=2)
    #     else:
    #         self.tca9555.clear_output_port_bit(port=0,bit=2)


    @property
    def discharge_enable(self):
        '''output for enabling battery discharge
        '''
        return self._reg_map.read_bit(reg_addr=0x2,bit_num=0)

    @discharge_enable.setter
    def discharge_enable(self, enable: bool):
        if self.charge_enable and enable:
            raise GPIOError('cannot enable discharge during charge')
        else:
            self._reg_map.write_bit(reg_addr=0x2,bit_num=0,value=enable)

    # TODO
    # @property
    # def discharge_sw_alert(self):
    #     '''input for detecting discharge switch alert
    #     '''
    #     return self.tca9555.read_input_port_bit(port=0,bit=6)

    # @property
    # def discharge_dmm_alert(self):
    #     '''input for detecting charge switch alert
    #     '''
    #     return self.tca9555.read_input_port_bit(port=0,bit=3)

    # @property
    # def discharge_diag_en(self):
    #     '''output for enabling charge switch alerts
    #     '''
    #     return self.tca9555.read_output_port_bit(port=0,bit=2)

    # @discharge_diag_en.setter
    # def discharge_diag_en(self,enable):
    #     if enable:
    #         self.tca9555.set_output_port_bit(port=0,bit=2)
    #     else:
    #         self.tca9555.clear_output_port_bit(port=0,bit=2)    
    
    @property
    def led_run_enable(self,enable: int):
        '''output for enabling run indication led
        '''
        return self._reg_map.read_bit(reg_addr=0x3,bit_num=2)

    @led_run_enable.setter
    def led_run_enable(self, enable: int):
        self._reg_map.write_bit(reg_addr=0x3,bit_num=2,value=enable) 

    @property
    def led_done_enable(self) -> int:
        '''output for enabling run indication led
        '''
        return self._reg_map.read_bit(reg_addr=0x3,bit_num=3)

    @led_done_enable.setter
    def led_done_enable(self,enable: int):
        self._reg_map.write_bit(reg_addr=0x3,bit_num=3,value=enable) 

    @property
    def led_error_enable(self):
        return self._reg_map.read_bit(reg_addr=0x3,bit_num=1)

    @led_error_enable.setter
    def led_error_enable(self,enable):
        self._reg_map.write_bit(reg_addr=0x3,bit_num=1,value=enable)
    
class GPIOError(Exception):
    pass