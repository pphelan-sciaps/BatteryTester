'''
'''

# standard library
import logging

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
        address: int = 0x27
    ):
        self.logger = logging.getLogger('batman.TestBoxIF.GPIO.GPIO')

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
        try:
            self._reg_map.write_all()
        except:
            print('unable to write registers')

    def __del__(self):
        #disable all outputs
        outputs = [
            self.charge_enable,
            self.discharge_enable,
            self.led_error_enable,
            self.led_done_enable,
            self.led_run_enable
        ]
        
        for output in outputs:
            try:
                output = False
            except I2CError:
                pass

    # API
    @property
    def address(self):
        return self._address

    @property
    def input_port_word(self, port_num: int):
        if port_num == 0:
            return self._reg_map.read_reg(reg_addr=0x0, retries=3)
        elif port_num == 1:
            return self._reg_map.read_reg(reg_addr=0x1, retries=3)
        else:
            raise GPIOError('invalid input port')

    @property
    def output_port_word(self, port_num: int):
        if port_num == 0:
            return self._reg_map.read_reg(reg_addr=0x2, retries=3)
        elif port_num == 1:
            return self._reg_map.read_reg(reg_addr=0x3, retries=3)
        else:
            raise GPIOError('invalid output port')

    @property
    def battery_present(self):
        '''input for detecting inserted battery
        '''
        bat = not self._reg_map.read_bit(reg_addr=0x0, bit_num=7, retries=3)
        self.logger.info(f'get battery_present: {bat}')
        return bat

    @property
    def charge_enable(self):
        '''output for enabling battery charging
        '''
        ce = self._reg_map.read_bit(reg_addr=0x3, bit_num=0, retries=3)
        self.logger.info(f'get charge_enable: {ce}')
        return ce


    @charge_enable.setter
    def charge_enable(self,enable):
        if self.discharge_enable and enable:
            raise GPIOError('cannot enable charge during discharge')
        else:
            self._reg_map.write_bit(
                reg_addr=0x3,
                bit_num=0,
                value=enable,
                retries=3)
            self.logger.info(f'set charge_enable: {enable}')

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
        de = self._reg_map.read_bit(reg_addr=0x2,bit_num=0,retries=3)
        self.logger.info(f'get discharge_enable: {de}')
        return de

    @discharge_enable.setter
    def discharge_enable(self, enable: bool):
        if self.charge_enable and enable:
            raise GPIOError('cannot enable discharge during charge')
        else:
            self._reg_map.write_bit(reg_addr=0x2,bit_num=0,value=enable,retries=3)
            self.logger.info(f'set discharge_enable: {enable}')

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
    def led_run_enable(self):
        '''output for enabling run indication led
        '''
        return self._reg_map.read_bit(reg_addr=0x3,bit_num=2,retries=3)

    @led_run_enable.setter
    def led_run_enable(self, enable: int):
        self._reg_map.write_bit(reg_addr=0x3,bit_num=2,value=enable,retries=3) 

    @property
    def led_done_enable(self) -> int:
        '''output for enabling run indication led
        '''
        return self._reg_map.read_bit(reg_addr=0x3,bit_num=3,retries=3)

    @led_done_enable.setter
    def led_done_enable(self,enable: int):
        self._reg_map.write_bit(reg_addr=0x3,bit_num=3,value=enable,retries=3) 

    @property
    def led_error_enable(self):
        return self._reg_map.read_bit(reg_addr=0x3,bit_num=1,retries=3)

    @led_error_enable.setter
    def led_error_enable(self,enable):
        self._reg_map.write_bit(reg_addr=0x3,bit_num=1,value=enable,retries=3)


class GPIOError(Exception):
    pass